# TODO_TECHNICAL_DEBT.md

Actionable checklist derived from `PROJECT_REVIEW.md`. Ordering within each tier is recommended execution order.

---

## Critical

- [ ] **Rewrite `backup_service.restore_from_backup()`** — sequence: backup current state → validate zip (test extraction, expected members) → extract to temp → verify (DB opens, `PRAGMA integrity_check`) → atomic swap (rename old aside, move new in) → keep the safety copy. Never `rmtree` live data first. Remove/validate the arbitrary `path` parameter on `POST /api/settings/backups/restore` (restrict to filenames within `backups/`).
- [ ] **Consolidate schema ownership into a single migration system** — one `schema_migrations` version table; numbered migration files; runner applies pending migrations in order inside a transaction. Fold in: `init.sql` (as migration 001), `db.py:ensure_schema()` + `ensure_project_schema()`, `db_migrations.py` (focus_sessions, reminders). Stop running `executescript(init.sql)` on every startup. Single connection factory with `foreign_keys=ON` everywhere.
- [ ] **Decouple startup from network/IO** — move `run_report_audit()` to a post-startup background task; migrate `@app.on_event` → lifespan context; ensure a slow/failed AI call can never block app launch.
- [ ] **Introduce pytest + critical-path tests** — report generation (period math, artifacts, DB row, AI-failure path), backup create/restore, migration runner, AI context builder, prediction engine fixtures. (Expanded in Phase 3 / TESTING_GUIDE.md.)
- [ ] **Fix data-corrupting bugs**:
  - [ ] `snapshot_service.save_snapshot()` uses `date.strftime("%H%M%S")` → `000000`; same-day snapshots overwrite. Use a real `datetime`.
  - [ ] `routes/settings.py /storage` checks `database/productivity.db` (wrong name) — DB size always 0. Use the shared DB path constant.

## Important

- [ ] **Remove dead code**:
  - [ ] `backend/test_error.py` (debug script; triggers live report generation).
  - [ ] `backend/services/report_service.py` (7-line vestigial wrapper) — or make it the real façade and move generation logic into it.
  - [ ] `backend/services/report_scheduler_service.py` — bypassed by hardcoded `/reports/status`; delete or re-adopt (decide one).
  - [ ] Unused imports across routes/services (`Depends`, `re`, `Optional`, …).
- [ ] **Deduplicate report route logic** — extract the "existing report → return saved" branch shared by `/generate` and `/smart-generate`; have `/generate` delegate to the smart path.
- [ ] **Expand prediction accuracy tracking** — `predictions` table (predictor_type, target_id, risk, confidence, created_at); evaluate burnout/goal/consistency/focus outcomes, not just deadlines; match by ID not title; pick snapshot nearest to 7 days, not month-folder glob; aggregate rolling accuracy per predictor.
- [ ] **AI prompt token optimization** — replace raw JSON dumps (prompt sections 6–7) with compact summarized markdown lines per prediction; cap and prioritize note excerpts by recency.
- [ ] **Period-scope analytics in AI context** — `aggregate_analytics` and `generate_behavioral_summary` are all-time but embedded in weekly/monthly reports as if period-scoped.
- [ ] **Centralize configuration** — one module for `BASE_DIR`, DB path, artifact dirs (currently re-derived in 6+ files); store `reports.markdown_path` as relative path (one-time migration for existing rows).
- [ ] **Standardize logging** — replace `print()` with stdlib `logging` via `logging_service`; consistent format; keep critical/error file sinks.
- [ ] **Timezone configurability** — make logical-date timezone a setting (backend `date_service` + frontend `date.js`), default to system tz, IST fallback.
- [ ] **Report repair path** — detect reports whose AI section is the failure placeholder; allow regeneration instead of being blocked by the "already exists" check.

## Optional

- [ ] Missing indexes: `focus_sessions(start_time)`, `reminders(datetime)`, `reports(type, period_end)`, `projects(completed, deadline)`.
- [ ] `PRAGMA journal_mode=WAL` on connection open.
- [ ] CHECK constraints (progress 0–100, report type enum).
- [ ] Batch the N+1 in `scoring_service` (today's completions in one query) — it runs every 30s via frontend polling.
- [ ] Enforce the `APIResponse` envelope consistently across all routes.
- [ ] `integrity_service`: act on (or explicitly report) orphan milestones instead of commented-out cleanup.
- [ ] Lock CORS to localhost origins.
- [ ] Split `frontend/js/app.js` (600 lines) into matrix-rendering / task-CRUD / note modules; consider consolidating the two polling intervals in `productivity_os.js`.
- [ ] Replace hand-rolled `.env` parser with `python-dotenv`; fix default Gemini model name (`gemini-3.5-flash` is not a valid model).
- [ ] Reduce per-report artifact count (context JSON + prompt TXT behind a debug flag).
- [ ] Cache `/settings/storage` dir-size walks.
