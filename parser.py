"""Tokenize and evaluate basic arithmetic expressions safely."""

import re


_TOKEN_PATTERN = re.compile(r"\d+(?:\.\d*)?|\.\d+|[()+\-*/]")


def tokenize(expression):
    """Convert an expression string into numbers and operator tokens.

    Decimal numbers, parentheses, whitespace, + - * /, and the division
    symbol ÷ are accepted.
    """
    if not isinstance(expression, str):
        raise ValueError("Expression must be text.")

    # Treat the traditional division symbol exactly like a forward slash.
    expression = expression.replace("÷", "/")

    tokens = []
    position = 0

    while position < len(expression):
        if expression[position].isspace():
            position += 1
            continue

        match = _TOKEN_PATTERN.match(expression, position)
        if match is None:
            raise ValueError(
                f"Unsupported character at position {position + 1}: "
                f"{expression[position]!r}"
            )

        token = match.group()
        if token in {"+", "-", "*", "/", "(", ")"}:
            tokens.append(token)
        else:
            try:
                tokens.append(float(token))
            except ValueError as exc:
                raise ValueError(f"Invalid number: {token}") from exc

        position = match.end()

    if not tokens:
        raise ValueError("Please enter an expression.")

    return tokens


def resolve_brackets(tokens):
    """Compatibility helper: evaluate the supplied expression tokens."""
    return [evaluate_tokens(tokens)]


def evaluate_tokens(tokens):
    """Evaluate tokens using standard arithmetic precedence.

    Raises ValueError for malformed expressions and division by zero.
    """
    if not tokens:
        raise ValueError("Please enter an expression.")

    position = 0

    def parse_expression():
        nonlocal position
        result = parse_term()
        while position < len(tokens) and tokens[position] in {"+", "-"}:
            operator = tokens[position]
            position += 1
            right = parse_term()
            result = result + right if operator == "+" else result - right
        return result

    def parse_term():
        nonlocal position
        result = parse_factor()
        while position < len(tokens) and tokens[position] in {"*", "/"}:
            operator = tokens[position]
            position += 1
            right = parse_factor()
            if operator == "*":
                result *= right
            else:
                if right == 0:
                    raise ValueError("Cannot divide by zero.")
                result /= right
        return result

    def parse_factor():
        nonlocal position
        if position >= len(tokens):
            raise ValueError("Expression ends unexpectedly.")

        token = tokens[position]

        if token in {"+", "-"}:
            position += 1
            value = parse_factor()
            return value if token == "+" else -value

        if token == "(":
            position += 1
            value = parse_expression()
            if position >= len(tokens) or tokens[position] != ")":
                raise ValueError("Missing closing parenthesis.")
            position += 1
            return value

        if token == ")":
            raise ValueError("Unexpected closing parenthesis.")

        if isinstance(token, (int, float)) and not isinstance(token, bool):
            position += 1
            return float(token)

        raise ValueError(f"Expected a number, got {token!r}.")

    result = parse_expression()
    if position != len(tokens):
        token = tokens[position]
        if token == ")":
            raise ValueError("Unexpected closing parenthesis.")
        raise ValueError(f"Unexpected token: {token!r}.")

    return result
