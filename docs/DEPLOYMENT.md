# Deployment and source protection

This document is a deployment checklist, not a deployment to a specific hosting provider. The API is designed to run on a Python server separately from the browser-delivered frontend.

## Keep the backend server-side

Deploy `api.py`, `engine.py`, and the supporting Python modules to a Python-capable server. The website sends requests to the API and receives calculation results. Do not bundle private Python modules into frontend assets or provide file-reading endpoints.

The terminal calculator remains a separate interface and continues to call the same `engine.py` public API.

## Important: repository visibility

The GitHub repository `Shubhu02008/python-calculator-pro` is currently **public**. Running the backend on a server prevents the website from automatically downloading the backend source, but it does **not** hide code that is already available in a public GitHub repository.

If the backend source must be private before launch, choose one of these approaches deliberately:

- Change this repository to private, after considering the impact on public access and collaboration; or
- Keep a public project/demo repository and move the deployable backend into a separate private repository.

No repository visibility setting is changed by this project work. Do not assume that server-side deployment alone makes publicly hosted source code secret.

## Install and start

Use Python 3.11 or newer. Install the runtime dependencies:

```bash
python -m pip install -r requirements-api.txt
```

A typical production process command is:

```bash
uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
```

Use the start-command and port configuration recommended by the chosen hosting provider. The provider should run the process from the directory containing `api.py`. Keep the source repository and deployment credentials restricted to authorized maintainers if source privacy is required.

For local development, `uvicorn api:app --reload` is convenient. Do not use auto-reload for production.

## Required production configuration

### CORS

Set `CALCULATOR_CORS_ORIGINS` to the exact origin(s) of the production frontend, separated by commas if there is more than one. An origin includes the scheme and host, and a non-default port if present; it does not include a path.

Example:

```text
CALCULATOR_CORS_ORIGINS=https://calculator.example.com
```

The default list is for local development. Configure production origins explicitly. Avoid `*` unless intentionally allowing every website to make browser requests. CORS does not keep the API secret and does not replace other safeguards.

### HTTPS and traffic controls

- Terminate HTTPS at the hosting platform or reverse proxy.
- Configure request-rate limits at the platform, gateway, CDN, or reverse proxy. The calculator is designed to be publicly usable and does not include per-user authentication by default.
- Configure a request-body size limit and reasonable request timeouts at the hosting edge.
- Keep the server and dependencies updated.
- Use the `/healthz` endpoint for a basic process health check.
- Monitor server errors and resource use; do not log secrets or unnecessarily record complete user expressions.
- Do not expose arbitrary file access, Python `eval`/`exec`, shell commands, or internal implementation details through additional endpoints.

The API validates request fields and bounds expression lengths, operation list sizes, and graph sample counts. Edge-level limits are still important because they protect the application before request parsing and application logic run.

## API documentation

The service publishes interactive documentation at `/docs` and an OpenAPI schema at `/openapi.json`. These describe the HTTP contract but do not contain Python source code or secrets. If a deployment has a policy against public interactive docs, configure that policy in the deployment/application configuration before launch.

## Pre-launch checklist

- [ ] Decide whether the backend repository will be private or split from the public repository.
- [ ] Configure the production frontend origin in `CALCULATOR_CORS_ORIGINS`.
- [ ] Confirm HTTPS is enabled.
- [ ] Configure rate limits, body-size limits, and timeouts at the hosting edge.
- [ ] Install runtime dependencies from `requirements-api.txt`.
- [ ] Run the test suite using `requirements-dev.txt`.
- [ ] Confirm `/healthz`, `/docs`, and representative calculation endpoints behave as expected.
- [ ] Confirm no private credentials are stored in the repository or frontend assets.
- [ ] Verify that deployment logs and error responses do not reveal source paths, environment values, or stack traces.
