# Testing Strategy

## Document Control

- Product: My CFO
- Scope: V1 backend, frontend, API, data, import, security, and dashboard verification.
- Purpose: define the minimum test gates required before implementation is considered complete.
- Requirement IDs: use `TEST-x.y` for stable cross-references.

## TEST-1 Principles

Supports: `PRD-1.1`, `API-1`, `API-7`, `SEC-10`.

### TEST-1.1 Test Through Public Boundaries

Backend acceptance tests must use REST APIs and generated OpenAPI behavior. Unit tests may target services directly, but API behavior is the acceptance boundary.

### TEST-1.2 Traceability

Each implemented feature must reference at least one PRD/API/spec requirement ID in its tests or test module name/comment.

### TEST-1.3 Deterministic Data

Tests must use deterministic SQLite fixtures, deterministic timestamps, and deterministic FX rates. Network calls, including FX APIs, must be mocked.

## TEST-2 Required Local Commands

Use `uv` for all Python test commands.

```bash
uv run pytest
uv run ruff check .
npm run build
docker compose config
```

When frontend unit/component tests are added:

```bash
npm run test
```

## TEST-3 Backend Unit Tests

Supports: `PRD-3.x`, `PRD-5.x`, `PRD-8.4`.

Unit tests should cover pure domain behavior:

- decimal parsing and non-negative amount validation
- asset/liability net worth calculations
- snapshot item generation from active templates
- template field copying into snapshot items
- owner snapshot replacement and supersession
- group revision finalization rules
- frozen FX conversion
- soft delete and recovery rules

Unit tests must not depend on external network, production env files, or shared local databases.

## TEST-4 REST API Tests

Supports: `API-1` through `API-12`.

API tests must use an HTTP test client against the FastAPI app.

Required coverage:

- `/health`
- `/docs` and `/openapi.json` availability
- auth login/logout/me
- protected route rejection when unauthenticated
- owner/category/tag/template CRUD and recover/deactivate flows
- owner snapshot create/update/confirm/cancel/replacement flows
- household group create/finalize/reopen/cancel-draft flows
- FX quote and frozen FX set retrieval
- dashboard endpoints
- CSV export/import preview/commit

Invalid state transitions must return the standard error shape and the expected 4xx status.

## TEST-5 OpenAPI Verification

Supports: `API-1`, `API-7`.

OpenAPI tests must verify:

- every implemented `/api/v1` route appears in `/openapi.json`
- auth requirements are represented for protected routes
- request and response schemas expose decimal values as strings
- documented error responses use the standard error shape
- Swagger UI loads in development

## TEST-6 Data Model and Persistence Tests

Supports: `PRD-3.x`, `PRD-4.x`, `PRD-5.x`, `PRD-8.3`, `PRD-8.4`.

Persistence tests must use isolated temporary SQLite databases.

Required coverage:

- active owner set is frozen into finalized group revisions
- confirmed owner snapshots are immutable
- replacement snapshots link `replaces_snapshot_id` and `superseded_by_snapshot_id`
- group revisions reference owner snapshots and do not own editable amounts
- finalized group revisions freeze FX rate sets
- template edits do not mutate existing snapshot items
- tag rename does not mutate `tag_name_snapshot`
- soft-deleted records remain queryable for history but hidden from default active lists

## TEST-7 Security Tests

Supports: `SEC-1` through `SEC-10`.

Required coverage:

- wrong password fails login
- correct password creates HttpOnly session cookie
- logout clears the session cookie
- protected `/api/v1/*` endpoints reject unauthenticated requests
- `/health` remains available for health checks
- production startup rejects missing or placeholder `ADMIN_PASSWORD_HASH`
- production startup rejects missing or placeholder `SESSION_SECRET`
- secrets and session cookies are not logged by request handlers
- financial data is not stored in browser local/session storage by frontend code

## TEST-8 CSV Import/Export Tests

Supports: `PRD-6.x`, `IMP-1` through `IMP-9`, `SEC-8`.

Required coverage:

- export column order exactly matches `IMP-2.2`
- export includes active templates only
- export escapes or prefixes formula-triggering user text
- preview rejects missing, extra, reordered, or duplicate columns
- preview rejects changed template metadata
- preview rejects unknown or inactive owners, templates, system categories, and tags
- preview rejects invalid currencies
- preview rejects negative, malformed, and over-precision amounts
- preview returns row-level errors
- commit creates one draft owner snapshot per owner represented in the file
- commit is atomic and creates no partial records on failure
- commit rejects duplicate owner draft snapshots for the same `reporting_at`

## TEST-9 Dashboard Calculation Tests

Supports: `PRD-7.x`, `DASH-1` through `DASH-8`, `API-6.7`, `API-7.7`.

Required coverage:

- dashboard excludes draft, cancelled, superseded, and ungrouped snapshots
- official totals use finalized group revision FX rates
- display currency conversions are marked as estimates
- owner dashboards derive points from finalized group membership
- currency exposure groups by original currency
- tag drilldown uses tag ID continuity and historical tag display names
- negative net worth is valid
- mixed owner snapshot timestamps are exposed in latest group detail
- net worth delta is not labeled as cash flow

## TEST-10 Frontend Tests

Supports: `DUI-1` through `DUI-11`.

Minimum gates:

- `npm run build` must pass
- TypeScript type checks must pass
- dashboard API client types must match OpenAPI-derived or manually maintained schemas
- i18n toggle switches labels between English and Simplified Chinese
- user-provided owner/account/tag/institution text is not translated
- theme toggle applies light and dark tokens
- estimate badges appear when display currency differs from official base currency
- charts show accessible textual summaries or equivalent table data
- dashboard tables remain usable at mobile widths

## TEST-11 End-to-End Smoke Flow

A V1 smoke test should cover the core happy path:

1. login as admin
2. create owner
3. create system category and tag
4. create template
5. create draft owner snapshot
6. fill amount `0` and non-zero amount cases
7. confirm owner snapshot
8. create household group
9. finalize with manual FX rate
10. verify household dashboard official totals
11. logout

This smoke flow may run as API-only first. Browser automation can be added after the UI is implemented.

## TEST-12 Traceability Matrix

| Requirement Area | Test Coverage |
|---|---|
| `PRD-1.x` | smoke flow and auth setup |
| `PRD-2.x` | owner snapshot and household group workflow tests |
| `PRD-3.x` | data model, snapshot state, replacement, timestamp tests |
| `PRD-4.x` | category/tag/template validation tests |
| `PRD-5.x` | decimal, currency, FX, estimate tests |
| `PRD-6.x` | CSV import/export tests |
| `PRD-7.x` | dashboard calculation and frontend display tests |
| `PRD-8.x` | auth, secret, SQLite, soft-delete tests |
| `API-1` through `API-12` | REST API and OpenAPI tests |
| `SEC-1` through `SEC-10` | security tests |
| `IMP-1` through `IMP-9` | CSV tests |
| `DASH-1` through `DASH-8` | dashboard calculation tests |
| `DUI-1` through `DUI-11` | frontend UI tests |
