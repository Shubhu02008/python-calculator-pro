from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_calculus_derivative_endpoint():
    response = client.post(
        "/api/v1/calculus",
        json={"operation": "derivative", "expression": "x^3", "variable": "x"},
    )
    assert response.status_code == 200
    assert response.json()["result"] == "3*x**2"


def test_calculus_definite_integral_endpoint():
    response = client.post(
        "/api/v1/calculus",
        json={"operation": "definite_integral", "expression": "x^2", "lower": 0, "upper": 2},
    )
    assert response.status_code == 200
    assert response.json()["result"] == "8/3"


def test_calculus_rejects_unknown_fields():
    response = client.post(
        "/api/v1/calculus",
        json={"operation": "derivative", "expression": "x^2", "debug": True},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_statistics_endpoint():
    response = client.post(
        "/api/v1/statistics",
        json={"operation": "mean", "values": [2, 4, 6]},
    )
    assert response.status_code == 200
    assert response.json()["result"] == 4


def test_probability_binomial_endpoint():
    response = client.post(
        "/api/v1/probability",
        json={"operation": "binomial", "n": 4, "k": 2, "p": 0.5},
    )
    assert response.status_code == 200
    assert response.json()["result"] == 0.375


def test_capabilities_list_new_math_features():
    response = client.get("/api/v1/capabilities")
    assert response.status_code == 200
    features = response.json()["features"]
    assert "symbolic_calculus" in features
    assert "descriptive_statistics" in features
    assert "elementary_probability" in features
