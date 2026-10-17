from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_health_check():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_capabilities_include_supported_unit_catalog():
    response = client.get("/api/v1/capabilities")

    assert response.status_code == 200
    body = response.json()
    assert "unit_conversion" in body["features"]
    dimensions = {item["id"]: item["units"] for item in body["unit_dimensions"]}
    assert "km" in dimensions["length"]
    assert "bigha" in dimensions["area"]
    assert "megabyte" in dimensions["data_size"]


def test_expression_endpoint_returns_structured_result():
    response = client.post(
        "/api/v1/calculate",
        json={"expression": "sin(pi / 2) + √25"},
    )

    assert response.status_code == 200
    assert response.json()["result"] == 6


def test_named_operation_endpoint():
    response = client.post(
        "/api/v1/operations",
        json={"operation": "multiply", "numbers": [2, 3, 4]},
    )

    assert response.status_code == 200
    assert response.json() == {"result": 24}


def test_unit_conversion_endpoint():
    response = client.post(
        "/api/v1/units/convert",
        json={"value": 5, "from_unit": "km", "to_unit": "m"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "value": 5000.0,
        "from_unit": "km",
        "to_unit": "m",
    }


def test_equation_endpoint_supports_complex_roots_as_json():
    response = client.post(
        "/api/v1/equations/solve",
        json={"equation": "x^2 + 1 = 0"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "solved"
    assert body["solutions"] == [
        {"real": 0.0, "imaginary": -1.0},
        {"real": 0.0, "imaginary": 1.0},
    ]


def test_equation_endpoint_reports_no_solution():
    response = client.post(
        "/api/v1/equations/solve",
        json={"equation": "x = x + 1"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "no_solution"


def test_binomial_endpoint():
    response = client.post(
        "/api/v1/binomials/expand",
        json={"expression": "(x + 2)^3"},
    )

    assert response.status_code == 200
    assert response.json() == {"expansion": "x^3 + 6x^2 + 12x + 8"}


def test_graph_sampling_uses_null_for_undefined_points():
    response = client.post(
        "/api/v1/graph/sample",
        json={"expression": "1/x", "x_min": -1, "x_max": 1, "points": 3},
    )

    assert response.status_code == 200
    assert response.json()["points"] == [
        {"x": -1.0, "y": -1.0},
        {"x": 0.0, "y": None},
        {"x": 1.0, "y": 1.0},
    ]


def test_calculation_error_uses_stable_error_envelope():
    response = client.post("/api/v1/calculate", json={"expression": "1 / 0"})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "calculation_error"
    assert "message" in body["error"]


def test_invalid_request_uses_stable_error_envelope():
    response = client.post(
        "/api/v1/operations",
        json={"operation": "add", "numbers": [True, 2]},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "invalid_request"
    assert body["error"]["details"]


def test_unknown_request_fields_are_rejected():
    response = client.post(
        "/api/v1/calculate",
        json={"expression": "2 + 2", "debug": True},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"



def test_cors_allows_local_development_origin_without_credentials():
    response = client.options(
        "/api/v1/calculate",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in response.headers



def test_calculate_endpoint_includes_simplified_fraction_and_approximation():
    response = client.post("/api/v1/calculate", json={"expression": "3 / 9"})

    assert response.status_code == 200
    assert response.json() == {
        "result": 1 / 3,
        "exact_fraction": "1/3",
        "approximation": "0.3333",
    }


def test_calculate_endpoint_leaves_fraction_fields_empty_for_irrational_result():
    response = client.post("/api/v1/calculate", json={"expression": "sqrt(2)"})

    assert response.status_code == 200
    assert response.json()["exact_fraction"] is None
    assert response.json()["approximation"] is None
