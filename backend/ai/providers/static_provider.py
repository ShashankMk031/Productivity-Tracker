import math
from typing import Optional
from ai.providers.base import BaseProvider

class StaticProvider(BaseProvider):
    def __init__(self, **kwargs):
        super().__init__("static", api_key=None, model="local-static-generator", **kwargs)

    def generate(self, prompt: str, context: Optional[object] = None, **kwargs) -> str:
        if not context:
            return "# Static Reflection Report\n\nAI generation was unavailable and no context package was provided to generate a local fallback report."

        # Reconstruct typed variables from context package
        period_type = getattr(context, "period_type", "weekly")
        period_start = getattr(context, "period_start", "")
        period_end = getattr(context, "period_end", "")
        behavioral = getattr(context, "behavioral_patterns", None)
        notes = getattr(context, "notes", None)
        goals = getattr(context, "goals", [])
        projects = getattr(context, "projects", [])
        scores = getattr(context, "scores", {})
        focus_stats = getattr(context, "focus_stats", {})
        reminder_stats = getattr(context, "reminder_stats", {})
        prediction_summary = getattr(context, "prediction_summary_markdown", "")

        # Compute focus hours
        focus_sec = focus_stats.get("total_duration_sec", 0) if focus_stats else 0
        focus_hours = round(focus_sec / 3600.0, 1)

        # Build text-based progress bars helper
        def get_progress_bar(pct: int) -> str:
            filled = math.floor(pct / 10)
            empty = 10 - filled
            return f"`[{'█' * filled}{'░' * empty}]` {pct}%"

        lines = []

        if period_type == "monthly":
            lines.append("# Monthly Reflection")
            lines.append("## Executive Summary")
            lines.append(f"During the monthly cycle ending on **{period_end}**, the system compiled your productivity metrics locally.")
        else:
            lines.append("# Weekly Reflection")
            lines.append("## Overview")
            lines.append(f"Welcome to your weekly performance analysis for the period **{period_start}** to **{period_end}**.")

        # Quick Highlights
        completion_pct = behavioral.completion_rate if behavioral else 0
        current_streak = behavioral.current_streak if behavioral else 0
        longest_streak = behavioral.longest_streak if behavioral else 0
        active_tasks = behavioral.active_tasks_count if behavioral else 0

        lines.append(f"\nYour overall completion rate reached **{completion_pct}%** across **{active_tasks}** active habits, maintaining a perfect-day streak of **{current_streak} days** (all-time longest: **{longest_streak} days**). You spent **{focus_hours} hours** engaged in deep work focus sessions.")

        # 1. Wins / Major Progress
        lines.append("\n## Wins This Week" if period_type == "weekly" else "\n## Major Progress")
        wins = []
        if completion_pct >= 70:
            wins.append(f"High habit execution rate of **{completion_pct}%** shows strong routine consistency.")
        if current_streak >= 3:
            wins.append(f"Maintained an active habit completion streak of **{current_streak}** days.")
        if focus_hours >= 5.0:
            wins.append(f"Dedicated a substantial **{focus_hours} hours** of timed, high-focus work sessions.")
        
        # Check goals
        completed_goals = [g for g in goals if g.completed]
        for cg in completed_goals:
            wins.append(f"Successfully completed your strategic goal: **\"{cg.title}\"**.")
        high_prog_goals = [g for g in goals if not g.completed and g.progress >= 70]
        for hg in high_prog_goals:
            wins.append(f"Made outstanding progress on goal **\"{hg.title}\"** ({hg.progress}% complete).")

        # Check projects / milestones
        for p in projects:
            if p.progress >= 80:
                wins.append(f"Project **\"{p.title}\"** is near completion at **{p.progress}%**.")
            completed_m = [m for m in p.milestones if m.completed]
            if len(completed_m) > 0:
                wins.append(f"Checked off **{len(completed_m)}** milestone(s) for project **\"{p.title}\"**.")

        # Note themes
        if notes and notes.total_notes_analyzed > 0:
            wins.append(f"Logged **{notes.total_notes_analyzed}** daily notes, preserving rich contextual performance logs.")
            if notes.dominant_themes:
                wins.append(f"Positive momentum seen in recurring journal themes: *{', '.join(notes.dominant_themes[:3])}*.")

        if not wins:
            wins.append("Maintained baseline routines and logged tracker notes successfully.")
        
        for w in wins:
            lines.append(f"- ✓ {w}")

        # 2. Risks / Obstacles
        lines.append("\n## Emerging Risks" if period_type == "weekly" else "\n## Common Obstacles")
        risks = []
        
        # Check overdue projects
        for p in projects:
            if p.urgency == "RED":
                risks.append(f"Project **\"{p.title}\"** has reached a high-urgency/overdue warning state.")
            elif p.urgency == "YELLOW":
                risks.append(f"Project **\"{p.title}\"** is approaching its deadline soon.")

        # Check weak days
        if behavioral and behavioral.weak_weekdays:
            risks.append(f"Observed lower productivity trends on: **{', '.join(behavioral.weak_weekdays)}**.")
            
        # Check low focus sessions
        if focus_stats and focus_stats.get("total_sessions", 0) > 0:
            completed_ratio = focus_stats.get("completed_sessions", 0) / focus_stats.get("total_sessions", 1)
            if completed_ratio < 0.6:
                risks.append(f"Focus session dropout rate is high (only {focus_stats.get('completed_sessions')} of {focus_stats.get('total_sessions')} sessions were fully completed).")

        # Check reminder skips
        if reminder_stats and reminder_stats.get("total_reminders", 0) > 0:
            rem_pct = (reminder_stats.get("completed_reminders", 0) / reminder_stats.get("total_reminders", 1)) * 100
            if rem_pct < 60:
                risks.append(f"Task reminder adherence is low at **{rem_pct:.1f}%** (skipping alerts breaks momentum).")

        # Fallback
        if not risks:
            risks.append("No critical deadline risks or major consistency slips detected this period.")

        for r in risks:
            lines.append(f"- ⚠️ {r}")

        # 3. Consistency Analysis / Behavioral Patterns
        lines.append("\n## Consistency Analysis" if period_type == "monthly" else "\n## Behavioral Patterns")
        lines.append(f"- **Consistency Score**: {scores.get('consistency', 0)}/100")
        lines.append(f"- **Execution Score**: {scores.get('execution', 0)}/100")
        if behavioral and behavioral.productive_weekdays:
            lines.append(f"- **Peak Performance Days**: {', '.join(behavioral.productive_weekdays)}")
        if notes and notes.categories:
            lines.append("\n**Qualitative Note Log Distribution**:")
            for cat, details in notes.categories.items():
                if details.count > 0:
                    lines.append(f"  - **{cat}**: matched {details.count} times ({details.percentage}% of notes)")

        # 4. Goal Progress
        lines.append("\n## Goal Performance" if period_type == "monthly" else "\n## Goal Progress")
        if not goals:
            lines.append("No active strategic goals recorded.")
        else:
            for g in goals:
                status_label = "🏆 Completed" if g.completed else "In Progress"
                lines.append(f"- **{g.title}** ({g.category})")
                lines.append(f"  Progress: {get_progress_bar(g.progress)} | Status: {status_label}")

        # 5. Project Health
        lines.append("\n## Project Progress" if period_type == "monthly" else "\n## Project Health")
        if not projects:
            lines.append("No active project deliverables scheduled.")
        else:
            for p in projects:
                lines.append(f"- **{p.title}** (Deadline: {p.deadline})")
                lines.append(f"  Progress: {get_progress_bar(p.progress)} | Urgency: **{p.urgency}**")
                pending_m = [m.title for m in p.milestones if not m.completed]
                if pending_m:
                    lines.append(f"  *Next up:* {pending_m[0]}")

        # 6. Prediction Review (Static include)
        if prediction_summary:
            lines.append("\n## Prediction Review" if period_type == "monthly" else "\n## Forecasts")
            lines.append(prediction_summary.strip())

        # 7. Actionable Recommendations
        lines.append("\n## Recommendations")
        recs = []
        if completion_pct < 50:
            recs.append("Your execution rate is below 50%. Focus on simplifying your routine by disabling 1-2 non-critical habits.")
        else:
            recs.append("Routine consistency is healthy. Consider adding a 'step-up' milestone to challenge your weekly targets.")

        if focus_hours < 3.0:
            recs.append("Deep focused work hours are low. Schedule at least two 30-minute blocks using the Focus Session Timer.")
        
        has_overdue = any(p.urgency == "RED" for p in projects)
        if has_overdue:
            recs.append("You have overdue project deadlines. Dedicate your next focus session exclusively to checking off pending milestones.")

        if reminder_stats and reminder_stats.get("total_reminders", 0) > 0:
            rem_pct = (reminder_stats.get("completed_reminders", 0) / reminder_stats.get("total_reminders", 1)) * 100
            if rem_pct < 70:
                recs.append("Reminder check-ins are frequently skipped. Position your workspace dashboard in view to act on alerts.")

        for index, rec in enumerate(recs, 1):
            lines.append(f"{index}. {rec}")

        return "\n".join(lines)

    def check_health(self) -> str:
        # Static local generator is always online and healthy
        return "healthy"
