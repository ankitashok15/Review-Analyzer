#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
if [[ ! "$PORT" =~ ^[0-9]+$ ]]; then
  echo "Invalid PORT='$PORT', defaulting to 8000"
  PORT=8000
fi

# Skip migrations on Railway (Neon already migrated); run locally via: alembic upgrade head
if [ -z "${RAILWAY_SERVICE_ID:-}" ] && [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  (
    echo "Running database migrations..."
    alembic upgrade head || echo "WARNING: Database migrations failed."
  ) &
fi

echo "Starting API on port ${PORT}..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port "${PORT}"
