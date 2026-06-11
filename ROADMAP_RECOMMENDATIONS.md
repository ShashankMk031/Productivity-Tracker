# ROADMAP_RECOMMENDATIONS.md

Companion to `PROJECT_REVIEW.md`. Answers the five strategic questions.

---

## 1. What should be done before desktop packaging?

Blocking (the app will malfunction or endanger data when packaged):

1. **Backup restore safety rewrite** — never delete live data first; backup-current → validate archive → restore to temp → verify → swap. Also remove the arbitrary-path restore parameter.
2. **Path portability** — replace the 6+ scattered `BASE_DIR` derivations with one config module supporting a per-user data directory (packaged apps cannot write next to their own binary). Convert `reports.markdown_path` to relative paths with a one-time migration.
3. **Single migration system with version tracking** — packaged apps auto-update; user databases must upgrade safely across versions. This is non-negotiable before shipping v1.
4. **Remove network calls from startup** — move `run_report_audit()` to a background task after the server is up; migrate to FastAPI lifespan handlers. A desktop app that hangs on launch because Gemini is slow is unacceptable.
5. **Timezone configurability** — IST is hardcoded in backend and frontend. At minimum read system timezone with IST fallback.
6. **Critical-path test suite** — report generation, backup/restore, migrations. You cannot safely auto-update user installs without these.
7. Fix known bugs: `/settings/storage` wrong DB filename, snapshot timestamp `000000` collision.

Nice-to-have before packaging: lock CORS to localhost, WAL mode, report-regeneration path for AI-failed reports.

## 2. What should be improved after 2 weeks of real usage?

Let usage data decide; these are likely candidates:

- **Note analysis tuning** — extend/personalize the 7 keyword categories based on your actual vocabulary; the burnout detector's keyword list will likely need the same.
- **Report quality iteration** — compare 2 weekly + 1 monthly AI report against reality; tune coaching directives and the prediction summarization layer.
- **Prediction calibration** — after 2 weeks there are real outcomes; review whether burnout/goal risk levels matched reality and adjust thresholds (currently arbitrary: score ≥70 HIGH, ≥40 MEDIUM).
- **Polling pressure** — decide whether the 30s score refresh and 60s reminder daemon feel responsive or wasteful in real use.
- **Friction log** — capture UX pain points for the Phase 5 personal-workflow proposal instead of guessing now.

## 3. What parts appear overengineered?

- **Quadruple artifact persistence per report** — markdown report + context JSON + rendered prompt TXT + raw AI response TXT, across 3 directory trees with parallel naming schemes. Context+prompt archiving is debug tooling presented as a feature; one structured artifact (or a `--debug` flag) would do.
- **`report_scheduler_service`** — fully implemented weekly/monthly gating logic that the route deliberately bypasses with a hardcoded "always allowed". Either re-adopt it or delete it.
- **Filesystem-based snapshot/accuracy pipeline** — year/month folder trees, filename parsing, and glob-sorting to answer questions a single `predictions` table would answer with one SQL query.
- **`APIResponse` envelope inconsistency** — half the routes use the typed envelope, half return raw dicts; the abstraction exists without being enforced.

## 4. What parts are underdeveloped?

- **Prediction accuracy tracking** — ~20% built: deadline-only, title-matched, history-destroying timestamp bug, no aggregation, no feedback into confidence. The 'Prediction Accuracy' phase title overstates what exists.
- **Testing** — nonexistent.
- **Health dashboard (Phase 5C)** — `/settings/health` returns 5 row counts; integrity results from startup aren't surfaced, log contents aren't viewable, backup health isn't shown.
- **Notifications** — browser `Notification` API only, dependent on an open tab + polling; no backend scheduling. Will need rework for desktop (Tauri native notifications).
- **Calendar page** — minimal relative to its roadmap billing.
- **Logging** — `logging_service` covers only critical/error file appends; everything else is `print()`.

## 5. Highest-ROI improvements

Ranked by (risk reduced × effort saved) per hour invested:

1. **Backup restore safety** (~half day) — converts the single worst data-loss vector into the safety net it claims to be.
2. **Unified migrations + version table** (~1 day) — unblocks packaging, auto-update, and every future schema change.
3. **Critical-path pytest suite** (~1–2 days) — every subsequent phase (debt sprint, MPA conversion, packaging) becomes dramatically safer.
4. **Prompt summarization layer** (~half day) — cuts AI cost/latency on every report forever and improves model focus.
5. **`predictions` table + all-type accuracy evaluation** (~1 day) — turns the intelligence layer from "plausible guesses" into a measurable, improvable system; prerequisite for honest confidence scores.
6. **Dead code removal + logging standardization** (~half day) — cheap clarity gains for every future session in the codebase.
