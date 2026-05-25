# Automatic deployment (GitHub Actions → SSH → your server)

No self-hosted runner. The `Deploy` workflow runs on a GitHub-hosted runner
(`ubuntu-latest`), connects to your server over SSH, syncs the repo, and runs
`docker compose up -d --build` **on the server**. You just add a few
secrets/variables once.

## Flow

```
push to main
   │
   ▼ GitHub-hosted runner (ubuntu-latest)
   ├─ render .env from GitHub Secrets
   ├─ rsync repo  ──SSH──►  your server: $DEPLOY_PATH
   └─ ssh server: ./infra/scripts/deploy.sh
                         backup → build → migrate → up -d → smoke test → rollback on fail
```

## One-time server prep

```bash
# Docker Engine + Compose v2
curl -fsSL https://get.docker.com | sh

# A dedicated deploy user (member of docker group)
sudo useradd -m -s /bin/bash deployer
sudo usermod -aG docker deployer

# Open ports: 80/tcp, 443/tcp, and 51820/udp for the WireGuard hub
```

## Create an SSH deploy key

On your machine (or anywhere), generate a dedicated keypair — no passphrase:

```bash
ssh-keygen -t ed25519 -f deploy_key -N "" -C "github-actions-deploy"
```

- Put the **public** key on the server:
  ```bash
  ssh-copy-id -i deploy_key.pub deployer@YOUR_SERVER
  # or append deploy_key.pub to /home/deployer/.ssh/authorized_keys
  ```
- Put the **private** key (`deploy_key`, the whole file incl. BEGIN/END lines)
  into the GitHub secret `SSH_PRIVATE_KEY`.

## GitHub configuration

Repository → **Settings → Secrets and variables → Actions**.

### Secrets (sensitive)

| Secret | Example / meaning |
|--------|-------------------|
| `SSH_HOST` | server IP or hostname |
| `SSH_USER` | `deployer` |
| `SSH_PRIVATE_KEY` | contents of the `deploy_key` private key file |
| `SECRET_KEY` | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | strong DB password |
| `FIRST_SUPERADMIN_EMAIL` | first admin login |
| `FIRST_SUPERADMIN_PASSWORD` | first admin password |
| `ACME_EMAIL` | email for Let's Encrypt |
| `PUBLIC_API_BASE_URL` | e.g. `https://cp.example.com` |

### Variables (non-sensitive, optional — sensible defaults shown)

| Variable | Default |
|----------|---------|
| `SSH_PORT` | `22` |
| `DEPLOY_PATH` | `/opt/control-plane` |
| `ADMIN_DOMAIN` | _none_ — **required** for TLS; the panel's public hostname (e.g. `admin.mishteam.site`). Traefik uses it as the `Host()` matcher and the Let's Encrypt cert domain. If unset, the panel is served with a self-signed cert and browsers reject it. |

## Trigger

- Automatic: every push to `main`.
- Manual: Actions → **Deploy** → *Run workflow*.

Deploys are serialised (`concurrency: production-deploy`) so two pushes can't
race on the host.

## Notes

- Images are built **on the server** (`docker compose build`), so no container
  registry is needed. If you later prefer building on GitHub, push images to
  GHCR in CI and switch the server to `docker compose pull` — the compose files
  already name the services.
- The rendered `.env` is created on the GitHub runner from secrets, copied to
  the server, and only lives inside `$DEPLOY_PATH` (which `rsync --delete`
  keeps in sync). It is never committed.
- DNS (A-records → server IP) and the WireGuard hub/tunnels are set up once and
  are independent of the deploy pipeline (see `docs/networking.md`).
