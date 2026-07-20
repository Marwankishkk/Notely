#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   REDIS_URL=redis://localhost:6379/0 ./scripts/backup_redis.sh

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT_DIR="${BACKUP_DIR:-./backups/redis}"
mkdir -p "$OUT_DIR"

if [[ -z "${REDIS_URL:-}" ]]; then
  echo "REDIS_URL is required" >&2
  exit 1
fi

FILE="$OUT_DIR/dump-$STAMP.rdb"
redis-cli -u "$REDIS_URL" BGSAVE >/dev/null
# Give Redis a moment to finish SAVE on small instances
sleep 2
redis-cli -u "$REDIS_URL" --rdb "$FILE"
echo "Wrote $FILE"

find "$OUT_DIR" -name 'dump-*.rdb' -mtime +14 -delete
