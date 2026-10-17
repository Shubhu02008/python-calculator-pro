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
