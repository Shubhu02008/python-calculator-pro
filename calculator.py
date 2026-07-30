from parser import tokenize, evaluate_tokens


def calculate(expression):
    tokens = tokenize(expression)
    return evaluate_tokens(tokens)