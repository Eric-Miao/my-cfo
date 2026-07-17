# My CFO

Personal and household balance-sheet dashboard for snapshot-based net-worth
tracking.

## Architecture

The project uses a separated backend/frontend architecture:

- `backend/` contains the FastAPI REST API.
- `frontend/` contains the Vue 3 + Vite dashboard.
- `specs/` contains product, data, API, security, testing, and deployment specs.
- `deploy/compose.prod.yaml` defines the home-lab deployment topology.

The backend exposes Swagger/OpenAPI at `http://localhost:8000/docs`.

## Development

Use `uv` for all Python dependency and environment management.

```bash
uv sync
uv run uvicorn backend.app.main:app --reload
```

Run backend checks:

```bash
uv run pytest backend/tests
uv run ruff check backend
```

Run or build the frontend:

```bash
cd frontend
npm ci
npm run dev
npm run build
```

Validate production Compose configuration:

```bash
docker compose --env-file deploy/.env.production.example -f deploy/compose.prod.yaml config
```

Production secrets stay outside git. Copy `deploy/.env.production.example` to the
Mac mini environment path and replace placeholders there.

## V1 Workflow

The core API smoke path is covered by `backend/tests/test_v1_smoke_api.py`:
login, create master data, create and confirm an owner snapshot, finalize a
household group with manual FX, verify dashboard totals, and logout.
