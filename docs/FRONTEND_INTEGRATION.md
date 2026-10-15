# Frontend integration guide

This guide describes the versioned HTTP contract provided by `api.py`. The API is an adapter around the shared Python calculation engine; frontend code should call the HTTP endpoints rather than importing Python modules.

## Local development

1. Use Python 3.11 or newer.
2. Install the optional API dependencies with `python -m pip install -r requirements-api.txt`.
3. Start the service with `uvicorn api:app --reload`.
4. Open `http://127.0.0.1:8000/docs` to explore the OpenAPI schema and try requests.

For the complete automated test suite, install `requirements-dev.txt` and run `python -m pytest`.

## Base URL and versioning

The version-one endpoints use the `/api/v1` prefix. A frontend should keep the API base URL in its own configuration, not scatter hostnames through components. Future incompatible contract changes should use a new API version rather than silently changing existing response shapes.

## Discover capabilities

Call `GET /api/v1/capabilities` to discover supported operations, features, and unit dimensions. Each unit dimension includes canonical unit identifiers. Use these identifiers as the `from_unit` and `to_unit` values in conversion requests. The catalog is generated from the same registry used by the conversion engine, reducing duplicated frontend data.

Example response shape:

```json
{
  "api_version": "v1",
  "operations": ["add", "subtract", "multiply", "divide"],
  "features": ["expression_evaluation", "unit_conversion"],
  "unit_dimensions": [
    {"id": "length", "units": ["cm", "ft", "in", "km", "m", "mi", "mm", "yd"]}
  ]
}
```

The example above is abbreviated; the actual response includes every supported feature and dimension.

## Endpoint examples

### Evaluate an expression

`POST /api/v1/calculate`

Request:

```json
{"expression": "sin(pi / 2) + sqrt(25)"}
```

Response:

```json
{"result": 6.0}
```

### Run a basic operation

`POST /api/v1/operations`

```json
{"operation": "multiply", "numbers": [2, 3, 4]}
```

Response: `{"result": 24}`.

### Convert units

`POST /api/v1/units/convert`

```json
{"value": 5, "from_unit": "km", "to_unit": "m"}
```

Response:

```json
{"value": 5000.0, "from_unit": "km", "to_unit": "m"}
```

### Solve an equation

`POST /api/v1/equations/solve`

```json
{"equation": "x^2 + 1 = 0"}
```

The response uses `status`, `solutions`, and optional `message`. Each root has `real` and `imaginary` numeric fields. This avoids sending Python complex numbers, which are not a native JSON type. Infinite-solution and no-solution cases return an empty `solutions` list and a descriptive message.

### Expand a binomial

`POST /api/v1/binomials/expand`

```json
{"expression": "(x + 2)^3"}
```

Response: `{"expansion": "x^3 + 6x^2 + 12x + 8"}`.

### Evaluate or sample a graph function

`POST /api/v1/graph/evaluate` accepts `{"expression":"x^2","x_value":3}` and returns an `x`/`y` point.

`POST /api/v1/graph/sample` accepts `{"expression":"1/x","x_min":-1,"x_max":1,"points":3}` and returns a `points` array. Undefined y-values are `null`, so a chart can break a curve at discontinuities. The sample count is bounded by the backend.

## Consuming the API from JavaScript

Use the configured API base URL and handle non-success responses explicitly:

```javascript
async function calculateExpression(apiBaseUrl, expression) {
  const response = await fetch(`${apiBaseUrl}/api/v1/calculate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ expression }),
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload?.error?.message ?? "Calculation failed.");
  }
  return payload.result;
}
```

This is an integration example, not a frontend implementation. Do not put private credentials in browser JavaScript. Anything shipped to the browser can be inspected.

## Error contract

Validation failures and expected calculation errors use HTTP 422.

```json
{
  "error": {
    "code": "calculation_error",
    "message": "Cannot divide by zero."
  }
}
```

Schema-validation errors use `code: "invalid_request"` and include a `details` list with field paths and validation messages. The server does not echo submitted values in that list. Frontends should display a useful message to the user and avoid relying on the exact wording of every validation message; the error code is the stable discriminator.

## Browser origins

For local development, common Vite and React development origins are permitted by default. For production, configure `CALCULATOR_CORS_ORIGINS` to a comma-separated list of exact website origins, for example:

```text
CALCULATOR_CORS_ORIGINS=https://calculator.example.com
```

CORS is a browser policy, not authentication or rate limiting. See the deployment guide for production safeguards.
