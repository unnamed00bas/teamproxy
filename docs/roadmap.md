# Roadmap

## MVP (this repository)

- [x] Monorepo + Docker Compose (dev + prod)
- [x] Auth (JWT) + RBAC (superadmin/operator/viewer)
- [x] CRUD: sites, peers, nodes, services, publications, DNS
- [x] WireGuard keypair generation + config templates (private key shown once)
- [x] Deterministic Traefik dynamic-config rendering
- [x] Config revisions, checksum, diff, preview, conflict detection
- [x] Apply (atomic write → hot reload) + rollback
- [x] Health checks (HTTP/TCP) + dashboard + audit log
- [x] Celery worker/beat (health sweeps, peer staleness, periodic render)
- [x] CI (lint/test/build) + CD via GitHub Actions over SSH (build/run on server)
- [x] Docs + `.env.example` + backup/restore scripts

## Already scaffolded, ready to extend

- TCP/UDP publications (data model + renderer support exist; expose Traefik
  `tcp-<port>` / `udp-<port>` entrypoints and add the UI form).
- Config revisions + dry-run + maintenance mode (wired end-to-end).

## V2

- **DNS provider integration** (Cloudflare/Route53 APIs) instead of a manual
  registry.
- **Secrets via Vault/SOPS**; store WireGuard private keys in a real vault
  referenced by `private_key_ref`.
- **Live WireGuard reconciliation** (netlink / `wg` syncconf, or wg-portal API
  behind our interface) to read real handshake/transfer stats.
- **Full TCP/UDP publish UI** (SSH, RDP, Postgres, MQTT, gRPC…).
- **Service templates / presets** (Grafana, n8n, Gitea, MinIO, SSH, Postgres).
- **Policy engine** + temporary/time-boxed access grants.
- **Multi-VPS edge clusters** + federation between edges.
- **Site agent** for auto-discovery of nodes/services.
- **Notifications** (Telegram): deploy failed, site offline, peer stale,
  cert expiring.
- **Normalized tags** (`tags` + `service_tags` tables) replacing JSON arrays.
- **SSO / OIDC** for admin login.
- **Generated TypeScript client** from the OpenAPI schema (replacing the
  hand-written `packages/shared-types`).
