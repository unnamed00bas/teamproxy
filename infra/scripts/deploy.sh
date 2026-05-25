#!/usr/bin/env bash
# Idempotent deploy script, executed ON THE SERVER (invoked over SSH by the
# GitHub Actions 'Deploy' workflow). Builds the stack, applies migrations, runs
# smoke checks and rolls back on critical failure. Safe to re-run by hand too.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

COMPOSE="docker compose -f infra/compose/docker-compose.yml -f infra/compose/docker-compose.prod.yml"
# Share the exact compose invocation with healthcheck.sh.
export COMPOSE_CMD="$COMPOSE"
BACKUP_DIR="${BACKUP_DIR:-$REPO_ROOT/backups}"
TS="$(date +%Y%m%d-%H%M%S)"

log() { echo "[deploy $(date +%T)] $*"; }

# Traefik builds the admin Host() matcher and Let's Encrypt cert domain from
# ADMIN_DOMAIN at compose-config time. Compose interpolation reads .env from the
# compose file's directory, not this repo root, so surface ADMIN_DOMAIN (and
# only it) into the shell — where interpolation always looks first — sourced
# from the rendered .env. Other vars stay on their compose defaults on purpose.
if [ -f "$REPO_ROOT/.env" ]; then
  ADMIN_DOMAIN="$(sed -n 's/^ADMIN_DOMAIN=//p' "$REPO_ROOT/.env" | tail -n1)"
  export ADMIN_DOMAIN
fi

# Fail fast on an empty domain. The prod overlay renders the router rules as
# Host(`${ADMIN_DOMAIN}`); an empty value produces the invalid rule Host(``),
# which Traefik refuses to load — so both routers are dropped, every request
# 404s, and ACME has no domain to request a certificate for. A broken outage is
# worse than a stopped deploy, so refuse to bring the stack up without it.
if [ -z "${ADMIN_DOMAIN:-}" ]; then
  log "CRITICAL: ADMIN_DOMAIN is unset or empty. Set it in $REPO_ROOT/.env (e.g. ADMIN_DOMAIN=admin.example.com) — the admin panel cannot be routed without it."
  exit 1
fi

# Fail closed on a missing wg-easy panel hash. wg-easy v14 gates the admin panel
# on PASSWORD_HASH; with no hash it serves the panel WITHOUT authentication. The
# hash is delivered to the container via .env.wgeasy (env_file). Refuse to ship
# an unprotected VPN admin panel — an open panel is worse than a stopped deploy.
WGEASY_HASH="$(sed -n 's/^PASSWORD_HASH=//p' "$REPO_ROOT/.env.wgeasy" 2>/dev/null | tail -n1)"
if [ -z "${WGEASY_HASH:-}" ]; then
  log "CRITICAL: PASSWORD_HASH is missing from $REPO_ROOT/.env.wgeasy — the wg-easy admin panel would be exposed without a password. Set the WGEASY_PASSWORD_HASH secret (bcrypt hash with each \$ doubled to \$\$); see .env.example."
  exit 1
fi

log "Backing up current dynamic configs and database…"
mkdir -p "$BACKUP_DIR"
"$REPO_ROOT/infra/scripts/backup.sh" || log "WARN: backup step reported an issue"

# Capture the currently running images so we can roll back.
PREV_BACKEND_IMAGE="$(docker compose -f infra/compose/docker-compose.yml images -q backend 2>/dev/null || true)"

log "Pulling base images and building app images…"
$COMPOSE pull --ignore-buildable-services || true
$COMPOSE build

log "Applying database migrations…"
$COMPOSE run --rm -e RUN_MIGRATIONS=0 backend alembic upgrade head

log "Recreating services…"
$COMPOSE up -d --remove-orphans

log "Waiting for backend health…"
if ! "$REPO_ROOT/infra/scripts/healthcheck.sh"; then
  log "CRITICAL: health check failed — rolling back."
  if [ -n "${PREV_BACKEND_IMAGE:-}" ]; then
    docker tag "$PREV_BACKEND_IMAGE" control-plane-backend:rollback || true
  fi
  $COMPOSE up -d --no-build || true
  exit 1
fi

log "Deploy succeeded."
