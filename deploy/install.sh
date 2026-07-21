#!/bin/bash
# Первый деплой БИТ.Технолог на Beget
# Использование: bash install.sh
# Что делает:
#   1. Ставит системные пакеты (если есть apt)
#   2. Клонирует репо
#   3. Создаёт venv, ставит requirements
#   4. Создаёт .env из шаблона
#   5. Создаёт каталоги (drawings, .rag, backups)
#   6. Ставит supervisor unit
#   7. Стартует + health-check

set -e
APP_DIR="/opt/beget/bit-technolog"
REPO_URL="https://github.com/swzhukov/bit-technolog-prototype.git"

echo "=== [1/7] system packages ==="
if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y --no-install-recommends \
        python3.11 python3.11-venv python3-pip \
        sqlite3 libsqlite3-0 \
        libpng-dev libfreetype6-dev \
        supervisor nginx certbot python3-certbot-nginx \
        2>&1 | tail -5 || echo "WARN: some packages failed (may be already installed)"
fi

echo "=== [2/7] clone ==="
if [ ! -d "$APP_DIR" ]; then
    mkdir -p /opt/beget
    cd /opt/beget
    git clone "$REPO_URL" bit-technolog
fi
cd "$APP_DIR"

echo "=== [3/7] venv ==="
python3.11 -m venv venv 2>/dev/null || python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo "=== [4/7] .env ==="
if [ ! -f .env ]; then
    if [ -f /workspace/bit-technolog-deploy/.env.vps ]; then
        cp /workspace/bit-technolog-deploy/.env.vps .env
    elif [ -f .env.example ]; then
        cp .env.example .env
    fi
    chmod 600 .env
    echo "EDIT .env BEFORE STARTING:"
    echo "  nano $APP_DIR/.env"
    echo "Required: LLM_API_KEY, LLM_MODEL, LLM_API_URL"
    echo "Optional: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID"
fi

echo "=== [5/7] dirs ==="
mkdir -p drawings .rag backups
chmod 755 drawings .rag backups

echo "=== [6/7] supervisor unit ==="
if [ -d /etc/supervisor/conf.d ]; then
    cp /workspace/bit-technolog-deploy/supervisor-bit.conf /etc/supervisor/conf.d/bit-technolog.conf
    supervisorctl reread
    supervisorctl update
    supervisorctl start bit-technolog
else
    echo "WARN: /etc/supervisor/conf.d not found, install supervisor:"
    echo "  apt-get install -y supervisor"
    echo "Or start manually: bash $APP_DIR/serve.sh &"
fi

echo "=== [7/7] health check ==="
sleep 5
curl -s http://127.0.0.1:8081/health | head -3 || echo "WARN: health check failed"
echo
echo "=== INSTALL COMPLETE ==="
echo "App:     http://127.0.0.1:8081 (via nginx → http://\$IP:80)"
echo "Logs:    tail -f /var/log/bit-technolog.log"
echo "Restart: supervisorctl restart bit-technolog"
echo "Update:  cd $APP_DIR && bash /workspace/bit-technolog-deploy/deploy.sh"
