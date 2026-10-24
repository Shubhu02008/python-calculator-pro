import pytest

import calculator_tools
from calculator_tools import (
    calculate_bmi,
    calculate_compound_interest,
    calculate_date,
    calculate_discount,
    calculate_emi,
    calculate_gst,
    calculate_simple_interest,
    convert_currency,
    convert_number_base,
)


def test_currency_conversion_uses_provider_rates(monkeypatch):
    monkeypatch.setattr(
        calculator_tools,
        "_fetch_currency_rates",
        lambda base: {"result": "success", "rates": {"INR": 83.25}, "time_last_update_utc": "today"},
    )
    result = convert_currency(10, "usd", "inr")
    assert result["converted_amount"] == 832.5
    assert result["exchange_rate"] == 83.25
    assert result["from_currency"] == "USD"
    assert result["to_currency"] == "INR"


@pytest.mark.parametrize("amount,source,target", [(-1, "USD", "INR"), (1, "US", "INR"), (1, "USD", "1NR")])
def test_currency_conversion_rejects_invalid_inputs(amount, source, target):
    with pytest.raises(ValueError):
        convert_currency(amount, source, target)


def test_currency_conversion_rejects_missing_rate(monkeypatch):
    monkeypatch.setattr(
        calculator_tools,
        "_fetch_currency_rates",
        lambda base: {"result": "success", "rates": {}, "time_last_update_utc": "today"},
    )
    with pytest.raises(ValueError, match="not supported"):
        convert_currency(1, "USD", "INR")


def test_discount_calculation():
    assert calculate_discount(1000, 15) == {
        "original_price": 1000.0,
        "discount_percent": 15.0,
        "discount_amount": 150.0,
        "final_price": 850.0,
    }


@pytest.mark.parametrize("percent", [-1, 101])
def test_discount_rejects_out_of_range_percentage(percent):
    with pytest.raises(ValueError):
        calculate_discount(100, percent)


def test_gst_exclusive_and_inclusive():
    assert calculate_gst(1000, 18) == {
        "base_amount": 1000.0, "gst_rate": 18.0, "gst_amount": 180.0,
        "total_amount": 1180.0, "inclusive": False,
    }
    inclusive = calculate_gst(1180, 18, inclusive=True)
    assert inclusive["base_amount"] == 1000
    assert inclusive["gst_amount"] == 180
    assert inclusive["total_amount"] == 1180


def test_simple_and_compound_interest():
    simple = calculate_simple_interest(1000, 10, 2)
    assert simple["interest"] == 200
    assert simple["total_amount"] == 1200
    compound = calculate_compound_interest(1000, 10, 2)
    assert compound["interest"] == 210
    assert compound["total_amount"] == 1210


def test_compound_interest_supports_monthly_compounding():
    result = calculate_compound_interest(1000, 12, 1, compounding_per_year=12)
    assert result["total_amount"] == pytest.approx(1126.83)


def test_emi_calculation_and_zero_interest():
    result = calculate_emi(100000, 12, 12)
    assert result["monthly_emi"] == pytest.approx(8884.88, abs=0.02)
    zero_rate = calculate_emi(12000, 0, 12)
    assert zero_rate["monthly_emi"] == 1000
    assert zero_rate["total_interest"] == 0


def test_number_base_conversion():
    assert convert_number_base("FF", 16, 2)["converted_value"] == "11111111"
    assert convert_number_base("-1010", 2, 10)["converted_value"] == "-10"
    assert convert_number_base("0", 10, 36)["converted_value"] == "0"


@pytest.mark.parametrize("value,source,target", [("2", 2, 1), ("2", 2, 37), ("2", 1, 10), ("G", 16, 10)])
def test_number_base_conversion_rejects_invalid_inputs(value, source, target):
    with pytest.raises(ValueError):
        convert_number_base(value, source, target)


def test_bmi_calculation_categories():
    assert calculate_bmi(70, 1.75)["bmi"] == 22.86
    assert calculate_bmi(45, 1.75)["category"] == "underweight"
    assert calculate_bmi(90, 1.75)["category"] == "overweight"
    assert calculate_bmi(110, 1.75)["category"] == "obesity"


@pytest.mark.parametrize("weight,height", [(0, 1.7), (70, 0), (-1, 1.7)])
def test_bmi_rejects_non_positive_measurements(weight, height):
    with pytest.raises(ValueError):
        calculate_bmi(weight, height)


def test_date_arithmetic_and_difference():
    assert calculate_date("add_days", "2024-02-28", days=2)["result_date"] == "2024-03-01"
    assert calculate_date("subtract_days", "2024-03-01", days=1)["result_date"] == "2024-02-29"
    result = calculate_date("difference", "2026-01-01", other_date="2026-01-31")
    assert result["days_difference"] == 30
    assert result["absolute_days"] == 30


def test_date_calculator_rejects_invalid_date_and_operation():
    with pytest.raises(ValueError, match="valid date"):
        calculate_date("add_days", "2025-02-30", days=1)
    with pytest.raises(ValueError, match="Operation"):
        calculate_date("next_month", "2025-01-01")



def test_emi_handles_high_rates_without_intermediate_overflow():
    result = calculate_emi(1000, 10000, 1200)
    assert result["monthly_emi"] == pytest.approx(8333.33, abs=0.01)
    assert result["monthly_emi"] > 0
