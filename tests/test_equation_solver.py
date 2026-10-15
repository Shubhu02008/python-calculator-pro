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


def test_quadratic_solver_avoids_catastrophic_cancellation():
    roots = solve_equation("x^2 + 10000000000000000x + 1 = 0")
    assert roots[0] == pytest.approx(-1e16)
    assert roots[1] == pytest.approx(-1e-16, rel=1e-12, abs=0.0)


def test_quadratic_solver_preserves_distinct_small_roots():
    roots = solve_equation("x^2 + 0.0000001x = 0")
    assert roots == pytest.approx([-1e-7, 0.0], abs=1e-20)


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


def test_cubic_solver_handles_very_large_roots():
    equation = (
        f"x^3 - {6 * 10**100}x^2 + "
        f"{11 * 10**200}x - {6 * 10**300} = 0"
    )
    roots = sorted(solve_equation(equation))
    assert roots == pytest.approx([1e100, 2e100, 3e100], rel=1e-12)


def test_cubic_solver_handles_very_small_roots():
    # Use fixed-point decimals because the polynomial tokenizer intentionally
    # does not accept scientific notation.
    c2 = format(6e-100, ".110f")
    c1 = format(11e-200, ".210f")
    c0 = format(6e-300, ".310f")
    roots = sorted(solve_equation(f"x^3 - {c2}x^2 + {c1}x - {c0} = 0"))
    assert [root / 1e-100 for root in roots] == pytest.approx(
        [1.0, 2.0, 3.0], rel=1e-12
    )


def test_cubic_solver_handles_near_zero_discriminant():
    roots = sorted(solve_equation("x^3 - 3x + 2.0000000000000004 = 0"))
    assert roots == pytest.approx([-2.0, 1.0, 1.0], abs=1e-7)


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

def test_solver_preserves_small_nonzero_linear_coefficient():
    assert solve_equation("0.0000000000001x = 1") == pytest.approx([1e13])


def test_solver_preserves_small_nonzero_cubic_coefficient():
    roots = solve_equation("0.0000000000001x^3 = 1")
    assert roots[0] == pytest.approx(10 ** (13 / 3), rel=1e-12)

@pytest.mark.parametrize(
    "equation",
    [
        "0.0000000000001x / 0.0000000000001 = 1",
        "0.0000000000001*x*x*x*x = 1",
        "x / (0.0000000000001x + 1) = 2",
    ],
)
def test_small_coefficients_do_not_bypass_structural_validation(equation):
    if equation == "0.0000000000001x / 0.0000000000001 = 1":
        assert solve_equation(equation) == pytest.approx([1.0])
    else:
        with pytest.raises(ValueError):
            solve_equation(equation)


def test_division_by_small_nonzero_constant_is_allowed():
    assert solve_equation("x / 0.0000000000001 = 1") == pytest.approx([1e-13])


@pytest.mark.parametrize(
    "equation",
    [
        "9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999x = 1",
        "9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999 = 1",
    ],
)
def test_rejects_numeric_literals_outside_float_range(equation):
    with pytest.raises(ValueError, match="supported numerical range"):
        solve_equation(equation)


def test_rejects_non_finite_coefficients_created_during_parsing():
    with pytest.raises(ValueError, match="coefficients exceed"):
        solve_equation("99999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999x * 99999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999 = 1")


def test_rejects_quadratic_discriminant_overflow():
    with pytest.raises(OverflowError, match="Quadratic calculation exceeds"):
        solve_equation("1e999x^2 = 1")
