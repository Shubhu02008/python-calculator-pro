"""Safe symbolic calculus, descriptive statistics, and elementary probability tools.

Symbolic input is parsed from a restricted Python expression AST; arbitrary Python
code, attribute access, indexing, and unknown function calls are rejected.
"""
import ast
import math
from collections import Counter

import sympy as sp


_SYMBOLS = {name: sp.Symbol(name, real=True) for name in ("x", "y", "z", "t")}
_SYMBOLS.update({"pi": sp.pi, "e": sp.E})
_FUNCTIONS = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "sqrt": sp.sqrt, "log": sp.log, "ln": sp.log, "log10": lambda x: sp.log(x, 10),
    "exp": sp.exp, "abs": sp.Abs, "factorial": sp.factorial,
}
_MAX_EXPRESSION_LENGTH = 1000


def _parse_expression(source):
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Expression must be non-empty text.")
    if len(source) > _MAX_EXPRESSION_LENGTH:
        raise ValueError(f"Expression must be at most {_MAX_EXPRESSION_LENGTH} characters.")
    try:
        tree = ast.parse(source.replace("^", "**"), mode="eval")
    except (SyntaxError, ValueError) as exc:
        raise ValueError("Invalid mathematical expression.") from exc

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if isinstance(node.value, float) and not math.isfinite(node.value):
                raise ValueError("Numeric literals must be finite.")
            return sp.Integer(node.value) if isinstance(node.value, int) else sp.Float(node.value)
        if isinstance(node, ast.Name):
            if node.id in _SYMBOLS:
                return _SYMBOLS[node.id]
            raise ValueError(f"Unsupported symbol or constant: {node.id}.")
        if isinstance(node, ast.BinOp) and type(node.op) in (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if right.is_number and right.is_real and abs(float(right)) > 1000:
                raise ValueError("Exponent magnitude is outside supported limits.")
            return left ** right
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS:
            if node.keywords or not 1 <= len(node.args) <= 2:
                raise ValueError("Function arguments are not supported in that form.")
            args = [visit(arg) for arg in node.args]
            if node.func.id in {"log", "log10"} and len(args) == 2:
                return sp.log(args[0], args[1])
            if len(args) != 1:
                raise ValueError("This function accepts one argument.")
            return _FUNCTIONS[node.func.id](args[0])
        raise ValueError("Expression contains an unsupported operation.")

    try:
        return visit(tree)
    except (TypeError, ZeroDivisionError, OverflowError) as exc:
        raise ValueError("Could not parse mathematical expression.") from exc


def calculate_calculus(operation, expression, *, variable="x", order=1, lower=None, upper=None, point="0", direction="both"):
    """Differentiate, integrate, compute a definite integral, or evaluate a limit."""
    if variable not in _SYMBOLS or variable in {"pi", "e"}:
        raise ValueError("Variable must be one of x, y, z, or t.")
    if isinstance(order, bool) or not isinstance(order, int) or not 1 <= order <= 10:
        raise ValueError("Derivative order must be an integer from 1 to 10.")
    symbol = _SYMBOLS[variable]
    expr = _parse_expression(expression)
    try:
        if operation == "derivative":
            result = sp.diff(expr, symbol, order)
        elif operation == "integral":
            result = sp.integrate(expr, symbol)
        elif operation == "definite_integral":
            if lower is None or upper is None:
                raise ValueError("A definite integral requires both lower and upper bounds.")
            lo, hi = _parse_bound(lower), _parse_bound(upper)
            result = sp.integrate(expr, (symbol, lo, hi))
        elif operation == "limit":
            target = _parse_bound(point)
            if direction not in {"both", "plus", "minus"}:
                raise ValueError("Limit direction must be both, plus, or minus.")
            if direction == "both":
                result = sp.limit(expr, symbol, target)
            else:
                result = sp.limit(expr, symbol, target, dir="+" if direction == "plus" else "-")
        else:
            raise ValueError("Unsupported calculus operation.")
    except (ValueError, TypeError, NotImplementedError, RecursionError) as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError("Could not solve this symbolic calculus expression.") from exc
    if result.has(sp.nan, sp.zoo) or result in (sp.oo, -sp.oo):
        result_text = str(result)
    else:
        result_text = str(sp.simplify(result))
    return {"operation": operation, "expression": expression, "variable": variable, "result": result_text}


def _parse_bound(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value):
            raise ValueError("Bounds and limit points must be finite, except for explicit infinity.")
        return sp.sympify(value)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Bound or limit point must be numeric text.")
    cleaned = value.strip().lower()
    if cleaned in {"oo", "+oo", "infinity", "+infinity"}:
        return sp.oo
    if cleaned in {"-oo", "-infinity"}:
        return -sp.oo
    if len(cleaned) > 50:
        raise ValueError("Bound or limit point is too long.")
    try:
        result = sp.Rational(cleaned)
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        raise ValueError("Bounds and limit points must be numbers or infinity.") from exc
    return result


def _median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return ordered[middle - 1] / 2 + ordered[middle] / 2


def calculate_statistics(operation, values):
    """Calculate descriptive statistics for a bounded list of finite real values."""
    if operation not in {
        "mean", "median", "mode", "range", "minimum", "maximum",
        "variance", "population_variance", "standard_deviation",
        "population_standard_deviation", "quartiles",
    }:
        raise ValueError("Unsupported statistics operation.")
    if not isinstance(values, (list, tuple)) or not values or len(values) > 10000:
        raise ValueError("Provide between 1 and 10000 data values.")
    checked = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("Every data value must be a finite real number.")
        checked.append(float(value))
    if operation == "mean":
        result = math.fsum(value / len(checked) for value in checked)
    elif operation == "median":
        result = _median(checked)
    elif operation == "mode":
        counts = Counter(checked)
        highest = max(counts.values())
        result = sorted(value for value, count in counts.items() if count == highest)
        if highest == 1:
            result = []
    elif operation == "range":
        result = max(checked) - min(checked)
    elif operation == "minimum":
        result = min(checked)
    elif operation == "maximum":
        result = max(checked)
    elif operation in {"variance", "standard_deviation", "population_variance", "population_standard_deviation"}:
        if operation in {"variance", "standard_deviation"} and len(checked) < 2:
            raise ValueError("Sample variance and standard deviation require at least two values.")
        # Compute the mean once. Dividing each term first avoids overflowing the
        # intermediate sum for many large, same-sign finite observations.
        mean = math.fsum(value / len(checked) for value in checked)
        divisor = len(checked) - 1 if operation in {"variance", "standard_deviation"} else len(checked)
        try:
            squared_deviations = [(value - mean) ** 2 for value in checked]
            variance = math.fsum(squared_deviations) / divisor
        except (OverflowError, ValueError) as exc:
            raise ValueError("Data values are too large to calculate variance safely.") from exc
        if not math.isfinite(variance):
            raise ValueError("Data values are too large to calculate variance safely.")
        result = variance if operation in {"variance", "population_variance"} else math.sqrt(variance)
    else:
        ordered = sorted(checked)
        median = _median(ordered)
        mid = len(ordered) // 2
        lower_half = ordered[:mid]
        upper_half = ordered[(mid + (len(ordered) % 2)):]
        result = {"q1": _median(lower_half) if lower_half else None,
                  "q2": median,
                  "q3": _median(upper_half) if upper_half else None}
    numeric_results = result.values() if isinstance(result, dict) else (
        result if isinstance(result, list) else [result]
    )
    if any(
        isinstance(value, (int, float)) and not math.isfinite(value)
        for value in numeric_results
    ):
        raise ValueError("The requested statistic is outside the supported numeric range.")
    return {"operation": operation, "count": len(checked), "result": result}


def calculate_probability(operation, *, favorable=None, total=None, event_a=None, event_b=None, intersection=None, n=None, r=None, p=None, k=None):
    """Calculate elementary event probabilities, combinations, permutations, or binomial probability."""
    if operation == "simple":
        if not _is_nonnegative_integer(favorable) or not _is_positive_integer(total) or favorable > total:
            raise ValueError("Simple probability requires integers with 0 <= favorable <= total and total > 0.")
        result = favorable / total
    elif operation == "complement":
        event = _probability(event_a, "event_a")
        result = 1 - event
    elif operation == "conditional":
        joint = _probability(intersection, "intersection")
        condition = _probability(event_b, "event_b")
        if condition == 0:
            raise ValueError("Conditional probability is undefined when P(B) is zero.")
        if joint > condition:
            raise ValueError("P(A and B) cannot exceed P(B).")
        result = joint / condition
    elif operation == "union":
        a, b, joint = _probability(event_a, "event_a"), _probability(event_b, "event_b"), _probability(intersection, "intersection")
        if joint > min(a, b) or a + b - joint > 1:
            raise ValueError("Probabilities are inconsistent for a union.")
        result = a + b - joint
    elif operation in {"permutation", "combination"}:
        if not _is_nonnegative_integer(n) or not _is_nonnegative_integer(r) or r > n or n > 10000:
            raise ValueError("Require integers with 0 <= r <= n <= 10000.")
        result = math.perm(n, r) if operation == "permutation" else math.comb(n, r)
    elif operation == "binomial":
        if not _is_nonnegative_integer(n) or not _is_nonnegative_integer(k) or k > n or n > 10000:
            raise ValueError("Binomial probability requires integers with 0 <= k <= n <= 10000.")
        probability = _probability(p, "p")
        result = math.comb(n, k) * probability**k * (1 - probability)**(n-k)
    else:
        raise ValueError("Unsupported probability operation.")
    # JSON consumers commonly use IEEE-754 numbers, which cannot exactly
    # represent integers above 2**53 - 1. Return large exact counts as decimal
    # strings, and reject values too large for Python's safe decimal conversion.
    if isinstance(result, int) and not isinstance(result, bool):
        decimal_digits = int((result.bit_length() - 1) * math.log10(2)) + 1 if result else 1
        if decimal_digits > 4000:
            raise ValueError("Result is too large to return safely; reduce n or r.")
        if abs(result) > (2**53 - 1):
            result = str(result)
    return {"operation": operation, "result": result}


def _is_nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_positive_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _probability(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{label} must be a probability between 0 and 1.")
    return float(value)
