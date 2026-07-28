def tokenize(expression):
    tokens = []
    number = ""

    for char in expression:
        if char.isdigit() or char == ".":
            number += char

        else:
            if number:
                tokens.append(float(number) if "." in number else int(number))
                number = ""

            if char.strip():
                tokens.append(char)

    if number:
        tokens.append(float(number) if "." in number else int(number))

    return tokens