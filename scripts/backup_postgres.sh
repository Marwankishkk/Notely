#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   DATABASE_URL=postgresql://... ./scripts/backup_postgres.sh
#   BACKUP_DIR=/var/backups/notely ./scripts/backup_postgres.sh

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT_DIR="${BACKUP_DIR:-./backups/postgres}"
mkdir -p "$OUT_DIR"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

FILE="$OUT_DIR/notely-$STAMP.dump"
pg_dump "$DATABASE_URL" --format=custom --file="$FILE"
echo "Wrote $FILE"

find "$OUT_DIR" -name 'notely-*.dump' -mtime +14 -delete
