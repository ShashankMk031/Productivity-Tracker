from datetime import date
from pathlib import Path

import services.report_history_service as rhs
from ai.ai_service import AI_FAILURE_PLACEHOLDER, AIService


def test_generate_weekly_report(workspace, seeded_db, mock_ai):
    target = date(2026, 5, 31)
    data = rhs.generate_and_save_report(seeded_db, "weekly", report_date=target)
    seeded_db.commit()

    row = seeded_db.execute("SELECT * FROM reports WHERE id = ?", (data["id"],)).fetchone()
    assert row["type"] == "weekly"
    assert row["period_end"] == "2026-05-31"
    assert row["period_start"] == "2026-05-25"

    md_file = Path(row["markdown_path"])
    assert md_file.exists()
    content = md_file.read_text()
    assert "Mock AI reflection." in content
    assert "## Productivity Metrics" in content

    # Raw AI response artifact saved
    assert (workspace / "ai_reports" / "2026" / "May").exists()


def test_generate_monthly_report_period_math(workspace, seeded_db, mock_ai):
    target = date(2026, 4, 30)
    data = rhs.generate_and_save_report(seeded_db, "monthly", report_date=target)
    seeded_db.commit()

    row = seeded_db.execute("SELECT * FROM reports WHERE id = ?", (data["id"],)).fetchone()
    assert row["type"] == "monthly"
    assert row["period_start"] == "2026-04-01"
    assert row["period_end"] == "2026-04-30"


def test_failed_report_detected_and_regenerated_in_place(workspace, seeded_db, monkeypatch):
    target = date(2026, 5, 31)

    monkeypatch.setattr(AIService, "generate_reflection", lambda self, prompt: AI_FAILURE_PLACEHOLDER)
    data = rhs.generate_and_save_report(seeded_db, "weekly", report_date=target)
    seeded_db.commit()
    assert rhs.report_ai_failed(seeded_db, data["id"]) is True

    monkeypatch.setattr(AIService, "generate_reflection", lambda self, prompt: "Recovered reflection.")
    regenerated = rhs.generate_and_save_report(
        seeded_db, "weekly", report_date=target, replace_report_id=data["id"]
    )
    seeded_db.commit()

    assert regenerated["id"] == data["id"]
    assert rhs.report_ai_failed(seeded_db, data["id"]) is False
    count = seeded_db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    assert count == 1


def test_snapshot_files_do_not_overwrite_same_day(workspace, seeded_db):
    """Regression test for the %H%M%S-on-a-date bug."""
    from intelligence.snapshot_service import save_snapshot
    import time

    first = save_snapshot(seeded_db, "manual")
    time.sleep(1.1)
    second = save_snapshot(seeded_db, "manual")
    assert first != second
    assert first.exists() and second.exists()
