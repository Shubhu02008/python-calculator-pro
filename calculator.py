from parser import tokenize, evaluate_tokens


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        return "Cannot divide by zero"
    return a / b


def calculate(operation, numbers=None):
    if numbers is None:
        tokens = tokenize(operation)
        return evaluate_tokens(tokens)

    if operation == "add":
        return sum(numbers)

    if operation == "subtract":
        result = numbers[0]
        for number in numbers[1:]:
            result = subtract(result, number)
        return result

    if operation == "multiply":
        result = 1
        for number in numbers:
            result = multiply(result, number)
        return result

    if operation == "divide":
        result = numbers[0]
        for number in numbers[1:]:
            result = divide(result, number)
            if result == "Cannot divide by zero":
                return result
        return result

    return "Invalid operation"
