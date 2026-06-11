# 🌱 AI Infrastructure Layer (Phase 4A)

This directory houses the structured AI foundation for the **Productivity Tracker**. It aggregates quantitative statistics, weekday consistency ratings, milestone statuses, and qualitative note diaries into unified context snapshots ready to be analyzed by Large Language Models.

---

## 🏗️ Architecture Design

```
backend/ai/
├── schemas.py              # Pydantic validation structures
├── note_analysis.py        # Case-insensitive keyword classifier
├── behavioral_summary.py   # Metric calculations and weekday rankers
├── context_builder.py      # Combines analytics, notes, goals, and projects
├── prompt_builder.py       # Renders LLM text analysis templates
└── ai_service.py           # Provider router & dry-run reflection mocking
```

### 1. Data Pipeline
```
[User Notes / Daily Entries] ──┐
[Project / Milestones Data] ──┼─> [Context Builder] ──> [Context JSON Package] ──> [Prompt Builder]
[Goal Statuses & Analytics] ──┘                                                      │
                                                                                    ▼
[Final Reflection Report] <─── [AI Service Layer] <─────────────────────────── [LLM Prompt Text]
```

---

## 📝 Behavioral Note Engine

The note categorization engine performs keyword mappings across 7 core tags:

*   **Fatigue**: matches sleep cycles, tiredness (*tired, sleep, fatigue, sluggish*).
*   **Stress**: tracks anxiety, burn-out patterns (*stress, pressure, panic, burn*).
*   **Deep Work**: focuses on focused timeblocks (*focus, deep work, flow, zone*).
*   **Distraction**: evaluates attention drifts (*distracted, phone, browsing, social media*).
*   **Motivation**: records inspiration spikes (*motivated, low energy, excited*).
*   **Progress**: aggregates positive checks (*completed, milestone, done, built*).
*   **External Factors**: covers environmental issues (*weather, meeting, sick, call*).

---

## ⚡ Environment Settings

Copy the example configuration to activate customization:
```bash
cp backend/.env.example backend/.env
```

### Variables
*   `AI_PROVIDER`: `'openai'` or `'gemini'` (default is `'openai'`).
*   `OPENAI_API_KEY`: API key from OpenAI.
*   `GEMINI_API_KEY`: API key from Google AI Studio.
*   `AI_MODEL` / `GEMINI_MODEL`: Override targets (e.g. `gpt-4o`, `gemini-1.5-pro`).

---

## 📂 Context Snapshots (`/ai_context`)

Context packages are saved locally during each report generation:
```
ai_context/
└── 2026/
    ├── may_week_1_context.json   # Unified JSON data
    └── may_week_1_prompt.txt     # Formatted prompt string
```
These snapshots provide:
1.  **Debugging**: Validate exactly what data is being channeled to LLMs.
2.  **Reproducibility**: Re-run identical prompts through different model versions for evaluation.
3.  **Auditing**: Review local behavioral trends historically.
