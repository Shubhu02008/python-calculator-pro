import math

import pytest

from advanced_math import (
    calculate_calculus,
    calculate_probability,
    calculate_statistics,
)


def test_polynomial_derivative():
    result = calculate_calculus("derivative", "x^3 + 2*x", order=1)
    assert result["result"] == "3*x**2 + 2"


def test_higher_order_derivative():
    result = calculate_calculus("derivative", "x^4", order=2)
    assert result["result"] == "12*x**2"


def test_indefinite_integral():
    result = calculate_calculus("integral", "x^2")
    assert result["result"] == "x**3/3"


def test_definite_integral():
    result = calculate_calculus("definite_integral", "x^2", lower=0, upper=3)
    assert result["result"] == "9"


def test_limit_at_removable_discontinuity():
    result = calculate_calculus("limit", "(x^2 - 1)/(x - 1)", point="1")
    assert result["result"] == "2"


def test_one_sided_limit():
    result = calculate_calculus("limit", "1/x", point="0", direction="plus")
    assert result["result"] == "oo"


def test_calculus_rejects_unknown_function_and_python_code():
    with pytest.raises(ValueError, match="unsupported"):
        calculate_calculus("derivative", "__import__('os').system('whoami')")
    with pytest.raises(ValueError, match="unsupported"):
        calculate_calculus("derivative", "unknown(x)")


def test_statistics_mean_median_and_mode():
    assert calculate_statistics("mean", [1, 2, 3, 4])["result"] == 2.5
    assert calculate_statistics("median", [1, 4, 2, 3])["result"] == 2.5
    assert calculate_statistics("mode", [1, 2, 2, 3])["result"] == [2.0]


def test_sample_and_population_variance_are_distinct():
    assert calculate_statistics("variance", [1, 2, 3])["result"] == pytest.approx(1)
    assert calculate_statistics("population_variance", [1, 2, 3])["result"] == pytest.approx(2 / 3)
    assert calculate_statistics("population_standard_deviation", [1, 2, 3])["result"] == pytest.approx(math.sqrt(2 / 3))


def test_quartiles_return_none_for_missing_halves():
    result = calculate_statistics("quartiles", [7])
    assert result["result"] == {"q1": None, "q2": 7.0, "q3": None}


def test_statistics_reject_non_finite_values():
    with pytest.raises(ValueError, match="finite"):
        calculate_statistics("mean", [1, float("inf")])


def test_simple_probability():
    assert calculate_probability("simple", favorable=2, total=5)["result"] == pytest.approx(0.4)


def test_conditional_probability():
    assert calculate_probability("conditional", intersection=0.2, event_b=0.5)["result"] == pytest.approx(0.4)


def test_union_probability():
    assert calculate_probability("union", event_a=0.4, event_b=0.5, intersection=0.1)["result"] == pytest.approx(0.8)


def test_combinations_permutations_and_binomial_probability():
    assert calculate_probability("combination", n=5, r=2)["result"] == 10
    assert calculate_probability("permutation", n=5, r=2)["result"] == 20
    assert calculate_probability("binomial", n=4, k=2, p=0.5)["result"] == pytest.approx(0.375)


def test_probability_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_probability("simple", favorable=6, total=5)
    with pytest.raises(ValueError):
        calculate_probability("conditional", intersection=0.3, event_b=0)



def test_probability_large_exact_counts_are_returned_as_strings():
    result = calculate_probability("combination", n=10000, r=5000)["result"]
    assert isinstance(result, str)
    assert result.startswith("159")
    assert len(result) == 3009


def test_probability_rejects_counts_too_large_for_safe_json_output():
    with pytest.raises(ValueError, match="too large to return safely"):
        calculate_probability("permutation", n=10000, r=10000)


def test_statistics_large_values_do_not_overflow_the_mean():
    result = calculate_statistics("mean", [1e308, 1e308])
    assert result["result"] == pytest.approx(1e308)


def test_statistics_rejects_variance_that_overflows():
    with pytest.raises(ValueError, match="too large to calculate variance"):
        calculate_statistics("population_variance", [-1e308, 1e308])



def test_statistics_rejects_non_finite_range_result():
    with pytest.raises(ValueError, match="outside the supported numeric range"):
        calculate_statistics("range", [-1e308, 1e308])



def test_calculus_supports_reciprocal_trigonometric_functions():
    import sympy as sp

    x = sp.Symbol("x")
    results = {
        "sec": calculate_calculus("derivative", "sec(x)")["result"],
        "cosec": calculate_calculus("derivative", "cosec(x)")["result"],
        "cot": calculate_calculus("derivative", "cot(x)")["result"],
    }
    local_functions = {"x": x, "sec": sp.sec, "tan": sp.tan,
                       "csc": sp.csc, "cot": sp.cot, "sin": sp.sin}
    assert sp.simplify(sp.sympify(results["sec"], locals=local_functions) - sp.diff(sp.sec(x), x)) == 0
    assert sp.simplify(sp.sympify(results["cosec"], locals=local_functions) - sp.diff(sp.csc(x), x)) == 0
    assert sp.simplify(sp.sympify(results["cot"], locals=local_functions) - sp.diff(sp.cot(x), x)) == 0
