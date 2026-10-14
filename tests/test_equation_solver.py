import pytest

from equation_solver import solve_equation


def test_solves_quadratic_with_two_real_roots():
    assert solve_equation("x^2 - 5x + 6 = 0") == [2.0, 3.0]


def test_solves_linear_equation():
    assert solve_equation("2x + 4 = 10") == [3.0]


def test_solves_equation_with_variable_on_both_sides():
    assert solve_equation("3x + 2 = x + 10") == [4.0]


def test_solves_quadratic_with_repeated_root():
    assert solve_equation("x^2 - 4x + 4 = 0") == [2.0]


def test_returns_complex_roots_for_quadratic():
    roots = solve_equation("x^2 + 1 = 0")
    assert roots[0] == -1j
    assert roots[1] == 1j


def test_supports_implicit_multiplication_and_parentheses():
    assert solve_equation("x(x - 3) = 0") == [0.0, 3.0]


def test_solves_cubic_with_three_distinct_real_roots():
    roots = solve_equation("x^3 - 6x^2 + 11x - 6 = 0")
    assert sorted(roots) == pytest.approx([1.0, 2.0, 3.0])


def test_solves_cubic_with_one_real_and_two_complex_roots():
    roots = solve_equation("x^3 + 1 = 0")
    assert roots[0] == pytest.approx(-1.0)
    assert roots[1] == pytest.approx(complex(0.5, 3**0.5 / 2))
    assert roots[2] == pytest.approx(complex(0.5, -(3**0.5) / 2))


def test_solves_cubic_with_repeated_roots():
    roots = solve_equation("x^3 - 3x + 2 = 0")
    assert roots == pytest.approx([-2.0, 1.0, 1.0])


def test_supports_cubic_notation_and_superscript():
    assert solve_equation("x³ - 1 = 0")[0] == pytest.approx(1.0)


def test_reports_no_solution():
    assert solve_equation("x + 1 = x + 2") == "No solution"


def test_reports_infinite_solutions():
    assert solve_equation("2x + 2 = 2(x + 1)") == "Infinite solutions"


@pytest.mark.parametrize(
    "equation",
    [
        "x^4 = 16",
        "x = 2 = 3",
        "x + = 2",
        "x + 1",
        "x / (x + 1) = 2",
        "2 3 = 6",
        "1.2.3x = 4",
    ],
)
def test_rejects_unsupported_or_malformed_equations(equation):
    with pytest.raises(ValueError):
        solve_equation(equation)
