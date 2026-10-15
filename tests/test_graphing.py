import math

import pytest

from graphing import evaluate_function


@pytest.mark.parametrize(
    "expression,x_value,expected",
    [
        ("x^2", 3, 9),
        ("x^2 - 4", -2, 0),
        ("2x + 1", 4, 9),
        ("sin(x)", math.pi / 2, 1),
        ("sqrt(x)", 9, 3),
        ("(x + 1)^2", -3, 4),
        ("5", 10, 5),
    ],
)
def test_evaluate_function_at_x(expression, x_value, expected):
    assert evaluate_function(expression, x_value) == pytest.approx(expected)


def test_replaces_only_standalone_x_identifier():
    assert evaluate_function("exp(1) + x", 2) == pytest.approx(math.e + 2)


@pytest.mark.parametrize("x_value", [True, "2", None, math.inf, -math.inf, math.nan])
def test_rejects_invalid_x_values(x_value):
    with pytest.raises(ValueError, match="x value"):
        evaluate_function("x^2", x_value)


@pytest.mark.parametrize("expression", ["", "   ", "x / 0", "sqrt(x)", "x @ 2"])
def test_rejects_invalid_or_undefined_function_evaluations(expression):
    with pytest.raises(ValueError):
        evaluate_function(expression, -1 if expression == "sqrt(x)" else 2)


def test_negative_x_is_parenthesized_before_substitution():
    assert evaluate_function("x^2", -3) == 9


def test_does_not_execute_python_code():
    with pytest.raises(ValueError):
        evaluate_function("__import__('os')", 1)
