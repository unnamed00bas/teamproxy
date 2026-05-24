#!/usr/bin/env bash
# Back up the database and the rendered dynamic configs.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

COMPOSE="docker compose -f infra/compose/docker-compose.yml"
BACKUP_DIR="${BACKUP_DIR:-$REPO_ROOT/backups}"
TS="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

POSTGRES_USER="${POSTGRES_USER:-control}"
POSTGRES_DB="${POSTGRES_DB:-control_plane}"

echo "[backup] dumping database -> $BACKUP_DIR/db-$TS.sql.gz"
$COMPOSE exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_DIR/db-$TS.sql.gz"

echo "[backup] archiving dynamic configs -> $BACKUP_DIR/dynamic-$TS.tar.gz"
$COMPOSE run --rm -T --no-deps backend tar -czf - -C /data/traefik dynamic \
  > "$BACKUP_DIR/dynamic-$TS.tar.gz" 2>/dev/null || echo "[backup] no dynamic configs yet"

# Retain last 14 backups of each kind.
ls -1t "$BACKUP_DIR"/db-*.sql.gz 2>/dev/null | tail -n +15 | xargs -r rm -f
ls -1t "$BACKUP_DIR"/dynamic-*.tar.gz 2>/dev/null | tail -n +15 | xargs -r rm -f

echo "[backup] done"
