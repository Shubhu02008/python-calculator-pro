# Python Calculator Pro

A Python calculator engine for arithmetic, scientific functions, polynomial equations, and binomial expansions. The current interface is command-line based; a mobile button interface is a separate next step.

**Requirements:** Python 3.11 or newer.

## Features

- Addition, subtraction, multiplication, and division
- Multiplication symbols `*`, `×`, and `·`; division symbols `/` and `÷`
- Decimal numbers, scientific notation, parentheses, and standard precedence
- Powers with `^`, `**`, and superscripts `²` / `³`
- Square roots `√25` / `sqrt(25)` and cube roots `∛27` / `cbrt(27)`
- Trigonometry: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sinh`, `cosh`, `tanh` (angles are in radians)
- Logs and exponentials: `log` (base 10), `ln`, `log10`, `exp`, and `log(value, base)`
- Other functions: `abs`, `floor`, `ceil`, `factorial`, `degrees`, and `radians`
- Constants `pi` / `π`, `e`, and `tau`
- Percentages with postfix `%`, factorials with `!`, and implicit multiplication such as `2pi` and `3(4+5)`
- Linear, quadratic, and cubic equation solving in `x`
- Binomial theorem expansion
- Unit conversion for length, mass, volume, temperature, area, speed, time, pressure, energy, power, force, digital storage, frequency, electrical measurements, and cooking/US/Imperial volume units, and Indian land-area units
- Backend graphing support to evaluate functions and generate bounded coordinate samples
- Clear errors for malformed expressions and common mathematical domain errors

Equation solving supports polynomial equations up to degree 3. The binomial expansion tool accepts simple numeric or single-letter terms and non-negative integer exponents up to 100.

## Run the command-line interface

```bash
python main.py
```

Choose **5** to evaluate an expression, for example `sin(pi/2) + √25`.

Choose **6** to solve a linear, quadratic, or cubic equation, for example:

```text
x^3 - 6x^2 + 11x - 6 = 0
```

Choose **7** to expand a binomial, for example `(x + 2)^3`.

## Run the HTTP API

The HTTP API is an optional adapter for websites and other clients. It calls the same public calculation engine used by the terminal interface.

Install the API dependencies and start the development server:

```bash
python -m pip install -r requirements-api.txt
uvicorn api:app --reload
```

The local server listens at `http://127.0.0.1:8000`. Interactive API documentation is available at `/docs`, and the machine-readable OpenAPI schema is at `/openapi.json`. Currency conversion requires outbound network access to the exchange-rate provider; other new calculators run locally. The BMI category is a general adult screening range, not a medical diagnosis.

### API endpoints

| Method and path | Purpose |
| --- | --- |
| `GET /healthz` | Health check for the hosting platform |
| `GET /api/v1/capabilities` | Available operations, features, and canonical unit identifiers |
| `POST /api/v1/calculate` | Evaluate an arithmetic/scientific expression |
| `POST /api/v1/operations` | Run add, subtract, multiply, or divide |
| `POST /api/v1/units/convert` | Convert compatible measurement units |
| `POST /api/v1/equations/solve` | Solve a supported polynomial equation |
| `POST /api/v1/binomials/expand` | Expand a supported binomial |
| `POST /api/v1/graph/evaluate` | Evaluate a function at one x-coordinate |
| `POST /api/v1/graph/sample` | Generate bounded graph samples |

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"expression":"sin(pi / 2) + sqrt(25)"}'
```

Expected response:

```json
{"result": 6.0}
```

Invalid requests and calculation errors return HTTP 422 with an `error` object containing a stable `code` and human-readable `message`. Graph samples represent undefined y-values as JSON `null`. Equation roots are returned as objects with `real` and `imaginary` fields so complex roots remain valid JSON.

Browser origins are controlled by the `CALCULATOR_CORS_ORIGINS` environment variable. The default permits common local development origins only. Set it to the exact production website origin(s) before deployment; see [Deployment and source protection](docs/DEPLOYMENT.md) and the [frontend integration guide](docs/FRONTEND_INTEGRATION.md).

## Use the public engine API

New integrations should import from `engine.py`, rather than depending on CLI code or parser internals. All public operations raise `CalculatorError` (a `ValueError` subclass) for invalid inputs and unsupported calculations.

```python
from engine import (
    CalculatorError,
    approximate_expression,
    calculate_operation,
    convert_unit,
    evaluate_expression,
    expand_binomial,
    list_supported_units,
    evaluate_function,
    sample_function,
    solve_equation,
)

print(evaluate_expression("10 ÷ 2"))
print(evaluate_expression("sin(pi / 2) + √25"))
print(approximate_expression("sqrt(2)"))  # Decimal rounded to 15 significant digits
print(approximate_expression("1 / 3", significant_digits=6))
print(calculate_operation("multiply", [2, 3, 4]))
print(convert_unit(5, "km", "m"))  # 5000.0
print(list_supported_units()["length"])  # canonical unit identifiers
print(convert_unit(20, "C", "F"))  # 68.0
print(evaluate_function("x^2 - 4", 3))  # 5
print(sample_function("x^2", -1, 1, points=3))  # [(-1.0, 1), (0.0, 0), (1.0, 1)]
print(solve_equation("x^2 - 5x + 6 = 0"))
print(expand_binomial("(x + 2)^3"))

try:
    evaluate_expression("10 / 0")
except CalculatorError as error:
    print("Calculation error:", error)
```

### Public API

- `evaluate_expression(expression)` — evaluate an arithmetic/scientific expression. Integer-only arithmetic can preserve exact integer results; decimal and scientific-function calculations may use floating-point arithmetic.
- `approximate_expression(expression, significant_digits=15)` — return a `Decimal` rounded to 1–100 significant digits (default 15). This rounds the parser's result; it does **not** increase the internal precision used by the existing floating-point expression parser.
- `calculate_operation(operation, numbers)` — run `add`, `subtract`, `multiply`, or `divide`.
- `list_supported_units()` — return a stable catalog of canonical unit identifiers grouped by measurement dimension. Use these identifiers as the `from_unit` and `to_unit` values when building dynamic conversion controls.
- `convert_unit(value, from_unit, to_unit)` — convert between supported compatible units. Examples include `km`/`m`, `kg`/`lb`, `C`/`F`/`K`, `km/h`/`m/s`, `min`/`s`, `bar`/`Pa`, `kWh`/`J`, `hp`/`W`, `lbf`/`N`, decimal/binary storage units, `GHz`/`MHz`, electrical units such as `kV`/`V` and `mA`/`A`, and cooking measures such as cups, teaspoons, tablespoons, US fluid ounces, and separate Imperial volume units, plus bigha and biswa. The land-area conversions use a fixed pucca-bigha convention of 27,000 square feet per bigha and 20 biswa per bigha. Unknown units and cross-dimension conversions raise `CalculatorError`.
- `evaluate_function(expression, x_value)` — evaluate a supported expression at one x-coordinate, for example `evaluate_function("x^2", 3)`.
- `sample_function(expression, x_min, x_max, points=101)` — generate evenly spaced `(x, y)` samples for graphing. Undefined values are returned as `(x, None)` so a future plotting interface can leave a gap. Sampling is limited to 2,000 points.
- `solve_equation(equation)` — solve supported polynomial equations in `x`.
- `expand_binomial(expression)` — expand supported binomial expressions.
- `CalculatorError` — consistent exception type for interface code to catch.

## Project documentation

- [Frontend integration guide](docs/FRONTEND_INTEGRATION.md)
- [Deployment and source protection](docs/DEPLOYMENT.md)

## Tests

```bash
python -m pip install pytest
python -m pytest
```

## Author

Shubhankar
