"""Stable, UI-independent public API for Python Calculator Pro.

Application interfaces should call this module instead of importing parser or
CLI implementation details directly. Public operations raise CalculatorError
for invalid input and unsupported numerical results.
"""

import math
from decimal import Decimal, InvalidOperation, localcontext
from numbers import Real

from binomial_theorem import expand_binomial as _expand_binomial
from calculator import calculate as _calculate
from equation_solver import solve_equation as _solve_equation


_DEFAULT_APPROXIMATION_PRECISION = 15
_MAX_APPROXIMATION_PRECISION = 100


class CalculatorError(ValueError):
    """An input or calculation error suitable for display by any interface."""


def _finite_number(value, *, label="value"):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise CalculatorError(f"{label.capitalize()} must be a real number.")
    # Python integers have arbitrary precision and are always finite.
    if isinstance(value, int):
        return value
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise CalculatorError(f"{label.capitalize()} must be finite.")
    return value


def _check_result(value):
    """Reject non-finite numerical outputs without restricting status messages."""
    if isinstance(value, bool) or isinstance(value, int):
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
    """Evaluate an arithmetic/scientific expression and return its numeric result.

    The existing expression parser uses floating-point arithmetic, so results
    involving scientific functions or decimal literals may be approximate.
    """
    if not isinstance(expression, str):
        raise CalculatorError("Expression must be text.")
    return _run(lambda: _calculate(expression))


def approximate_expression(expression, significant_digits=_DEFAULT_APPROXIMATION_PRECISION):
    """Evaluate an expression and round its result to significant decimal digits.

    This controls the returned decimal precision; it does not increase the
    precision used internally by the existing floating-point expression parser.
    """
    if (
        isinstance(significant_digits, bool)
        or not isinstance(significant_digits, int)
        or not 1 <= significant_digits <= _MAX_APPROXIMATION_PRECISION
    ):
        raise CalculatorError(
            f"Approximation precision must be an integer from 1 to "
            f"{_MAX_APPROXIMATION_PRECISION}."
        )
    result = evaluate_expression(expression)
    try:
        decimal_result = Decimal(str(result))
        with localcontext() as context:
            context.prec = significant_digits
            return +decimal_result
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise CalculatorError("Could not format the approximate result.") from exc


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
    "approximate_expression",
    "calculate_operation",
    "evaluate_expression",
    "expand_binomial",
    "solve_equation",
]
