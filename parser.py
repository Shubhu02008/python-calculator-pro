"""Safely tokenize and evaluate scientific calculator expressions."""

import math
import re


_MAX_EXPRESSION_LENGTH = 10_000
_MAX_INTEGER_DIGITS = 1_000
_MAX_EXACT_INTEGER_EXPONENT = 10_000

_NUMBER = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")

_CONSTANTS = {
    "pi": math.pi,
    "π": math.pi,
    "e": math.e,
    "tau": math.tau,
}
def _reciprocal(function, label):
    def evaluate(value):
        denominator = function(value)
        if math.isclose(denominator, 0.0, abs_tol=1e-15):
            raise ValueError(f"{label} is undefined for this angle.")
        return 1.0 / denominator
    return evaluate


def _tangent(value):
    denominator = math.cos(value)
    if math.isclose(denominator, 0.0, abs_tol=1e-15):
        raise ValueError("tan is undefined for this angle.")
    return math.sin(value) / denominator


def _cotangent(value):
    denominator = math.sin(value)
    if math.isclose(denominator, 0.0, abs_tol=1e-15):
        raise ValueError("cot is undefined for this angle.")
    return math.cos(value) / denominator


_FUNCTIONS = {
    "sin": math.sin, "cos": math.cos, "tan": _tangent,
    "sec": _reciprocal(math.cos, "sec"), "csc": _reciprocal(math.sin, "csc"),
    "cosec": _reciprocal(math.sin, "cosec"), "cot": _cotangent,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "sqrt": math.sqrt, "cbrt": math.cbrt, "abs": abs,
    "ln": math.log, "log": math.log10, "log10": math.log10,
    "exp": math.exp, "floor": math.floor, "ceil": math.ceil,
    "degrees": math.degrees, "radians": math.radians,
    "factorial": math.factorial,
}
_MULTI_ARG_FUNCTIONS = {"log": math.log}
_VALUE_END = {"NUMBER", "IDENT", ")", "POSTFIX"}
_VALUE_START = {"NUMBER", "IDENT", "("}


def tokenize(expression):
    """Convert expression text to tokens; supports scientific symbols and notation."""
    if not isinstance(expression, str):
        raise ValueError("Expression must be text.")
    if len(expression) > _MAX_EXPRESSION_LENGTH:
        raise ValueError(
            f"Expression is too long (maximum {_MAX_EXPRESSION_LENGTH} characters)."
        )

    expression = (
        expression.replace("×", "*").replace("·", "*").replace("÷", "/")
        .replace("−", "-").replace("π", "pi").replace("√", "sqrt ")
        .replace("∛", "cbrt ").replace("²", "^2").replace("³", "^3")
        .replace("**", "^")
    )
    tokens = []
    position = 0
    while position < len(expression):
        char = expression[position]
        if char.isspace():
            position += 1
            continue
        number = _NUMBER.match(expression, position)
        if number:
            literal = number.group()
            if "." not in literal and "e" not in literal.lower():
                if len(literal) > _MAX_INTEGER_DIGITS:
                    raise ValueError(
                        f"Integer literal is too long (maximum {_MAX_INTEGER_DIGITS} digits)."
                    )
                value = int(literal)
            else:
                value = float(literal)
                if not math.isfinite(value):
                    raise ValueError("Number is outside the supported range.")
            tokens.append(("NUMBER", value))
            position = number.end()
            continue
        identifier = _IDENTIFIER.match(expression, position)
        if identifier:
            tokens.append(("IDENT", identifier.group().lower()))
            position = identifier.end()
            continue
        if char in "+-*/^(),!%":
            if char in "!%":
                tokens.append(("POSTFIX", char))
            else:
                tokens.append((char, char))
            position += 1
            continue
        raise ValueError(
            f"Unsupported character at position {position + 1}: {char!r}"
        )

    if not tokens:
        raise ValueError("Please enter an expression.")

    # Insert implicit multiplication, e.g. 2pi, 3(4+5), and (2)(3).
    result = []
    for token in tokens:
        if result:
            previous = result[-1]
            # Two adjacent numeric tokens are almost always a malformed number
            # (for example, 1.2.3) or missing an operator (2 3), not multiplication.
            if previous[0] == "NUMBER" and token[0] == "NUMBER":
                raise ValueError("Invalid number or missing operator.")
            prev_end = previous[0] in {"NUMBER", "IDENT", ")", "POSTFIX"}
            curr_start = token[0] in {"NUMBER", "IDENT", "("}
            is_function_argument = (
                previous[0] == "IDENT"
                and ((previous[1] in _FUNCTIONS and token[0] == "(")
                     or (previous[1] in {"sqrt", "cbrt"}
                         and token[0] in {"NUMBER", "IDENT", "("}))
            )
            if prev_end and curr_start and not is_function_argument:
                result.append(("*", "*"))
        result.append(token)

    # Keep the original public tokenizer format for compatibility.
    return [token[1] if token[0] in {"NUMBER", "IDENT", "POSTFIX"} else token[0] for token in result]


def resolve_brackets(tokens):
    """Compatibility helper: evaluate the supplied expression tokens."""
    return [evaluate_tokens(tokens)]


def evaluate_tokens(tokens):
    """Evaluate arithmetic and scientific functions using calculator precedence."""
    if not tokens:
        raise ValueError("Please enter an expression.")

    # Preserve compatibility with the old public tokenizer, which returned
    # numbers and operator strings, while also accepting the new typed tokens.
    normalized = []
    for token in tokens:
        if isinstance(token, tuple) and len(token) == 2:
            normalized.append(token)
        elif isinstance(token, (int, float)) and not isinstance(token, bool):
            normalized.append(("NUMBER", token if isinstance(token, int) else float(token)))
        elif isinstance(token, str):
            if token in {"+", "-", "*", "/", "^", "(", ")", ","}:
                normalized.append((token, token))
            elif token in {"!", "%"}:
                normalized.append(("POSTFIX", token))
            else:
                normalized.append(("IDENT", token.lower()))
        else:
            raise ValueError(f"Invalid token: {token!r}")

    position = 0

    def peek(kind=None):
        if position >= len(normalized):
            return False
        return normalized[position][0] == kind if kind else normalized[position]

    def parse_expression():
        nonlocal position
        value = parse_term()
        while peek("+") or peek("-"):
            operator = normalized[position][0]
            position += 1
            right = parse_term()
            value = value + right if operator == "+" else value - right
        return value

    def parse_term():
        nonlocal position
        value = parse_unary()
        while peek("*") or peek("/"):
            operator = normalized[position][0]
            position += 1
            right = parse_unary()
            if operator == "*":
                value *= right
            else:
                if right == 0:
                    raise ValueError("Cannot divide by zero.")
                value /= right
        return value

    def parse_unary():
        nonlocal position
        if peek("+") or peek("-"):
            operator = normalized[position][0]
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
            if isinstance(value, int) and isinstance(exponent, int):
                if abs(exponent) > _MAX_EXACT_INTEGER_EXPONENT:
                    raise ValueError(
                        f"Integer exponent exceeds the supported limit of {_MAX_EXACT_INTEGER_EXPONENT}."
                    )
                # Bound exact-power output size before constructing potentially
                # enormous integers. This conservative estimate avoids large
                # allocations and outputs that Python cannot safely stringify.
                if exponent > 0 and abs(value) > 1:
                    magnitude = abs(value)
                    shift = max(0, magnitude.bit_length() - 53)
                    leading_bits = magnitude >> shift
                    estimated_log10 = (
                        math.log10(leading_bits) + shift * math.log10(2)
                    ) * exponent
                    if estimated_log10 >= 4_000:
                        raise ValueError("Exact integer power result is too large.")
            value = value ** exponent
            if isinstance(value, complex):
                raise ValueError("This expression has a complex result.")
        return value

    def parse_postfix():
        nonlocal position
        value = parse_primary()
        while peek("POSTFIX"):
            operator = normalized[position][1]
            position += 1
            if operator == "%":
                value /= 100
            else:
                if value < 0 or (not isinstance(value, int) and not float(value).is_integer()):
                    raise ValueError("Factorial requires a non-negative integer.")
                if value > 170:
                    raise ValueError("Factorial is too large to calculate.")
                value = math.factorial(int(value))
        return value

    def parse_primary():
        nonlocal position
        if position >= len(normalized):
            raise ValueError("Expression ends unexpectedly.")
        kind, value = normalized[position]

        if kind == "NUMBER":
            position += 1
            return value

        if kind == "(":
            position += 1
            value = parse_expression()
            if not peek(")"):
                raise ValueError("Missing closing parenthesis.")
            position += 1
            return value

        if kind == ")":
            raise ValueError("Unexpected closing parenthesis.")

        if kind == "IDENT":
            position += 1
            if value in _CONSTANTS:
                return _CONSTANTS[value]
            if value not in _FUNCTIONS:
                raise ValueError(f"Unknown function or constant: {value!r}.")
            function = _FUNCTIONS[value]
            if peek("("):
                position += 1
                args = [parse_expression()]
                while peek(","):
                    position += 1
                    args.append(parse_expression())
                if not peek(")"):
                    raise ValueError("Missing closing parenthesis in function.")
                position += 1
            elif value in {"sqrt", "cbrt"} and position < len(normalized):
                args = [parse_unary()]
            else:
                raise ValueError(f"Function {value} needs parentheses.")
            if value == "factorial" and len(args) == 1:
                number = args[0]
                if number < 0 or (not isinstance(number, int) and not float(number).is_integer()):
                    raise ValueError("Factorial requires a non-negative integer.")
                if number > 170:
                    raise ValueError("Factorial is too large to calculate.")
                result = math.factorial(int(number))
            elif value == "log" and len(args) == 2:
                try:
                    result = math.log(args[0], args[1])
                except (ValueError, ZeroDivisionError) as exc:
                    raise ValueError(
                        f"Invalid mathematical domain for {value}."
                    ) from exc
            else:
                try:
                    result = function(*args)
                except TypeError as exc:
                    raise ValueError(f"Invalid arguments for {value}.") from exc
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid mathematical domain for {value}."
                    ) from exc
            if isinstance(result, complex):
                raise ValueError("This expression has a complex result.")
            return result

        raise ValueError(f"Expected a number, got {value!r}.")

    try:
        result = parse_expression()
    except RecursionError as exc:
        raise ValueError("Expression is too deeply nested to evaluate safely.") from exc
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError("The result is outside the supported range.") from exc
    except ValueError:
        raise
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid mathematical expression.") from exc

    if position != len(normalized):
        token = normalized[position]
        if token[0] == ")":
            raise ValueError("Unexpected closing parenthesis.")
        raise ValueError(f"Unexpected token: {token[1]!r}.")
    if not isinstance(result, int) and not math.isfinite(result):
        raise ValueError("The result is outside the supported range.")
    return result
