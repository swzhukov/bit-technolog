#!/bin/bash
# V6-3: Бэкап с шифрованием через gpg (Fernet-ключ шифрует .env-производный пароль)
# В cron: 0 3 * * * /opt/beget/bit-technolog/backup.sh >> /var/log/bit-technolog-backup.log 2>&1

set -e
cd /opt/beget/bit-technolog

BACKUP_DIR="/opt/beget/backups/bit-technolog"
DATE=$(date +%Y-%m-%d_%H%M)
KEEP_DAYS=14
# V6-3: gpg-ключ для шифрования (опционально). Если нет — backup без шифрования.
GPG_RECIPIENT="${BACKUP_GPG_RECIPIENT:-}"
USE_GPG="false"
if command -v gpg &> /dev/null && [ -n "$GPG_RECIPIENT" ]; then
    USE_GPG="true"
    echo "[$DATE] GPG encryption enabled (recipient: $GPG_RECIPIENT)"
fi

mkdir -p "$BACKUP_DIR"

# 1. БД (через Python sqlite3 .backup — если sqlite3 CLI недоступен)
if command -v sqlite3 &> /dev/null; then
    sqlite3 bit_technolog.db ".backup '$BACKUP_DIR/db-$DATE.db'"
else
    /opt/beget/bit-technolog/venv/bin/python3 -c "
import sqlite3
src = sqlite3.connect('bit_technolog.db')
dst = sqlite3.connect('$BACKUP_DIR/db-$DATE.db')
with dst:
    src.backup(dst)
src.close()
dst.close()
print('db backup done via python sqlite3')
"
fi

# V6-3: шифрование БД если gpg доступен
if [ "$USE_GPG" = "true" ] && [ -f "$BACKUP_DIR/db-$DATE.db" ]; then
    gpg --batch --yes --trust-model always -e -r "$GPG_RECIPIENT" \
        "$BACKUP_DIR/db-$DATE.db" 2>/dev/null
    rm -f "$BACKUP_DIR/db-$DATE.db"  # удаляем нешифрованный
    echo "[$DATE] db encrypted"
fi

# 2. RAG-индекс (pickle) — содержит embeddings, шифруем если gpg есть
if [ -d .rag ]; then
    tar czf "$BACKUP_DIR/rag-$DATE.tar.gz" .rag/
    if [ "$USE_GPG" = "true" ]; then
        gpg --batch --yes --trust-model always -e -r "$GPG_RECIPIENT" \
            "$BACKUP_DIR/rag-$DATE.tar.gz" 2>/dev/null
        rm -f "$BACKUP_DIR/rag-$DATE.tar.gz"
    fi
fi

# 3. Чертежи
if [ -d drawings ]; then
    tar czf "$BACKUP_DIR/drawings-$DATE.tar.gz" drawings/
    if [ "$USE_GPG" = "true" ]; then
        gpg --batch --yes --trust-model always -e -r "$GPG_RECIPIENT" \
            "$BACKUP_DIR/drawings-$DATE.tar.gz" 2>/dev/null
        rm -f "$BACKUP_DIR/drawings-$DATE.tar.gz"
    fi
fi

# 4. .env (всегда шифруем — содержит LLM ключ!)
if [ -f .env ]; then
    cp .env "$BACKUP_DIR/env-$DATE"
    if [ "$USE_GPG" = "true" ]; then
        gpg --batch --yes --trust-model always -e -r "$GPG_RECIPIENT" \
            "$BACKUP_DIR/env-$DATE" 2>/dev/null
        rm -f "$BACKUP_DIR/env-$DATE"
    fi
fi

# Удалить старое (KEEP_DAYS дней)
find "$BACKUP_DIR" -type f -mtime +$KEEP_DAYS -delete

echo "[$DATE] Backup complete: $(ls -la $BACKUP_DIR 2>/dev/null | wc -l) files (encryption: $USE_GPG)"
