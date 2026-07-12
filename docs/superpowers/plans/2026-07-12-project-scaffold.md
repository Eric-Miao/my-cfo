# Project Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the initial separated backend/frontend scaffold for the personal finance dashboard.

**Architecture:** Backend is a FastAPI REST API with Swagger/OpenAPI at `/docs` and `/openapi.json`. Frontend is a lightweight Vue 3 + Vite + TypeScript app that consumes the backend API. Deployment is represented by Docker Compose with env-driven configuration.

**Tech Stack:** Python 3.12, uv, FastAPI, Uvicorn, pytest, Ruff, Vue 3, Vite, TypeScript, ECharts, Docker Compose.

## Global Constraints

- Always use `uv` for Python project and virtual environment management.
- Keep `main`/`master` as release branch, `dev` as integration branch, and implement on feature branches.
- Use `main.py` or `app.py` as application entry points.
- Deployment must include a Docker Compose file.
- Passwords and secrets must come from environment variables only.
- Keep requirements and design documents under `specs/`.

---

### Task 1: Backend API Skeleton

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_health.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `backend.app.main.app: FastAPI`
- Produces: `GET /health -> {"status": "ok", "service": "...", "environment": "..."}`
- Produces: Swagger/OpenAPI via FastAPI at `/docs` and `/openapi.json`

- [ ] Write backend tests for `/health` and OpenAPI availability.
- [ ] Run `uv run pytest backend/tests` and confirm tests fail because FastAPI app is missing.
- [ ] Add minimal FastAPI app and env-backed settings.
- [ ] Add runtime and dev dependencies through `uv`.
- [ ] Run `uv run pytest backend/tests` and confirm tests pass.

### Task 2: Frontend Skeleton

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/views/DashboardView.vue`
- Create: `frontend/src/styles.css`
- Create: `frontend/src/vite-env.d.ts`

**Interfaces:**
- Consumes: `VITE_API_BASE_URL`
- Consumes: backend `GET /health`
- Produces: Vite development server and static production build

- [ ] Add Vue/Vite/TypeScript scaffold.
- [ ] Add API client using `VITE_API_BASE_URL`.
- [ ] Add simple dashboard cards and an ECharts placeholder chart.
- [ ] Run frontend install/build if dependency installation is available.

### Task 3: Deployment, Specs, and Documentation

**Files:**
- Create: `compose.yaml`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `.env.example`
- Create: `specs/README.md`
- Create: `specs/product-requirements.md`
- Create: `specs/data-model.md`
- Create: `specs/dashboard-design.md`
- Create: `specs/api-contract.md`
- Create: `specs/security-privacy.md`
- Create: `specs/data-import.md`
- Create: `specs/testing-strategy.md`
- Create: `specs/deployment.md`
- Modify: `.gitignore`
- Modify: `README.md`
- Delete: `hello.py`

**Interfaces:**
- Produces: Docker Compose services `backend` and `frontend`
- Produces: documented spec backlog for the user to fill in next

- [ ] Add Dockerfiles and Compose service definitions.
- [ ] Add env example with placeholders only.
- [ ] Add spec templates in writing order.
- [ ] Update README quickstart.
- [ ] Remove obsolete `hello.py`.

### Task 4: Verification and Commit

**Files:**
- All scaffold files above.

- [ ] Run `uv run pytest backend/tests`.
- [ ] Run `uv run ruff check backend`.
- [ ] Run `docker compose config` when Docker Compose is available.
- [ ] Run frontend build if dependencies are installed.
- [ ] Inspect `git diff --stat`.
- [ ] Commit with `chore(scaffold): add application structure`.
