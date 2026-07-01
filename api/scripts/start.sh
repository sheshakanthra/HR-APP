#!/usr/bin/env bash
set -euo pipefail

echo "[start] waiting for database..."
python -m app.scripts.wait_for_db

echo "[start] running migrations..."
alembic upgrade head

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "[start] seeding database..."
  python -m app.seed || echo "[start] seed skipped/failed (non-fatal)"
  echo "[start] indexing published policies (downloads embedding model on first run)..."
  python -m app.scripts.ingest_policies || echo "[start] policy ingest skipped/failed (non-fatal)"
fi

echo "[start] launching API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
