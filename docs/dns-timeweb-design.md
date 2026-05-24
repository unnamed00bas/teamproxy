# DNS records — current model & Timeweb (future)

DNS provider for this deployment is **Timeweb Cloud** (zone e.g.
`mishteam.site`).

## What is implemented

Records are entered and edited **manually** in the panel (no provider
auto-discovery / list-fetch). The `domains` table is a registry of the records
an operator intends to exist:

- Fields: `fqdn`, `record_type` (A / AAAA / CNAME / TXT / MX / NS), `value`
  (the record target), `ttl`, `active`, optional `publication_id` link.
- Server-side validation (`apps/backend/app/api/v1/dns.py`): `A` → IPv4, `AAAA`
  → IPv6, `CNAME` → hostname; `ttl` within 60…2592000s. Value may be empty so a
  record can be registered before its target is known.
- Full CRUD via `/api/v1/dns` and a create/edit/delete UI on the DNS page.

### How settings actually "apply"

Edge **routing and TLS** are rendered from **publications**, not from the
`domains` table (`app/services/config_renderer/traefik.py`):

- A publication carries `domain_or_sni`, `tls_enabled`, `tls_mode`,
  `path_prefix`, etc. The renderer emits a deterministic Traefik dynamic config
  and writes it to the file-provider dir, which Traefik hot-reloads.
- HTTPS terminates on the VPS; `tls_enabled` publications get
  `certResolver: letsencrypt`, so the certificate is requested automatically.

So a DNS record is the "name should resolve to the VPS" half; the publication
is the "VPS should route that name to a backend over the tunnel" half. Linking a
record to its publication keeps the two views consistent in the UI.

## Future option: push records to Timeweb (NOT implemented)

If we later want the control plane to create the records in DNS itself
(instead of an operator doing it in the Timeweb panel):

- Settings: `DNS_PROVIDER=timeweb`, `TIMEWEB_API_TOKEN` (secret, env-only),
  `DNS_ROOT_ZONE`.
- A `DnsProvider` seam (`list_records` / `upsert_record` / `delete_record`)
  with a `TimewebProvider` using `httpx` + retry/backoff against the Timeweb
  Cloud DNS API (bearer token). Persist the provider record id for idempotent
  update/delete.
- On create/update/delete of a `domains` row, mirror the change to Timeweb.
- Treat the token as a secret (env + `SecretMetadata`); never return it.

This is intentionally deferred — current scope is manual entry + correct
Traefik/TLS generation.
