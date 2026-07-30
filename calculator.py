from parser import tokenize, evaluate_tokens


def calculate(expression):

    expression = expression.replace("×", "*")
    expression = expression.replace("÷", "/")

    tokens = tokenize(expression)

    result = evaluate_tokens(tokens)

    return result


while True:

    expression = input("Enter expression: ")

    if expression == "exit":
        break

    print("Answer:", calculate(expression))