"""Stable, UI-independent public API for Python Calculator Pro.

Application interfaces should call this module instead of importing parser or
CLI implementation details directly. Public operations raise CalculatorError
for invalid input and unsupported numerical results.
"""

import math
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from numbers import Real

from parser import tokenize

from advanced_math import (
    calculate_calculus as _calculate_calculus,
    calculate_statistics as _calculate_statistics,
    calculate_probability as _calculate_probability,
    solve_equation_system as _solve_equation_system,
)

from binomial_theorem import expand_binomial as _expand_binomial
from calculator import calculate as _calculate
from equation_solver import solve_equation as _solve_equation
from unit_conversion import convert_unit as _convert_unit
from unit_conversion import list_supported_units as _list_supported_units
from graphing import evaluate_function as _evaluate_function
from graphing import sample_function as _sample_function

from calculator_tools import (
    calculate_bmi as _calculate_bmi,
    calculate_compound_interest as _calculate_compound_interest,
    calculate_date as _calculate_date,
    calculate_discount as _calculate_discount,
    calculate_emi as _calculate_emi,
    calculate_gst as _calculate_gst,
    calculate_simple_interest as _calculate_simple_interest,
    convert_currency as _convert_currency,
    convert_number_base as _convert_number_base,
)


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
    except (ValueError, TypeError, IndexError, ZeroDivisionError, OverflowError, RecursionError) as exc:
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



def fraction_form(expression):
    """Return a simplified exact fraction and a four-significant-digit approximation.

    Only expressions made from rational numeric literals and arithmetic operators
    are eligible. Scientific functions and constants are deliberately excluded so
    irrational or inexact results are never presented as exact fractions.
    Returns None for integer results or expressions without a safe exact fraction.
    """
    if not isinstance(expression, str):
        return None

    try:
        tokens = tokenize(expression)
        operators = {"+", "-", "*", "/", "^", "(", ")", "!", "%"}
        if any(
            isinstance(token, str) and token not in operators
            for token in tokens
        ):
            return None

        position = 0

        def peek(operator=None):
            if position >= len(tokens):
                return False
            return tokens[position] == operator if operator is not None else tokens[position]

        def parse_expression():
            nonlocal position
            value = parse_term()
            while peek("+") or peek("-"):
                operator = tokens[position]
                position += 1
                right = parse_term()
                value = value + right if operator == "+" else value - right
            return value

        def parse_term():
            nonlocal position
            value = parse_unary()
            while peek("*") or peek("/"):
                operator = tokens[position]
                position += 1
                right = parse_unary()
                if operator == "*":
                    value *= right
                else:
                    if right == 0:
                        raise ValueError("Division by zero.")
                    value /= right
            return value

        def parse_unary():
            nonlocal position
            if peek("+") or peek("-"):
                operator = tokens[position]
                position += 1
                value = parse_unary()
                return value if operator == "+" else -value
            return parse_power()

        def parse_power():
            nonlocal position
            value = parse_postfix()
            if peek("^"):
                position += 1
                exponent = parse_unary()
                if exponent.denominator != 1 or abs(exponent.numerator) > 100:
                    raise ValueError("Exponent is outside exact fraction limits.")
                value = value ** exponent.numerator
            return value

        def parse_postfix():
            nonlocal position
            value = parse_primary()
            while peek("!") or peek("%"):
                operator = tokens[position]
                position += 1
                if operator == "%":
                    value /= 100
                else:
                    if value.denominator != 1 or value < 0 or value > 170:
                        raise ValueError("Factorial is outside exact fraction limits.")
                    import math
                    value = Fraction(math.factorial(value.numerator), 1)
            return value

        def parse_primary():
            nonlocal position
            if position >= len(tokens):
                raise ValueError("Unexpected end of expression.")
            token = tokens[position]
            if token == "(":
                position += 1
                value = parse_expression()
                if not peek(")"):
                    raise ValueError("Missing closing parenthesis.")
                position += 1
                return value
            if token == ")" or isinstance(token, str):
                raise ValueError("Not a rational arithmetic expression.")
            position += 1
            if isinstance(token, bool):
                raise ValueError("Boolean values are not numeric literals.")
            return Fraction(token) if isinstance(token, int) else Fraction(str(token))

        result = parse_expression()
        if position != len(tokens) or result.denominator == 1:
            return None
        # Avoid producing very large strings or spending excessive work formatting them.
        if len(str(abs(result.numerator))) > 1000 or len(str(result.denominator)) > 1000:
            return None
        with localcontext() as context:
            context.prec = 50
            approximate = Decimal(result.numerator) / Decimal(result.denominator)
            approximation = format(approximate, ".4g")
        return {
            "exact_fraction": f"{result.numerator}/{result.denominator}",
            "approximation": approximation,
        }
    except (ArithmeticError, ValueError, TypeError, OverflowError, ZeroDivisionError):
        return None


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


def convert_unit(value, from_unit, to_unit):
    """Convert a real value between compatible supported measurement units."""
    checked_value = _finite_number(value, label="value")
    if not isinstance(from_unit, str) or not isinstance(to_unit, str):
        raise CalculatorError("Source and target units must be text.")
    return _run(lambda: _convert_unit(checked_value, from_unit, to_unit))


def evaluate_function(expression, x_value):
    """Evaluate a supported function expression at one real x-coordinate."""
    if not isinstance(expression, str):
        raise CalculatorError("Function expression must be text.")
    checked_x = _finite_number(x_value, label="x value")
    return _run(lambda: _evaluate_function(expression, checked_x))


def sample_function(expression, x_min, x_max, points=101):
    """Return graph-ready (x, y) samples; undefined y values are None."""
    if not isinstance(expression, str):
        raise CalculatorError("Function expression must be text.")
    checked_min = _finite_number(x_min, label="x_min")
    checked_max = _finite_number(x_max, label="x_max")
    return _run(lambda: _sample_function(expression, checked_min, checked_max, points))


def solve_equation(equation):
    """Solve a linear, quadratic, or cubic equation in x."""
    if not isinstance(equation, str):
        raise CalculatorError("Equation must be text.")
    return _run(lambda: _solve_equation(equation))


def solve_equation_system(equations):
    """Solve a small symbolic system using the restricted expression parser."""
    if not isinstance(equations, (list, tuple)):
        raise CalculatorError("Equations must be provided as a list of lines.")
    return _run(lambda: _solve_equation_system(equations))


def expand_binomial(expression):
    """Expand a supported binomial expression and return its formatted text."""
    if not isinstance(expression, str):
        raise CalculatorError("Binomial expression must be text.")
    return _run(lambda: _expand_binomial(expression))



def calculate_calculus(operation, expression, *, variable="x", order=1, lower=None, upper=None, point="0", direction="both"):
    """Differentiate, integrate, or evaluate a symbolic limit safely."""
    return _run(lambda: _calculate_calculus(
        operation, expression, variable=variable, order=order,
        lower=lower, upper=upper, point=point, direction=direction
    ))


def calculate_statistics(operation, values):
    """Calculate descriptive statistics for a list of real values."""
    return _run(lambda: _calculate_statistics(operation, values))


def calculate_probability(operation, **kwargs):
    """Calculate elementary probabilities, combinations, permutations, or binomial probabilities."""
    return _run(lambda: _calculate_probability(operation, **kwargs))


def list_supported_units():
    """Return supported unit identifiers grouped by measurement dimension.

    Unit identifiers are canonical strings accepted by convert_unit(). Each
    dimension maps to a tuple of identifiers, sorted for stable presentation.
    """
    return _run(_list_supported_units)



def calculate_bmi(weight_kg, height_m):
    """Calculate BMI from kilograms and metres."""
    return _run(lambda: _calculate_bmi(weight_kg, height_m))


def calculate_compound_interest(principal, annual_rate, years, compounding_per_year=1):
    """Calculate compound interest and maturity amount."""
    return _run(lambda: _calculate_compound_interest(principal, annual_rate, years, compounding_per_year))


def calculate_date(operation, date_value, *, days=0, other_date=None):
    """Perform ISO date arithmetic."""
    return _run(lambda: _calculate_date(operation, date_value, days=days, other_date=other_date))


def calculate_discount(price, discount_percent):
    """Calculate discount amount and final price."""
    return _run(lambda: _calculate_discount(price, discount_percent))


def calculate_emi(principal, annual_rate, tenure_months):
    """Calculate monthly loan EMI and total repayment."""
    return _run(lambda: _calculate_emi(principal, annual_rate, tenure_months))


def calculate_gst(amount, gst_rate, *, inclusive=False):
    """Calculate GST on a pre-tax amount or extract tax from an inclusive total."""
    return _run(lambda: _calculate_gst(amount, gst_rate, inclusive=inclusive))


def calculate_simple_interest(principal, annual_rate, years):
    """Calculate simple interest and maturity amount."""
    return _run(lambda: _calculate_simple_interest(principal, annual_rate, years))


def convert_currency(amount, from_currency, to_currency):
    """Convert currencies using latest available reference rates."""
    return _run(lambda: _convert_currency(amount, from_currency, to_currency))


def convert_number_base(value, from_base, to_base):
    """Convert an integer literal between bases 2 and 36."""
    return _run(lambda: _convert_number_base(value, from_base, to_base))


__all__ = [
    "CalculatorError",
    "approximate_expression",
    "calculate_operation",
    "convert_unit",
    "evaluate_expression",
    "fraction_form",
    "expand_binomial",
    "evaluate_function",
    "list_supported_units",
    "sample_function",
    "solve_equation",
    "calculate_bmi",
    "calculate_compound_interest",
    "calculate_date",
    "calculate_discount",
    "calculate_emi",
    "calculate_gst",
    "calculate_simple_interest",
    "convert_currency",
    "convert_number_base",
    "calculate_calculus",
    "calculate_statistics",
    "calculate_probability",
]
