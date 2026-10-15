import math
from decimal import Decimal

import pytest

from engine import (
    CalculatorError,
    approximate_expression,
    calculate_operation,
    evaluate_expression,
    expand_binomial,
    solve_equation,
)


def test_evaluate_expression():
    assert evaluate_expression("sin(pi / 2) + √25") == pytest.approx(6)


def test_calculate_basic_operations():
    assert calculate_operation("add", [2, 3, 4]) == 9
    assert calculate_operation("subtract", [10, 3, 2]) == 5
    assert calculate_operation("multiply", [2, 3, 4]) == 24
    assert calculate_operation("divide", [20, 2, 5]) == 2


def test_integer_arithmetic_preserves_arbitrary_precision():
    large = 10**1000
    assert calculate_operation("add", [large, 1]) == large + 1
    assert calculate_operation("multiply", [large, 9]) == large * 9


def test_approximate_expression_defaults_to_15_significant_digits():
    assert approximate_expression("sqrt(2)") == Decimal("1.41421356237310")


def test_approximate_expression_accepts_custom_precision():
    assert approximate_expression("1 / 3", 6) == Decimal("0.333333")


@pytest.mark.parametrize("precision", [0, -1, 101, True, 2.5, "15"])
def test_approximation_rejects_invalid_precision(precision):
    with pytest.raises(CalculatorError, match="precision"):
        approximate_expression("sqrt(2)", precision)


def test_solve_equation():
    assert solve_equation("x^2 - 5x + 6 = 0") == [2.0, 3.0]


def test_expand_binomial():
    assert expand_binomial("(x + 2)^3") == "x^3 + 6x^2 + 12x + 8"


@pytest.mark.parametrize("expression", ["", "2 / 0", "1e308 * 1e308"])
def test_expression_errors_use_public_exception(expression):
    with pytest.raises(CalculatorError):
        evaluate_expression(expression)


@pytest.mark.parametrize(
    "operation,numbers",
    [
        ("add", [math.inf, 1]),
        ("multiply", [math.nan, 2]),
        ("divide", [10, 0]),
        ("subtract", [10]),
        ("unknown", [1, 2]),
        ("add", []),
    ],
)
def test_operation_errors_use_public_exception(operation, numbers):
    with pytest.raises(CalculatorError):
        calculate_operation(operation, numbers)


@pytest.mark.parametrize(
    "function,value",
    [
        (evaluate_expression, None),
        (solve_equation, 42),
        (expand_binomial, None),
    ],
)
def test_public_functions_reject_wrong_input_types(function, value):
    with pytest.raises(CalculatorError):
        function(value)


def test_solver_non_finite_roots_are_rejected():
    with pytest.raises(CalculatorError):
        solve_equation("1e308x^2 + x + 1 = 0")
