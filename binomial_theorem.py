"""Expand binomials using the binomial theorem."""

import math
import re


_TERM = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)?)\s*([A-Za-z]?)\s*$")
_MAX_BINOMIAL_EXPRESSION_LENGTH = 10_000


def _parse_term(term):
    match = _TERM.fullmatch(term)
    if match is None or not match.group(1) and not match.group(2):
        raise ValueError(f"Unsupported binomial term: {term!r}")

    coefficient_text, variable = match.groups()
    if coefficient_text in ("", "+"):
        coefficient = 1.0
    elif coefficient_text == "-":
        coefficient = -1.0
    else:
        coefficient = float(coefficient_text)

    if not math.isfinite(coefficient):
        raise ValueError("Binomial coefficients must be finite.")

    return coefficient, variable


def _format_number(number):
    if math.isclose(number, round(number), abs_tol=1e-10):
        return str(int(round(number)))
    return f"{number:.10g}"


def _format_monomial(coefficient, variables):
    pieces = []
    for variable, exponent in sorted(variables.items()):
        if exponent == 0:
            continue
        pieces.append(variable if exponent == 1 else f"{variable}^{exponent}")

    magnitude = abs(coefficient)
    if not pieces:
        body = _format_number(magnitude)
    else:
        prefix = "" if math.isclose(magnitude, 1.0, abs_tol=1e-12) else _format_number(magnitude)
        body = prefix + "".join(pieces)
    return body


def expand_binomial(expression):
    """Expand (a + b)^n for simple terms like x, 2x, 3, a, or -y.

    Example: '(x + 2)^3' -> 'x^3 + 6x^2 + 12x + 8'.
    Exponents from 0 through 100 are accepted.
    """
    if not isinstance(expression, str):
        raise ValueError("Binomial expression must be text.")
    if len(expression) > _MAX_BINOMIAL_EXPRESSION_LENGTH:
        raise ValueError(
            f"Binomial expression is too long (maximum "
            f"{_MAX_BINOMIAL_EXPRESSION_LENGTH} characters)."
        )

    match = re.fullmatch(
        r"\s*\(?\s*(.*?)\s*([+-])\s*(.*?)\s*\)?\s*\^\s*(\d+)\s*",
        expression,
    )
    if match is None:
        raise ValueError("Enter a binomial like (x + 2)^3 or (a - b)^4.")

    first_text, sign, second_text, exponent_text = match.groups()
    # Strip leading zeroes and bound the remaining decimal length before int()
    # so huge exponent strings cannot trigger Python's integer-string limit.
    normalized_exponent = exponent_text.lstrip("0") or "0"
    if len(normalized_exponent) > 3:
        raise ValueError("For readability, the exponent must be 100 or less.")
    exponent = int(normalized_exponent)
    if exponent > 100:
        raise ValueError("For readability, the exponent must be 100 or less.")

    first_coefficient, first_variable = _parse_term(first_text)
    second_coefficient, second_variable = _parse_term(second_text)
    if sign == "-":
        second_coefficient *= -1

    combined = {}
    for power in range(exponent, -1, -1):
        try:
            coefficient = (
                math.comb(exponent, power)
                * first_coefficient**power
                * second_coefficient ** (exponent - power)
            )
        except OverflowError as exc:
            raise ValueError(
                "The expanded coefficients are outside the supported range."
            ) from exc
        if not math.isfinite(coefficient):
            raise ValueError(
                "The expanded coefficients are outside the supported range."
            )
        variables = {}
        if first_variable:
            variables[first_variable] = variables.get(first_variable, 0) + power
        if second_variable:
            variables[second_variable] = (
                variables.get(second_variable, 0) + exponent - power
            )
        key = tuple(sorted((name, exp) for name, exp in variables.items() if exp))
        combined[key] = combined.get(key, 0.0) + coefficient

    terms = []
    for variables, coefficient in combined.items():
        if math.isclose(coefficient, 0.0, abs_tol=1e-12):
            continue
        body = _format_monomial(coefficient, dict(variables))
        if not terms:
            terms.append(("-" if coefficient < 0 else "") + body)
        else:
            terms.append((" - " if coefficient < 0 else " + ") + body)

    return "".join(terms) if terms else "0"
