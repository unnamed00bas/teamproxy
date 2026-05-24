# Architecture

## Goal

A single web-managed control plane that publishes selected services from
multiple NAT'd local sites to the internet through one VPS edge, while keeping
other services reachable only over the VPN for admins.

## Services

- **backend (FastAPI)** — the brain. Owns the data model, business logic,
  authn/authz, the config renderer, the WireGuard metadata, and the API the UI
  consumes. Stateless; all state is in Postgres.
- **frontend (Next.js)** — the only UI. Talks to the backend REST API.
- **worker / beat (Celery)** — background jobs: health sweeps, peer-staleness
  detection, periodic config rendering. Shares the backend code/image.
- **Traefik** — the edge reverse proxy. Uses the **file provider** (for the
  routes the control plane generates) and the **docker provider** (for infra
  services like the API/UI themselves) simultaneously.
- **WireGuard hub** — terminates tunnels from each site gateway on the VPS.
- **Postgres** — system of record.
- **Redis** — Celery broker/result backend.

## Layered backend design

```
app/
  api/        # HTTP layer: routers + dependencies (auth, RBAC, db session)
  schemas/    # Pydantic DTOs (request/response) — separate from ORM
  models/     # SQLAlchemy ORM models + enums
  crud/       # generic persistence helpers
  core/       # security (bcrypt/JWT), rbac, audit, logging
  services/   # business logic
    config_renderer/   # proxy-agnostic seam + Traefik renderer
    health/            # backend probing
    wireguard.py       # key generation + config templating
  tasks/      # Celery app + jobs
  db/         # engine/session, declarative base, seed
```

Key boundaries:

- **DTO ↔ ORM separation.** Routers accept/return Pydantic schemas; ORM models
  never leak directly into the API contract.
- **Proxy-agnostic config layer.** `services/config_renderer/renderer.py`
  exposes `render / preview / apply / diff / rollback` without Traefik
  specifics. `traefik.py` is the only Traefik-aware module, so a different
  ingress could be added later behind the same seam.
- **Determinism.** The renderer sorts every collection and emits YAML with
  stable key ordering, so identical inputs produce byte-identical output. That
  makes checksums and revision diffs meaningful.

## Config generation flow

1. Operator changes a service/publication via the UI/API (audited).
2. `ConfigRenderer.preview()` shows the rendered config + a unified diff vs the
   last revision + any domain conflicts — nothing is written yet.
3. `render_and_store()` persists a new `generated_configs` revision **only if
   the checksum changed**.
4. `apply()` writes `control-plane.yml` into the shared Traefik dynamic dir via
   an atomic temp-file + `os.replace`. Traefik watches the directory and hot
   reloads — no restart.
5. `rollback_to(revision)` re-applies a previous revision as a new revision.

## Access models

- **Publish mode** — a publication with `public_enabled=true` produces an edge
  route (`Host(domain) → backend`).
- **Private access mode** — services with `exposure_mode=private` are not given
  a public route; they are reachable only across the VPN by admin peers.

## Security posture

- bcrypt password hashing, JWT bearer tokens, three-tier RBAC.
- Every mutation writes an `audit_events` row (actor, action, target,
  before/after, result).
- WireGuard **private keys are never stored** — generated server-side and
  returned exactly once; only the public key + a secret reference persist.
- Secrets come from env / Docker secrets; only **metadata** is exposed via the
  API (`/settings/secrets`), never values.
- Docker socket mounted read-only into Traefik; the runner runs as a non-root
  user.
