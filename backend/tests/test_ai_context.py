from datetime import date, timedelta

from ai.context_builder import build_ai_context
from ai.schemas import AIContextPackage


def test_build_ai_context_on_seeded_db(workspace, seeded_db):
    today = date.today()
    ctx = build_ai_context(
        seeded_db,
        period_type="weekly",
        period_start=(today - timedelta(days=6)).isoformat(),
        period_end=today.isoformat(),
    )

    assert isinstance(ctx, AIContextPackage)
    assert ctx.period_type == "weekly"
    assert len(ctx.goals) == 1
    assert ctx.goals[0].title == "Learn SQL"
    assert len(ctx.projects) == 1
    assert len(ctx.projects[0].milestones) == 2
    assert ctx.focus_stats["total_sessions"] == 1
    assert ctx.reminder_stats["total_reminders"] == 1
    assert set(ctx.scores.keys()) == {"consistency", "execution", "goal_progress"}
    assert ctx.intelligence_snapshot is not None
