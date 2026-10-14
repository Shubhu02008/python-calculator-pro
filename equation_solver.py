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
            tokens.append(float(token))
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
            if i + j > 3 and not math.isclose(product, 0.0, abs_tol=1e-12):
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
                    if any(not math.isclose(right[i], 0.0, abs_tol=1e-12) for i in (1, 2, 3)):
                        raise ValueError("Division by an expression containing x is unsupported.")
                    if math.isclose(right[0], 0.0, abs_tol=1e-12):
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
    """Return all three roots of a real-coefficient cubic, including repeats."""
    a = quadratic / cubic
    b = linear / cubic
    c = constant / cubic

    p = b - a * a / 3
    q = 2 * a**3 / 27 - a * b / 3 + c
    discriminant = (q / 2) ** 2 + (p / 3) ** 3
    shift = a / 3
    tolerance = 1e-12

    if discriminant > tolerance:
        root_disc = math.sqrt(discriminant)
        u = _real_cuberoot(-q / 2 + root_disc)
        v = _real_cuberoot(-q / 2 - root_disc)
        real_root = u + v - shift
        real_part = -(u + v) / 2 - shift
        imaginary_part = math.sqrt(3) * (u - v) / 2
        return [real_root, complex(real_part, imaginary_part), complex(real_part, -imaginary_part)]

    if abs(discriminant) <= tolerance:
        u = _real_cuberoot(-q / 2)
        roots = [2 * u - shift, -u - shift, -u - shift]
        if math.isclose(roots[0], roots[1], abs_tol=1e-10):
            return [roots[0]] * 3
        return roots

    radius = 2 * math.sqrt(-p / 3)
    cosine = (3 * q / (2 * p)) * math.sqrt(-3 / p)
    cosine = max(-1.0, min(1.0, cosine))
    angle = math.acos(cosine) / 3
    return [
        radius * math.cos(angle - 2 * math.pi * k / 3) - shift
        for k in range(3)
    ]


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
    constant, linear, quadratic, cubic = _add(left, right, -1)

    if math.isclose(cubic, 0.0, abs_tol=1e-12):
        if math.isclose(quadratic, 0.0, abs_tol=1e-12):
            if math.isclose(linear, 0.0, abs_tol=1e-12):
                return "Infinite solutions" if math.isclose(
                    constant, 0.0, abs_tol=1e-12
                ) else "No solution"
            return [-constant / linear]

        discriminant = linear * linear - 4 * quadratic * constant
        if discriminant >= 0:
            root = math.sqrt(discriminant)
            roots = [
                (-linear - root) / (2 * quadratic),
                (-linear + root) / (2 * quadratic),
            ]
            return [roots[0]] if math.isclose(roots[0], roots[1], abs_tol=1e-12) else roots
        root = cmath.sqrt(discriminant)
        return [
            (-linear - root) / (2 * quadratic),
            (-linear + root) / (2 * quadratic),
        ]

    return _solve_cubic(constant, linear, quadratic, cubic)
