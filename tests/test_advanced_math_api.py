import pytest

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



def test_calculus_indefinite_integral_endpoint():
    response = client.post(
        "/api/v1/calculus",
        json={"operation": "integral", "expression": "x^2", "variable": "x"},
    )
    assert response.status_code == 200
    assert response.json()["result"] == "x**3/3"


@pytest.mark.parametrize(
    ("direction", "expected"),
    [("both", "2"), ("plus", "oo"), ("minus", "-oo")],
)
def test_calculus_limit_endpoint_supports_direction(direction, expected):
    expression = "(x^2 - 1)/(x - 1)" if direction == "both" else "1/x"
    point = "1" if direction == "both" else "0"
    response = client.post(
        "/api/v1/calculus",
        json={
            "operation": "limit",
            "expression": expression,
            "variable": "x",
            "point": point,
            "direction": direction,
        },
    )
    assert response.status_code == 200
    assert response.json()["result"] == expected


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"operation": "mean", "values": [2, 4, 6]}, 4),
        ({"operation": "median", "values": [1, 3, 5, 7]}, 4),
        ({"operation": "mode", "values": [1, 2, 2, 3]}, [2]),
        ({"operation": "range", "values": [2, 9]}, 7),
        ({"operation": "minimum", "values": [2, 9]}, 2),
        ({"operation": "maximum", "values": [2, 9]}, 9),
        ({"operation": "variance", "values": [1, 2, 3]}, 1),
        ({"operation": "population_variance", "values": [1, 2, 3]}, 2 / 3),
        ({"operation": "standard_deviation", "values": [1, 2, 3]}, 1),
        ({"operation": "population_standard_deviation", "values": [1, 2, 3]}, (2 / 3) ** 0.5),
        ({"operation": "quartiles", "values": [1, 2, 3, 4]}, {"q1": 1.5, "q2": 2.5, "q3": 3.5}),
    ],
)
def test_statistics_endpoint_supports_each_operation(payload, expected):
    response = client.post("/api/v1/statistics", json=payload)
    assert response.status_code == 200
    assert response.json()["result"] == expected


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"operation": "simple", "favorable": 1, "total": 4}, 0.25),
        ({"operation": "complement", "event_a": 0.2}, 0.8),
        ({"operation": "conditional", "intersection": 0.2, "event_b": 0.5}, 0.4),
        ({"operation": "union", "event_a": 0.2, "event_b": 0.5, "intersection": 0.1}, 0.6),
        ({"operation": "permutation", "n": 5, "r": 2}, 20),
        ({"operation": "combination", "n": 5, "r": 2}, 10),
        ({"operation": "binomial", "n": 4, "k": 2, "p": 0.5}, 0.375),
    ],
)
def test_probability_endpoint_supports_each_operation(payload, expected):
    response = client.post("/api/v1/probability", json=payload)
    assert response.status_code == 200
    actual = response.json()["result"]
    if isinstance(expected, (dict, list)):
        assert actual == expected
    else:
        assert actual == pytest.approx(expected)


def test_probability_endpoint_returns_large_exact_counts_as_strings():
    response = client.post(
        "/api/v1/probability",
        json={"operation": "combination", "n": 10000, "r": 5000},
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert isinstance(result, str)
    assert len(result) == 3009


def test_probability_endpoint_rejects_result_too_large_for_safe_output():
    response = client.post(
        "/api/v1/probability",
        json={"operation": "permutation", "n": 10000, "r": 10000},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "calculation_error"


def test_statistics_endpoint_rejects_overflowing_variance():
    response = client.post(
        "/api/v1/statistics",
        json={"operation": "population_variance", "values": [-1e308, 1e308]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "calculation_error"
