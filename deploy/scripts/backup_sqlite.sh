#!/bin/sh
set -eu

DB_PATH="${SQLITE_PATH:-/data/my-cfo.db}"
BACKUP_DIR="${MY_CFO_BACKUP_DIR:-/backups}"
RETENTION="${MY_CFO_BACKUP_RETENTION:-30}"
KIND="${BACKUP_KIND:-daily}"

mkdir -p "$BACKUP_DIR/$KIND"

if [ ! -f "$DB_PATH" ]; then
  echo "database not found at $DB_PATH"
  exit 0
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="$BACKUP_DIR/$KIND/${KIND}-${STAMP}.db"

sqlite3 "$DB_PATH" ".backup '$TARGET'"
find "$BACKUP_DIR/$KIND" -name "${KIND}-*.db" -type f | sort -r | tail -n "+$((RETENTION + 1))" | xargs -r rm -f

echo "backup created: $TARGET"
