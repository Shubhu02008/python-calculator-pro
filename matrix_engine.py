"""Safe symbolic and numerical matrix calculations for Python Calculator Pro."""
import ast
import operator
from sympy import (
    Matrix, Symbol, Integer, Rational, Float, sin, cos, tan, asin, acos, atan,
    sinh, cosh, tanh, sqrt, log, exp, pi, E, eye, zeros, simplify, sympify,
)
from sympy.matrices.exceptions import NonInvertibleMatrixError

MAX_DIMENSION = 8
MAX_CELLS = 64
_ALLOWED_FUNCTIONS = {
    "sin": sin, "cos": cos, "tan": tan, "asin": asin, "acos": acos, "atan": atan,
    "sinh": sinh, "cosh": cosh, "tanh": tanh, "sqrt": sqrt, "log": log,
    "ln": log, "exp": exp, "abs": abs,
}
_ALLOWED_CONSTANTS = {"pi": pi, "e": E}
_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow,
}
_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def parse_expression(value):
    """Parse a restricted arithmetic expression without eval/sympify on raw text."""
    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid matrix entries.")
    if isinstance(value, (int, float)):
        return Integer(value) if isinstance(value, int) else Float(value)
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise ValueError("Each matrix entry must be a number or expression up to 200 characters.")
    text = value.strip().replace("^", "**").replace("π", "pi").replace("×", "*")
    try:
        root = ast.parse(text, mode="eval").body
    except (SyntaxError, ValueError) as exc:
        raise ValueError(f"Invalid matrix expression: {value!r}.") from exc

    def visit(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return Integer(node.value) if isinstance(node.value, int) else Float(node.value)
        if isinstance(node, ast.Name):
            if node.id in _ALLOWED_CONSTANTS:
                return _ALLOWED_CONSTANTS[node.id]
            if node.id.isidentifier() and len(node.id) <= 30:
                return Symbol(node.id)
            raise ValueError("Invalid variable name.")
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and right.is_number and abs(float(right)) > 100:
                raise ValueError("Exponents above 100 are not supported.")
            return _BINOPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
            return _UNARYOPS[type(node.op)](visit(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _ALLOWED_FUNCTIONS:
            if node.keywords or not 1 <= len(node.args) <= 2:
                raise ValueError("Function calls accept one or two positional arguments.")
            return _ALLOWED_FUNCTIONS[node.func.id](*(visit(arg) for arg in node.args))
        raise ValueError("Unsupported syntax in matrix entry. Use numbers, variables, arithmetic, and supported math functions.")

    try:
        result = simplify(visit(root))
    except (ArithmeticError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Could not parse this matrix expression.") from exc
    if len(str(result)) > 1000:
        raise ValueError("The resulting expression is too large.")
    return result


def _matrix(raw, label="matrix"):
    if not isinstance(raw, list) or not raw or not all(isinstance(row, list) and row for row in raw):
        raise ValueError(f"{label.capitalize()} must be a non-empty list of rows.")
    rows, cols = len(raw), len(raw[0])
    if rows > MAX_DIMENSION or cols > MAX_DIMENSION or rows * cols > MAX_CELLS:
        raise ValueError(f"{label.capitalize()} is limited to {MAX_DIMENSION} rows/columns and {MAX_CELLS} cells.")
    if any(len(row) != cols for row in raw):
        raise ValueError(f"Every row in {label} must have the same number of columns.")
    return Matrix([ [parse_expression(item) for item in row] for row in raw ])


def _format_matrix(matrix):
    return [[str(simplify(matrix[r, c])) for c in range(matrix.cols)] for r in range(matrix.rows)]


def _require_square(matrix, operation):
    if matrix.rows != matrix.cols:
        raise ValueError(f"{operation.capitalize()} requires a square matrix.")


def _minor_steps(matrix, steps, depth=0):
    if matrix.rows == 1:
        return matrix[0, 0]
    if matrix.rows == 2:
        result = simplify(matrix[0, 0] * matrix[1, 1] - matrix[0, 1] * matrix[1, 0])
        steps.append({"title": "Use the 2×2 determinant formula", "formula": "ad − bc", "substitution": f"({matrix[0,0]})({matrix[1,1]}) − ({matrix[0,1]})({matrix[1,0]})", "result": str(result)})
        return result
    if depth > 4:
        return simplify(matrix.det(method="domain-ge"))
    terms = []
    for col in range(matrix.cols):
        entry = matrix[0, col]
        if entry == 0:
            continue
        minor = matrix.minor_submatrix(0, col)
        minor_det = _minor_steps(minor, steps, depth + 1)
        signed = simplify((-1) ** col * entry * minor_det)
        terms.append(signed)
        steps.append({"title": f"Expand along row 1, column {col+1}", "entry": str(entry), "sign": "+" if col % 2 == 0 else "−", "minor": _format_matrix(minor), "minor_determinant": str(minor_det), "term": str(signed)})
    return simplify(sum(terms, Integer(0)))


def _row_reduction_steps(matrix):
    work = matrix.copy()
    steps = []
    pivot_row = 0
    for col in range(work.cols):
        pivot = next((r for r in range(pivot_row, work.rows) if simplify(work[r, col]) != 0), None)
        if pivot is None:
            continue
        if pivot != pivot_row:
            work.row_swap(pivot, pivot_row)
            steps.append({"title": "Swap rows", "operation": f"R{pivot_row+1} ↔ R{pivot+1}", "matrix": _format_matrix(work)})
        pivot_value = simplify(work[pivot_row, col])
        if pivot_value != 1:
            work.row_op(pivot_row, lambda v, _: simplify(v / pivot_value))
            steps.append({"title": "Normalize pivot", "operation": f"R{pivot_row+1} → R{pivot_row+1}/({pivot_value})", "matrix": _format_matrix(work)})
        for r in range(work.rows):
            if r != pivot_row and simplify(work[r, col]) != 0:
                factor = simplify(work[r, col])
                work.row_op(r, lambda v, j: simplify(v - factor * work[pivot_row, j]))
                steps.append({"title": "Eliminate column entry", "operation": f"R{r+1} → R{r+1} − ({factor})R{pivot_row+1}", "matrix": _format_matrix(work)})
        pivot_row += 1
        if pivot_row == work.rows:
            break
    return work, steps


def calculate_matrix(request):
    """Execute a named matrix operation and return JSON-friendly structured output."""
    if not isinstance(request, dict):
        raise ValueError("Request must be an object.")
    operation = request.get("operation")
    if operation not in {
        "add", "subtract", "multiply", "scalar_multiply", "transpose", "power",
        "trace", "identity", "zero", "equals", "determinant", "minor", "cofactor",
        "adjoint", "inverse", "rank", "rref", "solve", "cramer", "lu", "eigen",
        "characteristic_polynomial", "linear_independence"
    }:
        raise ValueError("Unsupported matrix operation.")
    steps_enabled = bool(request.get("steps", False))
    steps = []
    if operation in {"identity", "zero"}:
        size = request.get("size")
        if isinstance(size, bool) or not isinstance(size, int) or not 1 <= size <= MAX_DIMENSION:
            raise ValueError("size must be an integer from 1 to 8.")
        result = eye(size) if operation == "identity" else zeros(size)
        return {"operation": operation, "result": _format_matrix(result), "steps": steps}
    a = _matrix(request.get("matrix"), "matrix")
    if operation in {"add", "subtract", "multiply", "equals"}:
        b = _matrix(request.get("matrix_b"), "second matrix")
        if operation in {"add", "subtract", "equals"} and a.shape != b.shape:
            raise ValueError("Both matrices must have the same dimensions for this operation.")
        if operation == "multiply" and a.cols != b.rows:
            raise ValueError("Matrix A columns must equal matrix B rows for multiplication.")
        if operation == "equals":
            result = all(simplify(x-y) == 0 for x, y in zip(a, b))
            return {"operation": operation, "result": result, "steps": steps}
        result = a + b if operation == "add" else a - b if operation == "subtract" else a * b
        if steps_enabled:
            steps.append({"title": "Apply the matrix operation", "matrix_a": _format_matrix(a), "matrix_b": _format_matrix(b), "result": _format_matrix(result)})
        return {"operation": operation, "result": _format_matrix(result), "steps": steps}
    if operation == "scalar_multiply":
        scalar = parse_expression(request.get("scalar"))
        result = a.applyfunc(lambda value: simplify(scalar * value))
        if steps_enabled:
            steps.append({"title": "Multiply every entry by the scalar", "scalar": str(scalar), "result": _format_matrix(result)})
        return {"operation": operation, "result": _format_matrix(result), "steps": steps}
    if operation == "transpose":
        return {"operation": operation, "result": _format_matrix(a.T), "steps": steps}
    if operation == "power":
        _require_square(a, "Matrix power")
        power = request.get("power")
        if isinstance(power, bool) or not isinstance(power, int) or not -10 <= power <= 10:
            raise ValueError("power must be an integer from -10 to 10.")
        if power < 0 and simplify(a.det()) == 0:
            raise ValueError("A singular matrix cannot be raised to a negative power.")
        return {"operation": operation, "result": _format_matrix(a ** power), "steps": steps}
    if operation == "trace":
        _require_square(a, "Trace")
        return {"operation": operation, "result": str(simplify(a.trace())), "steps": steps}
    if operation == "determinant":
        _require_square(a, "Determinant")
        det = _minor_steps(a, steps) if steps_enabled else simplify(a.det())
        return {"operation": operation, "result": str(simplify(det)), "steps": steps}
    if operation in {"minor", "cofactor"}:
        _require_square(a, operation)
        row, col = request.get("row"), request.get("column")
        if any(isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= a.rows for v in (row, col)):
            raise ValueError("row and column must be valid 1-based matrix positions.")
        minor = simplify(a.minor(row-1, col-1))
        result = minor if operation == "minor" else simplify((-1) ** (row+col) * minor)
        if steps_enabled:
            steps.append({"title": "Calculate the minor", "submatrix": _format_matrix(a.minor_submatrix(row-1, col-1)), "minor": str(minor), "cofactor": str(simplify((-1) ** (row+col) * minor))})
        return {"operation": operation, "result": str(result), "steps": steps}
    if operation == "adjoint":
        _require_square(a, "Adjoint")
        cofactors = a.cofactor_matrix()
        result = cofactors.T
        if steps_enabled:
            steps.append({"title": "Construct the cofactor matrix", "result": _format_matrix(cofactors)})
            steps.append({"title": "Transpose the cofactor matrix", "result": _format_matrix(result)})
        return {"operation": operation, "result": _format_matrix(result), "steps": steps}
    if operation == "inverse":
        _require_square(a, "Inverse")
        det = simplify(a.det())
        if det == 0:
            raise ValueError("This matrix is singular, so it has no inverse.")
        method = request.get("method", "adjoint")
        if method not in {"adjoint", "gauss_jordan"}:
            raise ValueError("method must be 'adjoint' or 'gauss_jordan'.")
        if method == "adjoint":
            result = a.adjugate() / det
            if steps_enabled:
                steps.append({"title": "Calculate the determinant", "result": str(det)})
                steps.append({"title": "Calculate the adjoint", "result": _format_matrix(a.adjugate())})
                steps.append({"title": "Use A⁻¹ = adj(A)/det(A)", "formula": "A⁻¹ = adj(A) / det(A)", "result": _format_matrix(result)})
        else:
            augmented = a.row_join(eye(a.rows))
            reduced, row_steps = _row_reduction_steps(augmented)
            result = reduced[:, a.cols:]
            if steps_enabled:
                steps.extend(row_steps)
                steps.append({"title": "Read the inverse from the right-hand block", "result": _format_matrix(result)})
        return {"operation": operation, "method": method, "result": _format_matrix(result), "steps": steps}
    if operation in {"rank", "rref", "linear_independence"}:
        reduced, row_steps = _row_reduction_steps(a)
        rank = len([r for r in range(reduced.rows) if any(simplify(reduced[r,c]) != 0 for c in range(reduced.cols))])
        if operation == "rank":
            result = rank
        elif operation == "rref":
            result = _format_matrix(reduced)
        else:
            result = {"independent": rank == a.cols, "rank": rank, "columns": a.cols}
        return {"operation": operation, "result": result, "steps": row_steps if steps_enabled else []}
    if operation in {"solve", "cramer"}:
        b_raw = request.get("vector")
        if not isinstance(b_raw, list) or len(b_raw) != a.rows:
            raise ValueError("vector must contain one value for each row of matrix A.")
        b = Matrix([parse_expression(v) for v in b_raw])
        if operation == "cramer":
            _require_square(a, "Cramer's rule")
            if a.rows != b.rows:
                raise ValueError("Cramer's rule requires a square coefficient matrix.")
            det_a = simplify(a.det())
            if det_a == 0:
                raise ValueError("Cramer's rule requires a non-zero determinant.")
            result = [str(simplify(a.copy().subs({})[:, i].col_join(Matrix([])))) for i in []]
            values = []
            for col in range(a.cols):
                replaced = a.copy()
                replaced[:, col] = b
                values.append(str(simplify(replaced.det() / det_a)))
            result = values
            if steps_enabled:
                steps.append({"title": "Calculate the determinant of A", "determinant": str(det_a)})
                steps.append({"title": "Apply Cramer's rule", "values": values})
        else:
            try:
                solution, parameters = a.gauss_jordan_solve(b, freevar=True)
                result = [str(simplify(v)) for v in solution]
                if parameters.rows:
                    result = {"general_solution": result, "parameters": [str(v) for v in parameters]}
                if steps_enabled:
                    _, row_steps = _row_reduction_steps(a.row_join(b))
                    steps.extend(row_steps)
            except ValueError:
                result = {"status": "no_solution"}
        return {"operation": operation, "result": result, "steps": steps}
    if operation == "lu":
        _require_square(a, "LU decomposition")
        lower, upper, perm = a.LUdecomposition()
        return {"operation": operation, "result": {"L": _format_matrix(lower), "U": _format_matrix(upper), "permutation": perm}, "steps": steps}
    if operation in {"eigen", "characteristic_polynomial"}:
        _require_square(a, "Eigenvalue calculation")
        lam = Symbol("lambda")
        poly = a.charpoly(lam).as_expr()
        if operation == "characteristic_polynomial":
            return {"operation": operation, "result": str(simplify(poly)), "steps": steps}
        try:
            eigenvals = a.eigenvals()
            eigenvects = a.eigenvects()
            result = {
                "characteristic_polynomial": str(simplify(poly)),
                "eigenvalues": [{"value": str(value), "multiplicity": multiplicity} for value, multiplicity in eigenvals.items()],
                "eigenvectors": [{"value": str(value), "vectors": [_format_matrix(vector) for vector in vectors]} for value, _mult, vectors in eigenvects],
            }
        except (NotImplementedError, ArithmeticError, ValueError) as exc:
            raise ValueError("Could not compute exact eigenvalues for this matrix.") from exc
        return {"operation": operation, "result": result, "steps": steps}
    raise ValueError("Unsupported matrix operation.")


def interpret_matrix_instruction(instruction):
    """Map common natural-language matrix requests to safe supported operations."""
    if not isinstance(instruction, str) or not instruction.strip() or len(instruction) > 500:
        raise ValueError("instruction must be non-empty text up to 500 characters.")
    text = instruction.lower().replace("’", "'")
    if "eigen" in text:
        operation = "eigen"
    elif "characteristic polynomial" in text:
        operation = "characteristic_polynomial"
    elif "linear independence" in text or "linearly independent" in text:
        operation = "linear_independence"
    elif "cramer" in text:
        operation = "cramer"
    elif "rank" in text:
        operation = "rank"
    elif "rref" in text or "reduced row echelon" in text:
        operation = "rref"
    elif "lu decomposition" in text or "decompose" in text:
        operation = "lu"
    elif "transpose" in text:
        operation = "transpose"
    elif "trace" in text:
        operation = "trace"
    elif "adjoint" in text or "adjugate" in text:
        operation = "adjoint"
    elif "inverse" in text:
        operation = "inverse"
    elif "determinant" in text or "det(" in text:
        operation = "determinant"
    elif "solve" in text or "simultaneous equation" in text or "system of equation" in text:
        operation = "solve"
    elif "multiply" in text or "product" in text:
        operation = "multiply"
    elif "subtract" in text or "difference" in text:
        operation = "subtract"
    elif "add" in text or "sum" in text:
        operation = "add"
    else:
        raise ValueError("I could not identify a supported matrix operation. Try determinant, inverse, rank, transpose, multiplication, or solve.")
    method = "gauss_jordan" if "gauss" in text or "row reduction" in text else "adjoint"
    return {"operation": operation, "steps": ("step" in text or "explain" in text or "working" in text), "method": method}
