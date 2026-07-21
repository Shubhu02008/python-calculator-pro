from calculator import add, subtract


def test_add():
    assert add(5, 3) == 8


def test_subtract():
    assert subtract(5, 3) == 2