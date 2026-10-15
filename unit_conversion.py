"""Unit conversion helpers for common everyday measurements.

The module is intentionally UI-independent and uses only the Python standard
library. Values are converted through a canonical base unit for each dimension.
"""

import math
from numbers import Real


# Each unit maps to (dimension, multiplier to base unit). The base units are
# metre for length, kilogram for mass, and litre for volume.
_UNITS = {
    # Length: base unit metre.
    "m": ("length", 1.0),
    "km": ("length", 1_000.0),
    "cm": ("length", 0.01),
    "mm": ("length", 0.001),
    "mi": ("length", 1_609.344),
    "yd": ("length", 0.9144),
    "ft": ("length", 0.3048),
    "in": ("length", 0.0254),
    # Mass: base unit kilogram.
    "kg": ("mass", 1.0),
    "g": ("mass", 0.001),
    "mg": ("mass", 0.000001),
    "lb": ("mass", 0.45359237),
    "oz": ("mass", 0.028349523125),
    # Volume: base unit litre.
    "l": ("volume", 1.0),
    "ml": ("volume", 0.001),
    "m3": ("volume", 1_000.0),
    "gal": ("volume", 3.785411784),
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
}


def _normalize_unit(unit):
    """Return the canonical unit symbol or raise a helpful ValueError."""
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("Unit names must be non-empty text.")
    key = unit.strip().lower()
    key = _ALIASES.get(key, key)
    if key not in _UNITS:
        raise ValueError(f"Unsupported unit: {unit!r}.")
    return key


def convert_unit(value, from_unit, to_unit):
    """Convert a finite real value between compatible length, mass, or volume units.

    Unit names are case-insensitive and common full-word names are accepted.
    The result is a float. Conversions between different dimensions are rejected.
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
    source_dimension, source_factor = _UNITS[source]
    target_dimension, target_factor = _UNITS[target]
    if source_dimension != target_dimension:
        raise ValueError(
            f"Cannot convert {source_dimension} to {target_dimension}."
        )

    result = float(value) * source_factor / target_factor
    if not math.isfinite(result):
        raise ValueError("Converted value is outside the supported range.")
    return result


__all__ = ["convert_unit"]
