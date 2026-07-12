# My CFO

Personal finance management and dashboard application.

## Architecture

The project uses a separated backend/frontend architecture:

- `backend/` contains the FastAPI REST API.
- `frontend/` contains the Vue 3 + Vite dashboard.
- `specs/` contains product, data, API, security, testing, and deployment specs.
- `compose.yaml` defines the local deployment topology.

The backend exposes Swagger/OpenAPI at `http://localhost:8000/docs`.

## Development

Use `uv` for all Python dependency and environment management.

```bash
uv sync
uv run uvicorn backend.app.main:app --reload
```

Run backend tests:

```bash
uv run pytest backend/tests
```

Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Run with Docker Compose:

```bash
cp .env.example .env
docker compose up --build
```
