# TESTING_GUIDE.md

Critical-path test suite introduced in the stability sprint (Sprint 1).

## Setup

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
```

## Running the suite

```bash
cd backend
pytest            # full suite
pytest -v         # verbose
pytest tests/test_backup_restore.py   # one file
pytest -k restore                     # by keyword
```

`backend/pytest.ini` points pytest at `backend/tests`. The suite needs no
running server and never touches real data.

## Isolation guarantees

- **Database**: every test gets a temporary SQLite database created by the
  unified migration runner (`database/migrations.py`). The real
  `database/tracker.db` is never opened.
- **Filesystem**: the `workspace` fixture redirects all artifact
  directories (`backups/`, `reports/`, `ai_reports/`, `ai_context/`,
  `intelligence_snapshots/`) into a pytest temp directory.
- **Network**: the `mock_ai` fixture replaces `AIService.generate_reflection`
  so no live Gemini/OpenAI calls are ever made. Any test that triggers
  report generation must use `mock_ai` (or its own monkeypatch).

## Fixtures (backend/tests/conftest.py)

| Fixture | Provides |
|---|---|
| `workspace` | Temp dir with a migrated DB and all artifact dirs redirected |
| `db` | Open `sqlite3` connection (Row factory, foreign keys ON) to the temp DB |
| `seeded_db` | `db` plus a small realistic data set (task, entries with notes, goal, project + milestones, focus session, reminder) |
| `mock_ai` | Deterministic AI reflection, no network |

## What is covered

| File | Coverage |
|---|---|
| `test_migrations.py` | Runner creates all tables, records versions, is idempotent, legacy columns present |
| `test_backup_restore.py` | Backup archive contents; restore roundtrip; safety copy preservation; rejection of unmanaged paths, traversal, corrupt archives, archives without a database |
| `test_reports.py` | Weekly/monthly period math, artifacts on disk, DB row, failed-AI detection and in-place regeneration, snapshot filename regression test |
| `test_ai_context.py` | `build_ai_context` returns a complete `AIContextPackage` from a seeded DB |
| `test_predictions.py` | Snapshot shape on empty and seeded DBs, predictor output contract, overdue-goal risk |
| `test_goal_crud.py` | Goal create/read/update/delete, 404 on missing |
| `test_project_crud.py` | Project + milestone CRUD, auto progress, cascade delete, 404 on missing |

## Adding tests

1. Put new files in `backend/tests/` named `test_*.py`.
2. Depend on `workspace`/`db` instead of touching real paths; never
   hardcode `BASE_DIR`-relative locations.
3. Mock anything that performs network IO (see `mock_ai`).
4. When fixing a bug, add a regression test that fails on the old behavior
   (see `test_snapshot_files_do_not_overwrite_same_day`).
