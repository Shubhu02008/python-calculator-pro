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
        (1, "bar", "kPa", 100),
        (1, "atm", "Pa", 101325),
        (14.6959487755, "psi", "atm", 1),
        (1, "kWh", "J", 3_600_000),
        (1, "kcal", "kJ", 4.184),
        (1, "eV", "J", 1.602176634e-19),
        (1, "hp", "W", 745.6998715822702),
        (1, "lbf", "N", 4.4482216152605),
        (1, "kgf", "N", 9.80665),
        (1, "MPa", "kPa", 1000),
        (1, "mW", "W", 0.001),
        (1, "MW", "kW", 1000),
    ],
)
def test_pressure_energy_power_and_force_conversions(value, source, target, expected):
    assert convert_unit(value, source, target) == pytest.approx(expected)


def test_rejects_incompatible_physics_dimensions():
    with pytest.raises(ValueError, match="Cannot convert pressure to energy"):
        convert_unit(1, "bar", "J")
    with pytest.raises(ValueError, match="Cannot convert force to power"):
        convert_unit(1, "N", "W")


@pytest.mark.parametrize(
    "value,source,target,expected",
    [
        (1, "KB", "byte", 1000),
        (1, "KiB", "byte", 1024),
        (1, "MB", "KB", 1000),
        (1, "Mb", "kb", 1000),
        (1, "GHz", "MHz", 1000),
        (120, "rpm", "Hz", 2),
        (1, "kV", "V", 1000),
        (1, "mA", "A", 0.001),
        (1, "kΩ", "ohm", 1000),
        (1, "uF", "farad", 1e-6),
        (1, "mAh", "coulomb", 3.6),
        (1, "mH", "henry", 0.001),
    ],
)
def test_data_frequency_and_electrical_conversions(value, source, target, expected):
    assert convert_unit(value, source, target) == pytest.approx(expected)


def test_rejects_incompatible_technical_dimensions():
    with pytest.raises(ValueError, match="Cannot convert data_size to frequency"):
        convert_unit(1, "GB", "GHz")
    with pytest.raises(ValueError, match="Cannot convert voltage to current"):
        convert_unit(1, "V", "A")


@pytest.mark.parametrize(
    "value,source,target,expected",
    [
        (1, "cup", "ml", 236.5882365),
        (1, "tsp", "ml", 4.92892159375),
        (1, "tbsp", "tsp", 3),
        (1, "US gallon", "L", 3.785411784),
        (1, "imperial gallon", "L", 4.54609),
        (1, "pt", "cup", 2),
        (1, "qt", "pt", 2),
        (1, "imperial pint", "imperial fl oz", 20),
    ],
)
def test_cooking_and_additional_volume_conversions(value, source, target, expected):
    assert convert_unit(value, source, target) == pytest.approx(expected)


def test_cooking_volume_units_remain_volume_dimension():
    assert convert_unit(1, "cup", "l") == pytest.approx(0.2365882365)
    with pytest.raises(ValueError, match="Cannot convert volume to mass"):
        convert_unit(1, "cup", "g")
