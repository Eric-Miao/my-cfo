# Repository Guidelines

## Project Structure & Architecture

Use a separated frontend/backend architecture. Keep backend code under `backend/`, frontend code under `frontend/`, automated tests under `tests/`, and requirements or design documents under `specs/`. Mirror source modules in the test tree where practical.

The application entry point must be named `main.py` or `app.py`; do not introduce alternative entry-point names. Backend functionality must be exposed through REST APIs with an up-to-date Swagger/OpenAPI interface. The frontend must consume those APIs rather than importing backend implementation code.

## Build, Test, and Development Commands

Use `uv` exclusively for Python project, dependency, and virtual environment management.

- `uv sync` creates or updates the local environment from `pyproject.toml`.
- `uv run python main.py` runs the application; substitute `app.py` when applicable.
- `uv add <package>` adds a runtime dependency.
- `uv add --dev pytest ruff` adds standard development tools.
- `uv run pytest` runs the test suite.
- `uv run ruff check .` and `uv run ruff format .` lint and format Python code.

Do not use `pip`, `python -m venv`, Poetry, or Conda.

## Deployment & Configuration

Any deployment workflow must provide a Docker Compose file, preferably `compose.yaml`, defining the required services, networks, volumes, health checks, and environment-variable inputs. Keep development and production differences explicit through Compose overrides or environment files.

Never commit passwords, tokens, private keys, connection strings, or other secrets. Read them from environment variables. Commit only safe examples such as `.env.example` with placeholder values; keep `.env` files ignored.

## Coding & Testing Conventions

Follow PEP 8 with four-space indentation. Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants. Add type hints to public functions and keep modules focused.

Use `pytest`; name files `test_*.py` and tests `test_<behavior>()`. Cover normal behavior, boundaries, and expected failures. Bug fixes require regression tests. Backend acceptance must include REST API tests and verification through the generated Swagger/OpenAPI specification. Isolate network and filesystem effects with fixtures or mocks.

## Branching, Commits & Pull Requests

Treat `main` or `master` as the release branch and `dev` as the latest integration branch. Never develop directly on either branch. Create a dedicated branch for every change, using names such as `feature/cash-flow`, `fix/missing-currency`, or `docs/api-guide`.

Use Conventional Commits, for example `feat(cfo): add cash-flow forecast`. Keep commits focused and summaries imperative. Squash commits when merging, then delete the merged branch.

Merge feature branches into `dev`. Changes may reach `main` or `master` only through a pull request, and release pull requests require manual approval from the repository owner; automated or agent approval is not sufficient. PRs must explain the change, link relevant issues or specs, and list verification commands. Include screenshots for user-visible changes and note configuration or dependency updates.

## Project Management

Track work in GitHub Projects. Use a Kanban board for workflow state, milestones or iterations for sprints, and GitHub Issues for actionable work. Every feature, fix, and documentation change should have an issue with acceptance criteria and should be linked to its branch and pull request. Keep status, assignee, priority, and target sprint current so the project board remains the source of truth.
