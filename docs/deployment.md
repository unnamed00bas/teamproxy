# Deployment

## Prerequisites (server)

- Linux host with a public IP and DNS pointing at it.
- Docker Engine + Compose v2.
- Ports 80/443 open. WireGuard UDP 51820 open (for the hub).
- An SSH user in the `docker` group + a deploy SSH key. Automatic deploys are
  driven by GitHub Actions over SSH — **no self-hosted runner**. See
  `infra/deploy/README.md`.

## First boot

```bash
git clone <repo> /opt/control-plane && cd /opt/control-plane
cp .env.example .env
# Edit .env: strong SECRET_KEY (openssl rand -hex 32), DB password,
# superadmin creds, ACME_EMAIL, ADMIN_DOMAIN, PUBLIC_API_BASE_URL.

# ADMIN_DOMAIN is the panel's public hostname. Traefik turns it into the
# Host() matcher and the Let's Encrypt cert domain; without it compose refuses
# to start, because an empty value renders the invalid rule Host(``) — Traefik
# drops both routers and every request 404s. Compose reads its interpolation
# .env from the compose-file directory rather than this one, so export
# ADMIN_DOMAIN for manual runs (deploy.sh does this for you).
export ADMIN_DOMAIN=admin.mishteam.site

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
| traefik | 80/443 | only public surface in prod; Let's Encrypt via `letsencrypt` resolver |
| frontend | via traefik | prod: `Host(ADMIN_DOMAIN)`, priority 1 |
| backend | via traefik | prod: `Host(ADMIN_DOMAIN) && (PathPrefix(/api), /docs, /healthz)` |
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
- Production CD: GitHub repository **Secrets** are rendered into a `.env` on the
  GitHub-hosted runner, `rsync`-ed to the server, and kept only inside
  `$DEPLOY_PATH`. Never committed.
- The API never returns secret values — only metadata via `/settings/secrets`.

## Automatic deployment

Push to `main` → GitHub Actions (`ubuntu-latest`) → SSH to the server → build &
run there. No self-hosted runner. Setup and the full secret/variable list are in
`infra/deploy/README.md`.
