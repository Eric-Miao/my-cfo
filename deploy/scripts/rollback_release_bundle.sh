#!/bin/sh
set -eu

: "${MY_CFO_ENV_FILE:?MY_CFO_ENV_FILE is required}"
: "${MY_CFO_DATA_DIR:?MY_CFO_DATA_DIR is required}"
: "${MY_CFO_BACKUP_DIR:?MY_CFO_BACKUP_DIR is required}"

LATEST_BACKUP="$(find "$MY_CFO_BACKUP_DIR/predeploy" -name 'predeploy-*.db' -type f | sort | tail -n 1)"
if [ -z "$LATEST_BACKUP" ]; then
  echo "no predeploy backup found"
  exit 1
fi

docker compose --env-file "$MY_CFO_ENV_FILE" -f deploy/compose.prod.yaml down
mkdir -p "$MY_CFO_DATA_DIR"
cp "$LATEST_BACKUP" "$MY_CFO_DATA_DIR/my-cfo.db"
docker compose --env-file "$MY_CFO_ENV_FILE" -f deploy/compose.prod.yaml up -d
