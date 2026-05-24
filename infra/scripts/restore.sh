#!/usr/bin/env bash
# Restore the database from a gzipped pg_dump produced by backup.sh.
#   infra/scripts/restore.sh backups/db-20240101-120000.sql.gz
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

DUMP="${1:?usage: restore.sh <db-dump.sql.gz>}"
COMPOSE="docker compose -f infra/compose/docker-compose.yml"
POSTGRES_USER="${POSTGRES_USER:-control}"
POSTGRES_DB="${POSTGRES_DB:-control_plane}"

echo "[restore] restoring $DUMP into $POSTGRES_DB"
gunzip -c "$DUMP" | $COMPOSE exec -T db psql -U "$POSTGRES_USER" "$POSTGRES_DB"
echo "[restore] done"
