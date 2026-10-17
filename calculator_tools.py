"""Validated utility calculators used by the public engine and HTTP API.

Currency rates are fetched on demand from open.er-api.com. Other calculators
use only the Python standard library and do not make network requests.
"""

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import math
import re
from numbers import Real
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


_CENT = Decimal("0.01")
_CURRENCY_CODE = re.compile(r"^[A-Z]{3}$")
_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _decimal(value, label, *, minimum=None, maximum=None):
    """Convert a finite real-like input to Decimal without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, (Real, Decimal)):
        raise ValueError(f"{label} must be a finite number.")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{label} must be a finite number.") from None
    if not number.is_finite():
        raise ValueError(f"{label} must be a finite number.")
    if minimum is not None and number < Decimal(str(minimum)):
        raise ValueError(f"{label} must be at least {minimum}.")
    if maximum is not None and number > Decimal(str(maximum)):
        raise ValueError(f"{label} must be at most {maximum}.")
    return number


def _money(value):
    return float(value.quantize(_CENT, rounding=ROUND_HALF_UP))


def _fetch_currency_rates(base_currency):
    """Fetch daily exchange rates; isolated for deterministic tests."""
    request = Request(
        f"https://open.er-api.com/v6/latest/{base_currency}",
        headers={"User-Agent": "PythonCalculatorPro/1.0"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise ValueError("Live currency rates are temporarily unavailable.") from exc
    if not isinstance(payload, dict) or payload.get("result") != "success" or not isinstance(payload.get("rates"), dict):
        raise ValueError("The currency-rate provider returned an invalid response.")
    return payload


def convert_currency(amount, from_currency, to_currency):
    """Convert money using the provider's latest available reference rates."""
    value = _decimal(amount, "Amount", minimum=0)
    if not isinstance(from_currency, str) or not _CURRENCY_CODE.fullmatch(from_currency.upper()):
        raise ValueError("Source currency must be a three-letter currency code.")
    if not isinstance(to_currency, str) or not _CURRENCY_CODE.fullmatch(to_currency.upper()):
        raise ValueError("Target currency must be a three-letter currency code.")
    source, target = from_currency.upper(), to_currency.upper()
    payload = _fetch_currency_rates(source)
    rates = payload["rates"]
    if source != target and target not in rates:
        raise ValueError(f"Currency {target} is not supported by the rate provider.")
    rate = Decimal("1") if source == target else _decimal(rates[target], "Exchange rate", minimum=0)
    converted = value * rate
    return {
        "amount": _money(value),
        "from_currency": source,
        "to_currency": target,
        "exchange_rate": float(rate),
        "converted_amount": _money(converted),
        "rate_date": payload.get("time_last_update_utc"),
        "source": "open.er-api.com",
    }


def calculate_discount(price, discount_percent):
    """Calculate the discount amount and final price."""
    original = _decimal(price, "Price", minimum=0)
    percent = _decimal(discount_percent, "Discount percentage", minimum=0, maximum=100)
    discount = original * percent / Decimal("100")
    final = original - discount
    return {
        "original_price": _money(original),
        "discount_percent": float(percent),
        "discount_amount": _money(discount),
        "final_price": _money(final),
    }


def calculate_gst(amount, gst_rate, *, inclusive=False):
    """Calculate GST on a pre-tax amount or extract GST from a tax-inclusive total."""
    entered = _decimal(amount, "Amount", minimum=0)
    rate = _decimal(gst_rate, "GST rate", minimum=0, maximum=100)
    multiplier = Decimal("1") + rate / Decimal("100")
    if inclusive:
        base = entered / multiplier
        tax = entered - base
        total = entered
    else:
        base = entered
        tax = base * rate / Decimal("100")
        total = base + tax
    return {
        "base_amount": _money(base),
        "gst_rate": float(rate),
        "gst_amount": _money(tax),
        "total_amount": _money(total),
        "inclusive": inclusive,
    }


def calculate_simple_interest(principal, annual_rate, years):
    """Calculate simple interest, treating annual_rate as a percentage."""
    p = _decimal(principal, "Principal", minimum=0)
    rate = _decimal(annual_rate, "Annual rate", minimum=0, maximum=10000)
    duration = _decimal(years, "Duration in years", minimum=0, maximum=10000)
    interest = p * rate * duration / Decimal("100")
    return {
        "principal": _money(p),
        "annual_rate": float(rate),
        "years": float(duration),
        "interest": _money(interest),
        "total_amount": _money(p + interest),
    }


def calculate_compound_interest(principal, annual_rate, years, compounding_per_year=1):
    """Calculate compound interest with a positive integer compounding frequency."""
    p = _decimal(principal, "Principal", minimum=0)
    rate = _decimal(annual_rate, "Annual rate", minimum=0, maximum=10000)
    duration = _decimal(years, "Duration in years", minimum=0, maximum=10000)
    if isinstance(compounding_per_year, bool) or not isinstance(compounding_per_year, int):
        raise ValueError("Compounding frequency must be a positive integer.")
    if not 1 <= compounding_per_year <= 365:
        raise ValueError("Compounding frequency must be from 1 to 365 per year.")
    total = p * (Decimal("1") + rate / Decimal("100") / compounding_per_year) ** (
        duration * compounding_per_year
    )
    interest = total - p
    return {
        "principal": _money(p),
        "annual_rate": float(rate),
        "years": float(duration),
        "compounding_per_year": compounding_per_year,
        "interest": _money(interest),
        "total_amount": _money(total),
    }


def calculate_emi(principal, annual_rate, tenure_months):
    """Calculate fixed monthly loan EMI using the standard reducing-balance formula."""
    p = _decimal(principal, "Principal", minimum=0)
    annual = _decimal(annual_rate, "Annual rate", minimum=0, maximum=10000)
    if isinstance(tenure_months, bool) or not isinstance(tenure_months, int):
        raise ValueError("Tenure must be a positive whole number of months.")
    if not 1 <= tenure_months <= 1200:
        raise ValueError("Tenure must be from 1 to 1200 months.")
    monthly_rate = float(annual / Decimal("1200"))
    principal_float = float(p)
    if monthly_rate == 0:
        emi = principal_float / tenure_months
    else:
        factor = (1 + monthly_rate) ** tenure_months
        emi = principal_float * monthly_rate * factor / (factor - 1)
    total = emi * tenure_months
    return {
        "principal": _money(p),
        "annual_rate": float(annual),
        "tenure_months": tenure_months,
        "monthly_emi": _money(Decimal(str(emi))),
        "total_payment": _money(Decimal(str(total))),
        "total_interest": _money(Decimal(str(total - principal_float))),
    }


def convert_number_base(value, from_base, to_base):
    """Convert an integer literal between bases 2 through 36."""
    if isinstance(from_base, bool) or not isinstance(from_base, int) or not 2 <= from_base <= 36:
        raise ValueError("Source base must be an integer from 2 to 36.")
    if isinstance(to_base, bool) or not isinstance(to_base, int) or not 2 <= to_base <= 36:
        raise ValueError("Target base must be an integer from 2 to 36.")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Number must be a non-empty string.")
    literal = value.strip().upper()
    try:
        number = int(literal, from_base)
    except ValueError:
        raise ValueError(f"{value!r} is not a valid base-{from_base} integer.") from None
    if number == 0:
        converted = "0"
    else:
        sign = "-" if number < 0 else ""
        number = abs(number)
        digits = []
        while number:
            number, remainder = divmod(number, to_base)
            digits.append(_DIGITS[remainder])
        converted = sign + "".join(reversed(digits))
    return {
        "input": literal,
        "from_base": from_base,
        "to_base": to_base,
        "decimal_value": int(literal, from_base),
        "converted_value": converted,
    }


def calculate_bmi(weight_kg, height_m):
    """Calculate body mass index; category labels use standard adult ranges."""
    weight = _decimal(weight_kg, "Weight", minimum=0)
    height = _decimal(height_m, "Height", minimum=0)
    if weight == 0:
        raise ValueError("Weight must be greater than zero.")
    if height == 0:
        raise ValueError("Height must be greater than zero.")
    bmi = float(weight / (height * height))
    if bmi < 18.5:
        category = "underweight"
    elif bmi < 25:
        category = "normal"
    elif bmi < 30:
        category = "overweight"
    else:
        category = "obesity"
    return {"weight_kg": float(weight), "height_m": float(height), "bmi": round(bmi, 2), "category": category}


def calculate_date(operation, date_value, *, days=0, other_date=None):
    """Perform ISO-date arithmetic: add days, subtract days, or find date difference."""
    if not isinstance(date_value, str):
        raise ValueError("Date must be text in YYYY-MM-DD format.")
    try:
        parsed = date.fromisoformat(date_value)
    except ValueError:
        raise ValueError("Date must be a valid date in YYYY-MM-DD format.") from None
    if operation in {"add_days", "subtract_days"}:
        if isinstance(days, bool) or not isinstance(days, int):
            raise ValueError("Days must be a whole number.")
        delta = days if operation == "add_days" else -days
        try:
            result = parsed + timedelta(days=delta)
        except OverflowError:
            raise ValueError("Calculated date is outside the supported range.") from None
        return {"operation": operation, "input_date": parsed.isoformat(), "result_date": result.isoformat(), "days": days}
    if operation == "difference":
        if not isinstance(other_date, str):
            raise ValueError("other_date is required for date difference.")
        try:
            other = date.fromisoformat(other_date)
        except ValueError:
            raise ValueError("other_date must be a valid date in YYYY-MM-DD format.") from None
        return {
            "operation": operation,
            "start_date": parsed.isoformat(),
            "end_date": other.isoformat(),
            "days_difference": (other - parsed).days,
            "absolute_days": abs((other - parsed).days),
        }
    raise ValueError("Operation must be add_days, subtract_days, or difference.")


__all__ = [
    "calculate_bmi", "calculate_compound_interest", "calculate_date",
    "calculate_discount", "calculate_emi", "calculate_gst",
    "calculate_simple_interest", "convert_currency", "convert_number_base",
]
