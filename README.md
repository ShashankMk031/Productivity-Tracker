# 🌱 Productivity Tracker — Phase 1 & Multi-Provider AI Framework

A local-first, offline-ready, GitHub-style daily habit tracker and strategic execution engine. It operates with zero cloud dependencies, zero user logins, and runs completely locally using a SQLite database, a FastAPI backend, and a modern Vanilla CSS/JS frontend.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- pip
- (Optional) Local LLM runner like **LM Studio** loaded with `google/gemma-4-12b-qat` or similar OpenAI-compatible API running on `http://localhost:1234`.

### 2. Installation
Clone the repository and install the backend dependencies:
```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
```

### 3. Environment Configuration
Copy the template configuration file:
```bash
cp backend/.env.example backend/.env
```
Open `backend/.env` and configure your API keys and provider preferences.

### 4. Running the Server
From the `/backend` directory, launch the FastAPI server using Uvicorn:
```bash
uvicorn main:app --reload --port 8000
```
The local database (`database/tracker.db`) is automatically initialized and migrated on the first launch.

### 5. Accessing the Application
Open your web browser and navigate to:
```
http://localhost:8000
```

---

## 📂 Project Structure

```
productivity-tracker/
├── backend/
│   ├── ai/                      # AI Reflection Framework
│   │   ├── providers/           # API integrations: Gemini, Groq, OpenRouter, LM Studio, Static
│   │   ├── ai_service.py        # Fallback router and orchestrator
│   │   ├── context_builder.py   # Context aggregation (habits, goals, projects, notes)
│   │   ├── prompt_builder.py    # LLM markdown template interpolation
│   │   └── ...
│   ├── analytics/               # Quantitative metric tracking (completion, streaks, charts)
│   ├── database/                # SQLite connection factory & versioned migrations
│   ├── intelligence/            # Forecast & Calibration engines (burnout, consistency)
│   ├── routes/                  # API routers (tasks, reports, projects, settings)
│   ├── services/                # Decoupled business logic controllers
│   ├── utils/                   # timezone (IST logical dates) & formatting helpers
│   ├── main.py                  # FastAPI App launcher & mount points
│   └── pytest.ini               # Test configurations
├── frontend/
│   ├── css/
│   │   ├── style.css            # Dark slate color variables and core stylesheets
│   │   └── strategic.css        # Layouts for goals and project views
│   ├── js/
│   │   ├── api.js               # Common fetch wrappers
│   │   ├── app.js               # Habits page & calendar grid logic
│   │   ├── navigation.js        # Sidebar nav and breadcrumbs dynamic generation
│   │   ├── reports_dashboard.js # Visual badges, comparison tools, and report previews
│   │   └── ...                  # Task scheduling, goals, projects, settings wiring
│   └── *.html                   # Monolithic MPA views served by FastAPI
├── database/
│   └── tracker.db               # SQLite database file (created automatically)
└── verify_ai_pipeline.py       # Infrastructure pipeline dry-run utility
```

---

## 🏗️ System & Routing Architecture

The application runs as a multi-page web application served directly by FastAPI.

### Page Routes (GET)
- `/` -> Redirects to `/dashboard`.
- `/dashboard` -> Today's execution metrics, Focus Session timer, Reminders, and Journal note.
- `/tasks` -> Habit grid contribution calendar (GitHub style), task controls, notes.
- `/goals` -> Strategic long-term, short-term, and step-up columns.
- `/projects` -> Project progress trackers, linked milestones, priority metrics.
- `/calendar` -> Unified history log (completions, milestones, notes consolidated per day).
- `/reports` -> Analytics dashboard, AI reflections, monthly/weekly status history.
- `/insights` -> Intelligence reports, burnout forecast charts, predictive metrics.
- `/settings` -> Local DB sizing, health indicators, backup manager, AI pipeline diagnostic pingers.

### Backend Services
- **[integrity_service.py](file:///Users/shashankmk/Documents/Projects-Development/HabitTracker/productivity-tracker/backend/services/integrity_service.py)**: Audits workspace structure, self-heals missing folder trees, check for orphans, and validates file synchronization.
- **[backup_service.py](file:///Users/shashankmk/Documents/Projects-Development/HabitTracker/productivity-tracker/backend/services/backup_service.py)**: Manages atomic database compression, safety copies, and zip integrity checks.
- **[scoring_service.py](file:///Users/shashankmk/Documents/Projects-Development/HabitTracker/productivity-tracker/backend/services/scoring_service.py)**: Implements math algorithms for Consistency, Execution, and Goal Progress scores.

---

## 🧠 AI Infrastructure & Fallback Chain

To guarantee report generation resilience against outages, timeouts, and rate limits (429s), the system uses a sequential **Multi-Provider Fallback Chain**.

```
[Context Data] ─> [Context Builder] ─> [Prompt Builder]
                                             │
   ┌─────────────────────────────────────────┘
   ▼
[Gemini API] (Primary)
   │ 429 / Timeout / Outage
   ▼
[Groq API] (Secondary)
   │ 429 / Timeout / Outage
   ▼
[OpenRouter API] (Tertiary)
   │ 429 / Timeout / Outage
   ▼
[LM Studio API] (Local local_fallback on http://localhost:1234 serving gemma-4-12b)
   │ Offline / Not Running
   ▼
[Static Local Report] (Hard fail-safe; renders templates of local logs metrics)
```

### Behavioral Note Engine
The AI prompt context analyses daily notes by categorizing entries into 7 key performance tags:
- **Fatigue**: Matches sleep patterns, exhaustion (*sluggish, sleep, tired*).
- **Stress**: Tracks anxiety levels (*stress, panic, pressure, burn*).
- **Deep Work**: Measures flow timeblocks (*focus, deep work, zone*).
- **Distraction**: Pinpoints attention drifts (*social media, phone, browse*).
- **Motivation**: Identifies energy spikes (*excited, inspired, motivated*).
- **Progress**: Aggregates completions (*completed, done, milestone, built*).
- **External**: Accounts for environment variables (*weather, sick, meeting*).

---

## 🗄️ Database Schema & Migrations

Database structures are updated dynamically using versioned schemas (`v1-v7` in `backend/database/migrations.py`):

- `tasks`: Core habits. Fields: `id`, `title`, `recurring`, `active_days` (JSON), `completed_forever`, `created_at`.
- `daily_entries`: Daily checkbox logs. Fields: `id`, `task_id`, `date`, `completed`, `note`.
- `goals`: Long-term targets. Fields: `id`, `title`, `description`, `category`, `progress`, `priority`, `target_date`, `completed`, `created_at`.
- `projects`: Deadline tracks. Fields: `id`, `title`, `description`, `deadline`, `progress`, `priority`, `completed`, `completed_at`, `goal_id`, `created_at`.
- `project_milestones`: Project sub-milestones. Fields: `id`, `project_id`, `title`, `completed`, `created_at`.
- `focus_sessions`: Logged timer sessions. Fields: `id`, `title`, `start_time`, `end_time`, `duration`, `notes`.
- `reminders`: Quick alarms/tasks. Fields: `id`, `title`, `datetime`, `recurring`, `completed`.
- `daily_notes`: General logs. Fields: `date` (PK), `content`.
- `prediction_records`: Snapshot predictions & evaluations. Fields: `id`, `predictor_type`, `target_id`, `target_date`, `predicted_value`, `actual_value`, `confidence`, `accuracy`, `evaluated_at`.
- `reports`: Weekly & Monthly reports metadata. Fields: `id`, `type`, `generated_at`, `markdown_path`, `summary`, `period_start`, `period_end`, `ai_provider`, `ai_model`.

---

## 🎨 UI/UX Design System Specification

Drive by custom CSS tokens in `style.css` and `strategic.css`:

### Color System
- **Backgrounds**: `--bg-dark` (`#060b0e`), `--bg-surface` (`#0a1216`), `--bg-surface-elevated` (`#111d24`).
- **Borders**: `--border-subtle` (12% opacity), `--border-default` (22% opacity), `--border-active` (`#54d14f` accent glow).
- **Semantic Badges**: Primary (`#54d14f`), Info (`#4a90e2`), Warning (`#ffaa00`), Danger (`#ff7a70`).

### Typography
- Standard Font: `'Outfit', 'Inter', -apple-system, sans-serif`.
- Text Accents: Primary Body (`#eef3f7`), Muted Labels (`#8ca1af`), Disabled (`#566570`).

### Interactive Elements
- `.ui-card`: Elevates slightly (translate Y -2px), background shifts to elevated shade, border transitions to green on hover.
- `.ui-metric-card`: Features a thick left accent border using the respective semantic color representing the metric scope.
- `.ui-btn`: Hover shifts gradient highlights; danger buttons smoothly fill background color on focus.

---

## 🧪 Testing & Verification Guide

The backend uses a critical-path test suite based on `pytest`.

### Workspace Isolation Guarantees
1. **Isolated DB**: Tests run against a temporary memory database built dynamically on the fly by `database/migrations.py`. The actual database is never read.
2. **Redirected Filesystem**: The `workspace` fixture intercepts and reroutes all local folders (`/backups`, `/reports`, `/ai_reports`, `/ai_context`, `/intelligence_snapshots`) into temporary system environments.
3. **Network Isolation**: The `mock_ai` fixture stubs out all external API requests, returning mock reflections instantly.

### Running Tests
To run the automated tests, run from the `/backend` directory:
```bash
pytest
```

To perform a manual infrastructure dry-run of the context aggregation, prompt parsing, and model API request chain, run from the project root:
```bash
python verify_ai_pipeline.py
```
