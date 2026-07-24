#!/bin/bash
# Применить все миграции (idempotent — CREATE IF NOT EXISTS)
set -e
DB="${1:-/app/data/bit_technolog_v0_8.db}"

for f in /app/migrations/*.sql; do
    echo "Applying $f..."
    sqlite3 "$DB" < "$f" || true
done
echo "All migrations applied"
