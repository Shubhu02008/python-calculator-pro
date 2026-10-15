"""Cooking and additional US/Imperial volume units, based on litres."""
EXTRA_UNITS = {
    # US customary volume units, converted to litres.
    "teaspoon": ("volume", 0.00492892159375, 0.0),
    "tablespoon": ("volume", 0.01478676478125, 0.0),
    "cup": ("volume", 0.2365882365, 0.0),
    "floz": ("volume", 0.0295735295625, 0.0),
    "pint": ("volume", 0.473176473, 0.0),
    "quart": ("volume", 0.946352946, 0.0),
    # Imperial units are separate from US customary units.
    "imperial_gallon": ("volume", 4.54609, 0.0),
    "imperial_quart": ("volume", 1.1365225, 0.0),
    "imperial_pint": ("volume", 0.56826125, 0.0),
    "imperial_floz": ("volume", 0.0284130625, 0.0),
}
EXTRA_ALIASES = {
    "tsp": "teaspoon", "teaspoons": "teaspoon",
    "tbsp": "tablespoon", "tablespoons": "tablespoon",
    "cups": "cup", "us cup": "cup", "us cups": "cup",
    "fluid ounce": "floz", "fluid ounces": "floz", "fl oz": "floz",
    "us fluid ounce": "floz", "us fl oz": "floz",
    "pints": "pint", "us pint": "pint", "us pints": "pint",
    "quarts": "quart", "us quart": "quart", "us quarts": "quart",
    "uk gallon": "imperial_gallon", "imperial gallons": "imperial_gallon",
    "uk quart": "imperial_quart", "imperial quarts": "imperial_quart",
    "uk pint": "imperial_pint", "imperial pints": "imperial_pint",
    "imperial fluid ounce": "imperial_floz", "imperial fluid ounces": "imperial_floz",
    "uk fl oz": "imperial_floz", "imperial fl oz": "imperial_floz",
}
EXTRA_SYMBOL_ALIASES = {
    "tsp": "teaspoon", "tbsp": "tablespoon", "cup": "cup",
    "fl oz": "floz", "pt": "pint", "qt": "quart",
}
