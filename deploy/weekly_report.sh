#!/bin/bash
# V3-11: Еженедельный пилот-отчёт
# В cron: 0 9 * * 1 (каждый понедельник в 9:00)
#
# Генерирует отчёт за последние 7 дней и отправляет в Telegram (если настроен)

set -e
cd /opt/beget/bit-technolog

# Проверка: если Telegram настроен — отправить, иначе просто сохранить
TELEGRAM_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" /opt/beget/bit-technolog/.env 2>/dev/null | cut -d= -f2-)
TELEGRAM_CHAT=$(grep "^TELEGRAM_CHAT_ID=" /opt/beget/bit-technolog/.env 2>/dev/null | cut -d= -f2-)

# Генерация отчёта
REPORT_FILE="/tmp/pilot_report_$(date +%Y-%m-%d).md"
/opt/beget/bit-technolog/venv/bin/python3 -c "
import sys
sys.path.insert(0, '/opt/beget/bit-technolog')
import os
os.environ['PILOT_AUTH_DISABLED'] = 'true'
from app import app
from pilot_report import generate_pilot_report
with app.test_client() as c:
    pass  # just init
r = generate_pilot_report(days=7)
with open('$REPORT_FILE', 'w') as f:
    f.write(r['markdown'])
print(f'Report saved: $REPORT_FILE ({len(r[\"markdown\"])} chars)')
"

# Отправка в Telegram если настроен
if [ -n "$TELEGRAM_TOKEN" ] && [ -n "$TELEGRAM_CHAT" ]; then
    /opt/beget/bit-technolog/venv/bin/python3 -c "
import urllib.request, urllib.parse
with open('$REPORT_FILE') as f:
    text = f.read()
# Telegram limit = 4096 chars
if len(text) > 4000:
    text = text[:4000] + '\n... (урезано)'
url = f'https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage'
data = urllib.parse.urlencode({'chat_id': '$TELEGRAM_CHAT', 'text': text, 'parse_mode': 'HTML'}).encode()
try:
    req = urllib.request.Request(url, data=data)
    urllib.request.urlopen(req, timeout=10)
    print('Sent to Telegram')
except Exception as e:
    print(f'Telegram send failed: {e}')
"
else
    echo "Telegram not configured — report saved to $REPORT_FILE only"
fi

# Ротация: удалить отчёты старше 30 дней
find /tmp -name "pilot_report_*.md" -mtime +30 -delete 2>/dev/null || true

echo "[$(date)] Weekly report: $REPORT_FILE"
