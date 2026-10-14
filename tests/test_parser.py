import math
import pytest

from parser import tokenize, evaluate_tokens


def evaluate(expression):
    return evaluate_tokens(tokenize(expression))


def test_basic_arithmetic_and_precedence():
    assert evaluate("5 + 10 * 3") == 35
    assert evaluate("(2 + 3) * 4") == 20
    assert evaluate("2 * (3 + (4 - 1))") == 12
    assert evaluate("1.5 + 2.25") == 3.75


def test_multiplication_and_division_symbols():
    assert evaluate("3 × 4") == 12
    assert evaluate("3 · 4") == 12
    assert evaluate("10 ÷ 2") == 5


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
    assert evaluate("∛27") == 3
    assert evaluate("cbrt(8)") == 2


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
    assert evaluate("2pi") == pytest.approx(2 * math.pi)
    assert evaluate("3(4+5)") == 27
    assert evaluate("(2)(3)") == 6


def test_scientific_notation():
    assert evaluate("1.2e3 + 2") == 1202


@pytest.mark.parametrize("expression", [
    "", "   ", ".", "1.2.3", "2 +", "* 2", "(2 + 3", "2 + 3)",
    "()", "hello", "2 @ 3", "10 / 0", "sqrt(-1)", "5.5!",
])
def test_invalid_expressions_raise_clear_errors(expression):
    with pytest.raises(ValueError):
        evaluate(expression)


def test_tokenize_preserves_legacy_simple_tokens():
    assert tokenize("5 + 10 * 3") == [
        ("NUMBER", 5.0), ("+", "+"), ("NUMBER", 10.0),
        ("*", "*"), ("NUMBER", 3.0)
    ]
