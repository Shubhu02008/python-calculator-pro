def calculate(operation, numbers):
    if operation == "add":
        return sum(numbers)

    elif operation == "subtract":
        result = numbers[0]
        for number in numbers[1:]:
            result -= number
        return result

    elif operation == "multiply":
        result = 1
        for number in numbers:
            result *= number
        return result

    elif operation == "divide":
        result = numbers[0]
        for number in numbers[1:]:
            if number == 0:
                return "Cannot divide by zero"
            result /= number
        return result

    else:
        return "Invalid operation"