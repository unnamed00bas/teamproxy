#!/usr/bin/env bash
set -euo pipefail

# Apply database migrations before serving. Idempotent and safe to run on every
# container start; the first superadmin is seeded by the app lifespan hook.
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "[entrypoint] applying database migrations..."
  alembic upgrade head
fi

echo "[entrypoint] starting: $*"
exec "$@"
