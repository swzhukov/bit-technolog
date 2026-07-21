#!/bin/bash
# V7-7: Health check — опрос /health каждые 5 минут, алерт если degraded
# В cron: */5 * * * * /opt/beget/bit-technolog/health_check.sh >> /var/log/bit-technolog-health.log 2>&1

set -e
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8081/health}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

# Запрос
RESPONSE=$(curl -s -w '\n%{http_code}' "$HEALTH_URL" 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

# Проверка
if [ "$HTTP_CODE" != "200" ]; then
    MSG="🚨 [БИТ.Технолог] /health вернул HTTP $HTTP_CODE (ожидался 200)"
    echo "[$(date)] $MSG"
    # Алерт в Telegram
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d "chat_id=$TELEGRAM_CHAT_ID" -d "text=$MSG" > /dev/null 2>&1
    fi
    exit 1
fi

# Парсим JSON (если есть python)
ALERTS=$(echo "$BODY" | /opt/beget/bit-technolog/venv/bin/python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    alerts = []
    if d.get('status') != 'ok':
        alerts.append(f\"status={d.get('status')}\")
    if not d.get('db_ok', True):
        alerts.append(f\"db_ok=false, error={d.get('db_error', '')[:50]}\")
    # Cost anomaly
    ca = d.get('cost_anomaly', {})
    if not ca.get('ok', True):
        for a in ca.get('anomalies', []):
            alerts.append(f\"cost: {a}\")
    if alerts:
        print(' | '.join(alerts))
    else:
        print('OK')
except Exception as e:
    print(f'PARSE_ERROR: {e}')
" 2>/dev/null)

if [ "$ALERTS" != "OK" ] && [ -n "$ALERTS" ]; then
    MSG="⚠️ [БИТ.Технолог] /health alerts: $ALERTS"
    echo "[$(date)] $MSG"
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d "chat_id=$TELEGRAM_CHAT_ID" -d "text=$MSG" > /dev/null 2>&1
    fi
    exit 1
fi

echo "[$(date)] health=OK"
exit 0
