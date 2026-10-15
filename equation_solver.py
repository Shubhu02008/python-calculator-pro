"""Solve linear, quadratic, and cubic equations in one variable, x."""

import cmath
import math
import re


_TOKEN_PATTERN = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)|[xX()+\-*/^]")


def _tokenize_polynomial(expression):
    expression = expression.replace("³", "^3").replace("²", "^2")
    tokens = []
    position = 0

    while position < len(expression):
        if expression[position].isspace():
            position += 1
            continue
        match = _TOKEN_PATTERN.match(expression, position)
        if match is None:
            raise ValueError(
                f"Unsupported character in equation: {expression[position]!r}"
            )
        token = match.group()
        if token.lower() == "x":
            tokens.append("x")
        elif token in {"+", "-", "*", "/", "^", "(", ")"}:
            tokens.append(token)
        else:
            # Adjacent numeric tokens indicate a malformed number or a missing
            # operator (for example, "1.2.3" or "2 3"), not multiplication.
            if tokens and isinstance(tokens[-1], (int, float)):
                raise ValueError("Invalid number or missing operator in equation.")
            number = float(token)
            if not math.isfinite(number):
                raise ValueError("Equation number exceeds the supported numerical range.")
            tokens.append(number)
        position = match.end()

    if not tokens:
        raise ValueError("Please enter both sides of an equation.")
    return tokens


def _add(left, right, sign=1):
    return tuple(left[i] + sign * right[i] for i in range(4))


def _multiply(left, right):
    result = [0.0, 0.0, 0.0, 0.0]
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            product = a * b
            if i + j > 3 and product != 0.0:
                raise ValueError("Only linear, quadratic, and cubic equations are supported.")
            if i + j <= 3:
                result[i + j] += product
    return tuple(result)


def _parse_polynomial(tokens):
    position = 0

    def parse_expression():
        nonlocal position
        result = parse_product()
        while position < len(tokens) and tokens[position] in {"+", "-"}:
            operator = tokens[position]
            position += 1
            right = parse_product()
            result = _add(result, right, 1 if operator == "+" else -1)
        return result

    def parse_product():
        nonlocal position
        result = parse_unary()
        while position < len(tokens):
            token = tokens[position]
            if token in {"*", "/"}:
                position += 1
                right = parse_unary()
                if token == "*":
                    result = _multiply(result, right)
                else:
                    if any(right[i] != 0.0 for i in (1, 2, 3)):
                        raise ValueError("Division by an expression containing x is unsupported.")
                    if right[0] == 0.0:
                        raise ValueError("Cannot divide by zero.")
                    result = tuple(value / right[0] for value in result)
            elif token == "x" or token == "(" or isinstance(token, (int, float)):
                result = _multiply(result, parse_unary())
            else:
                break
        return result

    def parse_unary():
        nonlocal position
        if position < len(tokens) and tokens[position] in {"+", "-"}:
            operator = tokens[position]
            position += 1
            value = parse_unary()
            return value if operator == "+" else tuple(-item for item in value)
        return parse_power()

    def parse_power():
        nonlocal position
        value = parse_atom()
        if position < len(tokens) and tokens[position] == "^":
            position += 1
            if position >= len(tokens) or not isinstance(tokens[position], (int, float)):
                raise ValueError("Use a numeric exponent of 0, 1, 2, or 3.")
            exponent = tokens[position]
            position += 1
            if not float(exponent).is_integer() or exponent not in (0, 1, 2, 3):
                raise ValueError("Only powers 0, 1, 2, and 3 are supported.")
            if exponent == 0:
                value = (1.0, 0.0, 0.0, 0.0)
            elif exponent == 2:
                value = _multiply(value, value)
            elif exponent == 3:
                value = _multiply(_multiply(value, value), value)
        return value

    def parse_atom():
        nonlocal position
        if position >= len(tokens):
            raise ValueError("Equation ends unexpectedly.")
        token = tokens[position]
        if token == "x":
            position += 1
            return (0.0, 1.0, 0.0, 0.0)
        if isinstance(token, (int, float)):
            position += 1
            return (float(token), 0.0, 0.0, 0.0)
        if token == "(":
            position += 1
            value = parse_expression()
            if position >= len(tokens) or tokens[position] != ")":
                raise ValueError("Missing closing parenthesis.")
            position += 1
            return value
        if token == ")":
            raise ValueError("Unexpected closing parenthesis.")
        raise ValueError(f"Unexpected token: {token!r}.")

    result = parse_expression()
    if position != len(tokens):
        raise ValueError(f"Unexpected token: {tokens[position]!r}.")
    return result


def _real_cuberoot(value):
    return math.copysign(abs(value) ** (1 / 3), value)


def _solve_cubic(constant, linear, quadratic, cubic):
    """Return all three roots of a real-coefficient cubic, including repeats.

    Rescale the independent variable before applying Cardano's formula. This
    keeps the normalized coefficients and intermediate powers in a useful
    floating-point range even when the roots are extremely large or small.
    """
    coefficients = (constant, linear, quadratic, cubic)
    if not all(math.isfinite(value) for value in coefficients):
        raise ValueError("Equation coefficients exceed the supported numerical range.")
    if cubic == 0:
        raise ValueError("A cubic equation requires a non-zero cubic coefficient.")

    log_leading = math.log(abs(cubic))
    scale_candidates = [
        (math.log(abs(value)) - log_leading) / (3 - degree)
        for degree, value in enumerate(coefficients[:3])
        if value != 0
    ]
    log_scale = max(scale_candidates, default=0.0)
    try:
        scale = math.exp(log_scale)
    except OverflowError as exc:
        raise OverflowError("Cubic roots exceed the supported numerical range.") from exc
    if not math.isfinite(scale) or scale == 0:
        raise OverflowError("Cubic roots exceed the supported numerical range.")

    def scaled_coefficient(value, degree):
        if value == 0:
            return 0.0
        exponent = (
            math.log(abs(value))
            - log_leading
            - (3 - degree) * log_scale
        )
        # The chosen scale makes this magnitude at most one; clamp tiny
        # positive round-off in the logarithmic calculation.
        magnitude = math.exp(min(0.0, exponent))
        sign = math.copysign(1.0, value) * math.copysign(1.0, cubic)
        return math.copysign(magnitude, sign)

    a = scaled_coefficient(quadratic, 2)
    b = scaled_coefficient(linear, 1)
    c = scaled_coefficient(constant, 0)

    p = b - a * a / 3
    q = 2 * a**3 / 27 - a * b / 3 + c
    positive_term = (q / 2) ** 2
    negative_term = (p / 3) ** 3
    discriminant = positive_term + negative_term
    # The discriminant is dimensionless after rescaling. Estimate its
    # round-off from the magnitudes of the two terms instead of using a fixed
    # absolute tolerance that behaves differently at different scales.
    tolerance = 32 * math.ulp(1.0) * (
        abs(positive_term) + abs(negative_term)
    )
    shift = a / 3

    if discriminant > tolerance:
        root_disc = math.sqrt(discriminant)
        # Choose the larger-magnitude Cardano radicand, then recover the
        # second cube root from u*v = -p/3 to reduce cancellation.
        q_half = -q / 2
        radicand = q_half - math.copysign(root_disc, q if q != 0 else 1.0)
        u = _real_cuberoot(radicand)
        v = -p / (3 * u) if u != 0 else _real_cuberoot(
            q_half + math.copysign(root_disc, q if q != 0 else 1.0)
        )
        pair_real = -(u + v) / 2 - shift
        pair_imaginary = math.sqrt(3) * abs(u - v) / 2
        roots = [
            u + v - shift,
            complex(pair_real, pair_imaginary),
            complex(pair_real, -pair_imaginary),
        ]
    elif discriminant < -tolerance:
        radius = 2 * math.sqrt(-p / 3)
        cosine = (3 * q / (2 * p)) * (math.sqrt(3) / math.sqrt(-p))
        cosine = max(-1.0, min(1.0, cosine))
        angle = math.acos(cosine) / 3
        roots = [
            radius * math.cos(angle - 2 * math.pi * k / 3) - shift
            for k in range(3)
        ]
    else:
        u = _real_cuberoot(-q / 2)
        roots = [2 * u - shift, -u - shift, -u - shift]

    scaled_roots = []
    for root in roots:
        if isinstance(root, complex):
            scaled = complex(root.real * scale, root.imag * scale)
            finite = math.isfinite(scaled.real) and math.isfinite(scaled.imag)
            underflowed = (
                (root.real != 0 and scaled.real == 0)
                or (root.imag != 0 and scaled.imag == 0)
            )
        else:
            scaled = root * scale
            finite = math.isfinite(scaled)
            underflowed = root != 0 and scaled == 0
        if not finite or underflowed:
            raise OverflowError("A cubic root is outside the supported numerical range.")
        scaled_roots.append(scaled)
    return scaled_roots

def solve_equation(equation):
    """Solve a linear, quadratic, or cubic polynomial equation in x.

    Supports implicit multiplication (5x, x(x - 3)), powers through x^3,
    equations on both sides of '=', and complex roots for quadratics/cubics.
    """
    if not isinstance(equation, str):
        raise ValueError("Equation must be text.")
    if equation.count("=") != 1:
        raise ValueError("Enter an equation with exactly one '=' sign.")

    left_text, right_text = equation.split("=")
    left = _parse_polynomial(_tokenize_polynomial(left_text))
    right = _parse_polynomial(_tokenize_polynomial(right_text))
    if not all(math.isfinite(value) for value in (*left, *right)):
        raise ValueError("Equation coefficients exceed the supported numerical range.")
    constant, linear, quadratic, cubic = _add(left, right, -1)
    if not all(math.isfinite(value) for value in (constant, linear, quadratic, cubic)):
        raise ValueError("Equation coefficients exceed the supported numerical range.")

    # Polynomial degree is determined by whether a coefficient is zero,
    # not by its absolute magnitude. A small but nonzero leading coefficient
    # can still produce valid roots (for example, 1e-13*x^3 = 1).
    if cubic == 0.0:
        if quadratic == 0.0:
            if linear == 0.0:
                return "Infinite solutions" if constant == 0.0 else "No solution"
            root = -constant / linear
            if not math.isfinite(root):
                raise OverflowError("A linear root is outside the supported numerical range.")
            return [root]

        discriminant = linear * linear - 4 * quadratic * constant
        if not math.isfinite(discriminant):
            raise OverflowError("Quadratic calculation exceeds the supported numerical range.")
        if discriminant >= 0:
            root = math.sqrt(discriminant)
            if root == 0:
                root = (-linear / quadratic) / 2
                if not math.isfinite(root):
                    raise OverflowError("A quadratic root is outside the supported numerical range.")
                return [root]

            # Avoid catastrophic cancellation when the linear term and square
            # root are nearly equal. Compute one root with the stable q formula,
            # then recover the other from the product of roots (c / a).
            q = -0.5 * linear - math.copysign(0.5 * root, linear)
            if q == 0:
                roots = [
                    ((-linear / 2) - (root / 2)) / quadratic,
                    ((-linear / 2) + (root / 2)) / quadratic,
                ]
            else:
                roots = [q / quadratic, constant / q]
            roots.sort()
            if not all(math.isfinite(value) for value in roots):
                raise OverflowError("A quadratic root is outside the supported numerical range.")
            return roots

        root = cmath.sqrt(discriminant)
        roots = [
            ((-linear / 2) - (root / 2)) / quadratic,
            ((-linear / 2) + (root / 2)) / quadratic,
        ]
        if not all(math.isfinite(value.real) and math.isfinite(value.imag) for value in roots):
            raise OverflowError("A quadratic root is outside the supported numerical range.")
        return roots

    return _solve_cubic(constant, linear, quadratic, cubic)
