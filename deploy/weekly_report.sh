#!/bin/bash
# V8-1: Простой weekly report (заглушка, т.к. pilot_report.py deprecated)
# Был старый Flask-стиль app.test_client() — больше не работает в FastAPI
# Этот скрипт просто пишет краткий отчёт в лог

set -e
cd /opt/beget/bit-technolog

DATE=$(date +%Y-%m-%d)
LOG="/var/log/bit-technolog-weekly.log"
echo "=== Weekly report $DATE ===" >> "$LOG"

/opt/beget/bit-technolog/venv/bin/python3 -c "
import sqlite3
c = sqlite3.connect('data/bit_technolog_v0_8.db')
print(f'Items: {c.execute(\"SELECT COUNT(*) FROM items\").fetchone()[0]}')
print(f'Tech cards: {c.execute(\"SELECT COUNT(*) FROM tech_cards\").fetchone()[0]}')
print(f'Etalons: {c.execute(\"SELECT COUNT(*) FROM etalons\").fetchone()[0]}')
print(f'Equipment: {c.execute(\"SELECT COUNT(*) FROM equipment\").fetchone()[0]}')
print(f'Notices: {c.execute(\"SELECT COUNT(*) FROM change_notices\").fetchone()[0]}')
print(f'History: {c.execute(\"SELECT COUNT(*) FROM history\").fetchone()[0]}')
" >> "$LOG" 2>&1
echo "=== Done ===" >> "$LOG"
