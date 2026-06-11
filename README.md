# 🌱 Productivity Tracker — Phase 1

A local-first, GitHub-style daily habit & task tracker.  
Dark theme · SQLite · FastAPI · Vanilla JS · No cloud, no auth.

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- pip

### 2. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run the server

```bash
# From the project root
uvicorn backend.main:app --reload --port 8000
```

Or from inside `/backend`:

```bash
uvicorn main:app --reload --port 8000
```

### 4. Open the app

```
http://localhost:8000
```

The database (`database/tracker.db`) is created automatically on first run.

---

## Folder Structure

```
productivity-tracker/
├── frontend/
│   ├── index.html          # Main HTML shell
│   ├── css/
│   │   └── style.css       # Dark theme stylesheet
│   └── js/
│       ├── app.js          # Main app controller
│       ├── api.js          # Backend API client
│       └── ui.js           # UI helpers (modals, toast, dates)
├── backend/
│   ├── main.py             # FastAPI app + all routes
│   └── requirements.txt
├── database/
│   ├── init.sql            # SQLite schema (auto-applied on startup)
│   └── tracker.db          # Created automatically
├── reports/                # (Phase 2: export reports here)
├── exports/                # (Phase 2: CSV/JSON exports here)
├── assets/                 # Static assets
└── README.md
```

---

## Features (Phase 1)

| Feature | Status |
|---|---|
| Dark GitHub-style UI | ✅ |
| Add / delete tasks | ✅ |
| Recurring monthly tasks | ✅ |
| Schedule-aware active days | ✅ |
| Daily checkbox grid (like GitHub contributions) | ✅ |
| Click to toggle completion | ✅ |
| Notes per day per task | ✅ |
| Notes visible inline below task row | ✅ |
| Current streak counter | ✅ |
| Completion % + progress bar | ✅ |
| Month navigation (prev/next) | ✅ |
| Completed Goals archive | ✅ |
| Restore archived tasks | ✅ |
| SQLite local database | ✅ |
| Fully local — no internet required | ✅ |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/tasks` | List active tasks |
| GET | `/api/tasks/archived` | List completed goals |
| POST | `/api/tasks` | Add task `{title, recurring}` |
| PUT | `/api/tasks/:id` | Update task |
| DELETE | `/api/tasks/:id` | Delete task |
| POST | `/api/tasks/:id/archive` | Move to completed goals |
| POST | `/api/tasks/:id/restore` | Restore from archive |
| GET | `/api/entries/:year/:month` | Fetch month grid + stats |
| POST | `/api/entries/toggle` | Toggle day completion |
| PUT | `/api/entries/note` | Update day note |
| GET | `/api/stats/streak` | Current streak |

Full interactive docs: `http://localhost:8000/docs`

---

## Database Schema

```sql
tasks (
  id              INTEGER PRIMARY KEY,
  title           TEXT,
  recurring       INTEGER DEFAULT 1,
  created_at      TEXT,
  completed_forever INTEGER DEFAULT 0,
  sort_order      INTEGER DEFAULT 0
)

daily_entries (
  id        INTEGER PRIMARY KEY,
  task_id   INTEGER → tasks.id,
  date      TEXT (YYYY-MM-DD),
  completed INTEGER DEFAULT 0,
  note      TEXT DEFAULT ''
)
```

---

## Usage Tips

- **Click any active square** → toggles completion + opens inline note editor below the row
- **Blue dot** on a square = note attached
- **↻ badge** = recurring task (carries forward each month)
- **⋯ menu** = choose task schedule (every day, weekdays, weekends, or custom days)
- **✓ button** (appears on hover) → moves task to Completed Goals
- **✕ button** → permanently deletes task + all history
- Navigate months with **‹ ›** arrows

---

## Phase 2 Ideas (not implemented)

- CSV / JSON export to `/exports`
- Monthly PDF reports to `/reports`
- Task reordering (drag-and-drop)
- Per-task streaks
- Heatmap calendar view
