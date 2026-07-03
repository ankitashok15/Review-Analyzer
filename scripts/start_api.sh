#!/usr/bin/env bash
set -euo pipefail

echo "Running database migrations..."
alembic upgrade head

PORT="${PORT:-8000}"
echo "Starting API on port ${PORT}..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port "${PORT}"
