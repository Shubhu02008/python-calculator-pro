"""Basic arithmetic operations and expression evaluation."""

import math

from parser import tokenize, evaluate_tokens


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        return "Cannot divide by zero"
    return a / b


def _is_finite_number(value):
    """Return whether value is a finite real number supported by the engine."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _require_finite_result(result):
    """Reject arithmetic results that exceed the supported numeric range."""
    if not _is_finite_number(result):
        raise ValueError("The result is outside the supported range.")
    return result


def calculate(operation, numbers=None):
    """Calculate a named operation or evaluate an arithmetic expression.

    When numbers is None, operation is treated as an expression string.
    Named operations accept a non-empty list of finite real numeric values.
    """
    if numbers is None:
        return evaluate_tokens(tokenize(operation))

    if not isinstance(numbers, (list, tuple)) or not numbers:
        raise ValueError("Please provide at least one number.")

    if operation not in {"add", "subtract", "multiply", "divide"}:
        return "Invalid operation"

    if not all(_is_finite_number(number) for number in numbers):
        raise ValueError("Numbers must be finite real numeric values.")

    if operation == "add":
        result = sum(numbers)
    elif operation == "subtract":
        result = numbers[0]
        for number in numbers[1:]:
            result = subtract(result, number)
    elif operation == "multiply":
        result = 1
        for number in numbers:
            result = multiply(result, number)
    else:
        result = numbers[0]
        for number in numbers[1:]:
            result = divide(result, number)
            if result == "Cannot divide by zero":
                return result

    return _require_finite_result(result)
