import pytest

from calculator import calculate


def test_add():
    assert calculate("add", [5, 3]) == 8


def test_multiple_add():
    assert calculate("add", [5, 10, 20]) == 35


def test_subtract():
    assert calculate("subtract", [5, 3]) == 2


def test_multiple_subtract():
    assert calculate("subtract", [10, 3, 2]) == 5


def test_multiply():
    assert calculate("multiply", [5, 3]) == 15


def test_multiple_multiply():
    assert calculate("multiply", [2, 3, 4]) == 24


def test_divide():
    assert calculate("divide", [10, 2]) == 5


def test_divide_by_zero():
    assert calculate("divide", [10, 0]) == "Cannot divide by zero"


def test_invalid_operation():
    assert calculate("unknown", [5, 3]) == "Invalid operation"

@pytest.mark.parametrize("numbers", [[float("nan")], [float("inf")], [float("-inf")], ["5"], [True]])
def test_named_operations_reject_invalid_or_non_finite_inputs(numbers):
    with pytest.raises(ValueError, match="finite real numeric values"):
        calculate("add", numbers)


@pytest.mark.parametrize(
    "operation,numbers",
    [
        ("add", [1e308, 1e308]),
        ("multiply", [1e308, 1e308]),
    ],
)
def test_named_operations_reject_non_finite_results(operation, numbers):
    with pytest.raises(ValueError, match="outside the supported range"):
        calculate(operation, numbers)


def test_named_operation_rejects_integer_beyond_supported_float_range():
    with pytest.raises(ValueError, match="finite real numeric values"):
        calculate("add", [10**1000])


def test_invalid_operation_remains_compatible():
    assert calculate("unknown", ["not a number"]) == "Invalid operation"


def test_expression_calculation():
    assert calculate("5 + 10 * 3") == 35


def test_empty_number_list_is_rejected():
    with pytest.raises(ValueError, match="at least one number"):
        calculate("add", [])


def test_empty_number_tuple_is_rejected():
    with pytest.raises(ValueError, match="at least one number"):
        calculate("subtract", ())
