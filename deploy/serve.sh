#!/bin/bash
# БИТ.Технолог — production start script
# Запускает FastAPI через uvicorn на 127.0.0.1:8081
# Используется supervisord (см. supervisor-bit.conf)

set -e
cd /opt/beget/bit-technolog

# Подгружаем .env (БЕЗ echo в логи)
set -a
source .env
set +a

# Активируем venv
source venv/bin/activate

# Запуск
exec uvicorn app:app \
    --host 127.0.0.1 \
    --port 8081 \
    --workers 1 \
    --no-access-log \
    --log-level info \
    --proxy-headers \
    --forwarded-allow-ips="127.0.0.1"
