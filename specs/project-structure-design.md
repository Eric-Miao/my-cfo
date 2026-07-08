# Project Structure Design

## Objective

Create a minimal, maintainable foundation for a personal financial dashboard. The initial scaffold establishes architectural boundaries and development tooling without implementing financial features.

## Technology Stack

- Backend: Python 3.12, FastAPI, Uvicorn, and pytest, managed exclusively with `uv`.
- Frontend: Vue 3, Vite, and TypeScript.
- Visualization: Apache ECharts with tree-shakable imports.
- Deployment: Docker Compose with separate frontend and backend services.
- API contract: FastAPI-generated OpenAPI and Swagger UI.

## Repository Layout

```text
backend/
  app/
    main.py
    api/
    core/
    models/
    schemas/
    services/
  tests/
frontend/
  src/
    api/
    components/
    views/
    charts/
  public/
specs/
compose.yaml
.env.example
```

The backend owns business rules, persistence, validation, and REST APIs. The frontend owns presentation and client-side state, and communicates with the backend only through documented HTTP endpoints. `backend/app/main.py` is the backend entry point; `frontend/src/main.ts` is the standard Vite bootstrap file.

## Initial Runtime Behavior

The backend scaffold exposes a health endpoint and generated API documentation. The frontend scaffold renders a placeholder dashboard shell and verifies API connectivity. No account, transaction, authentication, or financial calculation behavior is included in this phase.

Configuration is read from environment variables. `.env.example` documents safe placeholders; real `.env` files and secrets remain untracked. Compose passes configuration into each service and defines health checks.

## Verification

Backend verification includes pytest coverage for the health endpoint and validation that the OpenAPI document is available. Frontend verification includes type checking and a production build. Docker Compose configuration must parse successfully.

## Specification Backlog

Write specifications in this order:

1. `product-requirements.md`: users, goals, scope, metrics, and non-goals.
2. `data-model.md`: accounts, assets, liabilities, transactions, categories, and budgets.
3. `dashboard-design.md`: pages, metrics, charts, filters, and empty states.
4. `api-contract.md`: resources, endpoints, schemas, errors, and versioning.
5. `security-privacy.md`: authentication, authorization, secrets, retention, and sensitive data.
6. `data-import.md`: CSV formats, mapping, validation, deduplication, and rollback.
7. `testing-strategy.md`: test boundaries, fixtures, acceptance criteria, and coverage targets.
8. `deployment.md`: environments, Compose services, backups, restoration, and upgrades.

`architecture.md` should be derived from the accepted product, data, and API decisions rather than written independently before them.
