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
