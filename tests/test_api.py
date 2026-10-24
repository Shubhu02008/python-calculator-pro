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
    assert "currency_conversion" in body["features"]
    assert "gst_calculator" in body["features"]


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


def test_general_polynomial_mode_handles_multivariable_mixed_terms_and_degree_four():
    response = client.post(
        "/api/v1/equations/solve",
        json={"equation": "xy + yz = 3x^2yz", "equation_type": "polynomial"},
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["status"] == "infinite_solutions"
    assert body["variables"] == ["x", "y", "z"]
    assert body["degree"] == 4
    assert body["relations"]


def test_general_polynomial_mode_solves_single_variable_degree_five():
    response = client.post(
        "/api/v1/equations/solve",
        json={"equation": "x^5 - 1 = 0", "equation_type": "polynomial"},
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["status"] == "solved"
    assert body["degree"] == 5
    assert len(body["solutions"]) == 5


def test_equation_system_solves_two_variables():
    response = client.post(
        "/api/v1/equations/system",
        json={"equations": ["x + y = 5", "y - x = 1"]},
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["status"] == "solved"
    assert body["variables"] == ["x", "y"]
    assert body["solutions"] == [{"x": "2", "y": "3"}]


def test_equation_system_rejects_a_single_equation():
    response = client.post(
        "/api/v1/equations/system",
        json={"equations": ["x + y = 5"]},
    )

    assert response.status_code == 422


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



def test_discount_endpoint():
    response = client.post(
        "/api/v1/discount/calculate",
        json={"price": 1000, "discount_percent": 10},
    )
    assert response.status_code == 200
    assert response.json()["final_price"] == 900


def test_gst_endpoint():
    response = client.post(
        "/api/v1/gst/calculate",
        json={"amount": 1000, "gst_rate": 18},
    )
    assert response.status_code == 200
    assert response.json()["gst_amount"] == 180
    assert response.json()["total_amount"] == 1180


def test_simple_interest_endpoint():
    response = client.post(
        "/api/v1/finance/simple-interest",
        json={"principal": 1000, "annual_rate": 10, "years": 2},
    )
    assert response.status_code == 200
    assert response.json()["interest"] == 200
    assert response.json()["total_amount"] == 1200


def test_compound_interest_endpoint():
    response = client.post(
        "/api/v1/finance/compound-interest",
        json={"principal": 1000, "annual_rate": 10, "years": 2},
    )
    assert response.status_code == 200
    assert response.json()["total_amount"] == 1210


def test_emi_endpoint():
    response = client.post(
        "/api/v1/finance/emi",
        json={"principal": 12000, "annual_rate": 0, "tenure_months": 12},
    )
    assert response.status_code == 200
    assert response.json()["monthly_emi"] == 1000


def test_number_base_endpoint():
    response = client.post(
        "/api/v1/numbers/convert-base",
        json={"value": "FF", "from_base": 16, "to_base": 2},
    )
    assert response.status_code == 200
    assert response.json()["converted_value"] == "11111111"


def test_bmi_endpoint():
    response = client.post(
        "/api/v1/health/bmi",
        json={"weight_kg": 70, "height_m": 1.75},
    )
    assert response.status_code == 200
    assert response.json()["bmi"] == 22.86
    assert response.json()["category"] == "normal"


def test_date_calculator_endpoint():
    response = client.post(
        "/api/v1/dates/calculate",
        json={"operation": "add_days", "date": "2024-02-28", "days": 2},
    )
    assert response.status_code == 200
    assert response.json()["result_date"] == "2024-03-01"


def test_currency_endpoint_uses_calculator_without_network(monkeypatch):
    monkeypatch.setattr(
        "api.convert_currency",
        lambda amount, source, target: {
            "amount": float(amount),
            "from_currency": source.upper(),
            "to_currency": target.upper(),
            "exchange_rate": 83.0,
            "converted_amount": 83.0 * float(amount),
            "rate_date": "test-date",
            "source": "test",
        },
    )
    response = client.post(
        "/api/v1/currency/convert",
        json={"amount": 1, "from_currency": "usd", "to_currency": "inr"},
    )
    assert response.status_code == 200
    assert response.json()["converted_amount"] == 83.0


def test_utility_endpoint_validation_errors_are_normalized():
    response = client.post(
        "/api/v1/gst/calculate",
        json={"amount": 100, "gst_rate": 18, "extra": True},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"



def test_root_describes_api_service():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Python Calculator Pro API"
    assert body["docs"] == "/docs"


def test_graph_evaluate_endpoint():
    response = client.post(
        "/api/v1/graph/evaluate",
        json={"expression": "x^2 + 1", "x_value": 3},
    )
    assert response.status_code == 200
    assert response.json() == {"x": 3.0, "y": 10.0}



def test_single_two_variable_linear_equation_returns_relation():
    response = client.post(
        "/api/v1/equations/solve",
        json={"equation": "2x + 3y = 12"},
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["status"] == "infinite_solutions"
    assert body["variables"] == ["x", "y"]
    assert body["relations"]
    assert body["relations"][0].startswith("y = ")


def test_single_two_variable_quadratic_equation_returns_both_branches():
    response = client.post(
        "/api/v1/equations/solve",
        json={"equation": "x^2 + y^2 = 25"},
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["status"] == "infinite_solutions"
    assert body["variables"] == ["x", "y"]
    assert len(body["relations"]) == 2
    assert all(relation.startswith("y = ") for relation in body["relations"])


def test_multivariable_quadratic_equation_with_three_variables_returns_relation():
    response = client.post(
        "/api/v1/equations/solve",
        json={
            "equation": "x^2 + y + z + 18 = 0",
            "equation_type": "multivariable_quadratic",
        },
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["status"] == "infinite_solutions"
    assert body["variables"] == ["x", "y", "z"]
    assert body["relations"]
    assert body["relations"][0].startswith("z = ")


def test_equation_type_rejects_wrong_polynomial_degree():
    response = client.post(
        "/api/v1/equations/solve",
        json={"equation": "x^2 + 1 = 0", "equation_type": "linear"},
    )

    assert response.status_code == 422
    assert "degree 1" in response.json()["error"]["message"]


def test_multivariable_equation_type_requires_multiple_variables():
    response = client.post(
        "/api/v1/equations/solve",
        json={"equation": "x + 2 = 0", "equation_type": "multivariable_linear"},
    )

    assert response.status_code == 422
    assert "at least two" in response.json()["error"]["message"]



def test_implicit_graph_endpoint_plots_sideways_parabola():
    response = client.post(
        "/api/v1/graph/relation",
        json={
            "relation": "y^2 = 18x",
            "x_min": -1,
            "x_max": 10,
            "y_min": -10,
            "y_max": 10,
            "grid_size": 80,
        },
    )
    assert response.status_code == 200, response.json()
    body = response.json()
    assert len(body["segments"]) > 20
    assert any(segment["y1"] > 1 and segment["y2"] > 1 for segment in body["segments"])
    assert any(segment["y1"] < -1 and segment["y2"] < -1 for segment in body["segments"])


def test_implicit_graph_endpoint_plots_circle():
    response = client.post(
        "/api/v1/graph/relation",
        json={
            "relation": "x^2 + y^2 = 25",
            "x_min": -6,
            "x_max": 6,
            "y_min": -6,
            "y_max": 6,
            "grid_size": 80,
        },
    )
    assert response.status_code == 200, response.json()
    assert len(response.json()["segments"]) > 100
