# Control Plane — multi-site service publishing via a VPS edge

Self-hosted control plane for publishing services that live on several local
sites (behind NAT) to the internet through a single VPS with a public IP and
domains. A web UI manages sites, VPN peers, nodes, services, publications, DNS,
TLS, deployments and a full audit trail. Everything runs via Docker Compose and
auto-deploys on push to `main` via GitHub Actions over SSH (no self-hosted
runner).

## Architecture at a glance

```
                 internet
                    │  (DNS → VPS public IP)
              ┌─────▼──────┐
              │  Traefik   │  edge ingress (HTTP/HTTPS now, TCP/UDP ready)
              │  (VPS)     │◄── dynamic config files written by the control plane
              └─────┬──────┘
        ┌───────────┼───────────────┐
   ┌────▼────┐ ┌────▼────┐     ┌─────▼─────┐
   │ backend │ │frontend │     │ WireGuard │  hub on VPS, peers per site
   │ FastAPI │ │ Next.js │     │   hub     │
   └────┬────┘ └─────────┘     └─────┬─────┘
        │  Postgres + Redis           │ encrypted tunnels
   ┌────▼─────┐ ┌────────┐       ┌────▼─────────┐   ┌──────────────┐
   │ worker   │ │ beat   │       │ site gateway │…  │ site gateway │
   │ (Celery) │ │(sched) │       │  + services  │   │  + services  │
   └──────────┘ └────────┘       └──────────────┘   └──────────────┘
```

Components (a monorepo):

| Path | What |
|------|------|
| `apps/backend` | FastAPI API, SQLAlchemy 2.x models, Alembic, auth/RBAC, config renderer, Celery tasks |
| `apps/frontend` | Next.js (App Router) admin UI |
| `apps/worker` | Celery worker/beat (runs from the backend image) |
| `infra/compose` | `docker-compose.yml` (dev) + `docker-compose.prod.yml` |
| `infra/traefik` | Traefik static config + base dynamic config (file provider) |
| `infra/wireguard` | hub/gateway config templates |
| `infra/scripts` | deploy / backup / restore / healthcheck |
| `infra/deploy` | automatic-deploy setup (GitHub Actions over SSH) |
| `packages/shared-types` | canonical TypeScript API contracts |
| `packages/config-schema` | JSON Schema for the publication contract |
| `.github/workflows` | `ci.yml` (lint/test/build) + `deploy.yml` (CD) |
| `docs/` | architecture, deployment, networking, data model, CI/CD, roadmap |

## Quick start (local)

```bash
cp .env.example .env          # then edit SECRET_KEY etc.
docker compose -f infra/compose/docker-compose.yml up -d --build
```

- UI:        http://localhost:3000
- API docs:  http://localhost:8000/docs
- Traefik:   http://localhost:8080 (dashboard, dev only)

Log in with `FIRST_SUPERADMIN_EMAIL` / `FIRST_SUPERADMIN_PASSWORD` from `.env`.

## Backend development

```bash
cd apps/backend
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL="sqlite+aiosqlite:///:memory:" SECRET_KEY=dev
pytest -q                      # tests
ruff check app tests           # lint
uvicorn app.main:app --reload  # run API (needs a real DATABASE_URL for persistence)
```

Migrations:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Frontend development

```bash
cd apps/frontend
npm install
npm run dev        # http://localhost:3000
npm run typecheck && npm run lint && npm run build
```

## MVP capabilities

- JWT auth + RBAC (superadmin / operator / viewer)
- CRUD for sites, peers, nodes, services, publications, DNS records
- WireGuard keypair generation (private key returned once, never stored)
- Deterministic Traefik dynamic-config generation with revisions, diff,
  preview, conflict detection, apply (atomic file write → hot reload) and
  rollback
- Health checks (HTTP + TCP), dashboard aggregation
- Full audit log on every mutation
- Docker Compose deployment + GitHub Actions CD over SSH (build & run on the server)

See `docs/` for details and `docs/roadmap.md` for what comes after the MVP.
