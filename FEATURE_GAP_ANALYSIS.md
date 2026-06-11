# FEATURE_GAP_ANALYSIS.md

Comparison of the original phase roadmap against the current implementation.

Legend: ✅ complete · 🟡 partial · 🔲 placeholder · ❌ missing · 💀 dead/abandoned

---

## Phase 1 — Habit Tracker Foundation — ✅ Complete

| Feature | Status | Notes |
|---|---|---|
| Task CRUD, recurring tasks, active-day schedules | ✅ | `routes/tasks.py`, `task_service`, schedule presets in frontend |
| Daily matrix grid, toggle, notes | ✅ | `app.js` monthly matrix with inline notes |
| Streaks, completion %, archive/restore | ✅ | `analytics/streaks.py`, archive flow |
| SQLite local-first | ✅ | `tracker.db`, no auth/cloud |

## Phase 2 — Analytics & Weekly/Monthly Reports — ✅ Complete (one inconsistency)

| Feature | Status | Notes |
|---|---|---|
| Metrics/charts/streak analytics | ✅ | `analytics/` package, `/api/reports/analytics` |
| Weekly/monthly markdown reports | ✅ | `generate_and_save_report()` with period math + artifacts |
| Report history & retrieval | ✅ | DB metadata + disk markdown |
| Scheduled gating (Mon/1st rules) | 💀 | `report_scheduler_service.check_report_status()` fully built but bypassed — `/reports/status` hardcodes always-allowed |
| ⚠️ Analytics in reports | 🟡 | All-time metrics embedded in period reports as if period-scoped |

## Phase 3 — Goals, Deadline Projects, Milestones — ✅ Complete

| Feature | Status | Notes |
|---|---|---|
| Goal CRUD + progress + categories + target dates | ✅ | `goal_service`, `goals.js` |
| Projects with deadlines + progress | ✅ | `project_service`, countdown urgency RED/YELLOW/GREEN |
| Milestones (cascade delete) | ✅ | `project_milestones` table, FK cascade |

## Phase 4A — AI Infrastructure — ✅ Complete

| Feature | Status | Notes |
|---|---|---|
| Context builder | ✅ | `build_ai_context()` — broad aggregation into Pydantic package |
| Prompt builder | ✅ | Mandated-section prompt, weekly/monthly variants |
| Note analysis | ✅ | 7-category keyword/regex classifier |
| Behavioral summary | ✅ | `behavioral_summary.py` |

## Phase 4B — AI Reflection Reports & Integration — ✅ Complete (quality gaps)

| Feature | Status | Notes |
|---|---|---|
| Gemini/OpenAI integration with fallback | ✅ | `AIService`, provider order, graceful degradation |
| AI report archives | ✅ | `ai_reports/`, `ai_context/` trees + `/ai_reports` endpoints |
| ⚠️ Failure recovery | ❌ | A report generated during AI outage persists the warning text and blocks regeneration |
| ⚠️ Token efficiency | 🟡 | Raw JSON blobs in prompt (see review) |

## Phase 5A — Productivity OS Core — 🟡 Mostly complete

| Feature | Status | Notes |
|---|---|---|
| Reminders (CRUD + recurring + completion) | ✅ | `reminder_service`, 60s frontend daemon |
| Focus sessions (start/stop/duration/notes) | ✅ | `focus_service`, live timer UI |
| Productivity scores (consistency/execution/goal) | ✅ | `scoring_service`, 30s refresh |
| Calendar | 🟡 | Page exists (`calendar.html`/`calendar.js`) but thin relative to roadmap billing |
| Notifications | 🟡 | Browser Notification API only — requires open tab + permission; no backend scheduling; will not survive desktop packaging as-is |

## Phase 5B — Intelligence & Prediction Layer — 🟡 Partial

| Feature | Status | Notes |
|---|---|---|
| Burnout detection | ✅ | Keyword + focus-decline + missed-task scoring with explainable output |
| Deadline forecasting | ✅ | `deadline_forecaster` + accuracy evaluation |
| Goal forecasting | ✅* | Implemented inline in `prediction_engine.py` (odd placement) — works, never accuracy-evaluated |
| Consistency & focus prediction | ✅* | Generated and displayed — never accuracy-evaluated |
| Prediction accuracy | 🟡 | **Deadline-only**; title-based matching; brittle month-folder snapshot lookup; same-day snapshot overwrite bug destroys history; no aggregation; confidence scores hardcoded, never calibrated |
| Insights dashboard | ✅ | `insights.js` cards from `/api/intelligence/dashboard` |

## Phase 5C — Backup, Integrity, Self-Healing, Health Dashboard — 🟡 Partial

| Feature | Status | Notes |
|---|---|---|
| Backup creation (manual/auto/export) | ✅ | Zip of 6 dirs; auto pre-monthly-report; `/settings/export` download |
| Backup restore | 🔲 | Exists but **unsafe placeholder-grade**: deletes live data before copying, no validation/verification, accepts arbitrary path |
| Data integrity checks | 🟡 | Detects orphan milestones + missing report files at startup; remediation commented out; results not surfaced in UI |
| Self-healing | 🟡 | Directory recreation only |
| Health dashboard | 🔲 | `/settings/health` = 5 row counts; `/settings/storage` reports DB size 0 (wrong filename bug); integrity/log/backup status not shown |

## Dead / Abandoned Functionality

| Item | Disposition |
|---|---|
| `services/report_scheduler_service.py` | 💀 Bypassed by hardcoded route — delete or re-adopt |
| `services/report_service.py` | 💀 7-line vestige — delete or promote to real façade |
| `backend/test_error.py` | 💀 Debug script (fires live report generation) — delete |
| Orphan-milestone auto-cleanup | 💀 Commented out in `integrity_service` |
| Assorted unused imports | 💀 Sweep during debt sprint |

## Missing Integrations

- Integrity-check results → health dashboard (computed at startup, shown nowhere).
- Prediction accuracy → confidence scores (no feedback loop).
- `logging_service` → general application logging (only critical/error use it).
- Backup restore → app lifecycle (restore while DB is open by the running process).

## Bottom Line

Phases 1–4B are genuinely complete. Phase 5A is complete except notifications/calendar depth. **Phase 5B's accuracy tracking and Phase 5C's restore-safety + health dashboard are the two roadmap items whose implementation does not equal completion** — both are addressed as Critical items in `TODO_TECHNICAL_DEBT.md`.
