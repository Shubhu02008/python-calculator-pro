def tokenize(expression):
    tokens = []

    number = ""

    for index, char in enumerate(expression):

        if char.isdigit() or char == ".":
            number += char

        elif char == "-" and (
            index == 0 or expression[index - 1] in "+-*/("
        ):
            number += char

        else:
            if number:
                tokens.append(float(number))
                number = ""

            if char != " ":
                tokens.append(char)

    if number:
        tokens.append(float(number))

    return tokens

def resolve_brackets(tokens):

    while "(" in tokens:

        start = None

        for index, token in enumerate(tokens):
            if token == "(":
                start = index

            elif token == ")":
                end = index
                break

        inside = tokens[start + 1:end]

        result = evaluate_tokens(inside)

        tokens[start:end + 1] = [result]

    return tokens


def evaluate_tokens(tokens):

    tokens = resolve_brackets(tokens)

    # Multiplication and division first
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


    # Addition and subtraction
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