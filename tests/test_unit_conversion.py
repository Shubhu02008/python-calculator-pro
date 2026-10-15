import math

import pytest

from unit_conversion import convert_unit


@pytest.mark.parametrize(
    "value,source,target,expected",
    [
        (1, "km", "m", 1000),
        (250, "cm", "m", 2.5),
        (1, "mi", "km", 1.609344),
        (1, "ft", "in", 12),
        (1, "kg", "g", 1000),
        (2500, "mg", "g", 2.5),
        (1, "lb", "kg", 0.45359237),
        (1, "l", "ml", 1000),
        (1, "m3", "l", 1000),
        (1, "gal", "l", 3.785411784),
    ],
)
def test_convert_supported_units(value, source, target, expected):
    assert convert_unit(value, source, target) == pytest.approx(expected)


def test_unit_names_are_case_insensitive_and_accept_aliases():
    assert convert_unit(1, "Kilometers", "METERS") == pytest.approx(1000)
    assert convert_unit(1, "pound", "kg") == pytest.approx(0.45359237)


def test_same_unit_conversion_preserves_value():
    assert convert_unit(12.5, "m", "meters") == pytest.approx(12.5)


@pytest.mark.parametrize("value", [True, "3", None, math.inf, -math.inf, math.nan])
def test_rejects_non_real_or_non_finite_values(value):
    with pytest.raises(ValueError, match="real number|finite"):
        convert_unit(value, "m", "km")


@pytest.mark.parametrize(
    "source,target",
    [("m", "kg"), ("l", "m"), ("km", "g")],
)
def test_rejects_incompatible_dimensions(source, target):
    with pytest.raises(ValueError, match="Cannot convert"):
        convert_unit(1, source, target)


@pytest.mark.parametrize("unit", ["", "parsecs", None, 10])
def test_rejects_unknown_or_invalid_units(unit):
    with pytest.raises(ValueError, match="Unit"):
        convert_unit(1, unit, "m")
