#!/usr/bin/env bash
set -euo pipefail

APP_CONTAINER="clo835-app"
DB_CONTAINER="clo835-mysql"
NETWORK="clo835-net"

docker rm -f "$APP_CONTAINER" "$DB_CONTAINER" >/dev/null 2>&1 || true
docker network rm "$NETWORK" >/dev/null 2>&1 || true

echo "Stopped local containers and removed network."
