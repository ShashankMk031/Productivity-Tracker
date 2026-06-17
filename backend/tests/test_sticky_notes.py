from fastapi.testclient import TestClient
from main import app
import pytest

def test_sticky_notes_lifecycle(workspace):
    client = TestClient(app)

    # 1. Fetching empty board should automatically create exactly one draft sticky note
    response = client.get("/api/sticky-notes")
    assert response.status_code == 200
    res_data = response.json()["data"]
    assert len(res_data) == 1
    
    draft = res_data[0]
    assert draft["is_draft"] is True
    assert draft["is_completed"] is False
    assert draft["content"] == ""
    assert draft["tag"] is None
    draft_id = draft["id"]

    # 2. Update the draft note's content and tag (autosave simulations)
    response = client.put(f"/api/sticky-notes/{draft_id}", json={
        "content": "Study for algorithm exams",
        "tag": "#college"
    })
    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["content"] == "Study for algorithm exams"
    assert updated["tag"] == "#college"
    assert updated["is_draft"] is True  # Should still remain a draft until explicitly pinned

    # 3. Modify coordinates, size, custom colors, rotation, and z_index (simulation of drag-and-drop, resizing, color picking, and tilting)
    response = client.put(f"/api/sticky-notes/{draft_id}", json={
        "position_x": 250.0,
        "position_y": 420.0,
        "width": 300.0,
        "height": 180.0,
        "text_color": "#ff0000",
        "z_index": 5,
        "rotation": 45.5
    })
    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["position_x"] == 250.0
    assert updated["position_y"] == 420.0
    assert updated["width"] == 300.0
    assert updated["height"] == 180.0
    assert updated["text_color"] == "#ff0000"
    assert updated["z_index"] == 5
    assert updated["rotation"] == 45.5

    # 4. Pin the draft note. This makes it a real note, and the backend should auto-generate a new empty draft.
    response = client.put(f"/api/sticky-notes/{draft_id}", json={
        "is_draft": False
    })
    assert response.status_code == 200
    pinned_note = response.json()["data"]
    assert pinned_note["is_draft"] is False

    # Fetch board again. We should now have 2 notes: the pinned note, and a new empty draft note.
    response = client.get("/api/sticky-notes")
    notes = response.json()["data"]
    assert len(notes) == 2
    
    draft_ids = [n["id"] for n in notes]
    assert draft_id in draft_ids
    
    # Locate the new draft note
    new_draft = [n for n in notes if n["id"] != draft_id][0]
    assert new_draft["is_draft"] is True
    assert new_draft["content"] == ""
    new_draft_id = new_draft["id"]

    # 5. Test search filter (by content and tag)
    # Search for "algorithm" -> should match our pinned note
    response = client.get("/api/sticky-notes?query=algorithm")
    search_res = response.json()["data"]
    assert len(search_res) == 1
    assert search_res[0]["id"] == draft_id

    # Search for "#college" -> should match our pinned note
    response = client.get("/api/sticky-notes?query=%23college")
    search_res = response.json()["data"]
    assert len(search_res) == 1
    assert search_res[0]["id"] == draft_id

    # Search for something non-existent -> should match nothing
    response = client.get("/api/sticky-notes?query=impossiblephrase")
    search_res = response.json()["data"]
    assert len(search_res) == 0

    # 6. Toggle complete checkbox
    response = client.put(f"/api/sticky-notes/{draft_id}", json={
        "is_completed": True
    })
    assert response.status_code == 200
    assert response.json()["data"]["is_completed"] is True

    # 7. Bulk archive completed notes
    response = client.post("/api/sticky-notes/archive-completed")
    assert response.status_code == 200
    assert response.json()["data"]["archived_count"] == 1

    # Verify that the archived note is no longer in the active notes list
    response = client.get("/api/sticky-notes")
    active_ids = [n["id"] for n in response.json()["data"]]
    assert draft_id not in active_ids
    # The active list should now contain only the active draft note (size 1)
    assert len(active_ids) == 1
    assert new_draft_id in active_ids

    # 8. Test delete sticky note
    response = client.delete(f"/api/sticky-notes/{new_draft_id}")
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True

    # Since we deleted the active draft, a new draft should have been auto-generated!
    response = client.get("/api/sticky-notes")
    notes_after_del = response.json()["data"]
    assert len(notes_after_del) == 1
    assert notes_after_del[0]["is_draft"] is True
    assert notes_after_del[0]["id"] != new_draft_id
