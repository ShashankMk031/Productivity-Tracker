# PROJECT_REVIEW.md

> Full repository audit — Phase 1 of the hardening program.
> Scope: inspection, analysis, documentation only. No application behavior was modified.

---

# Architecture Overview

## Frontend Structure

- **Stack**: Vanilla JS (ES modules), no framework, no build step. 4 HTML pages served directly by FastAPI (`index.html`, `reports.html`, `calendar.html`, `settings.html`).
- **Modules** (`frontend/js/`):
  - `app.js` (600 lines) — main controller: monthly habit matrix, task CRUD, notes, schedule drafts, archive. Holds a single mutable `state` object.
  - `productivity_os.js` (436 lines) — Phase 5A core: focus sessions, reminders (60s polling daemon), scores (30s polling), browser notifications.
  - `insights.js` — renders the intelligence dashboard cards from `/api/intelligence/dashboard`.
  - `api.js`, `ui.js`, `date.js`, `schedule.js` — API client, modal/toast helpers, IST logical-date logic, schedule presets.
  - `goals.js`, `projects.js`, `reports.js`, `reports_dashboard.js`, `calendar.js`, `settings.js` — per-page feature modules.
- **Styling**: `style.css` + `strategic.css`, dark GitHub-style theme.
- **Pattern**: Effectively a hybrid — one heavy main page (habit grid + Productivity OS widgets + insights) plus secondary pages. Navigation between pages is ad hoc.

## Backend Structure

- **Stack**: FastAPI 0.111 + SQLite (stdlib `sqlite3`, raw SQL, no ORM). Only 2 pinned dependencies (`fastapi`, `uvicorn`).
- **Entry point**: `backend/main.py` — mounts 9 routers under `/api`, serves frontend pages, serves `ai_reports/` files. Startup hook runs migrations, `init_db()`, integrity check, and report audit (which can synchronously call external AI APIs — see risks).
- **Layers**:
  - `routes/` — tasks, reports, goals, projects, scores, focus, reminders, intelligence, settings.
  - `services/` — 16 services (task, goal, project, focus, reminder, scoring, analytics, countdown, date, logging, backup, integrity, report_service, report_history, report_audit, report_scheduler).
  - `analytics/` — metrics, streaks, charts.
  - `schemas/` — Pydantic request/response models + `APIResponse` envelope.
  - `database/` — `db.py` (connection + ad-hoc schema patches), `db_migrations.py` (Phase 5A tables), `queries.py`.
  - `utils/` — helpers, timezone.

## Services

- **Domain CRUD**: `task_service`, `goal_service`, `project_service`, `focus_service`, `reminder_service`.
- **Derived metrics**: `analytics_service` (aggregation), `scoring_service` (3 weighted 0–100 scores: consistency, execution, goal progress), `countdown_service` (deadline urgency RED/YELLOW/GREEN).
- **Platform**: `date_service` (IST "logical date" — hardcoded timezone), `logging_service` (file-based critical/error logs), `backup_service` (zip archives of 6 data dirs), `integrity_service` (self-healing dirs, orphan detection, report-file mismatch detection).

## AI Layer (`backend/ai/`)

Pipeline: **context_builder → prompt_builder → ai_service**

1. `context_builder.build_ai_context()` aggregates analytics, keyword-based note analysis (`note_analysis.py`, 7 categories with word-boundary regex), behavioral summary, goals, projects+milestones, focus/reminder stats, productivity scores, a full intelligence snapshot, and prediction accuracy into a Pydantic `AIContextPackage`.
2. `prompt_builder.build_ai_prompt()` renders one large markdown prompt with mandated section headings (different sets for weekly/monthly), coaching directives, and **two raw JSON blobs** (intelligence snapshot + prediction accuracy) appended verbatim.
3. `ai_service.AIService` calls Gemini (default) or OpenAI via raw `urllib.request` (20s timeout, no retries), with provider fallback and graceful degradation to a warning string. Hand-rolled `.env` parser mutates `os.environ`.

## Report Pipeline

- **Single real implementation**: `report_history_service.generate_and_save_report()` does everything: saves an intelligence snapshot → (monthly only) pre-generation backup → aggregates analytics → builds AI context + prompt → calls AI → writes 4+ artifacts to disk (`reports/YYYY/Month/*.md`, `ai_context/YYYY/*.json` + `*.txt` prompt, `ai_reports/YYYY/Month/*.txt`) → inserts a `reports` row.
- **Triggers**: `/api/reports/generate` (legacy weekly), `/api/reports/smart-generate?type=`, and `report_audit_service.run_report_audit()` at startup, which auto-generates any missing weekly/monthly report for the last completed cycles.
- **Retrieval**: DB stores only metadata + `markdown_path`; markdown and AI reflection are re-read from disk. `get_report_ai_reflection()` reverse-engineers the AI response filename from the markdown path (fragile string surgery).

## Intelligence Layer (`backend/intelligence/`)

- `prediction_engine.generate_intelligence_snapshot()` composes 5 predictors: `burnout_detector` (keyword fatigue scan + focus decline + missed-task deltas over 14/30-day windows), `consistency_predictor`, `deadline_forecaster`, `focus_analyzer`, and inline `forecast_goals()` (velocity vs. days-remaining).
- All predictors return a uniform shape: `risk_level`, `warning_level`, `reason`, `supporting_metrics`, `confidence` — good explainability foundation.
- `snapshot_service.save_snapshot()` persists snapshots to `intelligence_snapshots/YYYY/Month/*.json`; `get_latest_snapshot()` actually regenerates live (name is misleading).
- `prediction_accuracy.evaluate_prediction_accuracy()` loads ~1-week-old snapshot from the filesystem and compares **deadline predictions only** against current project state.

## Storage Layout

SQLite DB (`database/tracker.db`) + 6 loose filesystem trees: `reports/`, `ai_reports/`, `ai_context/`, `intelligence_snapshots/`, `backups/`, `logs/`. The DB is the index; files are the payload. This split is the root of several integrity and portability risks below.

---

# Technical Debt, Duplicate Code, Dead Code, Fragile Areas, Architectural Risks

## HIGH

1. **Zero automated tests.** No test framework, no CI. The only `test_*` file (`backend/test_error.py`) is a debug script that runs the report audit (and would call live AI APIs) — it is dead code, not a test.
2. **Schema management fragmentation.** Three competing mechanisms with no version tracking:
   - `database/init.sql` (executescript on every startup),
   - `db.py: ensure_schema()` / `ensure_project_schema()` (ad-hoc ALTERs),
   - `db_migrations.py: run_migrations()` (Phase 5A tables, opens its own raw connection without `foreign_keys=ON`).
   Adding a column currently requires guessing which of the three places to touch.
3. **Destructive backup restore.** `backup_service.restore_from_backup()` does `shutil.rmtree()` on live directories — including `database/` while the SQLite file may be open by the running app — *before* copying restored data. A failed copy mid-loop leaves the system partially destroyed. No pre-restore safety backup, no archive validation, no integrity verification, no atomic swap. The restore endpoint also accepts an arbitrary filesystem `path` parameter (path traversal: any zip on disk can be "restored").
4. **Startup performs network calls and heavy writes.** `main.py` startup → `run_report_audit()` → `generate_and_save_report()` → live Gemini/OpenAI calls + multi-file writes. A missing report or slow provider delays/blocks app startup. Also uses deprecated `@app.on_event("startup")` instead of lifespan handlers.
5. **Prediction accuracy is deadline-only and fragile** (details in Prediction System Review).

## MEDIUM

6. **Dead/duplicate report code.** `report_scheduler_service.check_report_status()` is bypassed — `/api/reports/status` hardcodes `can_generate: True`. `report_service.py` is a 7-line vestigial wrapper around `aggregate_analytics`. The "report already exists" branch is copy-pasted between `/generate` and `/smart-generate` in `routes/reports.py`.
7. **`settings.py /storage` checks the wrong DB filename** — `database/productivity.db` instead of `tracker.db`, so reported DB size is always 0. Symptom of path constants being re-derived in 6+ files (`BASE_DIR = Path(__file__).parent.parent.parent` everywhere) instead of one config module.
8. **Snapshot filename timestamps are broken.** `snapshot_service.save_snapshot()` calls `now.strftime("%Y%m%d_%H%M%S")` on a *date* (from `get_logical_date_ist()`), so `%H%M%S` renders `000000` — same-day snapshots of the same type overwrite each other, silently truncating prediction history.
9. **Prediction accuracy matches projects by title**, not ID. Renaming a project silently breaks historical evaluation.
10. **Hardcoded IST timezone** baked into `date_service` and frontend `date.js` — a desktop app shipped to any other timezone misbehaves.
11. **AI config fragility.** Hand-rolled `.env` parser mutates `os.environ`; default Gemini model is `"gemini-3.5-flash"` (not a real model name — works only if overridden in `.env`); no retry/backoff; `AIService` instantiated per-report.
12. **CORS `allow_origins=["*"]`** — acceptable for localhost-only use, wrong default for packaging.
13. **N+1 queries** in `scoring_service` (per-task daily-entry lookup for today's completion) and similar per-row patterns in project serialization.

## LOW

14. `print()`-based logging everywhere; `logging_service` exists but only handles critical/error file logs. No log levels, no rotation policy coordination.
15. Inline `import` statements scattered mid-function (`routes/reports.py`, `context_builder.py`, `report_history_service.py`).
16. `frontend/js/app.js` at 600 lines mixes state, rendering, and event wiring; `productivity_os.js` polls two intervals (60s + 30s) permanently.
17. `integrity_service` detects orphan milestones but the auto-cleanup is commented out — detection without remediation.
18. Unused imports (`Depends` in routes, `re` in `burnout_detector`, `Optional` in `ai_service`).
19. Emoji-laden console output (`✓`, `❌`) in server logs.

---

# Missing Tests (Critical Untested Paths)

There are **no tests at all**. Highest-value gaps, in order:

1. **Report workflows** — `generate_and_save_report()` (period math: "Sunday of previous week", "last day of previous month"; file layout; DB row insertion; AI-failure fallback path), `run_report_audit()` idempotency (must not double-generate), duplicate-report short-circuit in routes.
2. **AI workflows** — `build_ai_context()` against a seeded in-memory DB (empty DB, missing tables, period filtering); `build_ai_prompt()` section contract for weekly vs monthly; `AIService.generate_reflection()` provider fallback ordering and graceful-degradation string (HTTP mocked).
3. **Backup workflows** — `create_backup()` archive contents; `restore_from_backup()` (currently dangerous — tests must precede the rewrite); `get_available_backups()` sorting.
4. **Prediction workflows** — each predictor against synthetic fixtures (burnout keyword deltas, goal velocity edge cases: `days_elapsed=0`, passed target dates, `pct_per_day=0`); `evaluate_prediction_accuracy()` outcome matrix (on-time/late/missed/pending × predicted risk).
5. **Domain CRUD** — goals, projects+milestones (cascade delete), tasks (active_days schedule logic), scoring formula bounds (0–100 clamping, empty-DB 100% defaults — note: empty goals table yields a perfect goal-progress score, which is itself questionable behavior worth pinning in a test).
6. **Integrity & date logic** — `run_integrity_check()` orphan/missing-file detection; `date_service` logical-date boundaries (the IST day-rollover rule).

Infrastructure needed: `pytest`, in-memory/temp SQLite fixture, temp-dir patching for the 6 artifact directories, HTTP mocking for AI calls. No app refactor required to start — services already accept a `db` connection.

---

# Database Architecture Review

## Schema Weaknesses

- **No schema version table.** Three uncoordinated mechanisms (see HIGH #2). `init.sql` is missing the Phase 5A tables (`focus_sessions`, `reminders`), which only exist via `db_migrations.py` — a fresh checkout depends on execution order.
- `reports.markdown_path` stores **absolute paths** — breaks on machine migration, directory rename, or desktop packaging (per-user data dirs). Should be relative.
- No CHECK constraints (`progress` 0–100, `type IN ('weekly','monthly')`, urgency enums).
- `daily_entries.note` doubles as behavioral corpus — fine, but there is no FTS index if note search is ever needed.
- `goals.target_date`/`projects.deadline` are free-text ISO strings parsed with `datetime.fromisoformat` in multiple places with inconsistent error handling (goal forecaster swallows `ValueError`; deadline accuracy does not).

## Indexing Opportunities

Existing: `daily_entries(task_id, date)`, `daily_entries(date)` — good, they cover the hottest paths. Missing:

- `focus_sessions(start_time)` — every analytics/burnout/report query filters on it.
- `reminders(datetime)` and `reminders(completed, datetime)` — polled every 60s by the frontend daemon.
- `reports(type, period_end)` — the existence check before every generation.
- `projects(completed, deadline)` — forecaster and countdown scans.

At personal-tracker scale none of these are urgent, but they are free wins and matter as `daily_entries` grows over years.

## Performance Concerns

- Connection-per-request via context manager is fine for single-user; no WAL mode is set — enabling `PRAGMA journal_mode=WAL` would improve resilience to the concurrent startup writes (audit + integrity + migrations).
- `executescript(init.sql)` on every startup is wasteful but harmless today; it becomes a liability once real migrations exist.
- N+1 in `scoring_service` (called every 30s by frontend polling) — batchable into one query.
- `get_dir_size()` walks entire artifact trees on every `/settings/storage` call.

---

# AI System Review

## Prompt Quality — Good

The prompt (`prompt_builder.py`) is genuinely well-designed: mandated exact section headings per report type, "note-backed priority" directive, anti-fluff rules, explicit "do not guess, use these statistical outputs" instruction for predictions, and a no-preamble output contract. This is above-average prompt engineering for a personal project.

## Context Quality — Good Foundation, Two Gaps

- Note analysis is keyword/regex-based (7 categories) — robust and cheap, but excerpts are capped at 5 per category with no recency or severity weighting; a month with 100 notes and a week with 3 produce the same-shaped context.
- **`aggregate_analytics(db)` and `generate_behavioral_summary(db)` are not period-scoped** — weekly reports embed all-time stats labeled as if they describe the period. Focus/reminder stats *are* period-filtered. This inconsistency can mislead the model (and the user).

## Token Efficiency — The Main Weakness

- Sections 6 and 7 dump the **entire intelligence snapshot and accuracy evaluation as raw indented JSON**, including `generated_at`, `prediction_version`, verbose `supporting_metrics`, and repeated keys. This is the single largest token cost and the least information-dense part of the prompt.
- No token budgeting anywhere: unbounded goals/projects/milestones lists, full note text in excerpts.
- **Fix**: render predictions as compact markdown lines (`- Burnout: MEDIUM (75% conf) — focus duration down 34%`) via a summarization layer between snapshot and prompt. Estimated 40–60% reduction in prediction-section tokens with zero information loss for the model's purpose.

## Report Usefulness

- Structure is excellent (forced sections make weekly/monthly reports comparable over time).
- Risk: when both providers fail, the warning string is embedded into a *persisted* report markdown and the report row is still created — the failed report then blocks regeneration via the "already exists" check. There is no regenerate/repair path.

## Suggested Improvements (priority order)

1. Summarized prediction/context rendering instead of raw JSON (token efficiency).
2. Period-scope analytics and behavioral summary to the report window.
3. Regeneration path for reports whose AI section failed.
4. Retry-with-backoff (1 retry is enough) before provider fallback; fix the fictional default Gemini model name.
5. Adopt `python-dotenv` or at minimum stop mutating `os.environ`.

---

# Prediction System Review

## Explainability — Strong

Uniform output contract (`risk_level`, `warning_level`, `reason`, `supporting_metrics`, `confidence`) across all 5 predictors, with human-readable reasons ("Fatigue mentions increased (1 → 4)"). This is the system's best architectural decision.

## Confidence Scores — Cosmetic

Confidence values are hardcoded tiers (85/75/65/90) or naive formulas (`min(85, 40 + days_elapsed * 2)`). They are not derived from data quality, sample size, or historical accuracy, and are never calibrated against outcomes. They communicate false precision.

## Prediction Accuracy Tracking — The Weakest Subsystem

- **Only deadline predictions are evaluated.** Burnout, goal, consistency, and focus forecasts are generated, persisted, shown to the user, and fed to the AI — but never scored.
- Snapshot selection is brittle: it looks in the *calendar-month folder of one week ago* and takes the last file by name sort — not the snapshot closest to 7 days old.
- Matches projects by **title** (rename = silent evaluation loss).
- Same-day snapshots overwrite each other due to the `%H%M%S`-on-a-date bug (MEDIUM #8), destroying the very history this system needs.
- Results are not aggregated (no rolling precision/recall per predictor) and never feed back into confidence values.

## Future Improvements

1. Persist predictions in a `predictions` table (predictor, target_id, predicted risk, created_at) instead of filesystem JSON archaeology — evaluation becomes a SQL join.
2. Expand evaluation to all predictor types with per-type outcome definitions (burnout: did completion/focus actually collapse in the following 14 days? goals: did the goal hit its target date? consistency: predicted vs. actual completion rate).
3. Calibrate confidence from rolling historical accuracy per predictor.
4. Track accuracy by ID, not title.
5. Fix snapshot timestamping (use real datetime).

---

# Overall Health Summary

| Area | Grade | Notes |
|---|---|---|
| Architecture/layering | B+ | Clean route→service split, uniform predictor contract |
| Schema management | D | Three competing mechanisms, no versioning |
| Data safety (backup/restore) | D- | Restore can destroy live data |
| Test coverage | F | Zero tests |
| AI pipeline | B | Strong prompts, weak token economy & period scoping |
| Intelligence layer | B- | Great explainability, accuracy tracking ~20% built |
| Frontend | C+ | Functional, growing monoliths, polling-heavy |
| Desktop-packaging readiness | Not ready | Absolute paths, IST hardcoding, startup network calls, restore safety |
