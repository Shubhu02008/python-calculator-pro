"""JEE-oriented matrix practice helpers."""
import random
from matrix_engine import calculate_matrix


def generate_matrix_practice(topic="determinant", difficulty="medium", count=1, seed=None):
    if topic not in {"determinant", "inverse", "rank", "matrix_multiplication"}:
        raise ValueError("topic must be determinant, inverse, rank, or matrix_multiplication.")
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be easy, medium, or hard.")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 10:
        raise ValueError("count must be an integer from 1 to 10.")
    rng = random.Random(seed)
    questions = []
    for index in range(count):
        size = 2 if difficulty == "easy" else 3
        matrix = [[rng.randint(-4, 5) for _ in range(size)] for _ in range(size)]
        if topic == "matrix_multiplication":
            second = [[rng.randint(-4, 5) for _ in range(size)] for _ in range(size)]
            answer = calculate_matrix({"operation": "multiply", "matrix": matrix, "matrix_b": second})["result"]
            questions.append({"id": index + 1, "topic": topic, "difficulty": difficulty, "matrix": matrix, "matrix_b": second, "prompt": "Calculate A × B.", "answer": answer})
        else:
            operation = topic
            if topic == "inverse":
                matrix = [[2, 1], [1, 1]] if size == 2 else [[2, 1, 0], [1, 2, 1], [0, 1, 2]]
            answer = calculate_matrix({"operation": operation, "matrix": matrix})["result"]
            prompts = {"determinant": "Find det(A).", "inverse": "Find A⁻¹.", "rank": "Find rank(A)."}
            questions.append({"id": index + 1, "topic": topic, "difficulty": difficulty, "matrix": matrix, "prompt": prompts[topic], "answer": answer})
    return {"topic": topic, "difficulty": difficulty, "questions": questions}


def check_matrix_answer(expected, submitted):
    """Compare submitted and expected symbolic/nested answers conservatively."""
    if isinstance(expected, list) and isinstance(submitted, list):
        return len(expected) == len(submitted) and all(check_matrix_answer(a, b) for a, b in zip(expected, submitted))
    if isinstance(expected, dict) and isinstance(submitted, dict):
        return expected.keys() == submitted.keys() and all(check_matrix_answer(expected[k], submitted[k]) for k in expected)
    if str(expected).strip().replace(" ", "") == str(submitted).strip().replace(" ", ""):
        return True
    try:
        from matrix_engine import parse_expression
        return parse_expression(str(expected)) == parse_expression(str(submitted))
    except (ValueError, TypeError):
        return False
