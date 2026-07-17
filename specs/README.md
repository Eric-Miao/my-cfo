# Specs

Write specs before implementation. Keep them short, decision-oriented, and linked to GitHub Issues and pull requests.

Recommended writing order:

1. `product-requirements.md`
2. `data-model.md`
3. `dashboard-design.md`
4. `api-contract.md`
5. `security-privacy.md`
6. `data-import.md`
7. `testing-strategy.md`
8. `deployment.md`

Create `architecture.md` after the product, data model, and API contract are stable.

## V1 Implementation Trace

Implementation follows `docs/superpowers/plans/2026-07-17-v1-implementation.md`.
Use requirement IDs from specs when adding API tests, implementation tickets, or
PR descriptions.

Current verification gates:

```bash
uv run pytest backend/tests
uv run ruff check backend
cd frontend && npm run build
docker compose --env-file deploy/.env.production.example -f deploy/compose.prod.yaml config
```
