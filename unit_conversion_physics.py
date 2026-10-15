"""Additional pressure, energy, power, and force units.

All factors convert to the canonical SI unit for the dimension.
"""
EXTRA_UNITS = {
    # Pressure: pascal.
    "pa": ("pressure", 1.0, 0.0),
    "kpa": ("pressure", 1_000.0, 0.0),
    "mpa": ("pressure", 1_000_000.0, 0.0),
    "bar": ("pressure", 100_000.0, 0.0),
    "mbar": ("pressure", 100.0, 0.0),
    "atm": ("pressure", 101_325.0, 0.0),
    "psi": ("pressure", 6_894.757293168, 0.0),
    "mmhg": ("pressure", 133.322387415, 0.0),
    "torr": ("pressure", 101_325.0 / 760.0, 0.0),
    "millipascal": ("pressure", 0.001, 0.0),
    # Energy: joule.
    "j": ("energy", 1.0, 0.0),
    "kj": ("energy", 1_000.0, 0.0),
    "megajoule": ("energy", 1_000_000.0, 0.0),
    "cal": ("energy", 4.184, 0.0),
    "kcal": ("energy", 4_184.0, 0.0),
    "wh": ("energy", 3_600.0, 0.0),
    "kwh": ("energy", 3_600_000.0, 0.0),
    "ev": ("energy", 1.602176634e-19, 0.0),
    "millijoule": ("energy", 0.001, 0.0),
    # Power: watt.
    "w": ("power", 1.0, 0.0),
    "kw": ("power", 1_000.0, 0.0),
    "megawatt": ("power", 1_000_000.0, 0.0),
    "milliwatt": ("power", 0.001, 0.0),
    "hp": ("power", 745.6998715822702, 0.0),
    # Force: newton.
    "n": ("force", 1.0, 0.0),
    "kn": ("force", 1_000.0, 0.0),
    "meganewton": ("force", 1_000_000.0, 0.0),
    "lbf": ("force", 4.4482216152605, 0.0),
    "kgf": ("force", 9.80665, 0.0),
}
EXTRA_ALIASES = {
    "pascal": "pa", "pascals": "pa", "kilopascal": "kpa", "kilopascals": "kpa",
    "megapascal": "mpa", "megapascals": "mpa", "millibar": "mbar", "millibars": "mbar",
    "atmosphere": "atm", "atmospheres": "atm", "pound per square inch": "psi",
    "pounds per square inch": "psi", "millimeters of mercury": "mmhg",
    "millimetres of mercury": "mmhg", "joule": "j", "joules": "j",
    "kilojoule": "kj", "kilojoules": "kj", "megajoules": "megajoule",
    "calorie": "cal", "calories": "cal", "kilocalorie": "kcal", "kilocalories": "kcal",
    "watt hour": "wh", "watt-hours": "wh", "kilowatt hour": "kwh",
    "kilowatt-hours": "kwh", "electronvolt": "ev", "electronvolts": "ev",
    "watt": "w", "watts": "w", "kilowatt": "kw", "kilowatts": "kw",
    "megawatts": "megawatt", "milliwatts": "milliwatt", "horsepower": "hp",
    "newton": "n", "newtons": "n", "kilonewton": "kn", "kilonewtons": "kn",
    "meganewtons": "meganewton", "pound-force": "lbf", "pounds-force": "lbf",
    "kilogram-force": "kgf",
}
EXTRA_SYMBOL_ALIASES = {
    "Pa": "pa", "kPa": "kpa", "MPa": "mpa", "mPa": "millipascal",
    "J": "j", "kJ": "kj", "MJ": "megajoule", "mJ": "millijoule",
    "W": "w", "kW": "kw", "MW": "megawatt", "mW": "milliwatt",
    "N": "n", "kN": "kn", "MN": "meganewton",
    "Wh": "wh", "kWh": "kwh", "eV": "ev",
}
