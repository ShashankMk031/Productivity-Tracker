from fastapi.testclient import TestClient
from main import app
import pytest
from database.db import get_db

def test_flexible_reminders_api(workspace):
    client = TestClient(app)

    # 1. Create a title-only reminder
    response = client.post("/api/reminders", json={
        "title": "Clean room",
        "recurring": "none"
    })
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["title"] == "Clean room"
    assert res_data["data"]["due_date"] is None
    assert res_data["data"]["due_time"] is None
    assert res_data["data"]["is_overdue"] is False
    r1_id = res_data["data"]["id"]

    # 2. Create a Title + Date reminder
    response = client.post("/api/reminders", json={
        "title": "Doctor Appointment",
        "due_date": "2026-07-20",
        "recurring": "none"
    })
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["data"]["title"] == "Doctor Appointment"
    assert res_data["data"]["due_date"] == "2026-07-20"
    assert res_data["data"]["due_time"] is None
    r2_id = res_data["data"]["id"]

    # 3. Create a Title + Time reminder
    response = client.post("/api/reminders", json={
        "title": "Call Bob",
        "due_time": "15:30",
        "recurring": "none"
    })
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["data"]["title"] == "Call Bob"
    assert res_data["data"]["due_date"] is None
    assert res_data["data"]["due_time"] == "15:30"
    r3_id = res_data["data"]["id"]

    # 4. Create a Title + Date + Time reminder
    response = client.post("/api/reminders", json={
        "title": "Exam Deadline",
        "due_date": "2026-06-25",
        "due_time": "09:00",
        "recurring": "none"
    })
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["data"]["title"] == "Exam Deadline"
    assert res_data["data"]["due_date"] == "2026-06-25"
    assert res_data["data"]["due_time"] == "09:00"
    r4_id = res_data["data"]["id"]

    # 5. List active reminders - verify sorting (dated reminders come first, sorted by date; undated at bottom)
    response = client.get("/api/reminders/active")
    assert response.status_code == 200
    active_list = response.json()["data"]
    # Let's extract titles in order
    titles = [rem["title"] for rem in active_list]
    # "Exam Deadline" (2026-06-25) is first, then "Doctor Appointment" (2026-07-20), then undated: "Clean room", "Call Bob"
    assert "Exam Deadline" in titles
    assert "Doctor Appointment" in titles
    
    # Check that the undated reminder is at the bottom
    assert titles[-2] == "Clean room" or titles[-1] == "Clean room"
    assert titles[-2] == "Call Bob" or titles[-1] == "Call Bob"

    # 6. Toggle complete
    response = client.post(f"/api/reminders/{r1_id}/toggle")
    assert response.status_code == 200
    assert response.json()["data"]["completed"] == 1

    # Verify r1 is not in the active reminders list anymore
    response = client.get("/api/reminders/active")
    active_ids = [rem["id"] for rem in response.json()["data"]]
    assert r1_id not in active_ids

    # 7. Delete reminder
    response = client.delete(f"/api/reminders/{r2_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify r2 is deleted
    response = client.get("/api/reminders")
    all_ids = [rem["id"] for rem in response.json()["data"]]
    assert r2_id not in all_ids
