from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_and_list_workspaces():
    response = client.post(
        "/v1/workspaces",
        json={
            "name": "Demo Workspace",
            "owner_id": "user-123",
            "description": "Simple demo workspace",
        },
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["name"] == "Demo Workspace"
    assert payload["status"] == "active"

    list_response = client.get("/v1/workspaces")
    assert list_response.status_code == 200
    workspaces = list_response.json()["data"]
    assert any(item["id"] == payload["id"] for item in workspaces)
