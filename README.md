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

## Use the public engine API

New integrations should import from `engine.py`, rather than depending on CLI code or parser internals. All public operations raise `CalculatorError` (a `ValueError` subclass) for invalid inputs and unsupported calculations.

```python
from engine import (
    CalculatorError,
    approximate_expression,
    calculate_operation,
    evaluate_expression,
    expand_binomial,
    solve_equation,
)

print(evaluate_expression("10 ÷ 2"))
print(evaluate_expression("sin(pi / 2) + √25"))
print(approximate_expression("sqrt(2)"))  # Decimal rounded to 15 significant digits
print(approximate_expression("1 / 3", significant_digits=6))
print(calculate_operation("multiply", [2, 3, 4]))
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
- `solve_equation(equation)` — solve supported polynomial equations in `x`.
- `expand_binomial(expression)` — expand supported binomial expressions.
- `CalculatorError` — consistent exception type for interface code to catch.

## Tests

```bash
python -m pip install pytest
python -m pytest
```

## Author

Shubhankar
