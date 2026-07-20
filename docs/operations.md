# Operations: backups & monitoring

## Health check

`GET /health` returns database and Redis status:

```json
{ "status": "ok", "checks": { "database": "ok", "redis": "ok" } }
```

Point an uptime monitor (Better Stack, UptimeRobot, CloudWatch, etc.) at:

`https://your-api.example.com/health`

Alert when `status` is not `ok` or the endpoint is unreachable.

## Postgres backup

Daily logical backup (adjust connection URL and destination):

```bash
#!/usr/bin/env bash
set -euo pipefail

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT_DIR="${BACKUP_DIR:-./backups/postgres}"
mkdir -p "$OUT_DIR"

# Requires pg_dump matching your Postgres major version
pg_dump "$DATABASE_URL" --format=custom --file="$OUT_DIR/notely-$STAMP.dump"

# Keep 14 days
find "$OUT_DIR" -name 'notely-*.dump' -mtime +14 -delete
```

Restore:

```bash
pg_restore --clean --if-exists --dbname="$DATABASE_URL" backups/postgres/notely-YYYYMMDD.dump
```

On managed Postgres (RDS, Neon, Supabase, Railway), enable automated snapshots / PITR in the provider console and still keep an offsite `pg_dump` if you need portable copies.

## Redis backup

Dawwen uses Redis for rate limiting and refresh-token revocation. Prefer AOF or RDB snapshots:

```bash
#!/usr/bin/env bash
set -euo pipefail

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT_DIR="${BACKUP_DIR:-./backups/redis}"
mkdir -p "$OUT_DIR"

# Trigger a background save, then copy the dump (path depends on redis.conf)
redis-cli -u "$REDIS_URL" BGSAVE
sleep 2
redis-cli -u "$REDIS_URL" --rdb "$OUT_DIR/dump-$STAMP.rdb"
```

Losing Redis is recoverable (users re-login; rate-limit counters reset) but plan for it. On managed Redis, enable persistence + automated backups.

## Suggested schedule

| Job | Cadence |
|-----|---------|
| `/health` probe | every 1 minute |
| Postgres `pg_dump` | daily |
| Redis snapshot | daily (or provider continuous) |
| Restore drill | quarterly |

Store backups encrypted, off the app server, and test restore regularly.
