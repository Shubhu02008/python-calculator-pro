"""HTTP API adapter for Python Calculator Pro.

Run locally with:
    python -m pip install -r requirements-api.txt
    uvicorn api:app --reload

The API delegates calculations to engine.py. It never evaluates Python code
from requests and does not expose the implementation modules as file endpoints.
"""

import math
import os
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, field_validator

from matrix_engine import calculate_matrix, interpret_matrix_instruction
from matrix_learning import generate_matrix_practice, check_matrix_answer

from engine import (
    CalculatorError,
    calculate_operation,
    convert_unit,
    evaluate_expression,
    fraction_form,
    evaluate_function,
    expand_binomial,
    list_supported_units,
    sample_function,
    solve_equation,
    calculate_bmi,
    calculate_compound_interest,
    calculate_date,
    calculate_discount,
    calculate_emi,
    calculate_gst,
    calculate_simple_interest,
    convert_currency,
    convert_number_base,
    calculate_calculus,
    calculate_statistics,
    calculate_probability,
)


Number = StrictInt | StrictFloat
_DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000,"
    "http://127.0.0.1:3000,"
    "http://localhost:5173,"
    "http://127.0.0.1:5173"
)


def _validate_finite_number(value, label):
    """Reject booleans, non-real values, and values outside the finite range."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite real number.")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{label} must be a finite real number.")
    return value


def _nonblank_text(value, label):
    if not value.strip():
        raise ValueError(f"{label} must not be blank.")
    return value


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExpressionRequest(RequestModel):
    expression: str = Field(min_length=1, max_length=10_000)

    @field_validator("expression")
    @classmethod
    def expression_must_not_be_blank(cls, value):
        return _nonblank_text(value, "Expression")


class OperationRequest(RequestModel):
    operation: Literal["add", "subtract", "multiply", "divide"]
    numbers: list[Number] = Field(min_length=1, max_length=1_000)

    @field_validator("numbers")
    @classmethod
    def numbers_must_be_finite(cls, values):
        return [_validate_finite_number(value, "Each number") for value in values]


class UnitConversionRequest(RequestModel):
    value: Number
    from_unit: str = Field(min_length=1, max_length=100)
    to_unit: str = Field(min_length=1, max_length=100)

    @field_validator("value")
    @classmethod
    def value_must_be_finite(cls, value):
        return _validate_finite_number(value, "Value")

    @field_validator("from_unit", "to_unit")
    @classmethod
    def units_must_not_be_blank(cls, value):
        return _nonblank_text(value, "Unit")


class EquationRequest(RequestModel):
    equation: str = Field(min_length=1, max_length=10_000)

    @field_validator("equation")
    @classmethod
    def equation_must_not_be_blank(cls, value):
        return _nonblank_text(value, "Equation")


class BinomialRequest(RequestModel):
    expression: str = Field(min_length=1, max_length=10_000)

    @field_validator("expression")
    @classmethod
    def expression_must_not_be_blank(cls, value):
        return _nonblank_text(value, "Expression")


class FunctionRequest(RequestModel):
    expression: str = Field(min_length=1, max_length=10_000)
    x_value: Number

    @field_validator("expression")
    @classmethod
    def expression_must_not_be_blank(cls, value):
        return _nonblank_text(value, "Expression")

    @field_validator("x_value")
    @classmethod
    def x_value_must_be_finite(cls, value):
        return _validate_finite_number(value, "x value")


class GraphSampleRequest(RequestModel):
    expression: str = Field(min_length=1, max_length=10_000)
    x_min: Number
    x_max: Number
    points: StrictInt = Field(default=101, ge=2, le=2_000)

    @field_validator("expression")
    @classmethod
    def expression_must_not_be_blank(cls, value):
        return _nonblank_text(value, "Expression")

    @field_validator("x_min", "x_max")
    @classmethod
    def bounds_must_be_finite(cls, value):
        return _validate_finite_number(value, "Graph bound")



class CurrencyConversionRequest(RequestModel):
    amount: Number
    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(min_length=3, max_length=3)

    @field_validator("amount")
    @classmethod
    def amount_must_be_finite(cls, value):
        return _validate_finite_number(value, "Amount")


class DiscountRequest(RequestModel):
    price: Number
    discount_percent: Number

    @field_validator("price", "discount_percent")
    @classmethod
    def values_must_be_finite(cls, value):
        return _validate_finite_number(value, "Value")


class GSTRequest(RequestModel):
    amount: Number
    gst_rate: Number
    inclusive: bool = False

    @field_validator("amount", "gst_rate")
    @classmethod
    def values_must_be_finite(cls, value):
        return _validate_finite_number(value, "Value")


class SimpleInterestRequest(RequestModel):
    principal: Number
    annual_rate: Number
    years: Number

    @field_validator("principal", "annual_rate", "years")
    @classmethod
    def values_must_be_finite(cls, value):
        return _validate_finite_number(value, "Value")


class CompoundInterestRequest(SimpleInterestRequest):
    compounding_per_year: StrictInt = Field(default=1, ge=1, le=365)


class EMIRequest(RequestModel):
    principal: Number
    annual_rate: Number
    tenure_months: StrictInt = Field(ge=1, le=1200)

    @field_validator("principal", "annual_rate")
    @classmethod
    def values_must_be_finite(cls, value):
        return _validate_finite_number(value, "Value")


class NumberBaseRequest(RequestModel):
    value: str = Field(min_length=1, max_length=10_000)
    from_base: StrictInt = Field(ge=2, le=36)
    to_base: StrictInt = Field(ge=2, le=36)


class BMIRequest(RequestModel):
    weight_kg: Number
    height_m: Number

    @field_validator("weight_kg", "height_m")
    @classmethod
    def values_must_be_finite(cls, value):
        return _validate_finite_number(value, "Value")


class DateCalculationRequest(RequestModel):
    operation: Literal["add_days", "subtract_days", "difference"]
    date: str = Field(min_length=1, max_length=10)
    days: StrictInt = 0
    other_date: str | None = Field(default=None, max_length=10)



class CalculusRequest(RequestModel):
    operation: Literal["derivative", "integral", "definite_integral", "limit"]
    expression: str = Field(min_length=1, max_length=1000)
    variable: Literal["x", "y", "z", "t"] = "x"
    order: StrictInt = Field(default=1, ge=1, le=10)
    lower: StrictInt | StrictFloat | str | None = None
    upper: StrictInt | StrictFloat | str | None = None
    point: StrictInt | StrictFloat | str = "0"
    direction: Literal["both", "plus", "minus"] = "both"

    @field_validator("expression")
    @classmethod
    def expression_must_not_be_blank(cls, value):
        return _nonblank_text(value, "Expression")


class StatisticsRequest(RequestModel):
    operation: Literal[
        "mean", "median", "mode", "range", "minimum", "maximum",
        "variance", "population_variance", "standard_deviation",
        "population_standard_deviation", "quartiles"
    ]
    values: list[Number] = Field(min_length=1, max_length=10000)

    @field_validator("values")
    @classmethod
    def values_must_be_finite(cls, values):
        return [_validate_finite_number(value, "Each data value") for value in values]


class ProbabilityRequest(RequestModel):
    operation: Literal["simple", "complement", "conditional", "union", "permutation", "combination", "binomial"]
    favorable: StrictInt | None = Field(default=None, ge=0)
    total: StrictInt | None = Field(default=None, ge=1)
    event_a: Number | None = None
    event_b: Number | None = None
    intersection: Number | None = None
    n: StrictInt | None = Field(default=None, ge=0, le=10000)
    r: StrictInt | None = Field(default=None, ge=0, le=10000)
    p: Number | None = None
    k: StrictInt | None = Field(default=None, ge=0, le=10000)

    @field_validator("event_a", "event_b", "intersection", "p")
    @classmethod
    def probabilities_must_be_finite(cls, value):
        if value is not None:
            return _validate_finite_number(value, "Probability")
        return value


class MatrixRequest(RequestModel):
    operation: Literal[
        "add", "subtract", "multiply", "scalar_multiply", "transpose", "power",
        "trace", "identity", "zero", "equals", "determinant", "minor", "cofactor",
        "adjoint", "inverse", "rank", "rref", "solve", "cramer", "lu", "eigen",
        "characteristic_polynomial", "linear_independence"
    ]
    matrix: list[list[str | int | float]] | None = Field(default=None, max_length=8)
    matrix_b: list[list[str | int | float]] | None = Field(default=None, max_length=8)
    vector: list[str | int | float] | None = Field(default=None, max_length=8)
    scalar: str | int | float | None = None
    size: StrictInt | None = Field(default=None, ge=1, le=8)
    power: StrictInt | None = Field(default=None, ge=-10, le=10)
    row: StrictInt | None = Field(default=None, ge=1, le=8)
    column: StrictInt | None = Field(default=None, ge=1, le=8)
    method: Literal["adjoint", "gauss_jordan"] | None = None
    steps: bool = False


class MatrixInstructionRequest(RequestModel):
    instruction: str = Field(min_length=1, max_length=500)

    @field_validator("instruction")
    @classmethod
    def instruction_must_not_be_blank(cls, value):
        return _nonblank_text(value, "Instruction")


class MatrixPracticeRequest(RequestModel):
    topic: Literal["determinant", "inverse", "rank", "matrix_multiplication"] = "determinant"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    count: StrictInt = Field(default=1, ge=1, le=10)
    seed: StrictInt | None = None


class MatrixAnswerRequest(RequestModel):
    expected: object
    submitted: object

class NumericResult(BaseModel):
    result: int | float
    exact_fraction: str | None = None
    approximation: str | None = None


class UnitConversionResult(BaseModel):
    value: float
    from_unit: str
    to_unit: str


class RootValue(BaseModel):
    real: float
    imaginary: float = 0.0


class EquationSolutionResult(BaseModel):
    status: Literal["solved", "no_solution", "infinite_solutions"]
    solutions: list[RootValue]
    message: str | None = None


class BinomialExpansionResult(BaseModel):
    expansion: str


class GraphPoint(BaseModel):
    x: float
    y: float | None


class GraphSamplesResult(BaseModel):
    points: list[GraphPoint]


class UnitDimension(BaseModel):
    id: str
    units: list[str]


class CapabilitiesResult(BaseModel):
    api_version: str
    operations: list[str]
    features: list[str]
    unit_dimensions: list[UnitDimension]


app = FastAPI(
    title="Python Calculator Pro API",
    description="Versioned HTTP interface for the Python Calculator Pro engine.",
    version="1.0.0",
    debug=False,
)

_cors_setting = os.getenv("CALCULATOR_CORS_ORIGINS", _DEFAULT_CORS_ORIGINS)
_cors_origins = [origin.strip() for origin in _cors_setting.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(CalculatorError)
async def calculator_error_handler(_request: Request, exc: CalculatorError):
    """Return a stable, safe error envelope for invalid calculations."""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "calculation_error",
                "message": str(exc),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    _request: Request, exc: RequestValidationError
):
    """Normalize schema-validation errors without echoing submitted values."""
    details = []
    for error in exc.errors():
        location = error.get("loc", ())
        if location and location[0] == "body":
            location = location[1:]
        details.append(
            {
                "field": ".".join(str(part) for part in location) or "request",
                "message": error.get("msg", "Invalid value."),
                "type": error.get("type", "validation_error"),
            }
        )
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "invalid_request",
                "message": "Request validation failed.",
                "details": details,
            }
        },
    )


@app.get("/")
def root():
    """Describe the service without exposing implementation details."""
    return {
        "name": "Python Calculator Pro API",
        "version": app.version,
        "docs": "/docs",
    }


@app.get("/healthz")
def health_check():
    """Lightweight process health check for hosting platforms."""
    return {"status": "ok"}


@app.get("/api/v1/capabilities", response_model=CapabilitiesResult)
def capabilities():
    """List available operations, features, and canonical unit identifiers."""
    units = list_supported_units()
    return {
        "api_version": "v1",
        "operations": ["add", "subtract", "multiply", "divide"],
        "features": [
            "expression_evaluation",
            "unit_conversion",
            "equation_solving",
            "binomial_expansion",
            "function_evaluation",
            "function_sampling",
            "currency_conversion",
            "discount_calculator",
            "gst_calculator",
            "simple_interest",
            "compound_interest",
            "loan_emi",
            "number_base_conversion",
            "bmi_calculator",
            "date_calculations",
            "matrix_operations",
            "symbolic_matrix_algebra",
            "matrix_step_by_step",
            "matrix_linear_algebra",
            "matrix_eigenvalues",
            "jee_matrix_practice",
            "matrix_instruction_interpreter",
            "symbolic_calculus",
            "descriptive_statistics",
            "elementary_probability",
        ],
        "unit_dimensions": [
            {"id": dimension, "units": list(unit_ids)}
            for dimension, unit_ids in units.items()
        ],
    }


@app.post("/api/v1/calculate", response_model=NumericResult)
def calculate(request: ExpressionRequest):
    """Evaluate an expression and include an exact fraction when applicable."""
    result = evaluate_expression(request.expression)
    fraction = fraction_form(request.expression)
    return {
        "result": result,
        "exact_fraction": fraction["exact_fraction"] if fraction else None,
        "approximation": fraction["approximation"] if fraction else None,
    }


@app.post("/api/v1/operations", response_model=NumericResult, response_model_exclude_none=True)
def operate(request: OperationRequest):
    """Run a named basic arithmetic operation."""
    return {
        "result": calculate_operation(request.operation, request.numbers)
    }


@app.post("/api/v1/units/convert", response_model=UnitConversionResult)
def convert(request: UnitConversionRequest):
    """Convert between compatible supported units."""
    return {
        "value": convert_unit(request.value, request.from_unit, request.to_unit),
        "from_unit": request.from_unit,
        "to_unit": request.to_unit,
    }


@app.post("/api/v1/equations/solve", response_model=EquationSolutionResult)
def solve(request: EquationRequest):
    """Solve a supported polynomial equation in x."""
    result = solve_equation(request.equation)
    if isinstance(result, str):
        status = (
            "infinite_solutions"
            if result == "Infinite solutions"
            else "no_solution"
        )
        return {"status": status, "solutions": [], "message": result}

    solutions = []
    for root in result:
        if isinstance(root, complex):
            solutions.append({"real": root.real, "imaginary": root.imag})
        else:
            solutions.append({"real": float(root), "imaginary": 0.0})
    return {"status": "solved", "solutions": solutions, "message": None}


@app.post("/api/v1/binomials/expand", response_model=BinomialExpansionResult)
def expand(request: BinomialRequest):
    """Expand a supported binomial expression."""
    return {"expansion": expand_binomial(request.expression)}


@app.post("/api/v1/graph/evaluate", response_model=GraphPoint)
def evaluate_graph_function(request: FunctionRequest):
    """Evaluate a supported function at one x-coordinate."""
    return {
        "x": float(request.x_value),
        "y": evaluate_function(request.expression, request.x_value),
    }


@app.post("/api/v1/graph/sample", response_model=GraphSamplesResult)
def sample_graph_function(request: GraphSampleRequest):
    """Return bounded coordinate samples; undefined y-values are null."""
    points = sample_function(
        request.expression,
        request.x_min,
        request.x_max,
        points=request.points,
    )
    return {
        "points": [{"x": x_value, "y": y_value} for x_value, y_value in points]
    }

@app.post("/api/v1/currency/convert")
def currency_convert(request: CurrencyConversionRequest):
    """Convert currencies using the latest available provider rates."""
    return convert_currency(request.amount, request.from_currency, request.to_currency)


@app.post("/api/v1/discount/calculate")
def discount_calculate(request: DiscountRequest):
    """Calculate a discount amount and the resulting price."""
    return calculate_discount(request.price, request.discount_percent)


@app.post("/api/v1/gst/calculate")
def gst_calculate(request: GSTRequest):
    """Calculate GST or extract the GST component from a tax-inclusive amount."""
    return calculate_gst(request.amount, request.gst_rate, inclusive=request.inclusive)


@app.post("/api/v1/finance/simple-interest")
def simple_interest(request: SimpleInterestRequest):
    """Calculate simple interest and maturity amount."""
    return calculate_simple_interest(request.principal, request.annual_rate, request.years)


@app.post("/api/v1/finance/compound-interest")
def compound_interest(request: CompoundInterestRequest):
    """Calculate compound interest and maturity amount."""
    return calculate_compound_interest(
        request.principal, request.annual_rate, request.years, request.compounding_per_year
    )


@app.post("/api/v1/finance/emi")
def loan_emi(request: EMIRequest):
    """Calculate a fixed monthly loan EMI and total repayment."""
    return calculate_emi(request.principal, request.annual_rate, request.tenure_months)


@app.post("/api/v1/numbers/convert-base")
def number_base_convert(request: NumberBaseRequest):
    """Convert an integer literal between bases 2 and 36."""
    return convert_number_base(request.value, request.from_base, request.to_base)


@app.post("/api/v1/health/bmi")
def bmi_calculate(request: BMIRequest):
    """Calculate BMI from kilograms and metres; category labels are adult ranges."""
    return calculate_bmi(request.weight_kg, request.height_m)


@app.post("/api/v1/dates/calculate")
def date_calculate(request: DateCalculationRequest):
    """Add/subtract days from an ISO date or calculate the signed day difference."""
    return calculate_date(
        request.operation, request.date, days=request.days, other_date=request.other_date
    )


@app.post("/api/v1/calculus")
def calculus(request: CalculusRequest):
    """Differentiate, integrate, or calculate a symbolic limit."""
    return calculate_calculus(
        request.operation,
        request.expression,
        variable=request.variable,
        order=request.order,
        lower=request.lower,
        upper=request.upper,
        point=request.point,
        direction=request.direction,
    )


@app.post("/api/v1/statistics")
def statistics(request: StatisticsRequest):
    """Calculate descriptive statistics for a list of observations."""
    return calculate_statistics(request.operation, request.values)


@app.post("/api/v1/probability")
def probability(request: ProbabilityRequest):
    """Calculate elementary event probabilities and counting quantities."""
    values = request.model_dump(exclude_none=True)
    operation = values.pop("operation")
    return calculate_probability(operation, **values)


@app.post("/api/v1/matrices/operations")
def matrix_operation(request: MatrixRequest):
    """Run a numeric or symbolic matrix operation, optionally with working."""
    try:
        return calculate_matrix(request.model_dump(exclude_none=True))
    except ValueError as exc:
        raise CalculatorError(str(exc)) from exc


@app.post("/api/v1/matrices/instructions")
def matrix_instruction(request: MatrixInstructionRequest):
    """Map common natural-language matrix instructions to a supported operation."""
    try:
        return interpret_matrix_instruction(request.instruction)
    except ValueError as exc:
        raise CalculatorError(str(exc)) from exc


@app.post("/api/v1/matrices/practice")
def matrix_practice(request: MatrixPracticeRequest):
    """Generate a small set of JEE-style matrix practice questions with answer keys."""
    return generate_matrix_practice(
        topic=request.topic,
        difficulty=request.difficulty,
        count=request.count,
        seed=request.seed,
    )


@app.post("/api/v1/matrices/check-answer")
def matrix_check_answer(request: MatrixAnswerRequest):
    """Check a submitted answer against an expected answer."""
    return {"correct": check_matrix_answer(request.expected, request.submitted)}
