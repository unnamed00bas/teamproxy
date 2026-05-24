# CI/CD

## CI — `.github/workflows/ci.yml`

Runs on every push and PR to `main`. Three parallel jobs:

- **backend** — `ruff check`, `pytest` (SQLite in-memory), and a migration
  smoke test (`alembic upgrade head` on a fresh DB).
- **frontend** — `tsc --noEmit`, `next lint`, `next build`.
- **compose** — `docker compose config` validation for the dev stack and the
  dev+prod overlay.

## CD — `.github/workflows/deploy.yml`

Triggers on push to `main` (and manual `workflow_dispatch`). Runs on the
**self-hosted runner on the VPS** (`runs-on: [self-hosted, linux, vps]`), so no
SSH is involved — `docker compose` runs locally against the production stack.

Pipeline steps:

1. Checkout.
2. Materialise a production `.env` from GitHub Secrets.
3. `infra/scripts/deploy.sh`:
   - back up DB + dynamic configs,
   - `docker compose pull` + `build`,
   - `alembic upgrade head` (one-off backend container),
   - `docker compose up -d --remove-orphans`,
   - **smoke test** via `healthcheck.sh` (`/readyz` must answer),
   - **rollback** the stack if the smoke test fails (non-zero exit).
4. Record the deployed revision.
5. Always remove the transient `.env`.

`concurrency: production-deploy` (no cancel-in-progress) serialises deploys so
two pushes can't race on the same host.

## Required secrets

Configure under **Settings → Secrets and variables → Actions**:

`SECRET_KEY`, `POSTGRES_PASSWORD`, `FIRST_SUPERADMIN_EMAIL`,
`FIRST_SUPERADMIN_PASSWORD`, `ACME_EMAIL`, `PUBLIC_API_BASE_URL`.

## Zero/minimal-downtime (optional upgrade)

The current flow recreates changed containers (brief blip for stateless app
containers behind Traefik). For smoother rollouts you can layer a rolling
update plugin (e.g. `docker rollout`) per app service — kept out of the MVP to
stay simple and robust.

## Deploy revisions in the app

The API exposes `/api/v1/deployments` so the pipeline (or an operator) can
register a revision with commit SHA, mode, status and health result, surfaced
on the Deployments screen.
