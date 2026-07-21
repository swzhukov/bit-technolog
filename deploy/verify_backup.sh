#!/bin/bash
# V5-1: Проверка backup — restore в /tmp и integrity_check
# Запускать ПОСЛЕ backup (например, 0 4 * * * — через час после backup в 3:00)
# Если ошибка — алерт в лог (можно подключить Telegram)

set -e
BACKUP_DIR="/opt/beget/backups/bit-technolog"
LATEST_DB=$(ls -t "$BACKUP_DIR"/db-*.db 2>/dev/null | head -1)

if [ -z "$LATEST_DB" ]; then
    echo "[$(date)] ERROR: no backup db found in $BACKUP_DIR"
    exit 1
fi

# Restore в /tmp
TEST_DB="/tmp/backup_verify_$(basename $LATEST_DB)"
cp "$LATEST_DB" "$TEST_DB"

# Проверка через Python sqlite3
RESULT=$(/opt/beget/bit-technolog/venv/bin/python3 -c "
import sqlite3
import sys
try:
    conn = sqlite3.connect('$TEST_DB')
    # integrity_check
    ic = conn.execute('PRAGMA integrity_check').fetchone()[0]
    if ic != 'ok':
        print(f'FAIL: integrity_check={ic}')
        sys.exit(1)
    # Считаем ключевые таблицы
    n_details = conn.execute('SELECT COUNT(*) FROM details').fetchone()[0]
    n_drafts = conn.execute('SELECT COUNT(*) FROM drafts').fetchone()[0]
    n_users = conn.execute('SELECT COUNT(*) FROM pilot_users').fetchone()[0]
    print(f'OK: integrity=ok, details={n_details}, drafts={n_drafts}, users={n_users}')
    conn.close()
except Exception as e:
    print(f'FAIL: {e}')
    sys.exit(2)
")
RC=$?
rm -f "$TEST_DB"

echo "[$(date)] Verify: $LATEST_DB → $RESULT"
exit $RC
