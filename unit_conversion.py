"""Unit conversion helpers for common everyday measurements.

The module is UI-independent and uses only the Python standard library. Each
unit maps to a dimension, a multiplier to a canonical base unit, and an offset
for affine scales such as temperature.
"""

import math
from numbers import Real


# Base units: metre, kilogram, litre, kelvin, square metre, metre/second, second.
# Conversion to base is value * scale + offset.
_UNITS = {
    # Length.
    "m": ("length", 1.0, 0.0),
    "km": ("length", 1_000.0, 0.0),
    "cm": ("length", 0.01, 0.0),
    "mm": ("length", 0.001, 0.0),
    "mi": ("length", 1_609.344, 0.0),
    "yd": ("length", 0.9144, 0.0),
    "ft": ("length", 0.3048, 0.0),
    "in": ("length", 0.0254, 0.0),
    # Mass.
    "kg": ("mass", 1.0, 0.0),
    "g": ("mass", 0.001, 0.0),
    "mg": ("mass", 0.000001, 0.0),
    "lb": ("mass", 0.45359237, 0.0),
    "oz": ("mass", 0.028349523125, 0.0),
    # Volume.
    "l": ("volume", 1.0, 0.0),
    "ml": ("volume", 0.001, 0.0),
    "m3": ("volume", 1_000.0, 0.0),
    "gal": ("volume", 3.785411784, 0.0),
    # Temperature, with kelvin as the canonical base.
    "k": ("temperature", 1.0, 0.0),
    "c": ("temperature", 1.0, 273.15),
    "f": ("temperature", 5.0 / 9.0, 255.3722222222222),
    # Area.
    "m2": ("area", 1.0, 0.0),
    "km2": ("area", 1_000_000.0, 0.0),
    "cm2": ("area", 0.0001, 0.0),
    "ft2": ("area", 0.09290304, 0.0),
    "acre": ("area", 4_046.8564224, 0.0),
    "mi2": ("area", 2_589_988.110336, 0.0),
    # Speed, with metres per second as the canonical base.
    "m/s": ("speed", 1.0, 0.0),
    "km/h": ("speed", 1.0 / 3.6, 0.0),
    "mph": ("speed", 0.44704, 0.0),
    "ft/s": ("speed", 0.3048, 0.0),
    # Time, with seconds as the canonical base.
    "s": ("time", 1.0, 0.0),
    "ms": ("time", 0.001, 0.0),
    "min": ("time", 60.0, 0.0),
    "h": ("time", 3_600.0, 0.0),
    "day": ("time", 86_400.0, 0.0),
}

_ALIASES = {
    "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "kilometer": "km", "kilometers": "km", "kilometre": "km", "kilometres": "km",
    "centimeter": "cm", "centimeters": "cm", "centimetre": "cm", "centimetres": "cm",
    "millimeter": "mm", "millimeters": "mm", "millimetre": "mm", "millimetres": "mm",
    "mile": "mi", "miles": "mi", "yard": "yd", "yards": "yd",
    "foot": "ft", "feet": "ft", "inch": "in", "inches": "in",
    "kilogram": "kg", "kilograms": "kg", "gram": "g", "grams": "g",
    "milligram": "mg", "milligrams": "mg", "pound": "lb", "pounds": "lb",
    "ounce": "oz", "ounces": "oz",
    "liter": "l", "liters": "l", "litre": "l", "litres": "l",
    "milliliter": "ml", "milliliters": "ml", "millilitre": "ml", "millilitres": "ml",
    "m^3": "m3", "m³": "m3", "cubic meter": "m3", "cubic metre": "m3",
    "gallon": "gal", "gallons": "gal", "us gallon": "gal",
    "kelvin": "k", "celsius": "c", "degree celsius": "c", "degrees celsius": "c",
    "°c": "c", "fahrenheit": "f", "degree fahrenheit": "f",
    "degrees fahrenheit": "f", "°f": "f", "°k": "k",
    "m^2": "m2", "m²": "m2", "square meter": "m2", "square metre": "m2",
    "km^2": "km2", "km²": "km2", "square kilometer": "km2", "square kilometre": "km2",
    "cm^2": "cm2", "cm²": "cm2", "square centimeter": "cm2", "square centimetre": "cm2",
    "ft^2": "ft2", "ft²": "ft2", "square foot": "ft2", "square feet": "ft2",
    "square miles": "mi2", "square mile": "mi2",
    "meters per second": "m/s", "metres per second": "m/s",
    "kilometers per hour": "km/h", "kilometres per hour": "km/h",
    "miles per hour": "mph", "feet per second": "ft/s",
    "second": "s", "seconds": "s", "millisecond": "ms", "milliseconds": "ms",
    "minute": "min", "minutes": "min", "hour": "h", "hours": "h",
    "days": "day",
}


from unit_conversion_physics import EXTRA_UNITS as _PHYSICS_UNITS
from unit_conversion_physics import EXTRA_ALIASES as _PHYSICS_ALIASES
from unit_conversion_physics import EXTRA_SYMBOL_ALIASES as _PHYSICS_SYMBOL_ALIASES
from unit_conversion_technical import EXTRA_UNITS as _TECHNICAL_UNITS
from unit_conversion_technical import EXTRA_ALIASES as _TECHNICAL_ALIASES
from unit_conversion_technical import EXTRA_SYMBOL_ALIASES as _TECHNICAL_SYMBOL_ALIASES
from unit_conversion_cooking import EXTRA_UNITS as _COOKING_UNITS
from unit_conversion_cooking import EXTRA_ALIASES as _COOKING_ALIASES
from unit_conversion_cooking import EXTRA_SYMBOL_ALIASES as _COOKING_SYMBOL_ALIASES
from unit_conversion_land import EXTRA_UNITS as _LAND_UNITS
from unit_conversion_land import EXTRA_ALIASES as _LAND_ALIASES
from unit_conversion_land import EXTRA_SYMBOL_ALIASES as _LAND_SYMBOL_ALIASES

_UNITS.update(_PHYSICS_UNITS)
_UNITS.update(_TECHNICAL_UNITS)
_UNITS.update(_COOKING_UNITS)
_UNITS.update(_LAND_UNITS)
_ALIASES.update(_PHYSICS_ALIASES)
_ALIASES.update(_TECHNICAL_ALIASES)
_ALIASES.update(_COOKING_ALIASES)
_ALIASES.update(_LAND_ALIASES)
_SYMBOL_ALIASES = dict(_PHYSICS_SYMBOL_ALIASES)
_SYMBOL_ALIASES.update(_TECHNICAL_SYMBOL_ALIASES)
_SYMBOL_ALIASES.update(_COOKING_SYMBOL_ALIASES)
_SYMBOL_ALIASES.update(_LAND_SYMBOL_ALIASES)


def list_supported_units():
    """Return supported unit identifiers grouped by measurement dimension.

    The returned mapping and tuples are newly created, so callers can inspect
    the unit catalog without mutating the converter's internal registry.
    Identifiers are the canonical values accepted by convert_unit().
    """
    grouped = {}
    for unit, (dimension, _scale, _offset) in _UNITS.items():
        grouped.setdefault(dimension, []).append(unit)
    return {
        dimension: tuple(sorted(units))
        for dimension, units in sorted(grouped.items())
    }


def _normalize_unit(unit):
    """Return the canonical unit symbol or raise a helpful ValueError."""
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("Unit names must be non-empty text.")
    raw = unit.strip()
    key = _SYMBOL_ALIASES.get(raw, raw.lower())
    key = _ALIASES.get(key, key)
    if key not in _UNITS:
        raise ValueError(f"Unsupported unit: {unit!r}.")
    return key


def convert_unit(value, from_unit, to_unit):
    """Convert a finite real value between compatible supported units.

    Supported dimensions include length, mass, volume, temperature, area, speed,
    and time. Unit names are case-insensitive; common full-word aliases work too.
    The result is a float. Incompatible dimensions and unsupported units are
    rejected rather than silently producing a misleading result.
    """
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("Value must be a real number.")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError("Value must be finite.")

    source = _normalize_unit(from_unit)
    target = _normalize_unit(to_unit)
    source_dimension, source_scale, source_offset = _UNITS[source]
    target_dimension, target_scale, target_offset = _UNITS[target]
    if source_dimension != target_dimension:
        raise ValueError(
            f"Cannot convert {source_dimension} to {target_dimension}."
        )

    try:
        base_value = float(value) * source_scale + source_offset
        result = (base_value - target_offset) / target_scale
    except OverflowError as exc:
        raise ValueError("Converted value is outside the supported range.") from exc
    if not math.isfinite(result):
        raise ValueError("Converted value is outside the supported range.")
    return result


__all__ = ["convert_unit", "list_supported_units"]
