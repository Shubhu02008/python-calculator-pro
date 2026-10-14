# Python Calculator Pro

A command-line calculator written in Python for arithmetic expressions, polynomial equations, and binomial expansions.

## Features

- Addition, subtraction, multiplication, and division
- Division with either `/` or `÷`
- Decimal and negative numbers, parentheses, and standard arithmetic precedence
- Linear, quadratic, and cubic equation solving in `x`
- Implicit multiplication, such as `5x` and `x(x - 3)`
- Real and complex roots, repeated roots, no-solution cases, and identities
- Binomial theorem expansion for expressions such as `(x + 2)^3` and `(a - b)^4`
- Clear errors for unsupported or malformed expressions

Equation solving supports polynomial equations up to degree 3. Powers 0 through 3 are supported; higher-degree equations and division by expressions containing `x` are not supported.

The binomial expansion tool accepts simple numeric or single-letter terms (such as `2x`, `x`, `3`, `a`, or `-b`) and non-negative integer exponents up to 100.

## Requirements

- Python 3.10 or newer (the automated workflow currently tests Python 3.12)
- `pytest` to run the test suite

## How to Run

Open a terminal in the project directory and run:

```bash
python main.py
```

Use `python3 main.py` if your system uses `python3` as the command.

Choose **5** to evaluate an arithmetic expression, for example `10 ÷ 2`.

Choose **6** to solve a linear, quadratic, or cubic equation, for example:

```text
x^3 - 6x^2 + 11x - 6 = 0
```

Choose **7** to expand a binomial, for example:

```text
(x + 2)^3
```

The expansion is:

```text
x^3 + 6x^2 + 12x + 8
```

Choose **0** to exit.

## Run the Tests

```bash
python -m pip install pytest
python -m pytest
```

## Use from Python

```python
from calculator import calculate
from equation_solver import solve_equation
from binomial_theorem import expand_binomial

print(calculate("10 ÷ 2"))
print(solve_equation("x^3 - 6x^2 + 11x - 6 = 0"))
print(expand_binomial("(x + 2)^3"))
```

## Author

Shubhankar
