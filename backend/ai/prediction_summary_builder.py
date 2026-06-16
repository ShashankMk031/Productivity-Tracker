from typing import Any


def _fmt_confidence(value: Any) -> str:
    try:
        return f"{int(value)}%"
    except (TypeError, ValueError):
        return "N/A"


def _fmt_predictor_line(label: str, item: dict) -> str:
    reason = item.get("reason", "No reason recorded.")
    risk = item.get("risk_level", "UNKNOWN").title()
    confidence = _fmt_confidence(item.get("confidence"))
    return f"- **{label}**: {risk} risk ({confidence}) — {reason}"


def build_prediction_summary(snapshot: dict | None, accuracy: dict | None) -> str:
    if not snapshot:
        return "No prediction snapshot available."

    lines = []
    burnout = snapshot.get("burnout")
    if burnout:
        lines.append("### Burnout")
        lines.append(_fmt_predictor_line("Burnout", burnout))

    habits = snapshot.get("habits") or []
    if habits:
        lines.append("\n### Consistency Risks")
        for item in sorted(habits, key=lambda row: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(row.get("risk_level"), 0), reverse=True)[:4]:
            label = item.get("task_title") or item.get("target_label") or "Habit"
            lines.append(_fmt_predictor_line(label, item))

    deadlines = snapshot.get("deadlines") or []
    if deadlines:
        lines.append("\n### Deadline Forecasts")
        for item in sorted(deadlines, key=lambda row: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(row.get("risk_level"), 0), reverse=True)[:4]:
            label = item.get("project_title") or item.get("target_label") or "Project"
            lines.append(_fmt_predictor_line(label, item))

    goals = snapshot.get("goals") or []
    if goals:
        lines.append("\n### Goal Forecasts")
        for item in sorted(goals, key=lambda row: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(row.get("risk_level"), 0), reverse=True)[:4]:
            label = item.get("goal_title") or item.get("target_label") or "Goal"
            lines.append(_fmt_predictor_line(label, item))

    focus = snapshot.get("focus")
    if focus:
        lines.append("\n### Focus Effectiveness")
        focus_label = focus.get("best_focus_range", "Focus")
        lines.append(_fmt_predictor_line(focus_label, focus))

    predictor_summary = (accuracy or {}).get("predictors", {})
    if predictor_summary:
        lines.append("\n### Historical Accuracy")
        for predictor_type, meta in predictor_summary.items():
            label = predictor_type.replace("_", " ").title()
            lines.append(
                f"- **{label}**: {meta.get('accuracy_pct', 0)}% average accuracy across {meta.get('total_evaluated', 0)} evaluated predictions"
            )

    return "\n".join(lines).strip()
