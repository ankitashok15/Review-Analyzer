#!/usr/bin/env bash
set -euo pipefail

echo "Running database migrations..."
if ! alembic upgrade head; then
  echo "WARNING: Database migrations failed. Starting API anyway."
fi

PORT="${PORT:-8000}"
echo "Starting API on port ${PORT}..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port "${PORT}"
