def evaluate_tokens(tokens):
    # First solve multiplication and division
    index = 0

    while index < len(tokens):
        if tokens[index] == "*" or tokens[index] == "/":
            left = tokens[index - 1]
            right = tokens[index + 1]

            if tokens[index] == "*":
                result = left * right
            else:
                if right == 0:
                    return "Cannot divide by zero"
                result = left / right

            tokens[index - 1:index + 2] = [result]
            index = 0

        else:
            index += 1

    # Then solve addition and subtraction
    index = 0

    while index < len(tokens):
        if tokens[index] == "+" or tokens[index] == "-":
            left = tokens[index - 1]
            right = tokens[index + 1]

            if tokens[index] == "+":
                result = left + right
            else:
                result = left - right

            tokens[index - 1:index + 2] = [result]
            index = 0

        else:
            index += 1

    return tokens[0]