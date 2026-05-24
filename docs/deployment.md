# Deployment

## Prerequisites (VPS)

- Linux host with a public IP and DNS pointing at it.
- Docker Engine + Compose v2.
- Ports 80/443 open. WireGuard UDP 51820 open (for the hub).
- A self-hosted GitHub Actions runner (see `infra/github-runner/README.md`).

## First boot

```bash
git clone <repo> /opt/control-plane && cd /opt/control-plane
cp .env.example .env
# Edit .env: strong SECRET_KEY (openssl rand -hex 32), DB password,
# superadmin creds, ACME_EMAIL, PUBLIC_API_BASE_URL.

docker compose \
  -f infra/compose/docker-compose.yml \
  -f infra/compose/docker-compose.prod.yml \
  up -d --build
```

The backend entrypoint runs `alembic upgrade head` automatically and the app
lifespan seeds the first superadmin if the users table is empty.

## What runs where

| Service | Exposed | Notes |
|---------|---------|-------|
| traefik | 80/443 | only public surface in prod |
| frontend | via traefik | `PathPrefix(/)`, priority 1 |
| backend | via traefik | `PathPrefix(/api), /docs, /healthz` |
| worker/beat | internal | Celery |
| db/redis | internal | named volumes `pgdata`, `redisdata` |

In `docker-compose.prod.yml` the host port bindings for backend/frontend are
removed (`!reset`) so only Traefik is reachable from outside.

## Health & readiness

- `GET /healthz` — liveness (process up).
- `GET /readyz` — readiness (DB reachable).
- Compose healthchecks gate `db`/`redis`; the backend image has its own
  `HEALTHCHECK` hitting `/healthz`.

## Backups

```bash
./infra/scripts/backup.sh        # pg_dump.gz + dynamic config tarball, keeps 14
./infra/scripts/restore.sh backups/db-YYYYMMDD-HHMMSS.sql.gz
```

The deploy script calls `backup.sh` before every deploy.

## Manual deploy / rollback

```bash
./infra/scripts/deploy.sh        # build → migrate → up → smoke test → rollback on fail
```

Config-level rollback (independent of container rollback) is available through
the API: `POST /api/v1/publications/rollback/{revision}`.

## Secrets

- Local: `.env` (gitignored).
- Production CD: GitHub repository **Secrets** are written into a transient
  `.env` by `deploy.yml` and removed afterwards.
- The API never returns secret values — only metadata via `/settings/secrets`.
