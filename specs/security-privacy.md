# Security & Privacy

## Document Control

- Product: My CFO
- Scope: V1 authentication, secret handling, data protection, and privacy boundaries.
- Purpose: define implementable security requirements for backend, deployment, and tests.
- Requirement IDs: use `SEC-x.y` for stable cross-references.

## SEC-1 Authentication Model

Supports: `PRD-1.2`, `PRD-8.1`, `API-3`.

### SEC-1.1 Single Admin Only

V1 uses one admin login identity. There is no registration, user table, role model, permission table, invitation flow, password reset, or owner-level access control.

### SEC-1.2 Owners Are Not Principals

Financial owners are data dimensions only. They must never be treated as authentication users or authorization principals.

### SEC-1.3 Full Admin Access

Every authenticated request has full admin access to all V1 data and actions.

### SEC-1.4 V2 Migration Path

V2 may introduce database-backed users by bootstrapping the first admin from the V1 environment-backed password hash. V1 should avoid code paths that assume multiple users.

## SEC-2 Passwords and Sessions

Supports: `PRD-8.2`, `API-3`.

### SEC-2.1 Password Hash

The admin password must be stored as a password hash in `ADMIN_PASSWORD_HASH`. The application must never accept or persist a plaintext admin password outside the login request body.

### SEC-2.2 Hashing Algorithm

Use Argon2id when available. If implementation constraints require a fallback, bcrypt is acceptable. The chosen algorithm and parameters must be documented in `.env.example` comments without including real hashes.

### SEC-2.3 Session Secret

Session signing/encryption must use `SESSION_SECRET` from the environment. The app must refuse to start in production if `SESSION_SECRET` is missing, empty, or a known placeholder.

### SEC-2.4 Cookie Session

Successful login creates an HttpOnly cookie session.

Required cookie attributes:

- `HttpOnly=true`
- `SameSite=Lax`
- `Path=/`
- `Secure=true` in public production
- finite expiration, default 7 days

For V1 LAN production without HTTPS, `Secure=false` is allowed only when `DEPLOYMENT_NETWORK=lan`. If public ingress or HTTPS is introduced later, `Secure=true` is required.

### SEC-2.5 Logout

Logout must invalidate the browser session by clearing the session cookie. If server-side session storage is added later, logout must also revoke the stored session.

## SEC-3 API Protection

Supports: `API-3`, `API-4`.

### SEC-3.1 FastAPI Dependency Auth

Use FastAPI dependency-based authentication on protected routers. Do not use global authentication middleware as the primary authorization mechanism.

### SEC-3.2 Protected Routes

All `/api/v1/*` routes require authentication except `POST /api/v1/auth/login`.

### SEC-3.3 Development Exceptions

`GET /health`, `/docs`, and `/openapi.json` may remain unauthenticated for local development. Production deployments may disable unauthenticated docs through configuration.

### SEC-3.4 Error Responses

Authentication failures return the standard API error shape with `401`. Authorization failures, if any are introduced later, return `403`.

## SEC-4 CSRF and Browser Safety

Supports: `API-3`.

### SEC-4.1 SameSite Baseline

Because V1 uses cookie authentication, session cookies must use `SameSite=Lax` at minimum.

### SEC-4.2 State-Changing Requests

State-changing requests must use non-GET methods only. The frontend must not trigger mutations through links or image/script loads.

### SEC-4.3 CSRF Token Decision

V1 may defer explicit CSRF tokens if the app is same-site only, uses `SameSite=Lax`, and does not embed cross-site workflows. If production deployment expands to cross-site usage, add CSRF tokens before enabling that deployment.

## SEC-5 Secret and Configuration Handling

Supports: `PRD-8.2`.

### SEC-5.1 Environment Only

Passwords, hashes, tokens, private keys, connection strings, FX API keys, and session secrets must come from environment variables.

### SEC-5.2 Repository Safety

Commit `.env.example` with placeholders only. Never commit `.env`, real hashes, real API keys, SQLite data files, exports containing personal financial data, or backups.

### SEC-5.3 Docker Compose

Compose files must declare required environment variable names but must not contain real secret values. Local secret values belong in ignored `.env` files or deployment secret stores.

### SEC-5.4 Startup Validation

Production startup must fail fast when required security variables are missing or set to known placeholder values.

## SEC-6 Financial Data Privacy

Supports: `PRD-8.3`.

### SEC-6.1 Sensitive Data Classes

Treat the following as sensitive:

- owner names
- account names
- institution names
- snapshot amounts
- CSV imports and exports
- SQLite database files
- backups and restore archives
- FX API keys and logs containing request metadata

### SEC-6.2 Logging

Application logs must not include passwords, session cookies, full CSV file contents, full snapshot item lists, or complete financial amounts by default. Validation logs may include row numbers and field names.

### SEC-6.3 Browser Storage

The frontend must not store sensitive financial data in `localStorage` or `sessionStorage`. In-memory state is acceptable. Downloaded CSV files are user-managed local files.

## SEC-7 SQLite, Backups, and File Protection

Supports: `PRD-8.3`, `PRD-8.4`.

### SEC-7.1 SQLite Location

The SQLite database path must be configurable through an environment variable such as `DATABASE_URL` or `SQLITE_PATH`.

### SEC-7.2 File Permissions

The database and backup files should be readable and writable only by the application user in production deployments.

### SEC-7.3 Backups

Backups contain sensitive financial data. Backup files must not be committed, logged, or served by the frontend. Restore workflows must require authenticated admin access.

### SEC-7.4 Soft Delete Privacy

Soft-deleted, inactive, cancelled, and superseded records remain sensitive and must remain protected by the same access controls as active records.

## SEC-8 CSV Safety

Supports: `PRD-6.1`, `PRD-6.3`, `PRD-6.4`, `PRD-6.5`.

### SEC-8.1 Strict Import

CSV import must follow the app-defined template schema. Unknown owners, templates, system categories, tags, currencies, malformed amounts, negative amounts, and schema deviations are rejected.

### SEC-8.2 Preview Before Commit

CSV import must validate and preview before creating draft snapshots. Failed imports must not create partial records.

### SEC-8.3 CSV Injection

CSV export should escape or prefix cells that begin with formula-triggering characters such as `=`, `+`, `-`, or `@` when those cells contain user-controlled text.

## SEC-9 Traceability Matrix

| Requirement | Security Coverage |
|---|---|
| `PRD-1.2`, `PRD-8.1` | Single-admin authentication |
| `PRD-8.2` | Env-only secrets, password hash, session secret, Compose rules |
| `PRD-8.3` | SQLite privacy, sensitive financial data handling, backups |
| `PRD-8.4` | Soft-deleted records remain protected |
| `PRD-6.1` through `PRD-6.5` | CSV validation, preview, injection mitigation |
| `API-3` | Dependency-based auth and HttpOnly cookie session |
| `API-4` | Standard auth and validation error behavior |

## SEC-10 Verification Requirements

- Auth tests must prove protected `/api/v1/*` endpoints reject unauthenticated requests.
- Login tests must prove wrong passwords fail and correct passwords establish a session.
- Logout tests must prove the session cookie is cleared.
- Secret validation tests must prove production startup rejects placeholder or missing secrets.
- CSV tests must prove invalid imports create no records.
- Logging tests or code review checks must confirm passwords and session cookies are not logged.
