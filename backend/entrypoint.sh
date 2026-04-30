#!/bin/sh
set -e

# If arguments were passed (e.g. celery ...), run them directly
if [ "$#" -gt 0 ]; then
  exec uv run "$@"
fi

echo "Running Alembic migrations..."
uv run alembic upgrade head

echo "Starting Uvicorn..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
