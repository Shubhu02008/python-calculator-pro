"""Safe function evaluation helpers for graphing backends."""

import math
import re
from numbers import Real

from calculator import calculate


_VARIABLE_X = re.compile(r"(?<![A-Za-z0-9_])x(?![A-Za-z0-9_])", re.IGNORECASE)


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


def sample_function(expression, x_min, x_max, points=101):
    """Return evenly spaced (x, y) samples for a function.

    Undefined or out-of-range y values are represented by None, allowing a
    future plotting layer to break a curve instead of joining across a gap.
    Sampling is bounded to keep accidental workloads reasonable.
    """
    for label, value in (("x_min", x_min), ("x_max", x_max)):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{label} must be a real number.")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError(f"{label} must be finite.")
    if x_min >= x_max:
        raise ValueError("x_min must be less than x_max.")
    if isinstance(points, bool) or not isinstance(points, int) or not 2 <= points <= 2000:
        raise ValueError("points must be an integer from 2 to 2000.")

    low, high = float(x_min), float(x_max)
    # Validate syntax once so malformed input doesn't silently become an
    # array of undefined points. A domain error at the midpoint is acceptable:
    # it is exactly the kind of gap this sampler is designed to represent.
    try:
        evaluate_function(expression, low * 0.5 + high * 0.5)
    except ValueError as exc:
        message = str(exc).lower()
        if not any(marker in message for marker in (
            "invalid mathematical domain",
            "cannot divide by zero",
            "complex result",
            "outside the supported range",
        )):
            raise
    samples = []
    for index in range(points):
        fraction = index / (points - 1)
        x_value = low * (1.0 - fraction) + high * fraction
        try:
            y_value = evaluate_function(expression, x_value)
        except ValueError as exc:
            message = str(exc).lower()
            if any(marker in message for marker in (
                "invalid mathematical domain",
                "cannot divide by zero",
                "complex result",
                "outside the supported range",
            )):
                y_value = None
            else:
                raise
        samples.append((x_value, y_value))
    return samples


__all__ = ["evaluate_function", "sample_function"]
