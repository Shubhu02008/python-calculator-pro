# Frontend

The frontend is a static HTML/CSS/JavaScript application. It uses the existing FastAPI backend; calculation logic is not reimplemented in the browser.

## Run locally

1. Start the API from the repository root:

   ```bash
   python -m pip install -r requirements-api.txt
   uvicorn api:app --reload
   ```

2. In another terminal, serve the frontend directory from the repository root:

   ```bash
   python -m http.server 5173 --directory frontend
   ```

3. Open [http://127.0.0.1:5173](http://127.0.0.1:5173).

The frontend defaults to `http://127.0.0.1:8000` for the API. Do not open `index.html` directly as a `file://` URL; serve it over HTTP so browser origin and CORS behavior are consistent.

## Configure the API URL

Before deploying to a different API host, set `window.CALCULATOR_API_BASE_URL` before `app.js` executes, or change the `API_BASE_URL` default at the top of `app.js`. The value is the API origin only (for example, `https://api.example.com`), without the `/api/v1` suffix. Configure the backend's `CALCULATOR_CORS_ORIGINS` to include the exact frontend origin.

## Phase 3 scope

- Scientific expression evaluation through `POST /api/v1/calculate`.
- API connection indicator using `GET /healthz`.
- Keyboard Enter to calculate; Escape clears the expression.
- On-screen keypad insertion, delete, clear, and calculate controls.
- DEG/RAD mode; DEG inputs convert the arguments of `sin`, `cos`, and `tan` to radians before submitting to the existing API.
- Inline calculation/API errors; expression is preserved for correction.
- Expandable exact-fraction/approximation details only when returned by the API.
- Browser-local history (up to 20 recent calculations), timestamps, copy result, reuse expression, and confirmation before clearing.

History is stored in this browser using localStorage. It is not synced across devices or sent to the backend.

## Current limits

Only the Scientific Calculator is functional in this phase. Other sidebar entries remain placeholders until their planned phases. The API does not provide general calculation steps, so the interface does not invent them.