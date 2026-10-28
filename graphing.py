"""Safe function evaluation helpers for graphing backends."""

import math
import re
from numbers import Real

from calculator import calculate


_VARIABLE_X = re.compile(r"(?<![A-Za-z_])x(?![A-Za-z0-9_])", re.IGNORECASE)
_VARIABLE_Y = re.compile(r"(?<![A-Za-z_])y(?![A-Za-z0-9_])", re.IGNORECASE)


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


def evaluate_surface(expression, x_value, y_value):
    """Evaluate a two-variable expression through the safe calculator parser."""
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Surface expression must be non-empty text.")
    if not math.isfinite(float(x_value)) or not math.isfinite(float(y_value)):
        raise ValueError("Surface coordinates must be finite.")
    text = _VARIABLE_X.sub("(" + repr(float(x_value)) + ")", expression)
    text = _VARIABLE_Y.sub("(" + repr(float(y_value)) + ")", text)
    result = calculate(text)
    if isinstance(result, bool) or not isinstance(result, Real) or not math.isfinite(result):
        raise ValueError("Surface expression must produce a finite real result.")
    return float(result)


def sample_surface(expression, x_min, x_max, y_min, y_max, grid_size=25):
    """Sample a bounded z=f(x,y) grid; undefined values are represented by None."""
    values = (x_min, x_max, y_min, y_max)
    if any(isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v) for v in values):
        raise ValueError("Surface bounds must be finite real numbers.")
    if x_min >= x_max or y_min >= y_max:
        raise ValueError("Surface minimum bounds must be smaller than their maximums.")
    if isinstance(grid_size, bool) or not isinstance(grid_size, int) or not 8 <= grid_size <= 60:
        raise ValueError("grid_size must be an integer from 8 to 60.")
    xs = [float(x_min) + (float(x_max)-float(x_min))*i/(grid_size-1) for i in range(grid_size)]
    ys = [float(y_min) + (float(y_max)-float(y_min))*j/(grid_size-1) for j in range(grid_size)]
    rows = []
    for y in ys:
        row = []
        for x in xs:
            try:
                z = evaluate_surface(expression, x, y)
            except ValueError as exc:
                message = str(exc).lower()
                if any(word in message for word in ("domain", "divide by zero", "complex result", "finite real result", "outside the supported range")):
                    z = None
                else:
                    raise
            row.append({"x": x, "y": y, "z": z})
        rows.append(row)
    return rows


def evaluate_relation(relation, x_value, y_value):
    """Evaluate an implicit relation F(x, y)=0 at one real coordinate."""
    if not isinstance(relation, str) or not relation.strip():
        raise ValueError("Relation must be non-empty text.")
    for label, value in (("x value", x_value), ("y value", y_value)):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{label} must be a real number.")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError(f"{label} must be finite.")
    x_literal, y_literal = repr(float(x_value)), repr(float(y_value))
    substituted = _VARIABLE_X.sub(f"({x_literal})", relation)
    substituted = _VARIABLE_Y.sub(f"({y_literal})", substituted)
    result = calculate(substituted)
    if isinstance(result, bool) or not isinstance(result, Real):
        raise ValueError("Relation must produce a real numeric result.")
    try:
        finite = math.isfinite(result)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError("Relation result is outside the supported range.")
    return float(result)


def sample_relation(relation, x_min, x_max, y_min, y_max, grid_size=80):
    """Sample the zero contour of F(x,y)=0 with a bounded marching-squares grid.

    The relation may be written as F(x,y)=0 or as an equation such as y^2=18x.
    Returned segments are independent line segments; callers must not join
    separate segments into one continuous curve.
    """
    for label, value in (("x_min", x_min), ("x_max", x_max),
                         ("y_min", y_min), ("y_max", y_max)):
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            raise ValueError(f"{label} must be a finite real number.")
    if x_min >= x_max or y_min >= y_max:
        raise ValueError("Each graph minimum must be less than its maximum.")
    if isinstance(grid_size, bool) or not isinstance(grid_size, int) or not 20 <= grid_size <= 150:
        raise ValueError("grid_size must be an integer from 20 to 150.")

    normalized = relation.replace("²", "^2").replace("³", "^3").replace("−", "-").replace("–", "-").replace("×", "*").replace("·", "*").replace("÷", "/")
    parts = normalized.split("=")
    if len(parts) > 2 or not parts[0].strip() or (len(parts) == 2 and not parts[1].strip()):
        raise ValueError("Enter one equation, such as y^2 = 18x.")
    expression = f"({parts[0]})-({parts[1]})" if len(parts) == 2 else parts[0]
    # Validate syntax independently of a particular grid point.
    try:
        evaluate_relation(expression, (float(x_min) + float(x_max)) / 2,
                          (float(y_min) + float(y_max)) / 2)
    except ValueError as exc:
        message = str(exc).lower()
        if not any(marker in message for marker in (
            "invalid mathematical domain", "cannot divide by zero",
            "complex result", "outside the supported range"
        )):
            raise

    xs = [float(x_min) + (float(x_max) - float(x_min)) * i / grid_size
          for i in range(grid_size + 1)]
    ys = [float(y_min) + (float(y_max) - float(y_min)) * j / grid_size
          for j in range(grid_size + 1)]
    values = []
    for j, y in enumerate(ys):
        row = []
        for i, x in enumerate(xs):
            try:
                row.append(evaluate_relation(expression, x, y))
            except ValueError as exc:
                message = str(exc).lower()
                if any(marker in message for marker in (
                    "invalid mathematical domain", "cannot divide by zero",
                    "complex result", "outside the supported range"
                )):
                    row.append(None)
                else:
                    raise
        values.append(row)

    segments = []
    def crossing(a, b):
        xa, ya, va = a
        xb, yb, vb = b
        if va is None or vb is None:
            return None
        if va == 0:
            return {"x": xa, "y": ya}
        if vb == 0:
            return {"x": xb, "y": yb}
        if (va < 0) == (vb < 0):
            return None
        fraction = va / (va - vb)
        return {"x": xa + fraction * (xb - xa), "y": ya + fraction * (yb - ya)}

    for j in range(grid_size):
        for i in range(grid_size):
            x0, x1, y0, y1 = xs[i], xs[i + 1], ys[j], ys[j + 1]
            corners = [
                (x0, y0, values[j][i]),
                (x1, y0, values[j][i + 1]),
                (x1, y1, values[j + 1][i + 1]),
                (x0, y1, values[j + 1][i]),
            ]
            intersections = []
            for edge in ((0, 1), (1, 2), (2, 3), (3, 0)):
                point = crossing(corners[edge[0]], corners[edge[1]])
                if point is not None and not any(
                    abs(point["x"] - old["x"]) < 1e-12 and abs(point["y"] - old["y"]) < 1e-12
                    for old in intersections
                ):
                    intersections.append(point)
            if len(intersections) == 2:
                segments.append({"x1": intersections[0]["x"], "y1": intersections[0]["y"],
                                 "x2": intersections[1]["x"], "y2": intersections[1]["y"]})
            elif len(intersections) == 4:
                # Deterministic pairing for saddle cells; finer sampling limits ambiguity.
                segments.append({"x1": intersections[0]["x"], "y1": intersections[0]["y"],
                                 "x2": intersections[1]["x"], "y2": intersections[1]["y"]})
                segments.append({"x1": intersections[2]["x"], "y1": intersections[2]["y"],
                                 "x2": intersections[3]["x"], "y2": intersections[3]["y"]})
    return segments


__all__ = ["evaluate_function", "sample_function", "evaluate_relation", "sample_relation"]
