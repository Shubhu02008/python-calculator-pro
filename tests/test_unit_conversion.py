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
    with pytest.raises(ValueError, match="(?i)unit"):
        convert_unit(1, unit, "m")



@pytest.mark.parametrize(
    "value,source,target,expected",
    [
        (0, "Celsius", "Fahrenheit", 32),
        (100, "°C", "K", 373.15),
        (32, "°F", "c", 0),
        (1, "km2", "m2", 1_000_000),
        (1, "ft²", "m2", 0.09290304),
        (1, "square mile", "km2", 2.589988110336),
        (36, "km/h", "m/s", 10),
        (60, "minutes", "seconds", 3600),
        (2, "hours", "min", 120),
    ],
)
def test_temperature_area_speed_and_time_conversions(value, source, target, expected):
    assert convert_unit(value, source, target) == pytest.approx(expected)


def test_rejects_temperature_to_non_temperature_conversion():
    with pytest.raises(ValueError, match="Cannot convert temperature to length"):
        convert_unit(20, "Celsius", "m")


def test_temperature_round_trip():
    fahrenheit = convert_unit(23, "C", "F")
    assert convert_unit(fahrenheit, "F", "C") == pytest.approx(23)


@pytest.mark.parametrize(
    "value,source,target,expected",
    [
        (1, "bar", "Pa", 100000),
        (1, "atm", "kPa", 101.325),
        (1, "psi", "kPa", 6.894757293168),
        (1, "kcal", "J", 4184),
        (1, "kWh", "MJ", 3.6),
        (1, "hp", "W", 745.6998715822702),
        (1, "lbf", "N", 4.4482216152605),
        (1, "km/h", "m/s", 1 / 3.6),
        (1, "MHz", "Hz", 1_000_000),
        (1, "rpm", "Hz", 1 / 60),
        (1, "kV", "V", 1000),
        (1, "mA", "A", 0.001),
        (1, "kΩ", "ohm", 1000),
        (1, "mAh", "coulomb", 3.6),
        (1, "μF", "farad", 1e-6),
        (1, "mH", "henry", 0.001),
        (1, "mS", "siemens", 0.001),
        (1, "kB", "byte", 1000),
        (1, "kb", "bit", 1000),
        (1, "KiB", "byte", 1024),
        (1, "MiB", "KiB", 1024),
        (8, "bit", "byte", 1),
    ],
)
def test_technical_and_digital_conversions(value, source, target, expected):
    assert convert_unit(value, source, target) == pytest.approx(expected)


def test_digital_symbols_distinguish_bits_and_bytes():
    assert convert_unit(1, "MB", "Mb") == pytest.approx(8)
    assert convert_unit(1, "MiB", "Mib") == pytest.approx(8)


@pytest.mark.parametrize(
    "source,target",
    [
        ("Pa", "J"),
        ("W", "N"),
        ("Hz", "V"),
        ("V", "A"),
        ("ohm", "farad"),
        ("byte", "joule"),
    ],
)
def test_technical_units_reject_incompatible_dimensions(source, target):
    with pytest.raises(ValueError, match="Cannot convert"):
        convert_unit(1, source, target)


def test_technical_word_aliases_are_case_insensitive():
    assert convert_unit(1, "KILOPASCALS", "Pa") == pytest.approx(1000)
    assert convert_unit(1, "Gigahertz", "MHz") == pytest.approx(1000)
    assert convert_unit(1, "Kilobytes", "byte") == pytest.approx(1000)

def test_case_sensitive_symbols_do_not_confuse_fahrenheit_with_farads():
    assert convert_unit(32, "F", "C") == pytest.approx(0)
    assert convert_unit(1, "MW", "W") == pytest.approx(1_000_000)
    assert convert_unit(1, "mW", "W") == pytest.approx(0.001)


@pytest.mark.parametrize(
    "value,source,target,expected",
    [
        (1, "cup", "ml", 236.5882365),
        (1, "tsp", "ml", 4.92892159375),
        (1, "tbsp", "tsp", 3),
        (1, "fl oz", "ml", 29.5735295625),
        (1, "pt", "cup", 2),
        (1, "qt", "cup", 4),
        (1, "metric cup", "ml", 250),
        (1, "metric teaspoon", "ml", 5),
        (1, "metric tablespoon", "ml", 15),
        (1, "imperial fluid ounce", "ml", 28.4130625),
        (1, "imperial pint", "ml", 568.26125),
        (1, "imperial gallon", "l", 4.54609),
    ],
)
def test_cooking_and_customary_volume_conversions(value, source, target, expected):
    assert convert_unit(value, source, target) == pytest.approx(expected)


def test_cooking_volume_units_remain_volume_units():
    with pytest.raises(ValueError, match="Cannot convert volume to mass"):
        convert_unit(1, "cup", "g")


@pytest.mark.parametrize(
    "value,source,target,expected",
    [
        (1, "hectare", "m2", 10000),
        (1, "acre", "ft2", 43560),
        (1, "square yard", "ft2", 9),
        (1, "square inch", "cm2", 6.4516),
        (1, "guntha", "ft2", 1089),
        (1, "kanal", "ft2", 5445),
        (1, "marla", "ft2", 272.25),
        (1, "cent", "ft2", 435.6),
        (1, "decimal", "ft2", 435.6),
        (1, "bigha", "ft2", 27225),
        (1, "bigha", "acre", 0.625),
        (1, "biswa", "bigha", 0.05),
        (1, "katha", "ft2", 1361.25),
        (1, "dhur", "ft2", 68.0625),
    ],
)
def test_extended_area_and_indian_land_conversions(value, source, target, expected):
    assert convert_unit(value, source, target) == pytest.approx(expected)


@pytest.mark.parametrize("unit", ["bigha", "biswa", "katha", "dhur", "kanal"])
def test_land_units_are_area_units(unit):
    assert convert_unit(1, unit, "m2") > 0
    with pytest.raises(ValueError, match="Cannot convert area to length"):
        convert_unit(1, unit, "m")
