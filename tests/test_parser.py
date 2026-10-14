import pytest

from parser import tokenize, evaluate_tokens


def evaluate(expression):
    return evaluate_tokens(tokenize(expression))


def test_tokenize():
    assert tokenize("5 + 10 * 3") == [5, "+", 10, "*", 3]


def test_basic_bodmas():
    assert evaluate("5 + 10 * 3") == 35


def test_parentheses():
    assert evaluate("(2 + 3) * 4") == 20


def test_nested_parentheses():
    assert evaluate("2 * (3 + (4 - 1))") == 12


def test_decimal_numbers():
    assert evaluate("1.5 + 2.25") == 3.75


def test_negative_numbers_and_unary_minus():
    assert evaluate("-5 + 2") == -3
    assert evaluate("5 * -2") == -10
    assert evaluate("-(2 + 3)") == -5


def test_division_by_zero_is_reported():
    with pytest.raises(ValueError, match="divide by zero"):
        evaluate("10 / 0")


def test_division_by_zero_inside_parentheses_is_reported():
    with pytest.raises(ValueError, match="divide by zero"):
        evaluate("2 + (10 / 0)")


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "   ",
        "1.2.3",
        ".",
        "2 ^ 3",
        "2 ** 3",
        "2 +",
        "* 2",
        "(2 + 3",
        "2 + 3)",
        "()",
        "2 3",
        "hello",
    ],
)
def test_malformed_or_unsupported_expressions_are_rejected(expression):
    with pytest.raises(ValueError):
        evaluate(expression)


def test_unsupported_character_is_rejected_by_tokenizer():
    with pytest.raises(ValueError, match="Unsupported character"):
        tokenize("2 % 3")
