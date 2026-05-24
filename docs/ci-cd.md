# CI/CD

## CI — `.github/workflows/ci.yml`

Runs on every push and PR to `main`. Three parallel jobs:

- **backend** — `ruff check`, `pytest` (SQLite in-memory), and a migration
  smoke test (`alembic upgrade head` on a fresh DB).
- **frontend** — `tsc --noEmit`, `next lint`, `next build`.
- **compose** — `docker compose config` validation for the dev stack and the
  dev+prod overlay.

## CD — `.github/workflows/deploy.yml`

Triggers on push to `main` (and manual `workflow_dispatch`). Runs on a
**GitHub-hosted runner** (`ubuntu-latest`) — **no self-hosted runner**. The job
connects to your server over SSH, syncs the code, and builds + runs the stack
**on the server**.

Pipeline steps:

1. Checkout.
2. Configure the SSH key from `SSH_PRIVATE_KEY` (+ `ssh-keyscan` of the host).
3. Render a production `.env` from GitHub Secrets.
4. `rsync` the working tree (including `.env`) to `$DEPLOY_PATH` on the server
   (`--delete`, excluding `.git`, `.venv`, `node_modules`, `.next`, `backups`).
5. SSH into the server and run `infra/scripts/deploy.sh`, which:
   - backs up DB + dynamic configs,
   - `docker compose build` (images built **on the server**),
   - `alembic upgrade head` (one-off backend container),
   - `docker compose up -d --remove-orphans`,
   - **smoke test** via `healthcheck.sh` (`compose exec backend curl /readyz`),
   - **rollback** the stack if the smoke test fails (non-zero exit).

`concurrency: production-deploy` (no cancel-in-progress) serialises deploys so
two pushes can't race on the host.

## Required configuration (one-time)

Full walkthrough in `infra/deploy/README.md`. Under **Settings → Secrets and
variables → Actions**:

- **Secrets:** `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, `SECRET_KEY`,
  `POSTGRES_PASSWORD`, `FIRST_SUPERADMIN_EMAIL`, `FIRST_SUPERADMIN_PASSWORD`,
  `ACME_EMAIL`, `PUBLIC_API_BASE_URL`.
- **Variables (optional):** `SSH_PORT` (default `22`),
  `DEPLOY_PATH` (default `/opt/control-plane`).

The server only needs Docker + Compose and an SSH user in the `docker` group —
no runner daemon, no registry (images build on the server).

## Zero/minimal-downtime (optional upgrade)

The current flow recreates changed containers (brief blip for stateless app
containers behind Traefik). For smoother rollouts you can layer a rolling
update plugin (e.g. `docker rollout`) per app service — kept out of the MVP to
stay simple and robust.

## Deploy revisions in the app

The API exposes `/api/v1/deployments` so the pipeline (or an operator) can
register a revision with commit SHA, mode, status and health result, surfaced
on the Deployments screen.
