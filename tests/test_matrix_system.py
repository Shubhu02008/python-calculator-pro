from fastapi.testclient import TestClient
from api import app
from matrix_engine import calculate_matrix, interpret_matrix_instruction
from matrix_learning import generate_matrix_practice

client = TestClient(app)

def test_symbolic_determinant_with_steps():
    result = calculate_matrix({"operation":"determinant","matrix":[["x","2"],["3","sin(theta)"]],"steps":True})
    assert result["result"] == "x*sin(theta) - 6"
    assert result["steps"]

def test_numeric_determinant_and_inverse():
    assert calculate_matrix({"operation":"determinant","matrix":[[1,2],[3,4]]})["result"] == "-2"
    result = calculate_matrix({"operation":"inverse","matrix":[[1,2],[3,4]],"method":"adjoint"})
    assert result["result"] == [["-2","1"],["3/2","-1/2"]]

def test_transpose_rectangular_matrix():
    result = calculate_matrix({"operation":"transpose","matrix":[[1,2,3],[4,5,6]]})
    assert result["result"] == [["1","4"],["2","5"],["3","6"]]

def test_parser_rejects_unsupported_syntax():
    for expression in ["foo()", "1 << 2", "[1,2]"]:
        try:
            from matrix_engine import parse_expression
            parse_expression(expression)
        except ValueError:
            continue
        raise AssertionError("Unsupported expression was accepted")

def test_instruction_interpreter():
    result = interpret_matrix_instruction("Find the inverse using Gauss-Jordan and explain steps")
    assert result == {"operation":"inverse","steps":True,"method":"gauss_jordan"}

def test_practice_is_reproducible():
    a = generate_matrix_practice(topic="determinant", difficulty="easy", count=2, seed=42)
    b = generate_matrix_practice(topic="determinant", difficulty="easy", count=2, seed=42)
    assert a == b

def test_matrix_api():
    response = client.post("/api/v1/matrices/operations", json={"operation":"determinant","matrix":[[1,2],[3,4]],"steps":True})
    assert response.status_code == 200
    assert response.json()["result"] == "-2"

def test_instruction_api():
    response = client.post("/api/v1/matrices/instructions", json={"instruction":"Find determinant and explain steps"})
    assert response.status_code == 200
    assert response.json()["operation"] == "determinant"
    assert response.json()["steps"] is True

def test_practice_api():
    response = client.post("/api/v1/matrices/practice", json={"topic":"rank","difficulty":"easy","count":2,"seed":10})
    assert response.status_code == 200
    assert len(response.json()["questions"]) == 2



def test_matrix_check_answer_api():
    correct = client.post(
        "/api/v1/matrices/check-answer",
        json={"expected": [["1", "2"], ["3", "4"]], "submitted": [[1, 2], [3, 4]]},
    )
    incorrect = client.post(
        "/api/v1/matrices/check-answer",
        json={"expected": [["1", "2"], ["3", "4"]], "submitted": [[1, 2], [3, 5]]},
    )
    assert correct.status_code == 200
    assert correct.json() == {"correct": True}
    assert incorrect.status_code == 200
    assert incorrect.json() == {"correct": False}
