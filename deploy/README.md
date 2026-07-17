# Deployment

V1 deploys with Docker Compose on a Mac mini home-lab runner. Staging and
production use separate Compose projects, ports, env files, data directories,
and backup directories.

Example production command:

```bash
docker compose \
  --env-file /opt/my-cfo/prd/env/production.env \
  -f deploy/compose.prod.yaml \
  up -d
```

Production env files must stay outside git. Use `deploy/.env.production.example`
as a template, then set real `ADMIN_PASSWORD_HASH` and `SESSION_SECRET`.

Rollback is release-bundle based: restore the previous SQLite backup and rerun
Compose with the previous immutable image tag.
