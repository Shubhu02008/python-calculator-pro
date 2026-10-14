# Python Calculator Pro

A small command-line calculator written in Python. It supports basic arithmetic operations and validated arithmetic expressions.

## Features

- Addition, subtraction, multiplication, and division
- Operations on multiple numbers
- Expression evaluation with `+`, `-`, `*`, and `/`
- Decimal and negative numbers
- Parentheses and standard operator precedence
- Clear errors for unsupported or malformed expressions and division by zero

## Requirements

- Python 3.10 or newer (the automated workflow currently tests Python 3.12)
- `pytest` to run the test suite

## How to Run

1. Clone or download this repository.
2. Open a terminal in the project directory.
3. Run:

   ```bash
   python main.py
   ```

On systems where Python 3 is invoked as `python3`, use `python3 main.py`.

Follow the menu prompts to select an operation and enter numbers separated by spaces. Choose **Evaluate an expression** to enter an expression such as:

```text
(2 + 3) * 4
```

Choose **0** to exit.

## Run the Tests

Install pytest if needed:

```bash
python -m pip install pytest
python -m pytest
```

## Use from Python

The calculation functions can also be imported:

```python
from calculator import calculate

print(calculate("add", [5, 3]))
print(calculate("(2 + 3) * 4"))
```

## Author

Shubhankar
