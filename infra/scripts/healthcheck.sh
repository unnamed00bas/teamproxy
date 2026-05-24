#!/usr/bin/env bash
# Post-deploy smoke check. Not just "container alive" — it verifies the API
# actually answers. In production the backend has no published host port (only
# Traefik is exposed), so we probe from inside the container via compose exec.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# Reuse the same compose invocation as deploy.sh when provided.
COMPOSE="${COMPOSE_CMD:-docker compose -f infra/compose/docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
RETRIES="${HEALTH_RETRIES:-20}"
SLEEP="${HEALTH_SLEEP:-3}"

echo "[healthcheck] probing backend /readyz via 'compose exec'"
for i in $(seq 1 "$RETRIES"); do
  if $COMPOSE exec -T backend curl -fsS http://localhost:8000/readyz >/dev/null 2>&1; then
    echo "[healthcheck] backend ready after ${i} attempt(s)"
    exit 0
  fi
  sleep "$SLEEP"
done

echo "[healthcheck] backend did not become ready in time" >&2
exit 1
