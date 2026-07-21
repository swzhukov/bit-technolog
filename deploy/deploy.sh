#!/bin/bash
# Деплой БИТ.Технолог из GitHub
# Использование: bash deploy.sh
# Что делает:
#   1. git pull (если есть remote)
#   2. Проверяет/создаёт venv
#   3. Устанавливает/обновляет requirements
#   4. Миграция .env из .env.example (если нужно)
#   5. supervisorctl restart (если supervisor настроен)
#   6. Health-check

set -e
cd /opt/beget/bit-technolog

echo "=== [1/6] git pull ==="
if [ -d .git ]; then
    git pull origin main
else
    echo "NOT a git repo — clone first:"
    echo "  cd /opt/beget && git clone https://github.com/swzhukov/bit-technolog-prototype.git bit-technolog"
    exit 1
fi

echo "=== [2/6] venv ==="
if [ ! -d venv ]; then
    python3.11 -m venv venv || python3 -m venv venv
fi
source venv/bin/activate

echo "=== [3/6] requirements ==="
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo "=== [4/6] .env check ==="
if [ ! -f .env ] && [ -f .env.example ]; then
    echo "WARNING: .env missing, copying from .env.example"
    echo "EDIT IT BEFORE RESTART: nano /opt/beget/bit-technolog/.env"
    cp .env.example .env
    chmod 600 .env
fi

echo "=== [5/6] dirs ==="
mkdir -p drawings .rag backups

echo "=== [6/6] restart ==="
if command -v supervisorctl &> /dev/null; then
    supervisorctl restart bit-technolog 2>&1 || supervisorctl update
    sleep 3
    echo "=== health check ==="
    curl -s http://127.0.0.1:8081/health || echo "WARN: health check failed"
else
    echo "supervisorctl not found — manual start:"
    echo "  bash serve.sh &"
fi

echo "=== DONE ==="
