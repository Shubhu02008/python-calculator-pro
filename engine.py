"""Stable, UI-independent public API for Python Calculator Pro.

Application interfaces should call this module instead of importing parser or
CLI implementation details directly. Public operations raise CalculatorError
for invalid input and unsupported numerical results.
"""

import math
from numbers import Real

from binomial_theorem import expand_binomial as _expand_binomial
from calculator import calculate as _calculate
from equation_solver import solve_equation as _solve_equation


class CalculatorError(ValueError):
    """An input or calculation error suitable for display by any interface."""


def _finite_number(value, *, label="value"):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise CalculatorError(f"{label.capitalize()} must be a real number.")
    if not math.isfinite(value):
        raise CalculatorError(f"{label.capitalize()} must be finite.")
    return value


def _check_result(value):
    """Reject non-finite numerical outputs without restricting status messages."""
    if isinstance(value, bool):
        return value
    if isinstance(value, Real):
        if not math.isfinite(value):
            raise CalculatorError("The result is outside the supported range.")
    elif isinstance(value, complex):
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise CalculatorError("The result is outside the supported range.")
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check_result(item)
    return value


def _run(operation):
    try:
        return _check_result(operation())
    except CalculatorError:
        raise
    except (ValueError, TypeError, IndexError, ZeroDivisionError, OverflowError) as exc:
        raise CalculatorError(str(exc) or "Invalid mathematical input.") from exc


def evaluate_expression(expression):
    """Evaluate an arithmetic/scientific expression and return its numeric result."""
    if not isinstance(expression, str):
        raise CalculatorError("Expression must be text.")
    return _run(lambda: _calculate(expression))


def calculate_operation(operation, numbers):
    """Run a named basic operation ('add', 'subtract', 'multiply', or 'divide')."""
    if not isinstance(operation, str):
        raise CalculatorError("Operation name must be text.")
    if operation not in {"add", "subtract", "multiply", "divide"}:
        raise CalculatorError(f"Unknown operation: {operation!r}.")
    if not isinstance(numbers, (list, tuple)) or not numbers:
        raise CalculatorError("Please provide at least one number.")
    checked_numbers = [_finite_number(number, label="number") for number in numbers]
    if operation in {"subtract", "divide"} and len(checked_numbers) < 2:
        raise CalculatorError(f"Operation {operation!r} requires at least two numbers.")
    if operation == "divide" and any(number == 0 for number in checked_numbers[1:]):
        raise CalculatorError("Cannot divide by zero.")
    result = _run(lambda: _calculate(operation, checked_numbers))
    if isinstance(result, str):
        raise CalculatorError(result)
    return result


def solve_equation(equation):
    """Solve a linear, quadratic, or cubic equation in x."""
    if not isinstance(equation, str):
        raise CalculatorError("Equation must be text.")
    return _run(lambda: _solve_equation(equation))


def expand_binomial(expression):
    """Expand a supported binomial expression and return its formatted text."""
    if not isinstance(expression, str):
        raise CalculatorError("Binomial expression must be text.")
    return _run(lambda: _expand_binomial(expression))


__all__ = [
    "CalculatorError",
    "calculate_operation",
    "evaluate_expression",
    "expand_binomial",
    "solve_equation",
]
