from fastapi.testclient import TestClient
from main import app

def test_daily_notes_api_endpoints(workspace):
    client = TestClient(app)
    test_date = "2026-06-12"
    
    # 1. Fetch empty note
    response = client.get(f"/api/daily-notes/{test_date}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["content"] == ""

    # 2. Save note
    response = client.put(f"/api/daily-notes/{test_date}", json={"content": "Completed my coding sprint! feeling accomplished."})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["content"] == "Completed my coding sprint! feeling accomplished."

    # 3. Retrieve note again
    response = client.get(f"/api/daily-notes/{test_date}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["content"] == "Completed my coding sprint! feeling accomplished."

    # 4. Clear/Delete note (empty string)
    response = client.put(f"/api/daily-notes/{test_date}", json={"content": ""})
    assert response.status_code == 200
    
    response = client.get(f"/api/daily-notes/{test_date}")
    assert response.json()["data"]["content"] == ""
