"""Safe function evaluation helpers for graphing backends."""

import math
import re
from numbers import Real

from calculator import calculate


_VARIABLE_X = re.compile(r"(?<![A-Za-z_])x(?![A-Za-z0-9_])", re.IGNORECASE)


def evaluate_function(expression, x_value):
    """Evaluate a supported calculator expression at one real x-coordinate.

    The expression is parsed by the existing safe calculator parser; Python
    eval/exec are never used. The variable x is substituted only as a complete
    identifier, so names such as exp and max-like identifiers are not rewritten.
    """
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Function expression must be non-empty text.")
    if isinstance(x_value, bool) or not isinstance(x_value, Real):
        raise ValueError("x value must be a real number.")
    try:
        finite_x = math.isfinite(x_value)
    except OverflowError:
        finite_x = False
    if not finite_x:
        raise ValueError("x value must be finite.")

    try:
        x_literal = repr(x_value) if isinstance(x_value, int) else repr(float(x_value))
    except OverflowError as exc:
        raise ValueError("x value is outside the supported range.") from exc
    substituted = _VARIABLE_X.sub(f"({x_literal})", expression)
    result = calculate(substituted)
    if isinstance(result, bool) or not isinstance(result, Real):
        raise ValueError("Function must produce a real numeric result.")
    try:
        finite_result = math.isfinite(result)
    except OverflowError:
        finite_result = False
    if not finite_result:
        raise ValueError("Function result is outside the supported range.")
    return result


__all__ = ["evaluate_function"]
