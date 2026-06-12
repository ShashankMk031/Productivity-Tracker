from datetime import datetime, timedelta

from intelligence.prediction_engine import generate_intelligence_snapshot, forecast_goals

EXPECTED_KEYS = {"generated_at", "prediction_version", "burnout", "habits", "deadlines", "goals", "focus"}
PREDICTOR_CONTRACT = ("risk_level", "warning_level", "reason", "supporting_metrics", "confidence")


def test_snapshot_on_empty_db(workspace, db):
    snap = generate_intelligence_snapshot(db)
    assert EXPECTED_KEYS <= set(snap.keys())
    assert snap["habits"] == []
    assert snap["deadlines"] == []
    assert snap["goals"] == []
    for key in PREDICTOR_CONTRACT:
        assert key in snap["burnout"]


def test_snapshot_on_seeded_db(workspace, seeded_db):
    snap = generate_intelligence_snapshot(seeded_db)
    assert len(snap["habits"]) == 1
    assert len(snap["deadlines"]) == 1
    assert len(snap["goals"]) == 1
    assert snap["deadlines"][0]["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    for key in PREDICTOR_CONTRACT:
        assert key in snap["deadlines"][0]


def test_goal_past_target_date_is_high_risk(workspace, db):
    created = (datetime.now() - timedelta(days=20)).date().isoformat()
    past_target = (datetime.now() - timedelta(days=5)).date().isoformat()
    db.execute(
        "INSERT INTO goals (title, category, progress, target_date, created_at) VALUES ('Overdue goal', 'General', 10, ?, ?)",
        (past_target, created),
    )
    db.commit()

    result = forecast_goals(db)
    assert len(result["goals"]) == 1
    assert result["goals"][0]["risk_level"] == "HIGH"
    assert result["goals"][0]["warning_level"] == "CRITICAL"
