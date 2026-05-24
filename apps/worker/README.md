# Worker

The background worker runs the **same image as the backend** (`apps/backend`)
but with a Celery command instead of the API server. This keeps the ORM models,
DB session layer and business logic in a single place (`apps/backend/app`)
rather than duplicating them.

Task code lives in `apps/backend/app/tasks/`:

- `celery_app.py` — Celery application + beat schedule.
- `jobs.py` — the actual jobs:
  - `sweep_service_health` — probes every enabled service (HTTP / TCP) and
    records a `health_checks` row.
  - `sweep_peer_staleness` — flags WireGuard peers whose handshake is stale and
    rolls the status up to the owning site.
  - `render_config_revision` — periodically re-renders the Traefik dynamic
    config and stores a new revision if anything changed.

## Running locally

```bash
# worker
celery -A app.tasks.celery_app.celery worker --loglevel=INFO
# beat (scheduler)
celery -A app.tasks.celery_app.celery beat --loglevel=INFO
```

In Docker Compose these run as the `worker` and `beat` services (see
`infra/compose/docker-compose.yml`).
