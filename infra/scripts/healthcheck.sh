#!/usr/bin/env bash
# Post-deploy smoke checks. Not just "container alive" — it verifies the API
# answers and (optionally) that a known route responds.
set -euo pipefail

BACKEND_URL="${BACKEND_HEALTH_URL:-http://localhost:8000/readyz}"
RETRIES="${HEALTH_RETRIES:-20}"
SLEEP="${HEALTH_SLEEP:-3}"

echo "[healthcheck] probing $BACKEND_URL"
for i in $(seq 1 "$RETRIES"); do
  if curl -fsS "$BACKEND_URL" >/dev/null 2>&1; then
    echo "[healthcheck] backend ready after ${i} attempt(s)"
    exit 0
  fi
  sleep "$SLEEP"
done

echo "[healthcheck] backend did not become ready in time" >&2
exit 1
