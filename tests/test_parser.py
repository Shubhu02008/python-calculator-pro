import math
import pytest

from parser import tokenize, evaluate_tokens


def evaluate(expression):
    return evaluate_tokens(tokenize(expression))


def test_tokenize():
    assert tokenize("5 + 10 * 3") == [5.0, "+", 10.0, "*", 3.0]


def test_basic_bodmas():
    assert evaluate("5 + 10 * 3") == 35


def test_parentheses():
    assert evaluate("(2 + 3) * 4") == 20


def test_nested_parentheses():
    assert evaluate("2 * (3 + (4 - 1))") == 12


def test_decimal_numbers():
    assert evaluate("1.5 + 2.25") == 3.75


def test_division_symbol():
    assert evaluate("10 ÷ 2") == 5
    assert evaluate("20 ÷ (2 + 3)") == 4


def test_negative_numbers_and_unary_minus():
    assert evaluate("-5 + 2") == -3
    assert evaluate("5 * -2") == -10
    assert evaluate("-(2 + 3)") == -5


def test_multiplication_symbols():
    assert evaluate("3 × 4") == 12
    assert evaluate("3 · 4") == 12


def test_powers_and_precedence():
    assert evaluate("2^3") == 8
    assert evaluate("2**3") == 8
    assert evaluate("5²") == 25
    assert evaluate("2^3^2") == 512
    assert evaluate("-2^2") == -4
    assert evaluate("2^-2") == 0.25


def test_roots():
    assert evaluate("√25") == 5
    assert evaluate("sqrt(16 + 9)") == 5
    # Cube roots may differ from the exact mathematical value by a tiny
    # floating-point rounding error, so compare approximately.
    assert evaluate("∛27") == pytest.approx(3)
    assert evaluate("cbrt(8)") == pytest.approx(2)


def test_scientific_functions_and_constants():
    assert evaluate("sin(pi/2)") == pytest.approx(1)
    assert evaluate("cos(0)") == 1
    assert evaluate("log(100)") == 2
    assert evaluate("ln(e)") == pytest.approx(1)
    assert evaluate("log(8, 2)") == 3
    assert evaluate("abs(-5)") == 5
    assert evaluate("exp(1)") == pytest.approx(math.e)


def test_percent_factorial_and_implicit_multiplication():
    assert evaluate("50%") == 0.5
    assert evaluate("200 * 10%") == 20
    assert evaluate("5!") == 120
    assert evaluate("factorial(5)") == 120
    assert evaluate("2pi") == pytest.approx(2 * math.pi)
    assert evaluate("3(4+5)") == 27
    assert evaluate("(2)(3)") == 6


def test_scientific_notation():
    assert evaluate("1.2e3 + 2") == 1202


def test_large_integer_expressions_preserve_exactness():
    assert evaluate("9007199254740993 + 1") == 9007199254740994
    assert evaluate("12345678901234567890 * 9") == 111111110111111111010
    assert evaluate("10^100") == 10**100


def test_integer_literals_over_digit_limit_are_rejected():
    with pytest.raises(ValueError, match="Integer literal is too long"):
        evaluate("9" * 1_001)


def test_exact_integer_power_has_exponent_limit():
    with pytest.raises(ValueError, match="exponent exceeds"):
        evaluate("2^10001")


def test_division_by_zero_is_reported():
    with pytest.raises(ValueError, match="divide by zero"):
        evaluate("10 / 0")


def test_division_by_zero_inside_parentheses_is_reported():
    with pytest.raises(ValueError, match="divide by zero"):
        evaluate("2 + (10 / 0)")


@pytest.mark.parametrize(
    "expression",
    [
        "", "   ", "1.2.3", ".", "2 +", "* 2", "(2 + 3",
        "2 + 3)", "()", "hello", "2 @ 3", "sqrt(-1)", "5.5!",
    ],
)
def test_malformed_or_invalid_expressions_are_rejected(expression):
    with pytest.raises(ValueError):
        evaluate(expression)


@pytest.mark.parametrize(
    "expression,function_name",
    [
        ("sqrt(-1)", "sqrt"),
        ("ln(0)", "ln"),
        ("asin(2)", "asin"),
        ("log(8, 1)", "log"),
    ],
)
def test_scientific_function_domain_errors_are_clear(expression, function_name):
    with pytest.raises(ValueError, match=f"Invalid mathematical domain for {function_name}"):
        evaluate(expression)


def test_unsupported_character_is_rejected_by_tokenizer():
    with pytest.raises(ValueError, match="Unsupported character"):
        tokenize("2 @ 3")


@pytest.mark.parametrize("expression", ["1e999", "1e308 * 1e308"])
def test_non_finite_numbers_and_results_are_rejected(expression):
    with pytest.raises(ValueError, match="supported range"):
        evaluate(expression)


def test_rejects_expressions_that_exceed_the_length_limit():
    expression = "1+" * 5_001 + "1"
    with pytest.raises(ValueError, match="too long"):
        tokenize(expression)


def test_reports_deeply_nested_expressions_as_input_errors():
    depth = 1_200
    expression = "(" * depth + "1" + ")" * depth
    with pytest.raises(ValueError, match="too deeply nested"):
        evaluate(expression)


def test_exact_integer_power_guard_handles_large_intermediate_without_string_conversion():
    # The intermediate product exceeds Python's default int-to-string digit
    # limit; the power guard should reject it cleanly using bit-length math.
    literal = "9" * 1_000
    expression = "(" + " * ".join([literal] * 5) + ")^2"
    with pytest.raises(ValueError, match="Exact integer power result is too large"):
        evaluate(expression)
