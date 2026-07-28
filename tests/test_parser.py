from parser import tokenize, evaluate_tokens


def test_tokenize():
    assert tokenize("5 + 10 * 3") == [5, "+", 10, "*", 3]


def test_basic_bodmas():
    assert evaluate_tokens(tokenize("5 + 10 * 3")) == 35