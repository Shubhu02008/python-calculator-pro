# Unified Math Studio: Architecture and Delivery Plan

## Product direction

Advanced Math Studio is the foundation for replacing the current Graphing Calculator, not a permanent separate calculator. The target is a connected mathematics workspace with capabilities comparable to the public GeoGebra Calculator Suite, implemented with original code, interface, and branding.

## Current baseline

- The main calculator uses a Python API and a custom SVG graph renderer.
- `graphing.py` safely samples explicit functions and implicit relations.
- `api.py` exposes graph sampling and has existing symbolic calculus, equation solving, matrix, statistics, and probability capabilities.
- `frontend/studio.html` currently contains an isolated function graph and a starter numeric spreadsheet.
- The Studio spreadsheet does not yet evaluate formulas or cell references, and its graph is not linked to a shared math document.

## Architecture principles

1. **One graphing experience:** consolidate the current Graphing Calculator and Studio graph workflow into one user-facing experience. Avoid maintaining two competing graph implementations.
2. **Shared math document:** expressions, variables, sliders, data ranges, geometry objects, and view settings should have stable IDs and explicit dependencies.
3. **Separate calculation from rendering:** Python API services validate/evaluate supported math; a dedicated frontend renderer owns interaction, coordinate transforms, overlays, and accessibility.
4. **Safe execution:** never use Python `eval`/ `exec` for user expressions. Validate all API inputs and bound sample counts, execution time, and data sizes.
5. **Exactness is explicit:** preserve exact symbolic results where supported; label numerical approximations and sampled estimates.
6. **Mobile-first interactions:** provide touch pan/zoom, usable controls, keyboard support, and a responsive layout.
7. **Regression-first delivery:** keep the existing calculator usable while the replacement is developed behind reviewed changes. Verify the deployed site after each release.

## Delivery milestones

### M1 — Interactive graphing foundation
- Multiple explicit functions in one coordinate plane.
- Pan and zoom, range controls, reset view, and responsive/touch input.
- Keep undefined regions discontinuous rather than joining across them.
- Clear loading, API error, and empty-result states.
- Function-value table and CSV export.
- Browser tests for graph controls and API error handling.

### M2 — Graph analysis and expression objects

**Implemented in the current working branch:** an x-coordinate trace readout with interpolated values for each plotted curve, plus sample-based candidate detection for roots, local extrema, and pairwise intersections. Results are explicitly approximate and limited to the current sampled viewport. These tools do not yet provide symbolic proofs or guarantee detection of tangential roots.
- Trace/cursor readout and function value at a chosen x.
- Numerical root, intersection, and extrema candidates with clear approximation labels.
- Sliders and parameter dependencies.
- Parametric and polar functions; improve implicit relation rendering.
- Shared graph state between the existing calculator route and Studio.

### M3 — Sliders and linked expressions

**Initial parameter-slider slice implemented:** expressions can reference named parameters such as `a` and `b`; parameter sliders substitute their current numeric values before the existing graph API is called and automatically replot after changes. The current UI supports up to eight uniquely named parameters, with values ranging from -10 to 10 in 0.1 steps. Parameters are local to the Studio session and are not yet saved or shared with spreadsheet cells. The browser smoke test now checks that slider changes send updated expressions to the API.

### M3 — Symbolic mathematics integration
- Reuse and test existing SymPy-backed API operations.
- Add simplification/factorization and calculus operations where absent.
- Connect symbolic results to graphable expressions.
- Distinguish unsupported operations from valid results with no real values.

### M4 — Spreadsheet engine
- Cell/range model, formulas, cell references, dependency graph, recalculation.
- Import/export CSV, numeric summaries, regression, and charts.
- Spreadsheet charts and generated functions share the same document state.
- Guard against cyclic references and excessive recalculation.

### M5 — Dynamic geometry
- Points, lines, segments, circles, polygons, intersections, measurements, transformations.
- Dependency-aware constructions and constraint handling.
- Accessible selection and touch manipulation.

### M6 — 3D and advanced tools
- 3D surfaces and parametric objects, spatial geometry, and advanced probability tools.
- Performance budgets, low-performance mode, and device/browser compatibility checks.

## First implementation slice

The current branch adds pointer-drag panning and wheel/trackpad zoom to the Studio graph. It updates the visible ranges and resamples through the existing graph API after interaction. This is an initial interaction milestone only, not completion of M1 or the full replacement.

## Acceptance checks before merging

- Static checks and existing Python tests pass.
- Browser test covers graph render, pan, zoom, reset, and API failure state.
- Verify no unbounded requests occur while dragging or zooming.
- Check mobile viewport and pointer/touch behavior.
- Deploy preview and inspect the actual rendered page before merging to `main`.
