# Python Calculator Pro

A Python calculator engine for arithmetic, scientific functions, polynomial equations, and binomial expansions. The current interface is command-line based; a mobile button interface is a separate next step.

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

## Run

```bash
python main.py
```

Choose **5** to evaluate an expression, for example `sin(pi/2) + √25`.

Choose **6** to solve a linear, quadratic, or cubic equation, for example:

```text
x^3 - 6x^2 + 11x - 6 = 0
```

Choose **7** to expand a binomial, for example `(x + 2)^3`.

## Tests

```bash
python -m pip install pytest
python -m pytest
```

## Use from Python

```python
from calculator import calculate

print(calculate("10 ÷ 2"))
print(calculate("sin(pi / 2) + √25"))
print(calculate("2^10 + 5!"))
```

## Author

Shubhankar
