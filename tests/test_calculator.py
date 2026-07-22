from calculator import calculate


def test_add():
    assert calculate("add", [5, 3]) == 8


def test_subtract():
    assert calculate("subtract", [5, 3]) == 2


def test_multiply():
    assert calculate("multiply", [5, 3]) == 15


def test_divide():
    assert calculate("divide", [10, 2]) == 5


def test_divide_by_zero():
    assert calculate("divide", [10, 0]) == "Cannot divide by zero"