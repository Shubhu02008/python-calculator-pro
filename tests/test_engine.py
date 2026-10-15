import math
from decimal import Decimal

import pytest

from engine import (
    CalculatorError,
    approximate_expression,
    calculate_operation,
    convert_unit,
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

@pytest.mark.parametrize(
    "operation",
    [
        lambda: evaluate_expression("9" * 1_001),
        lambda: evaluate_expression("2^10001"),
        lambda: solve_equation("(" * 1_200 + "x" + ")" * 1_200 + " = 0"),
        lambda: expand_binomial("(x + 2)^101"),
    ],
)
def test_public_api_normalizes_backend_validation_errors(operation):
    with pytest.raises(CalculatorError):
        operation()


def test_public_api_preserves_exact_integer_expression_result():
    assert evaluate_expression("9007199254740993 + 1") == 9007199254740994


@pytest.mark.parametrize(
    "value,source,target,expected",
    [
        (1, "km", "m", 1000),
        (0, "C", "F", 32),
        (36, "km/h", "m/s", 10),
        (1, "acre", "m2", 4046.8564224),
        (60, "min", "s", 3600),
    ],
)
def test_public_unit_conversion(value, source, target, expected):
    assert convert_unit(value, source, target) == pytest.approx(expected)


@pytest.mark.parametrize(
    "value,source,target",
    [
        (True, "m", "km"),
        (math.inf, "m", "km"),
        (1, "m", "kg"),
        (1, "parsec", "m"),
        (1, None, "m"),
    ],
)
def test_public_unit_conversion_errors_use_calculator_error(value, source, target):
    with pytest.raises(CalculatorError):
        convert_unit(value, source, target)


def test_public_graph_function_evaluation():
    from engine import evaluate_function

    assert evaluate_function("x^2 - 4", 3) == pytest.approx(5)
    assert evaluate_function("sin(x)", math.pi / 2) == pytest.approx(1)


def test_public_graph_sampling_returns_coordinate_pairs_and_gaps():
    from engine import sample_function

    assert sample_function("x^2", -1, 1, points=3) == pytest.approx(
        [(-1, 1), (0, 0), (1, 1)]
    )
    samples = sample_function("1/x", -1, 1, points=3)
    assert samples[1] == (0.0, None)


@pytest.mark.parametrize(
    "call",
    [
        lambda: __import__("engine").evaluate_function("x^2", math.inf),
        lambda: __import__("engine").sample_function("x^2", 1, -1),
        lambda: __import__("engine").sample_function("x^2", -1, 1, points=1),
        lambda: __import__("engine").evaluate_function("unknown(x)", 1),
    ],
)
def test_public_graph_errors_use_calculator_error(call):
    with pytest.raises(CalculatorError):
        call()
