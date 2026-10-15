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
    # Cooking and customary volume measures; the default US units are explicit.
    "uscup": ("volume", 0.2365882365, 0.0),
    "ustsp": ("volume", 0.00492892159375, 0.0),
    "ustbsp": ("volume", 0.01478676478125, 0.0),
    "usfloz": ("volume", 0.0295735295625, 0.0),
    "uspint": ("volume", 0.473176473, 0.0),
    "usquart": ("volume", 0.946352946, 0.0),
    "metriccup": ("volume", 0.25, 0.0),
    "metrictsp": ("volume", 0.005, 0.0),
    "metrictbsp": ("volume", 0.015, 0.0),
    "imperialfloz": ("volume", 0.0284130625, 0.0),
    "imperialpint": ("volume", 0.56826125, 0.0),
    "imperialquart": ("volume", 1.1365225, 0.0),
    "imperialgal": ("volume", 4.54609, 0.0),
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
    "in2": ("area", 0.00064516, 0.0),
    "yd2": ("area", 0.83612736, 0.0),
    "ha": ("area", 10_000.0, 0.0),
    "are": ("area", 100.0, 0.0),
    "guntha": ("area", 101.17141056, 0.0),
    "kanal": ("area", 505.8570528, 0.0),
    "marla": ("area", 25.29285264, 0.0),
    "cent": ("area", 40.468564224, 0.0),
    "decimal": ("area", 40.468564224, 0.0),
    # Fixed reference convention: 1 bigha = 27,225 square feet.
    # Biswa and katha are each 1/20 bigha; dhur is 1/20 of either.
    "bigha": ("area", 2_529.285264, 0.0),
    "biswa": ("area", 126.4642632, 0.0),
    "katha": ("area", 126.4642632, 0.0),
    "dhur": ("area", 6.32321316, 0.0),
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
    # Pressure, with pascal as the canonical base.
    "pa": ("pressure", 1.0, 0.0),
    "kpa": ("pressure", 1_000.0, 0.0),
    "mpa": ("pressure", 1_000_000.0, 0.0),
    "bar": ("pressure", 100_000.0, 0.0),
    "atm": ("pressure", 101_325.0, 0.0),
    "psi": ("pressure", 6_894.757293168, 0.0),
    "mmhg": ("pressure", 133.322387415, 0.0),
    # Energy, with joule as the canonical base.
    "j": ("energy", 1.0, 0.0),
    "kj": ("energy", 1_000.0, 0.0),
    "mj": ("energy", 1_000_000.0, 0.0),
    "cal": ("energy", 4.184, 0.0),
    "kcal": ("energy", 4_184.0, 0.0),
    "wh": ("energy", 3_600.0, 0.0),
    "kwh": ("energy", 3_600_000.0, 0.0),
    "ev": ("energy", 1.602176634e-19, 0.0),
    # Power, with watt as the canonical base.
    "w": ("power", 1.0, 0.0),
    "mw": ("power", 0.001, 0.0),
    "kw": ("power", 1_000.0, 0.0),
    "megawatt": ("power", 1_000_000.0, 0.0),
    "hp": ("power", 745.6998715822702, 0.0),
    # Force, with newton as the canonical base.
    "n": ("force", 1.0, 0.0),
    "kn": ("force", 1_000.0, 0.0),
    "lbf": ("force", 4.4482216152605, 0.0),
    "kgf": ("force", 9.80665, 0.0),
    # Frequency, with hertz as the canonical base.
    "hz": ("frequency", 1.0, 0.0),
    "khz": ("frequency", 1_000.0, 0.0),
    "mhz": ("frequency", 1_000_000.0, 0.0),
    "ghz": ("frequency", 1_000_000_000.0, 0.0),
    "rpm": ("frequency", 1.0 / 60.0, 0.0),
    # Electrical quantities.
    "v": ("voltage", 1.0, 0.0),
    "mv": ("voltage", 0.001, 0.0),
    "kv": ("voltage", 1_000.0, 0.0),
    "a": ("current", 1.0, 0.0),
    "ma": ("current", 0.001, 0.0),
    "ka": ("current", 1_000.0, 0.0),
    "ua": ("current", 0.000001, 0.0),
    "ohm": ("resistance", 1.0, 0.0),
    "kohm": ("resistance", 1_000.0, 0.0),
    "mohm": ("resistance", 1_000_000.0, 0.0),
    "coulomb": ("charge", 1.0, 0.0),
    "millicoulomb": ("charge", 0.001, 0.0),
    "ah": ("charge", 3_600.0, 0.0),
    "mah": ("charge", 3.6, 0.0),
    "farad": ("capacitance", 1.0, 0.0),
    "ufarad": ("capacitance", 0.000001, 0.0),
    "nfarad": ("capacitance", 0.000000001, 0.0),
    "pfarad": ("capacitance", 0.000000000001, 0.0),
    "henry": ("inductance", 1.0, 0.0),
    "mhenry": ("inductance", 0.001, 0.0),
    "uhenry": ("inductance", 0.000001, 0.0),
    "siemens": ("conductance", 1.0, 0.0),
    "msiemens": ("conductance", 0.001, 0.0),
    # Digital storage uses decimal SI units and binary IEC units separately.
    # The canonical base is byte; bit values are scaled by 1/8.
    "bit": ("data", 0.125, 0.0),
    "byte": ("data", 1.0, 0.0),
    "kbit": ("data", 125.0, 0.0),
    "mbit": ("data", 125_000.0, 0.0),
    "gbit": ("data", 125_000_000.0, 0.0),
    "tbit": ("data", 125_000_000_000.0, 0.0),
    "kbyte": ("data", 1_000.0, 0.0),
    "mbyte": ("data", 1_000_000.0, 0.0),
    "gbyte": ("data", 1_000_000_000.0, 0.0),
    "tbyte": ("data", 1_000_000_000_000.0, 0.0),
    "kibit": ("data", 128.0, 0.0),
    "mibit": ("data", 131_072.0, 0.0),
    "gibit": ("data", 134_217_728.0, 0.0),
    "tebit": ("data", 137_438_953_472.0, 0.0),
    "kibyte": ("data", 1_024.0, 0.0),
    "mibyte": ("data", 1_048_576.0, 0.0),
    "gibyte": ("data", 1_073_741_824.0, 0.0),
    "tebyte": ("data", 1_099_511_627_776.0, 0.0),
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
    "gallon": "gal", "gallons": "gal", "us gallon": "gal", "us gallons": "gal",
    "cup": "uscup", "cups": "uscup", "us cup": "uscup", "us cups": "uscup",
    "teaspoon": "ustsp", "teaspoons": "ustsp", "tsp": "ustsp", "us teaspoon": "ustsp",
    "tablespoon": "ustbsp", "tablespoons": "ustbsp", "tbsp": "ustbsp", "us tablespoon": "ustbsp",
    "fluid ounce": "usfloz", "fluid ounces": "usfloz", "fl oz": "usfloz", "us fluid ounce": "usfloz",
    "pint": "uspint", "pints": "uspint", "us pint": "uspint", "pt": "uspint",
    "quart": "usquart", "quarts": "usquart", "us quart": "usquart", "qt": "usquart",
    "metric cup": "metriccup", "metric cups": "metriccup",
    "metric teaspoon": "metrictsp", "metric teaspoons": "metrictsp",
    "metric tablespoon": "metrictbsp", "metric tablespoons": "metrictbsp",
    "imperial fluid ounce": "imperialfloz", "imperial fluid ounces": "imperialfloz",
    "imperial pint": "imperialpint", "imperial pints": "imperialpint",
    "imperial quart": "imperialquart", "imperial quarts": "imperialquart",
    "imperial gallon": "imperialgal", "imperial gallons": "imperialgal", "uk gallon": "imperialgal",
    "kelvin": "k", "celsius": "c", "degree celsius": "c", "degrees celsius": "c",
    "°c": "c", "fahrenheit": "f", "degree fahrenheit": "f",
    "degrees fahrenheit": "f", "°f": "f", "°k": "k",
    "m^2": "m2", "m²": "m2", "square meter": "m2", "square metre": "m2",
    "km^2": "km2", "km²": "km2", "square kilometer": "km2", "square kilometre": "km2",
    "cm^2": "cm2", "cm²": "cm2", "square centimeter": "cm2", "square centimetre": "cm2",
    "ft^2": "ft2", "ft²": "ft2", "square foot": "ft2", "square feet": "ft2",
    "square miles": "mi2", "square mile": "mi2",
    "in^2": "in2", "in²": "in2", "square inch": "in2", "square inches": "in2",
    "yd^2": "yd2", "yd²": "yd2", "square yard": "yd2", "square yards": "yd2",
    "hectare": "ha", "hectares": "ha", "ha": "ha", "ares": "are",
    "gunta": "guntha", "gunthas": "guntha",
    "kanals": "kanal", "marla": "marla", "marlas": "marla",
    "cents": "cent", "decimal land": "decimal", "decimals": "decimal",
    "bighas": "bigha", "biswas": "biswa", "kathas": "katha", "dhurs": "dhur",
    "meters per second": "m/s", "metres per second": "m/s",
    "kilometers per hour": "km/h", "kilometres per hour": "km/h",
    "miles per hour": "mph", "feet per second": "ft/s",
    "second": "s", "seconds": "s", "millisecond": "ms", "milliseconds": "ms",
    "minute": "min", "minutes": "min", "hour": "h", "hours": "h",
    "days": "day",
    # Pressure.
    "pascal": "pa", "pascals": "pa", "kilopascal": "kpa", "kilopascals": "kpa",
    "megapascal": "mpa", "megapascals": "mpa", "atmosphere": "atm", "atmospheres": "atm",
    "pounds per square inch": "psi", "millimeter of mercury": "mmhg",
    "millimeters of mercury": "mmhg", "torr": "mmhg",
    # Energy and power.
    "joule": "j", "joules": "j", "kilojoule": "kj", "kilojoules": "kj",
    "megajoule": "mj", "megajoules": "mj", "calorie": "cal", "calories": "cal",
    "kilocalorie": "kcal", "kilocalories": "kcal", "food calorie": "kcal",
    "watt hour": "wh", "watt-hours": "wh", "kilowatt hour": "kwh", "kilowatt-hours": "kwh",
    "electronvolt": "ev", "electron volts": "ev", "watt": "w", "watts": "w",
    "kilowatt": "kw", "kilowatts": "kw", "horsepower": "hp",
    # Force and frequency.
    "newton": "n", "newtons": "n", "kilonewton": "kn", "kilonewtons": "kn",
    "pound force": "lbf", "pound-force": "lbf", "kilogram force": "kgf",
    "hertz": "hz", "kilohertz": "khz", "megahertz": "mhz", "gigahertz": "ghz",
    "revolutions per minute": "rpm",
    # Electrical units.
    "volt": "v", "volts": "v", "millivolt": "mv", "millivolts": "mv",
    "kilovolt": "kv", "kilovolts": "kv", "ampere": "a", "amperes": "a",
    "amp": "a", "amps": "a", "milliamp": "ma", "milliamps": "ma",
    "kiloampere": "ka", "microamp": "ua", "microamps": "ua",
    "ohms": "ohm", "ohm": "ohm", "kiloohm": "kohm", "kilohm": "kohm",
    "megaohm": "mohm", "megohm": "mohm", "coulombs": "coulomb",
    "millicoulombs": "millicoulomb", "ampere hour": "ah", "amp-hours": "ah",
    "milliampere hour": "mah", "milliamp-hours": "mah",
    "farads": "farad", "microfarad": "ufarad", "microfarads": "ufarad",
    "nanofarad": "nfarad", "nanofarads": "nfarad", "picofarad": "pfarad",
    "picofarads": "pfarad", "henries": "henry", "millihenry": "mhenry",
    "millihenries": "mhenry", "microhenry": "uhenry", "microhenries": "uhenry",
    "siemen": "siemens", "millisiemens": "msiemens",
    # Digital storage words. Symbols are handled separately to distinguish b from B.
    "bits": "bit", "bytes": "byte", "kilobit": "kbit", "kilobits": "kbit",
    "megabit": "mbit", "megabits": "mbit", "gigabit": "gbit", "gigabits": "gbit",
    "terabit": "tbit", "terabits": "tbit", "kilobyte": "kbyte", "kilobytes": "kbyte",
    "megabyte": "mbyte", "megabytes": "mbyte", "gigabyte": "gbyte", "gigabytes": "gbyte",
    "terabyte": "tbyte", "terabytes": "tbyte", "kibibit": "kibit", "kibibits": "kibit",
    "mebibit": "mibit", "mebibits": "mibit", "gibibit": "gibit", "gibibits": "gibit",
    "tebibit": "tebit", "tebibits": "tebit", "kibibyte": "kibyte", "kibibytes": "kibyte",
    "mebibyte": "mibyte", "mebibytes": "mibyte", "gibibyte": "gibyte", "gibibytes": "gibyte",
    "tebibyte": "tebyte", "tebibytes": "tebyte",
}

# Exact symbols are checked before case-insensitive word aliases. This preserves
# the standard distinction between bit (b) and byte (B), and between SI and IEC
# storage prefixes such as kB and KiB.
_SYMBOL_ALIASES = {
    "b": "bit", "B": "byte",
    "kb": "kbit", "kB": "kbyte", "Mb": "mbit", "MB": "mbyte",
    "Gb": "gbit", "GB": "gbyte", "Tb": "tbit", "TB": "tbyte",
    "Kib": "kibit", "KiB": "kibyte", "Mib": "mibit", "MiB": "mibyte",
    "Gib": "gibit", "GiB": "gibyte", "Tib": "tebit", "TiB": "tebyte",
    "Pa": "pa", "kPa": "kpa", "MPa": "mpa", "mPa": "mpa",
    "Hz": "hz", "kHz": "khz", "MHz": "mhz", "GHz": "ghz",
    "V": "v", "mV": "mv", "kV": "kv", "MW": "megawatt", "A": "a", "mA": "ma", "kA": "ka",
    "uA": "ua", "μA": "ua", "Ω": "ohm", "kΩ": "kohm", "MΩ": "mohm",
    "uF": "ufarad", "μF": "ufarad", "nF": "nfarad", "pF": "pfarad",
    "H": "henry", "mH": "mhenry", "uH": "uhenry", "μH": "uhenry",
    "S": "siemens", "mS": "msiemens",
}


def _normalize_unit(unit):
    """Return the canonical unit symbol or raise a helpful ValueError."""
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("Unit names must be non-empty text.")
    raw = unit.strip()
    if raw in _SYMBOL_ALIASES:
        return _SYMBOL_ALIASES[raw]
    key = raw.lower()
    key = _ALIASES.get(key, key)
    if key not in _UNITS:
        raise ValueError(f"Unsupported unit: {unit!r}.")
    return key


def convert_unit(value, from_unit, to_unit):
    """Convert a finite real value between compatible supported units.

    Supported dimensions include common physical measurements, electrical units,
    frequency, and digital storage. Full-word aliases are case-insensitive; data
    symbols preserve standard case where b means bit and B means byte.
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


__all__ = ["convert_unit"]
