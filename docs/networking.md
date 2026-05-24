# Networking

## Topology

- The **VPS** has the public IP and terminates all external DNS + TLS.
- Each **site** runs a **gateway** that *initiates* a WireGuard tunnel out to
  the VPS hub (so sites can stay fully behind NAT — no inbound ports needed).
- The control plane manages peer metadata (keys, tunnel IPs, AllowedIPs, routes)
  and renders config; on stage one it does **not** drive the kernel/netlink
  directly.

```
site LAN 192.168.x.0/24
   │
   ▼ gateway (wg0)  ──encrypted──►  VPS hub (wg0, :51820)
                                       │
                                  Traefik (:80/:443)  ◄── internet
```

## Tunnel addressing

- Pick a tunnel subnet for the hub, e.g. `10.10.0.0/24`.
  - Hub: `10.10.0.1`
  - Site A gateway: `10.10.0.2`, Site B gateway: `10.10.0.3`, …
- On the hub, each site's `[Peer].AllowedIPs` lists the peer tunnel IP **plus**
  that site's local subnets so the VPS can reach backends inside the site.
- Backends are addressed by their **private IP reachable over the tunnel**
  (the `backend_host` on a service), e.g. `192.168.1.50:3000`.

## Key management

- `POST /api/v1/peers/{id}/rotate-keys` generates a Curve25519 keypair
  server-side and returns the private key + a ready `wg-quick` config **once**.
  Only the public key and a secret reference are persisted.
- Keys are standard `wg`-compatible (base64 of raw 32-byte X25519).

## Templates

- `infra/wireguard/templates/hub.conf.tmpl` — VPS hub interface + managed peer
  blocks.
- `infra/wireguard/templates/gateway.conf.tmpl` — per-site gateway.

## Edge routing (Traefik)

- **Entrypoints:** `web` (:80, redirects to https), `websecure` (:443),
  `traefik` (:8080 dashboard — restrict in prod).
- **Providers:** `file` (control-plane generated `control-plane.yml` + the
  shipped `base.yml`) and `docker` (infra services), running together.
- **HTTP publication →** `Host(domain) [&& PathPrefix(path)] → loadBalancer`.
- **TCP publication →** `HostSNI(sni)` router on a dedicated `tcp-<port>`
  entrypoint (architecture is in place; add the entrypoints to expose them).
- **UDP publication →** `udp-<port>` entrypoint router.
- **Maintenance mode** swaps in the `cp-maintenance` middleware (503).

## TLS

- HTTPS terminates on the VPS. Let's Encrypt via Traefik's `letsencrypt`
  resolver (HTTP-01 challenge on the `web` entrypoint).
- The `certificates` table tracks issuance status for the UI; ACME storage is
  the `letsencrypt` volume (`acme.json`).
