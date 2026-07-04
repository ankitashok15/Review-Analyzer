#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"

# Run migrations in the background so the API can start immediately (Railway healthcheck).
(
  echo "Running database migrations..."
  alembic upgrade head || echo "WARNING: Database migrations failed."
) &

echo "Starting API on port ${PORT}..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port "${PORT}"
