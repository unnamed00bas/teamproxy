#!/usr/bin/env bash
# Idempotent deploy script, executed ON THE SERVER (invoked over SSH by the
# GitHub Actions 'Deploy' workflow). Builds the stack, applies migrations, runs
# smoke checks and rolls back on critical failure. Safe to re-run by hand too.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# Point Compose at the repo-root .env for variable interpolation. By default
# Compose reads .env from the compose file's directory (infra/compose/), not the
# repo root where the rendered .env lives, so every ${VAR} in the compose files
# would silently fall back to its default (empty WGEASY_PASSWORD, localhost
# WG_HOST, placeholder ACME_EMAIL, etc.). --env-file makes interpolation read the
# real values. Per-service `env_file:` directives are unaffected.
COMPOSE="docker compose --env-file $REPO_ROOT/.env -f infra/compose/docker-compose.yml -f infra/compose/docker-compose.prod.yml"
# Share the exact compose invocation with healthcheck.sh.
export COMPOSE_CMD="$COMPOSE"
BACKUP_DIR="${BACKUP_DIR:-$REPO_ROOT/backups}"
TS="$(date +%Y%m%d-%H%M%S)"

log() { echo "[deploy $(date +%T)] $*"; }

# Read a single KEY=value from the rendered .env (last definition wins).
read_env() { sed -n "s/^$1=//p" "$REPO_ROOT/.env" 2>/dev/null | tail -n1; }

if [ ! -f "$REPO_ROOT/.env" ]; then
  log "CRITICAL: $REPO_ROOT/.env is missing. The production stack is configured entirely from it."
  exit 1
fi

# Fail fast on required settings before bringing the stack up — a stopped deploy
# is better than a broken or insecure one.
ADMIN_DOMAIN_VAL="$(read_env ADMIN_DOMAIN)"
ACME_EMAIL_VAL="$(read_env ACME_EMAIL)"
WGEASY_PASSWORD_VAL="$(read_env WGEASY_PASSWORD)"

# Empty ADMIN_DOMAIN renders the router rule as Host(``), which Traefik refuses
# to load — both routers drop, every request 404s, and ACME has no domain.
if [ -z "$ADMIN_DOMAIN_VAL" ]; then
  log "CRITICAL: ADMIN_DOMAIN is unset or empty. Set it in $REPO_ROOT/.env (e.g. ADMIN_DOMAIN=admin.example.com) — the admin panel cannot be routed without it."
  exit 1
fi

# Let's Encrypt rejects an unparseable or reserved contact address (example.com),
# which is exactly the "invalidContact / unable to parse email address" failure.
case "$ACME_EMAIL_VAL" in
  "" | *@example.com | *@example.org | *example*)
    log "CRITICAL: ACME_EMAIL is empty or a placeholder ('$ACME_EMAIL_VAL'). Set a real address in $REPO_ROOT/.env — Let's Encrypt rejects it otherwise and TLS certificates will not be issued."
    exit 1
    ;;
  *@*.*) : ;;
  *)
    log "CRITICAL: ACME_EMAIL ('$ACME_EMAIL_VAL') is not a valid email address. Fix it in $REPO_ROOT/.env."
    exit 1
    ;;
esac

# An empty wg-easy password leaves the admin panel open with no authentication.
if [ -z "$WGEASY_PASSWORD_VAL" ]; then
  log "CRITICAL: WGEASY_PASSWORD is unset or empty. Set it in $REPO_ROOT/.env — otherwise the wg-easy panel is reachable without a password."
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
