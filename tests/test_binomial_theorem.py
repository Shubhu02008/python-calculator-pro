import pytest

from binomial_theorem import expand_binomial


def test_expands_cube_of_x_plus_two():
    assert expand_binomial("(x + 2)^3") == "x^3 + 6x^2 + 12x + 8"


def test_expands_fourth_power_of_x_minus_one():
    assert expand_binomial("(x - 1)^4") == "x^4 - 4x^3 + 6x^2 - 4x + 1"


def test_expands_binomial_with_coefficient():
    assert expand_binomial("(2x + 3)^2") == "4x^2 + 12x + 9"


def test_expands_symbolic_binomial():
    assert expand_binomial("(a + b)^3") == "a^3 + 3a^2b + 3ab^2 + b^3"


def test_expands_subtraction_of_symbols():
    assert expand_binomial("(a - b)^2") == "a^2 - 2ab + b^2"


def test_zero_power():
    assert expand_binomial("(x + 2)^0") == "1"


def test_rejects_non_finite_binomial_coefficient():
    huge_coefficient = "9" * 400
    with pytest.raises(ValueError, match="coefficients must be finite"):
        expand_binomial(f"({huge_coefficient}x + 1)^2")


def test_rejects_binomial_expansion_overflow():
    with pytest.raises(ValueError, match="outside the supported range"):
        expand_binomial("(10000000000x + 1)^100")


@pytest.mark.parametrize(
    "expression",
    ["x + 2", "(x + 2)^101", "(x +)^3", "(x + 2)^-1", "hello"],
)
def test_rejects_invalid_binomials(expression):
    with pytest.raises(ValueError):
        expand_binomial(expression)
