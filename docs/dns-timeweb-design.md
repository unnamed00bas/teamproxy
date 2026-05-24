# DNS auto-discovery & sync — Timeweb Cloud (design)

Status: **design only** (not implemented). Goal: let the control plane pull the
existing records of a zone (e.g. `*.mishteam.site`) from Timeweb Cloud and show
them in the UI, instead of the current manual-only `domains` registry.

## Why this is needed

Today (`apps/backend/app/api/v1/dns.py`, `app/models/domain.py`) the `domains`
table is a hand-maintained list — there is no provider integration, so the UI
can only display what an operator typed in. To "show all `*.mishteam.site`
addresses" we must fetch them from the authoritative DNS, which is Timeweb.

> Note on wildcards: DNS itself cannot enumerate names behind a `*` record via
> normal queries (no zone transfer from public resolvers). Enumeration must come
> from the **provider API**, which lists the concrete records in the zone.

## Provider: Timeweb Cloud DNS API

- REST API, bearer-token auth: `Authorization: Bearer <TIMEWEB_API_TOKEN>`.
- Relevant endpoints (verify exact paths/shape against current Timeweb docs
  before coding):
  - List domains on the account.
  - List records of a domain (`A`, `AAAA`, `CNAME`, `TXT`, …) — this is the
    enumeration we surface.
  - Create / update / delete a record (for the optional write-back path).
- Token is a **secret**: inject via env (`TIMEWEB_API_TOKEN`), never persist in
  the DB; track only `SecretMetadata` like other secrets.

## Settings (config.py / .env)

```
DNS_PROVIDER=timeweb            # off | timeweb
TIMEWEB_API_TOKEN=              # secret, env-only
DNS_ROOT_ZONE=mishteam.site     # zone to enumerate
DNS_SYNC_INTERVAL_MINUTES=15    # background refresh cadence
```

Expose only non-sensitive fields via `/settings/info`
(`dns_provider`, `dns_root_zone`, `dns_configured`).

## Backend shape

New module `app/services/dns/` with a small provider interface so other
providers can be added later:

```python
class DnsProvider(Protocol):
    async def list_records(self, zone: str) -> list[DiscoveredRecord]: ...
    async def upsert_record(self, zone: str, rec: DiscoveredRecord) -> None: ...
    async def delete_record(self, zone: str, rec_id: str) -> None: ...

@dataclass
class DiscoveredRecord:
    fqdn: str
    record_type: str        # A / AAAA / CNAME / TXT ...
    value: str
    ttl: int | None
    provider_id: str        # Timeweb's record id, for idempotent sync
```

`TimewebProvider` implements it with `httpx.AsyncClient` + retry/backoff.

### Data model change

Extend `domains` (one Alembic migration) so discovered records are
distinguishable from manually-created ones and sync is idempotent:

- `source: str` — `manual` | `discovered` (default `manual`).
- `provider_id: str | None` — provider's record id (unique per provider).
- `value: str | None`, `ttl: int | None` — last-seen record data.
- `last_synced_at: datetime | None`.

Keep `fqdn` unique; on sync, match by `provider_id` first, then `fqdn`.

### API endpoints (`/api/v1/dns`)

- `POST /dns/sync` (operator) — pull the zone now, upsert discovered rows,
  mark rows that vanished from the provider as `active=false`; return a summary
  `{created, updated, removed}`. Audited as `dns.sync`.
- `GET /dns?source=discovered|manual` — filter in the existing list endpoint.
- (Optional, phase 2) `POST /dns/{id}/publish` — write a control-plane record
  back to Timeweb (e.g. point a new publication's host at the VPS IP).

### Background sync

Add a Celery beat task (`app/tasks/jobs.py`, scheduled in `celery_app.py`)
running every `DNS_SYNC_INTERVAL_MINUTES` that calls the same sync routine, so
the UI stays fresh without manual refresh. Make it a no-op when
`DNS_PROVIDER=off`.

## Frontend

- DNS page: add a **«Синхронизировать»** button (calls `POST /dns/sync`,
  then refreshes the list via the existing `refreshToken`), a "source" badge
  (ручная / из Timeweb), and `value` / `TTL` columns.
- Show a hint when `dns_configured` is false (no token/zone set).

## Security & failure modes

- Token only in env + `SecretMetadata`; never returned by any endpoint.
- Treat provider data as untrusted input (validate FQDN/type before storing).
- Network errors: retry with backoff; surface last sync status in the UI; never
  delete manual rows on a failed/partial sync (only flip `active` for
  previously-discovered rows that are confirmed gone).
- Rate limits: respect Timeweb limits; the 15-min cadence + manual button is
  enough for an admin panel.

## Open questions

1. One zone (`mishteam.site`) or multiple? (Design supports a list later.)
2. Should the control plane ever **write** records (phase 2), or only read?
3. Per-record TTL policy when we create A-records for new publications.
