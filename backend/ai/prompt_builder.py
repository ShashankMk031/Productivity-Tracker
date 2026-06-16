from .schemas import AIContextPackage

def build_ai_prompt(context: AIContextPackage) -> str:
    lines = []
    lines.append("# AI PRODUCTIVITY REFLECTION & ANALYSIS PROMPT")
    lines.append("\nYou are an elite productivity strategist and performance coach. Your goal is to analyze the user's historical habit logs, text notes, goal lists, and deadline-bound projects to provide a deep, highly personalized behavioral reflection report.")
    
    if context.period_type == "monthly":
        lines.append("\nYou MUST output a report containing the following mandatory markdown sections EXACTLY as defined below (use these exact heading levels, titles, and order):")
        lines.append("\n# Monthly Reflection")
        lines.append("## Executive Summary")
        lines.append("## Major Progress")
        lines.append("## Consistency Analysis")
        lines.append("## Behavioral Trends")
        lines.append("## Goal Performance")
        lines.append("## Project Progress")
        lines.append("## Deadline Health")
        lines.append("## Common Obstacles")
        lines.append("## Prediction Review")
        lines.append("## Forecast Accuracy")
        lines.append("## Next Month Outlook")
        lines.append("## Recommendations")
    else:
        lines.append("\nYou MUST output a report containing the following mandatory markdown sections EXACTLY as defined below (use these exact heading levels, titles, and order):")
        lines.append("\n# Weekly Reflection")
        lines.append("## Overview")
        lines.append("## Wins This Week")
        lines.append("## What Slowed You Down")
        lines.append("## Behavioral Patterns")
        lines.append("## Goal Progress")
        lines.append("## Project Health")
        lines.append("## Forecasts")
        lines.append("## Emerging Risks")
        lines.append("## Opportunity Areas")
        lines.append("## Recommendations")
        lines.append("## Focus For Next Week")

    lines.append("\n### CRITICAL COACHING DIRECTIVES & QUALITY RULES:")
    lines.append("1. **Note-Backed Priority**: Daily text notes are your primary raw data source. Heavily reference the user's recurring themes, emotional patterns, physical states, and behavioral causes from their logs. Do NOT make this a purely numerical summary; focus on note-backed behavioral triggers.")
    lines.append("2. **Insight Depth**: Identify recurring excuses, fatigue patterns (e.g., afternoon dips, exhaustion 'after lab'), distraction vectors (e.g., 'phone distraction', internet), deep work anchors (e.g., what makes a study or DSA session successful), and consistency fluctuations.")
    lines.append("3. **Actionable Recommendations**: Under the '## Recommendations' heading, provide concrete, realistic recommendations that are directly backed by the user's notes (e.g., 'Move DSA before 7 PM', 'Finish milestone 3 before Friday', 'Reduce late-night work sessions'). Every report must end with these actionable recommendations.")
    lines.append("4. **No Fluff**: Strictly avoid motivational fluff, repetitive remarks, or generic self-help advice. Be direct, objective, and evidence-based, making conclusions explicitly supported by the context entries.")
    
    lines.append("\n---")
    lines.append("## USER CONTEXT DATA PACKAGE")
    
    # 1. Overview & Highlights
    lines.append("\n### 1. Overview & Progress Highlights")
    lines.append(f"- **Report Period Type**: {context.period_type.capitalize()}")
    if context.period_start and context.period_end:
        lines.append(f"- **Report Window**: {context.period_start} → {context.period_end}")
    lines.append(f"- **Generation Timestamp**: {context.generated_at}")
    lines.append(f"- **Active Task Count**: {context.behavioral_patterns.active_tasks_count}")
    lines.append(f"- **Global Completion Rate**: {context.behavioral_patterns.completion_rate}%")
    lines.append(f"- **Current Perfect-Day Streak**: {context.behavioral_patterns.current_streak} days")
    lines.append(f"- **Longest Perfect-Day Streak**: {context.behavioral_patterns.longest_streak} days")
    lines.append(f"- **Missed Days Count**: {context.behavioral_patterns.missed_days_count}")
    
    # 2. Behavioral Patterns & Note Analysis
    lines.append("\n### 2. Behavioral Patterns")
    lines.append(f"- **Most Productive Weekdays**: {', '.join(context.behavioral_patterns.productive_weekdays) or 'N/A'}")
    lines.append(f"- **Weakest Weekdays**: {', '.join(context.behavioral_patterns.weak_weekdays) or 'N/A'}")
    lines.append(f"- **Dominant Themes Extracted from Notes**: {', '.join(context.notes.dominant_themes) or 'None'}")
    lines.append(f"- **Total Text Notes Analyzed**: {context.notes.total_notes_analyzed}")
    
    lines.append("\nCategorized Qualitative Note Frequency & Excerpts:")
    for cat, pattern in context.notes.categories.items():
        if pattern.count > 0:
            lines.append(f"\n*   **Category: {cat}** (Matched {pattern.count} times - {pattern.percentage}% of notes)")
            for entry in pattern.matching_entries[:5]:  # Limit to top 5 excerpts for brevity
                lines.append(f"    - [{entry['date']}] Task: '{entry['task_title']}' -> Note: \"{entry['note']}\"")
                
    # 3. Goal Progress
    lines.append("\n### 3. Goal Progress Board")
    if not context.goals:
        lines.append("- No active goals recorded.")
    else:
        for g in context.goals:
            status = "Completed" if g.completed else "In Progress"
            lines.append(f"- **Goal**: \"{g.title}\" | Category: {g.category} | Progress: {g.progress}% | Target: {g.target_date or 'No Target'} | Status: {status}")
            
    # 4. Project Health & Deadline Risk
    lines.append("\n### 4. Project Health & Deadline Risk")
    if not context.projects:
        lines.append("- No active projects recorded.")
    else:
        for p in context.projects:
            lines.append(f"\n- **Project**: \"{p.title}\"")
            lines.append(f"  - Deadline: {p.deadline}")
            lines.append(f"  - Completion Progress: {p.progress}%")
            lines.append(f"  - Urgency Status: {p.urgency} (Risk Tag)")
            lines.append("  - Milestones:")
            if not p.milestones:
                lines.append("    - No milestones added.")
            else:
                for m in p.milestones:
                    m_status = "Checked" if m.completed else "Pending"
                    lines.append(f"    * [{m_status}] {m.title}")
                    
    # 5. OS Dimension Metrics (Scoring, Focus, Reminders)
    lines.append("\n### 5. Productivity OS Core Metrics")
    period_metrics = context.analytics.get("metrics", {})
    lines.append("\n**Period-Scoped Productivity Metrics**:")
    lines.append(f"- **Completed Slots**: {period_metrics.get('completed_slots', 0)}")
    lines.append(f"- **Missed Slots**: {period_metrics.get('missed_slots', 0)}")
    lines.append(f"- **Perfect Days in Period**: {period_metrics.get('perfect_days', 0)}")

    if context.focus_stats:
        duration_sec = context.focus_stats.get('total_duration_sec', 0)
        hours = round(duration_sec / 3600.0, 2)
        lines.append("\n**Focus Session Analytics**:")
        lines.append(f"- **Total Focused Work**: {hours} hours")
        lines.append(f"- **Total Focus Sessions Started**: {context.focus_stats.get('total_sessions', 0)}")
        lines.append(f"- **Completed Focus Sessions**: {context.focus_stats.get('completed_sessions', 0)}")
        
    if context.reminder_stats:
        lines.append("\n**Task Reminders Adherence**:")
        lines.append(f"- **Total Reminders Set**: {context.reminder_stats.get('total_reminders', 0)}")
        lines.append(f"- **Reminders Completed**: {context.reminder_stats.get('completed_reminders', 0)}")

    if context.prediction_summary_markdown:
        lines.append("\n### 6. Statistical Predictions & Forecasts")
        lines.append("Use the following compact summaries directly. Do not invent risks that contradict them.")
        lines.append(context.prediction_summary_markdown)

    lines.append("\n---")
    lines.append("\nPlease review this context package carefully and formulate your reflection report. Make sure to adhere EXACTLY to the mandated section headers. Do not output any additional preambles or chat messages, start immediately with the top level header (# Weekly Reflection or # Monthly Reflection).")
    
    return "\n".join(lines)
