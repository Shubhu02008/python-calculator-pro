from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_surface_api_returns_grid():
    response = client.post(
        "/api/v1/graph/surface",
        json={
            "expression": "x^2+y^2",
            "x_min": -1,
            "x_max": 1,
            "y_min": -1,
            "y_max": 1,
            "grid_size": 9,
        },
    )
    assert response.status_code == 200, response.json()
    rows = response.json()["rows"]
    assert len(rows) == 9
    assert len(rows[0]) == 9
    assert rows[4][4]["z"] == 0


def test_surface_api_rejects_too_small_grid():
    response = client.post(
        "/api/v1/graph/surface",
        json={
            "expression": "x+y",
            "x_min": -1,
            "x_max": 1,
            "y_min": -1,
            "y_max": 1,
            "grid_size": 7,
        },
    )
    assert response.status_code == 422
