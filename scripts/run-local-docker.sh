#!/usr/bin/env bash
set -euo pipefail

APP_IMAGE="clo835-app:local"
DB_IMAGE="clo835-mysql:local"
APP_CONTAINER="clo835-app"
DB_CONTAINER="clo835-mysql"
NETWORK="clo835-net"

DB_PORT="${DB_PORT:-3306}"
APP_PORT="${APP_PORT:-81}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-pw}"
DB_NAME="${DB_NAME:-employees}"
APP_COLOR="${APP_COLOR:-lime}"
MY_NAME="${MY_NAME:-Group 9}"

echo "[1/6] Building MySQL image..."
docker build -t "$DB_IMAGE" ./clo835-app/mysql

echo "[2/6] Building app image..."
docker build -t "$APP_IMAGE" ./clo835-app/app

echo "[3/6] Preparing docker network..."
docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK" >/dev/null

echo "[4/6] Cleaning old containers (if any)..."
docker rm -f "$DB_CONTAINER" "$APP_CONTAINER" >/dev/null 2>&1 || true

echo "[5/6] Starting MySQL container..."
docker run -d \
  --name "$DB_CONTAINER" \
  --network "$NETWORK" \
  -p "${DB_PORT}:3306" \
  -e MYSQL_ROOT_PASSWORD="$DB_ROOT_PASSWORD" \
  -e MYSQL_DATABASE="$DB_NAME" \
  "$DB_IMAGE" >/dev/null

echo "Waiting for MySQL to be ready..."
for i in {1..30}; do
  if docker exec "$DB_CONTAINER" mysqladmin ping -uroot -p"$DB_ROOT_PASSWORD" --silent >/dev/null 2>&1; then
    echo "MySQL is ready."
    break
  fi

  if [[ "$i" -eq 30 ]]; then
    echo "MySQL did not become ready in time."
    docker logs "$DB_CONTAINER" --tail 80 || true
    exit 1
  fi

  sleep 2
done

echo "[6/6] Starting app container..."
docker run -d \
  --name "$APP_CONTAINER" \
  --network "$NETWORK" \
  -p "${APP_PORT}:81" \
  -e DBHOST="$DB_CONTAINER" \
  -e DBUSER=root \
  -e DBPWD="$DB_ROOT_PASSWORD" \
  -e DATABASE="$DB_NAME" \
  -e DBPORT=3306 \
  -e APP_COLOR="$APP_COLOR" \
  -e MY_NAME="$MY_NAME" \
  "$APP_IMAGE" >/dev/null

echo
echo "Local test environment is running."
echo "App URL: http://localhost:${APP_PORT}"
echo
echo "Useful commands:"
echo "  docker logs -f ${APP_CONTAINER}"
echo "  docker logs -f ${DB_CONTAINER}"
echo "  ./scripts/stop-local-docker.sh"
