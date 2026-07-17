# My CFO V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the V1 personal/family balance-sheet snapshot dashboard from the accepted specs.

**Architecture:** The backend is a FastAPI REST API with SQLite persistence, explicit service boundaries, and OpenAPI-backed tests. The frontend is a Vue 3 + Vite + TypeScript dashboard that consumes only REST APIs. Deployment uses Docker Compose, GHCR images, GitHub Actions, and Mac mini home-lab staging/production flows.

**Tech Stack:** Python 3.12, uv, FastAPI, SQLModel/SQLAlchemy, Alembic, pytest, Ruff, SQLite, Vue 3, Vite, TypeScript, ECharts, Docker Compose, GitHub Actions, GHCR, Caddy.

## Global Constraints

- Always use `uv` for Python project and virtual environment management.
- Use separated frontend/backend architecture.
- Backend entry point remains `backend/app/main.py`.
- Backend functionality must be exposed through REST APIs with Swagger/OpenAPI.
- SQLite is the V1 source of truth.
- Secrets must come from environment variables and must not be committed.
- Confirmed owner snapshots are immutable and corrected through replacement snapshots.
- Official dashboard values come only from finalized household group revisions.
- FX default provider is Frankfurter public API, which requires no API key; manual fallback is required.
- Tests must use deterministic fake FX providers and must not call real FX APIs.
- The provided balance-sheet sample is used as a structure reference for sanitized fixtures; do not commit raw pasted personal data without explicit approval.
- Production deployment target is Mac mini home lab with `stg` and `prd`.

---

## File Structure

Create or expand the following backend modules:

```text
backend/app/
  api/
    deps.py
    errors.py
    router.py
    routes/
      auth.py
      owners.py
      categories.py
      tags.py
      templates.py
      owner_snapshots.py
      snapshot_groups.py
      fx_rates.py
      dashboard.py
      csv_import.py
  core/
    config.py
    security.py
  db/
    base.py
    session.py
    migrations/
  domain/
    money.py
    snapshots.py
    dashboard.py
    csv_import.py
  models/
    owner.py
    category.py
    tag.py
    template.py
    snapshot.py
    group.py
    fx.py
  schemas/
    common.py
    auth.py
    owner.py
    category.py
    tag.py
    template.py
    snapshot.py
    group.py
    fx.py
    dashboard.py
    csv_import.py
  services/
    auth.py
    owners.py
    categories.py
    tags.py
    templates.py
    snapshots.py
    groups.py
    fx.py
    dashboard.py
    csv_import.py
  scripts/
    seed_staging.py
```

Create or expand the following tests:

```text
backend/tests/
  conftest.py
  fixtures/
    sample_balance_sheet.json
  test_health.py
  test_auth_api.py
  test_master_data_api.py
  test_templates_api.py
  test_owner_snapshots_api.py
  test_snapshot_groups_api.py
  test_fx_service.py
  test_dashboard_api.py
  test_csv_import_api.py
  test_openapi.py
```

Create or expand the following frontend modules:

```text
frontend/src/
  api/
    client.ts
    types.ts
  i18n/
    index.ts
    en-US.ts
    zh-CN.ts
  theme/
    theme.ts
  components/
    AppShell.vue
    MetricCard.vue
    ChartCard.vue
    FilterBar.vue
    LatestGroupTable.vue
  views/
    DashboardView.vue
    OwnerDashboardView.vue
    LoginView.vue
```

Create deployment artifacts:

```text
deploy/
  compose.prod.yaml
  Caddyfile
  .env.production.example
  README.md
  scripts/
    backup_sqlite.sh
    deploy_release_bundle.sh
    rollback_release_bundle.sh
.github/workflows/
  ci.yml
  deploy-staging.yml
  deploy-production.yml
```

---

### Task 1: Backend Dependencies and Configuration

**Files:**
- Modify: `pyproject.toml`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/main.py`
- Create: `backend/app/api/router.py`
- Create: `backend/app/api/errors.py`
- Test: `backend/tests/test_health.py`
- Test: `backend/tests/test_openapi.py`

**Interfaces:**
- Produces: `Settings` with database, auth, CORS, docs, FX, and deployment fields.
- Produces: standard API error response.
- Produces: `/health`, `/docs`, `/openapi.json`, and `/api/v1/meta`.

- [ ] **Step 1: Add backend dependencies**

Run:

```bash
uv add sqlmodel sqlalchemy alembic itsdangerous argon2-cffi python-multipart
uv add --dev freezegun
```

Expected: `pyproject.toml` and `uv.lock` update successfully.

- [ ] **Step 2: Add settings tests**

Create tests that verify:

```python
def test_production_rejects_placeholder_session_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SESSION_SECRET", "change-me")
    with pytest.raises(ValueError):
        Settings()
```

Run:

```bash
uv run pytest backend/tests/test_openapi.py backend/tests/test_health.py
```

Expected: new settings tests fail until config validation exists.

- [ ] **Step 3: Implement config and router skeleton**

Implement `Settings` fields:

```text
APP_NAME
APP_ENV
DATABASE_URL
ADMIN_PASSWORD_HASH
SESSION_SECRET
CORS_ORIGINS
ALLOW_PUBLIC_DOCS
DEPLOYMENT_NETWORK
COOKIE_SECURE
FX_PROVIDER
FRANKFURTER_BASE_URL
```

Keep `/health` public and mount `/api/v1` from `backend.app.api.router`.

- [ ] **Step 4: Verify**

Run:

```bash
uv run pytest backend/tests/test_health.py backend/tests/test_openapi.py
uv run ruff check backend
```

Expected: all tests pass and Ruff reports no errors.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock backend/app backend/tests
git commit -m "feat(backend): add configuration and API skeleton"
```

---

### Task 2: SQLite Models, Sessions, and Migrations

**Files:**
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/models/*.py`
- Create: `backend/app/schemas/*.py`
- Create: `backend/tests/conftest.py`
- Test: `backend/tests/test_master_data_api.py`
- Test: `backend/tests/test_owner_snapshots_api.py`

**Interfaces:**
- Produces: database session dependency `get_session()`.
- Produces: SQLModel models matching `specs/data-model.md`.
- Produces: isolated temporary SQLite fixture for tests.

- [ ] **Step 1: Write model persistence tests**

Test these behaviors:

```text
owner active/inactive persists
system_category item_type compatibility persists
template tag join persists
snapshot item copied fields persist
```

Run:

```bash
uv run pytest backend/tests/test_master_data_api.py -v
```

Expected: fail because models/session do not exist.

- [ ] **Step 2: Implement models**

Implement models for:

```text
Owner
SystemCategory
Tag
BalanceSheetItemTemplate
BalanceSheetItemTemplateTag
OwnerSnapshot
SnapshotItem
SnapshotItemTag
SnapshotGroup
SnapshotGroupRevision
SnapshotGroupMember
FxRateSet
FxRate
```

Use decimal strings for money/rates. Do not use floats.

- [ ] **Step 3: Implement test DB fixture**

Use temporary SQLite per test:

```python
@pytest.fixture()
def client(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    ...
```

- [ ] **Step 4: Verify**

Run:

```bash
uv run pytest backend/tests/test_master_data_api.py backend/tests/test_owner_snapshots_api.py
uv run ruff check backend
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db backend/app/models backend/app/schemas backend/tests
git commit -m "feat(data): add SQLite domain models"
```

---

### Task 3: Single-Admin Authentication

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/routes/auth.py`
- Create: `backend/app/services/auth.py`
- Test: `backend/tests/test_auth_api.py`

**Interfaces:**
- Produces: `POST /api/v1/auth/login`
- Produces: `POST /api/v1/auth/logout`
- Produces: `GET /api/v1/auth/me`
- Produces: `require_admin` FastAPI dependency.

- [ ] **Step 1: Write auth API tests**

Tests:

```text
wrong password returns 401
correct password sets HttpOnly cookie
GET /api/v1/auth/me requires session
protected /api/v1/owners rejects no session
logout clears cookie
```

Run:

```bash
uv run pytest backend/tests/test_auth_api.py -v
```

Expected: fail because auth routes do not exist.

- [ ] **Step 2: Implement password verification**

Use Argon2id via `argon2-cffi`.

Inputs:

```text
ADMIN_PASSWORD_HASH
SESSION_SECRET
COOKIE_SECURE
DEPLOYMENT_NETWORK
```

Cookie:

```text
HttpOnly
SameSite=Lax
Path=/
Secure=true only for public/HTTPS mode
```

- [ ] **Step 3: Protect `/api/v1` routers**

Apply dependency-based auth to protected routers. Keep login public.

- [ ] **Step 4: Verify**

Run:

```bash
uv run pytest backend/tests/test_auth_api.py
uv run pytest backend/tests/test_openapi.py
uv run ruff check backend
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app backend/tests/test_auth_api.py
git commit -m "feat(auth): add single-admin session login"
```

---

### Task 4: Master Data APIs

**Files:**
- Create: `backend/app/api/routes/owners.py`
- Create: `backend/app/api/routes/categories.py`
- Create: `backend/app/api/routes/tags.py`
- Create: `backend/app/api/routes/templates.py`
- Create: `backend/app/services/owners.py`
- Create: `backend/app/services/categories.py`
- Create: `backend/app/services/tags.py`
- Create: `backend/app/services/templates.py`
- Test: `backend/tests/test_master_data_api.py`
- Test: `backend/tests/test_templates_api.py`

**Interfaces:**
- Produces owner/category/tag/template CRUD and recover/deactivate endpoints from `API-6.3`.
- Produces `GET /api/v1/institution-suggestions`.

- [ ] **Step 1: Write master data API tests**

Cover:

```text
create owner
deactivate/recover owner
create asset system category
reject category/template item_type mismatch
create tag with normalized_name uniqueness
create template with tag ids
template update does not affect historical snapshot items
institution suggestions derive from existing template text
```

- [ ] **Step 2: Run failing tests**

```bash
uv run pytest backend/tests/test_master_data_api.py backend/tests/test_templates_api.py -v
```

Expected: fail for missing endpoints.

- [ ] **Step 3: Implement services and routes**

Implement standard list/create/patch endpoints using authenticated dependencies.

- [ ] **Step 4: Verify**

```bash
uv run pytest backend/tests/test_master_data_api.py backend/tests/test_templates_api.py
uv run ruff check backend
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app backend/tests/test_master_data_api.py backend/tests/test_templates_api.py
git commit -m "feat(api): add master data endpoints"
```

---

### Task 5: Owner Snapshot Workflow

**Files:**
- Create: `backend/app/domain/money.py`
- Create: `backend/app/domain/snapshots.py`
- Create: `backend/app/api/routes/owner_snapshots.py`
- Create: `backend/app/services/snapshots.py`
- Test: `backend/tests/test_owner_snapshots_api.py`

**Interfaces:**
- Produces draft snapshot generation from active templates.
- Produces item update, confirm, cancel, and replacement flow.

- [ ] **Step 1: Write snapshot workflow tests**

Cover:

```text
draft generated from active templates only
snapshot item copies template/category/tag fields
confirm rejects null amount
confirm accepts 0
negative amount rejected
confirmed snapshot item update returns 409
replacement draft copies confirmed snapshot
confirm replacement supersedes original
```

- [ ] **Step 2: Run failing tests**

```bash
uv run pytest backend/tests/test_owner_snapshots_api.py -v
```

Expected: fail.

- [ ] **Step 3: Implement money validation**

Implement:

```python
def parse_decimal_string(value: str) -> Decimal
def validate_non_negative_amount(value: str) -> str
```

Return normalized decimal strings with up to 8 places.

- [ ] **Step 4: Implement snapshot service**

Use service functions:

```python
create_draft_snapshot(owner_id, reporting_at, label, source)
update_draft_item(snapshot_id, item_id, amount_original, currency, note)
confirm_snapshot(snapshot_id)
create_replacement_snapshot(snapshot_id)
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest backend/tests/test_owner_snapshots_api.py
uv run ruff check backend
git add backend/app backend/tests/test_owner_snapshots_api.py
git commit -m "feat(snapshots): add owner snapshot workflow"
```

---

### Task 6: FX Provider and Household Groups

**Files:**
- Create: `backend/app/services/fx.py`
- Create: `backend/app/api/routes/fx_rates.py`
- Create: `backend/app/api/routes/snapshot_groups.py`
- Create: `backend/app/services/groups.py`
- Test: `backend/tests/test_fx_service.py`
- Test: `backend/tests/test_snapshot_groups_api.py`

**Interfaces:**
- Produces `FxRateProvider` interface.
- Produces Frankfurter provider using `https://api.frankfurter.dev/v2`.
- Produces manual fallback.
- Produces group create/finalize/reopen/cancel-draft.

- [ ] **Step 1: Write fake FX provider tests**

Use fake provider:

```python
class FakeFxProvider:
    def quote(self, base_currency, currencies, rate_timestamp):
        return {"USD": Decimal("7.25000000")}
```

Cover:

```text
quote returns Decimal rates
manual fallback freezes supplied rate
finalize requires every active owner
selected owner snapshot must be confirmed
group reporting_at generated by server
finalized revision freezes fx_rate_set
reopen creates draft revision without changing active finalized revision
```

- [ ] **Step 2: Run failing tests**

```bash
uv run pytest backend/tests/test_fx_service.py backend/tests/test_snapshot_groups_api.py -v
```

Expected: fail.

- [ ] **Step 3: Implement provider abstraction**

Implement:

```python
class FxRateProvider(Protocol):
    def quote(
        self,
        base_currency: str,
        currencies: list[str],
        rate_timestamp: datetime,
    ) -> dict[str, Decimal]: ...
```

Frankfurter notes:

```text
No API key is required.
Use Decimal parsing.
Cache is optional for V1.
Tests must mock HTTP.
```

- [ ] **Step 4: Implement group service**

Functions:

```python
create_snapshot_group(label, members)
update_draft_revision(group_id, members, note)
finalize_group(group_id, fx_mode, manual_rates)
reopen_group(group_id)
cancel_draft(group_id)
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest backend/tests/test_fx_service.py backend/tests/test_snapshot_groups_api.py
uv run ruff check backend
git add backend/app backend/tests/test_fx_service.py backend/tests/test_snapshot_groups_api.py
git commit -m "feat(groups): add FX-backed household groups"
```

---

### Task 7: Sanitized Fixtures and CSV Import

**Files:**
- Create: `backend/tests/fixtures/sample_balance_sheet.json`
- Create: `backend/app/domain/csv_import.py`
- Create: `backend/app/api/routes/csv_import.py`
- Create: `backend/app/services/csv_import.py`
- Test: `backend/tests/test_csv_import_api.py`

**Interfaces:**
- Produces strict template CSV export.
- Produces preview/commit flow.
- Produces sanitized fixture based on the provided two-section CNY/USD sample.

- [ ] **Step 1: Create sanitized fixture**

Transform the sample into fixture structure:

```json
{
  "owners": ["Owner A", "Owner B"],
  "reporting_at": "2026-03-05T15:59:59Z",
  "categories": [
    {"code": "cash", "item_type": "asset"},
    {"code": "marketable_assets", "item_type": "asset"},
    {"code": "credit_card", "item_type": "liability"}
  ],
  "currencies": ["CNY", "USD"],
  "templates": [
    {"account_name": "WeChat Wallet", "institution_name": "WeChat", "currency": "CNY"},
    {"account_name": "Fidelity Brokerage", "institution_name": "Fidelity", "currency": "USD"}
  ]
}
```

Use the pasted sample's structure and approximate coverage, not raw personal labels/amounts unless explicitly approved later.

- [ ] **Step 2: Write CSV tests**

Cover every `IMP-9` verification requirement:

```text
column order
active templates only
formula injection escaping
changed template metadata rejected
unknown/inactive references rejected
negative and over-precision amount rejected
one draft snapshot per owner
atomic no partial records
duplicate draft conflict
```

- [ ] **Step 3: Implement export/preview/commit**

Endpoints:

```text
GET /api/v1/csv/templates/export
POST /api/v1/csv/owner-snapshots/import/preview
POST /api/v1/csv/owner-snapshots/import/commit
```

Preview tokens can be signed short-lived tokens using `SESSION_SECRET` in V1.

- [ ] **Step 4: Verify and commit**

```bash
uv run pytest backend/tests/test_csv_import_api.py
uv run ruff check backend
git add backend/app backend/tests/fixtures backend/tests/test_csv_import_api.py
git commit -m "feat(import): add strict CSV workflow"
```

---

### Task 8: Dashboard Calculation APIs

**Files:**
- Create: `backend/app/domain/dashboard.py`
- Create: `backend/app/api/routes/dashboard.py`
- Create: `backend/app/services/dashboard.py`
- Test: `backend/tests/test_dashboard_api.py`

**Interfaces:**
- Produces household overview, trends, composition, and latest group detail endpoints.
- Produces official vs display estimate behavior.

- [ ] **Step 1: Write dashboard API tests**

Cover:

```text
draft/cancelled/superseded/ungrouped snapshots excluded
official totals use frozen group FX
display currency values marked estimates
owner dashboard uses finalized group membership
currency exposure groups original currencies
negative net worth valid
latest detail shows mixed owner snapshot timestamps
net worth delta not labeled cash flow
```

- [ ] **Step 2: Run failing tests**

```bash
uv run pytest backend/tests/test_dashboard_api.py -v
```

- [ ] **Step 3: Implement dashboard services**

Endpoints:

```text
GET /api/v1/dashboard/household-overview
GET /api/v1/dashboard/net-worth-trend
GET /api/v1/dashboard/assets-liabilities-trend
GET /api/v1/dashboard/owner-net-worth-trend
GET /api/v1/dashboard/composition
GET /api/v1/dashboard/latest-group-detail
```

- [ ] **Step 4: Verify and commit**

```bash
uv run pytest backend/tests/test_dashboard_api.py
uv run ruff check backend
git add backend/app backend/tests/test_dashboard_api.py
git commit -m "feat(dashboard): add official calculation APIs"
```

---

### Task 9: Frontend App Shell, Auth, Theme, and i18n

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/i18n/en-US.ts`
- Create: `frontend/src/i18n/zh-CN.ts`
- Create: `frontend/src/i18n/index.ts`
- Create: `frontend/src/theme/theme.ts`
- Create: `frontend/src/components/AppShell.vue`
- Create: `frontend/src/views/LoginView.vue`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/api/client.ts`

**Interfaces:**
- Produces top nav with language toggle, theme toggle, and logout.
- Produces login flow.
- Produces typed API client using cookie credentials.

- [ ] **Step 1: Add frontend tests dependency**

If component tests are implemented in V1:

```bash
npm install -D vitest @vue/test-utils jsdom
```

Add scripts:

```json
{
  "test": "vitest run"
}
```

- [ ] **Step 2: Implement i18n dictionaries**

Keys:

```text
nav.household
nav.owners
nav.import
nav.logout
theme.light
theme.dark
auth.password
auth.login
dashboard.netWorth
dashboard.totalAssets
dashboard.totalLiabilities
```

User-provided financial names are not translated.

- [ ] **Step 3: Implement theme tokens**

Use CSS variables from `specs/dashboard-ui-design.md`.

- [ ] **Step 4: Verify and commit**

```bash
npm run build
npm run test
git add frontend
git commit -m "feat(frontend): add app shell auth theme and i18n"
```

If `npm run test` is not added in this task, run `npm run build` and document why component tests start in Task 10.

---

### Task 10: Frontend Dashboard UI

**Files:**
- Create: `frontend/src/components/MetricCard.vue`
- Create: `frontend/src/components/ChartCard.vue`
- Create: `frontend/src/components/FilterBar.vue`
- Create: `frontend/src/components/LatestGroupTable.vue`
- Modify: `frontend/src/views/DashboardView.vue`
- Create: `frontend/src/views/OwnerDashboardView.vue`
- Modify: `frontend/src/styles.css`

**Interfaces:**
- Produces household overview dashboard.
- Produces owner dashboard view.
- Produces ECharts chart cards.

- [ ] **Step 1: Implement typed dashboard API methods**

Methods:

```typescript
getHouseholdOverview(params)
getNetWorthTrend(params)
getAssetsLiabilitiesTrend(params)
getOwnerNetWorthTrend(params)
getComposition(params)
getLatestGroupDetail(params)
```

- [ ] **Step 2: Implement components**

Use:

```text
MetricCard for summary values
ChartCard for ECharts containers
FilterBar for date/currency/tag/category filters
LatestGroupTable for latest group detail
```

- [ ] **Step 3: Implement estimate badges**

Show badge when:

```typescript
display_values_are_estimates === true
```

- [ ] **Step 4: Verify and commit**

```bash
npm run build
npm run test
git add frontend
git commit -m "feat(frontend): add dashboard views"
```

---

### Task 11: Deployment and CI/CD

**Files:**
- Create: `deploy/compose.prod.yaml`
- Create: `deploy/Caddyfile`
- Create: `deploy/.env.production.example`
- Create: `deploy/README.md`
- Create: `deploy/scripts/backup_sqlite.sh`
- Create: `deploy/scripts/deploy_release_bundle.sh`
- Create: `deploy/scripts/rollback_release_bundle.sh`
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/deploy-staging.yml`
- Create: `.github/workflows/deploy-production.yml`
- Modify: `backend/Dockerfile`
- Modify: `frontend/Dockerfile`

**Interfaces:**
- Produces GitHub-hosted CI.
- Produces GHCR image builds.
- Produces Mac mini self-hosted staging/prod deploy workflows.
- Produces release-bundle rollback scripts.

- [ ] **Step 1: Write deploy scripts**

Scripts must:

```text
backup SQLite with sqlite3 .backup
retain configured backup counts
stop services during prd deploy
restore previous release bundle on failed health check
never print env secrets
```

- [ ] **Step 2: Convert frontend Dockerfile to production static server**

Use multi-stage build:

```text
node build stage -> static server stage
```

Do not run Vite dev server in production.

- [ ] **Step 3: Add CI workflow**

Jobs:

```text
backend: uv run pytest, uv run ruff check .
frontend: npm ci, npm run build
compose: docker compose config
images: docker build backend/frontend
```

- [ ] **Step 4: Add deploy workflows**

Rules:

```text
dev push -> staging auto deploy
main push -> build images -> production environment approval -> Mac mini deploy
```

Mac mini runner labels:

```text
self-hosted
macmini
production
```

- [ ] **Step 5: Verify and commit**

```bash
docker compose config
uv run pytest
uv run ruff check .
npm run build
git add deploy .github backend/Dockerfile frontend/Dockerfile
git commit -m "feat(deploy): add home lab CI/CD artifacts"
```

---

### Task 12: Final V1 Smoke Verification

**Files:**
- Modify: `README.md`
- Modify: `specs/README.md`
- Create: `backend/tests/test_v1_smoke_api.py`

**Interfaces:**
- Produces API smoke test for the core happy path.
- Produces updated developer instructions.

- [ ] **Step 1: Implement smoke test**

Flow:

```text
login
create owner
create system category
create tag
create template
create draft snapshot
fill 0 and non-zero amounts
confirm snapshot
create household group
finalize with manual FX
verify dashboard official totals
logout
```

- [ ] **Step 2: Update README**

Include:

```text
uv sync
uv run pytest
npm install
npm run build
docker compose up --build
```

- [ ] **Step 3: Run full verification**

```bash
uv run pytest
uv run ruff check .
npm run build
docker compose config
```

Expected: all commands pass.

- [ ] **Step 4: Commit**

```bash
git add README.md specs/README.md backend/tests/test_v1_smoke_api.py
git commit -m "test(v1): add end-to-end API smoke coverage"
```

---

## Self-Review

### Spec Coverage

- PRD: covered by tasks 3-12.
- Data model: covered by tasks 2, 4, 5, 6, 8.
- API contract: covered by tasks 1, 3-8.
- Security/privacy: covered by tasks 1, 3, 7, 11.
- Data import: covered by task 7.
- Dashboard data/UI: covered by tasks 8-10.
- Testing strategy: covered across every task.
- Deployment: covered by task 11.

### Explicit Decisions

- FX provider: Frankfurter public API, no key required, manual fallback retained.
- Sample data: use as structure reference for sanitized fixtures; do not commit raw pasted data by default.
- Deployment: A1+B1, Mac mini self-hosted deploy runner, GHCR images, `dev -> stg`, `main -> prd`.

### Execution Notes

- Prefer one task per PR or commit series.
- Keep each task green before moving on.
- Do not run self-hosted Mac mini runner jobs for pull requests.
- Do not introduce `latest` image tag for production deployment.
