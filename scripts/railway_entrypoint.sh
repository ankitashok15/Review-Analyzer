#!/bin/sh
set -e

# Railway injects PORT; never hardcode. Empty PORT breaks healthchecks.
port="${PORT:-8000}"
case "$port" in
  ''|*[!0-9]*)
    echo "Invalid PORT='$PORT', defaulting to 8000"
    port=8000
    ;;
esac

echo "Railway entrypoint: binding 0.0.0.0:${port}"
exec uvicorn src.api.main:app --host 0.0.0.0 --port "$port"
