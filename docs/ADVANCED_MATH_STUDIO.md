# Advanced Math Studio — Build Plan

## Goal

Evolve Python Calculator Pro into an original, connected mathematics workspace inspired by the *capabilities* of interactive mathematics platforms. Do not copy GeoGebra's source code, branding, or exact interface.

## Current branch milestone: Studio foundation

- Add a standalone Advanced Math Studio entry point at `frontend/studio.html`.
- Plot multiple explicit functions through the existing safe Python graph-sampling API.
- Show coordinate axes, labelled grid lines, finite-sample counts, sampled function values, and basic numeric extrema estimates.
- Add an editable spreadsheet for numeric datasets, choose X/Y columns, visualize the selected data, and export graph samples/data to CSV.
- Link the new workspace from the main homepage.
- Keep this first slice separate from the existing calculator while its API and user experience are validated.

## Roadmap

### Phase 1 — Reliable 2D graphing
- Verify API errors, loading states, undefined/discontinuous regions, range validation, and mobile layout.
- Add pan/zoom, fit-to-view, coordinate inspection, trace, and per-function visibility.
- Add table-of-values controls and more robust handling for steep functions and asymptotes.
- Test with polynomials, trigonometric functions, exponentials, logarithms, reciprocal functions, and implicit relations.

### Phase 2 — Spreadsheet and data analysis
- Improve cell navigation, ranges, formulas, fill/copy, and undo.
- Add charts (scatter, line, bar), regression models, and descriptive statistics.
- Connect plotted points to spreadsheet rows and show source data on hover.
- Add import/export for CSV and local save/restore with explicit user controls.

### Phase 3 — Math engine integration
- Link algebraic expressions and graph objects.
- Add numeric roots, intersections, local extrema, and derivative-based analysis with transparent numerical limitations.
- Expand exact arithmetic and symbolic calculus only where supported by tested backend operations.

### Phase 4 — Geometry and 3D
- Introduce a separate geometry canvas for points, lines, circles, transformations, and constraints.
- Add a dedicated 3D renderer for surfaces and parametric objects.
- Keep these modules isolated so performance and accessibility remain manageable.

### Phase 5 — Reliability and product quality
- Add automated browser tests, API regression tests, accessibility checks, and performance budgets.
- Test on touch devices and low-performance phones.
- Add offline/installability only after the online calculation experience is dependable.

## Architecture rules

- Use the existing Python API for expression evaluation; never evaluate user expressions with JavaScript `eval` or `Function`.
- Bound sample counts, input sizes, request timeouts, and spreadsheet dimensions.
- Treat missing/undefined values as graph gaps rather than connecting them across discontinuities.
- Keep existing calculator workflows intact while the new workspace is validated.
- Do not claim a feature is complete until tests and deployed behavior are checked.

## Known limitations of the first slice

- The spreadsheet is a numeric data grid, not yet a full formula spreadsheet.
- The graph analysis is based on sampled values, not exact symbolic results.
- The initial plot is a static view; interactive pan/zoom and trace are follow-up work.
- Spreadsheet data is not yet saved persistently.
- This is a foundation, not a complete GeoGebra replacement.
