# Self-hosted GitHub Actions runner (on the VPS)

The deploy pipeline runs on a **self-hosted runner installed on the VPS**, so
`deploy.yml` can drive `docker compose` directly against the production stack
without SSH.

## Why self-hosted on the VPS

- The runner already sits on the target host → no remote SSH orchestration.
- `docker compose pull/build/up` runs locally against the live stack.
- Standard, widely used pattern for compose-based single-host deployments.

## Install (summary)

1. Create a dedicated, unprivileged user and add it to the `docker` group:
   ```bash
   sudo useradd -m -s /bin/bash gh-runner
   sudo usermod -aG docker gh-runner
   ```
2. As `gh-runner`, download and configure the runner from the repo's
   **Settings → Actions → Runners → New self-hosted runner** page.
3. Install it as a service so it survives reboots:
   ```bash
   sudo ./svc.sh install gh-runner
   sudo ./svc.sh start
   ```
   See `infra/systemd/github-runner.service` for a reference unit + hardening.

## Security notes

- Do **not** run the runner as root.
- The runner user needs docker group membership; treat that as root-equivalent
  and keep the host locked down.
- Production secrets (`SECRET_KEY`, DB password, ACME email, etc.) are provided
  via **GitHub Secrets** and/or a server-managed `.env`, never committed.
- The docker socket is mounted **read-only** into Traefik.

## Required repository secrets / variables

`deploy.yml` expects these (configure under Settings → Secrets and variables):

- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `FIRST_SUPERADMIN_EMAIL`, `FIRST_SUPERADMIN_PASSWORD`
- `ACME_EMAIL`
- `PUBLIC_API_BASE_URL`
