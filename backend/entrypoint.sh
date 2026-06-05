#!/bin/sh
set -e

echo "Waiting for database..."
until pg_isready -h "$(echo $DATABASE_URL | sed 's/.*@//' | sed 's/:.*//' | sed 's/\/.*//')" -U "$(echo $DATABASE_URL | sed 's/.*:\/\///' | sed 's/:.*//')"; do
  sleep 1
done

echo "Running migrations..."
alembic upgrade head

echo "Starting API..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
