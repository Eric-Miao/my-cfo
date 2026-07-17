#!/bin/sh
set -eu

: "${MY_CFO_ENV_FILE:?MY_CFO_ENV_FILE is required}"
: "${MY_CFO_BACKUP_DIR:?MY_CFO_BACKUP_DIR is required}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"

BACKUP_KIND="${BACKUP_KIND:-predeploy}"
export BACKUP_KIND

docker compose --env-file "$MY_CFO_ENV_FILE" -f deploy/compose.prod.yaml --profile backup run --rm backup
docker compose --env-file "$MY_CFO_ENV_FILE" -f deploy/compose.prod.yaml pull
docker compose --env-file "$MY_CFO_ENV_FILE" -f deploy/compose.prod.yaml up -d

echo "$IMAGE_TAG" > "$MY_CFO_BACKUP_DIR/last-image-tag.txt"
