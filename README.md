# Python Calculator Pro

A command-line calculator written in Python for arithmetic expressions and basic linear and quadratic equations.

## Features

- Addition, subtraction, multiplication, and division
- Division with either `/` or `÷`
- Decimal and negative numbers, parentheses, and standard arithmetic precedence
- Linear equation solving, such as `2x + 4 = 10`
- Quadratic equation solving, such as `x^2 - 5x + 6 = 0`
- Implicit multiplication, such as `5x` and `x(x - 3)`
- Real and complex roots, repeated roots, no-solution cases, and identities
- Clear errors for unsupported or malformed expressions

Equation solving supports polynomials of degree 1 or 2 in the variable `x). Powers 0, 1, and 2 are supported; higher-degree equations and division by expressions containing `x` are not supported.

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
Choose **6** to solve a linear or quadratic equation, for example:

```text
x^2 - 5x + 6 = 0
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

print(calculate("10 ÷ 2"))
print(solve_equation("x^2 - 5x + 6 = 0"))
```

## Author

Shubhankar
