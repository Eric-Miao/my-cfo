# Deployment

## Document Control

- Product: My CFO
- Scope: V1 home-lab deployment, CI/CD, backups, rollback, and operations.
- Purpose: define a complete but lightweight deployment model for Mac mini hosting.
- Requirement IDs: use `DEP-x.y` for stable cross-references.

## DEP-1 Deployment Target

Supports: `PRD-8.2`, `PRD-8.3`, `SEC-5`, `SEC-7`.

### DEP-1.1 Home Lab Target

V1 deploys to a Mac mini home lab using Docker Compose. The Mac mini has no public IP requirement and does not need public internet ingress.

### DEP-1.2 Network Mode

V1 uses LAN production mode:

```text
DEPLOYMENT_NETWORK=lan
```

HTTP on the LAN is allowed for V1. Public production mode is out of scope.

### DEP-1.3 Environments

V1 uses two deployed environments:

```text
stg = staging
prd = production
```

The project does not model separate `tst` or `uat` environments in V1.

## DEP-2 Environment Mapping

### DEP-2.1 Staging

Staging maps to the `dev` branch.

```text
branch: dev
deploy: automatic after CI passes
compose project: my-cfo-stg
port: 8081
env file: /opt/my-cfo/stg/env/staging.env
data dir: /opt/my-cfo/stg/data
backup dir: /opt/my-cfo/stg/backups
```

Staging uses dummy or test data only. Real personal finance data belongs in production.

### DEP-2.2 Production

Production maps to the `main` branch.

```text
branch: main
deploy: manual approval required
compose project: my-cfo-prd
port: 8080
env file: /opt/my-cfo/prd/env/production.env
data dir: /opt/my-cfo/prd/data
backup dir: /opt/my-cfo/prd/backups
```

Production stores real personal finance data.

## DEP-3 Services

V1 Compose deployment includes:

- `reverse-proxy`: LAN HTTP entrypoint and path routing.
- `frontend`: built Vue static application.
- `backend`: FastAPI REST API.
- `backup`: SQLite backup helper or scheduled backup container.

Routing:

```text
/             -> frontend
/api/v1/*     -> backend
/health       -> backend
/docs         -> backend, configurable
/openapi.json -> backend, configurable
```

## DEP-4 Compose Configuration

Supports: `SEC-5.3`.

### DEP-4.1 Committed Production Compose

Production/staging Compose config is committed to the repository and parameterized with environment variables.

Recommended files:

```text
deploy/compose.prod.yaml
deploy/Caddyfile
deploy/.env.production.example
deploy/README.md
```

### DEP-4.2 Parameterized Paths

Compose must support:

```text
MY_CFO_HTTP_PORT
MY_CFO_ENV_FILE
MY_CFO_DATA_DIR
MY_CFO_BACKUP_DIR
IMAGE_TAG
IMAGE_REGISTRY
IMAGE_NAMESPACE
DEPLOYMENT_NETWORK
COOKIE_SECURE
```

Example deployment command:

```bash
docker compose \
  --project-name my-cfo-prd \
  --env-file /opt/my-cfo/prd/env/production.env \
  -f deploy/compose.prod.yaml \
  up -d
```

## DEP-5 Secrets and Runtime Configuration

Supports: `SEC-2`, `SEC-5`.

### DEP-5.1 Runtime Secrets Stay on Mac mini

Runtime secrets are stored only on the Mac mini in environment files:

```text
/opt/my-cfo/stg/env/staging.env
/opt/my-cfo/prd/env/production.env
```

They are not stored in GitHub Secrets unless required for a non-runtime CI function.

### DEP-5.2 Required Runtime Variables

Production requires:

```text
APP_ENV=production
APP_NAME=my-cfo
DATABASE_URL=sqlite:////data/my-cfo.db
ADMIN_PASSWORD_HASH=...
SESSION_SECRET=...
CORS_ORIGINS=http://macmini.local:8080
DEPLOYMENT_NETWORK=lan
COOKIE_SECURE=false
ALLOW_PUBLIC_DOCS=false
IMAGE_TAG=<git-sha>
MY_CFO_HTTP_PORT=8080
MY_CFO_DATA_DIR=/opt/my-cfo/prd/data
MY_CFO_BACKUP_DIR=/opt/my-cfo/prd/backups
MY_CFO_ENV_FILE=/opt/my-cfo/prd/env/production.env
```

Staging uses equivalent `/opt/my-cfo/stg/*` paths and port `8081`.

### DEP-5.3 LAN Cookie Exception

`COOKIE_SECURE=false` is allowed only when:

```text
DEPLOYMENT_NETWORK=lan
```

If public ingress or HTTPS is added later, `COOKIE_SECURE=true` becomes required.

## DEP-6 CI/CD Architecture

Supports: `TEST-2`, `TEST-4`, `TEST-5`, `TEST-10`.

### DEP-6.1 Runner Split

GitHub-hosted runners run:

- pull request checks
- `dev` checks
- `main` checks
- lint
- tests
- frontend build
- Docker build
- GHCR image push

Mac mini self-hosted runner runs only:

- staging deploy from `dev`
- production deploy from `main` after manual approval

The Mac mini runner must not run pull request, feature branch, test, or build jobs.

### DEP-6.2 Image Delivery

CI builds backend and frontend images on GitHub-hosted runners and pushes them to GHCR. The Mac mini pulls images from GHCR.

Production does not build images locally.

### DEP-6.3 Image Tags

Every deployable image must have an immutable git SHA tag.

Do not deploy mutable tags such as:

```text
latest
main
dev
```

GitHub Releases are optional milestone records. When a release such as `v0.1.0` exists, the release tag should point to the same image digest as the corresponding SHA tag.

## DEP-7 Branch and Release Flow

Supports: repository branching policy.

```text
feature/* -> PR -> dev -> staging auto deploy
dev -> PR -> main -> production manual deploy
```

Rules:

- `dev` is the latest integration branch.
- `main` is the release branch and must always be deployable.
- Every `main` commit builds immutable SHA-tagged images.
- GitHub Release is created only for named milestones.
- No separate long-lived release branch exists in V1.
- Production deployment requires GitHub Environment approval by the repository owner.

## DEP-8 Staging Deployment

### DEP-8.1 Automatic Deploy

Pushes to `dev` run CI and then auto deploy staging if CI passes.

### DEP-8.2 Persistent Staging Data

Staging data persists across normal deploys.

### DEP-8.3 Manual Reset

A manual `workflow_dispatch` reset may:

1. stop staging
2. back up existing staging SQLite
3. remove or archive staging SQLite
4. start staging
5. optionally seed dummy data
6. run health checks

## DEP-9 Production Deployment

### DEP-9.1 Manual Approval

Pushes to `main` run CI, build images, and push GHCR images. Production deploy waits for GitHub Environment manual approval.

### DEP-9.2 Maintenance Window

Production deploy may stop services during upgrade. The app should not be used during the deploy window.

### DEP-9.3 Release Bundle

A production release bundle is:

```text
release bundle = image tag + matching SQLite backup
```

This simplifies V1 rollback by keeping the runnable app image and datastore together.

### DEP-9.4 Production Deploy Steps

Production deploy flow:

1. enter maintenance window
2. stop production services
3. back up current SQLite as the previous release bundle
4. pull new SHA-tagged images
5. start production services with the new `IMAGE_TAG`
6. run health checks
7. if healthy, back up post-deploy SQLite as the new release bundle
8. mark current release
9. exit maintenance window

### DEP-9.5 Automatic Rollback

If post-deploy health checks fail, the deploy workflow automatically restores the previous release bundle:

1. stop failed services
2. restore previous SQLite backup
3. restore previous `IMAGE_TAG`
4. start previous services
5. run health checks
6. mark previous release as current

Automatic rollback may overwrite the failed deploy datastore because production is unavailable during the deploy window.

## DEP-10 Backups

Supports: `SEC-7`.

### DEP-10.1 Local-Only Backup Scope

V1 uses local backups only. There is no HA, DR, S3, Vault, external drive, or NAS requirement.

Local-only backups are operational rollback protection, not disaster recovery.

### DEP-10.2 Production Backups

Production uses:

- pre-deploy release-bundle backup
- post-success release-bundle backup
- daily scheduled backup

Retention:

```text
release bundles: keep last 3
daily backups: keep last 30
```

### DEP-10.3 Staging Backups

Staging uses pre-deploy backup only.

Retention:

```text
staging predeploy backups: keep last 10
```

### DEP-10.4 Backup Command

Backups should use SQLite online backup behavior rather than raw file copy while the database may be open.

Example:

```bash
sqlite3 /data/my-cfo.db ".backup '/backups/daily/daily-20260717-020000.db'"
```

## DEP-11 Health Checks and Verification

Health checks:

- backend: `GET /health`
- frontend: `GET /`
- reverse proxy: LAN endpoint root and `/health`

Deployment verification commands:

```bash
docker compose config
docker compose pull
docker compose up -d
curl http://localhost:8080/health
curl http://localhost:8080/
```

CI verification commands:

```bash
uv run pytest
uv run ruff check .
npm run build
docker compose config
docker build .
```

## DEP-12 Traceability Matrix

| Requirement | Deployment Coverage |
|---|---|
| `PRD-8.2` | env-only runtime secrets and GitHub runner split |
| `PRD-8.3` | SQLite local data and backup paths |
| `SEC-5` | secret and Compose handling |
| `SEC-7` | SQLite and backup protection |
| `TEST-2` | local and CI verification commands |
| `TEST-4`, `TEST-5` | API/OpenAPI deploy gates |
| `TEST-10` | frontend build deploy gate |

## DEP-13 Open Implementation Items

These are implementation tasks, not unresolved design questions:

- add `deploy/compose.prod.yaml`
- add `deploy/Caddyfile`
- add GitHub Actions CI workflow
- add GitHub Actions staging deploy workflow
- add GitHub Actions production deploy workflow with manual environment approval
- add Mac mini runner setup documentation
- add backup and release-bundle scripts
- update security spec for LAN `COOKIE_SECURE=false` exception
