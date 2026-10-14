"""Solve linear and quadratic equations in one variable, x."""

import cmath
import math
import re


_TOKEN_PATTERN = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)|[xX()+\-*/^]")


def _tokenize_polynomial(expression):
    expression = expression.replace("²", "^2")
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
    return tuple(left[i] + sign * right[i] for i in range(3))


def _multiply(left, right):
    result = [0.0, 0.0, 0.0]
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            if i + j > 2 and not math.isclose(a * b, 0.0, abs_tol=1e-12):
                raise ValueError("Only linear and quadratic equations are supported.")
            if i + j <= 2:
                result[i + j] += a * b
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
                    if not math.isclose(right[1], 0.0, abs_tol=1e-12) or not math.isclose(
                        right[2], 0.0, abs_tol=1e-12
                    ):
                        raise ValueError("Division by an expression containing x is unsupported.")
                    if math.isclose(right[0], 0.0, abs_tol=1e-12):
                        raise ValueError("Cannot divide by zero.")
                    result = tuple(value / right[0] for value in result)
            elif token == "x" or token == "(" or isinstance(token, (int, float)):
                # Support conventional implicit multiplication, e.g. 5x and 2(x + 1).
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
                raise ValueError("Use a numeric exponent of 0, 1, or 2.")
            exponent = tokens[position]
            position += 1
            if not float(exponent).is_integer() or exponent not in (0, 1, 2):
                raise ValueError("Only powers 0, 1, and 2 are supported.")
            value = (1.0, 0.0, 0.0) if exponent == 0 else value
            if exponent == 2:
                value = _multiply(value, value)
        return value

    def parse_atom():
        nonlocal position
        if position >= len(tokens):
            raise ValueError("Equation ends unexpectedly.")
        token = tokens[position]
        if token == "x":
            position += 1
            return (0.0, 1.0, 0.0)
        if isinstance(token, (int, float)):
            position += 1
            return (float(token), 0.0, 0.0)
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


def solve_equation(equation):
    """Solve an equation containing x; return its root(s) or a no-solution label.

    Supports linear and quadratic polynomial equations, implicit multiplication
    (such as 5x), and powers 0 through 2. Complex roots are returned when needed.
    """
    if not isinstance(equation, str):
        raise ValueError("Equation must be text.")
    if equation.count("=") != 1:
        raise ValueError("Enter an equation with exactly one '=' sign.")

    left_text, right_text = equation.split("=")
    left = _parse_polynomial(_tokenize_polynomial(left_text))
    right = _parse_polynomial(_tokenize_polynomial(right_text))
    constant, linear, quadratic = _add(left, right, -1)

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
