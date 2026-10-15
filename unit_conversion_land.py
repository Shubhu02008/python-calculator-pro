"""Indian land-area units using one fixed pucca-bigha convention.

For this calculator, 1 bigha is defined as 27,000 square feet and 1 bigha
is 20 biswa. These are fixed conversion factors, not region-selectable settings.
"""
EXTRA_UNITS = {
    "bigha": ("area", 2_508.38208, 0.0),  # 27,000 square feet in square metres
    "biswa": ("area", 125.419104, 0.0),   # one twentieth of this bigha
}
EXTRA_ALIASES = {
    "bighas": "bigha",
    "biswas": "biswa",
    "bisva": "biswa",
    "bisvas": "biswa",
}
EXTRA_SYMBOL_ALIASES = {}
