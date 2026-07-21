# Деплой БИТ.Технолог на Beget VPS

**Дата:** 2026-07-19
**Сервер:** `seefeesnahurid.beget.app` (217.114.7.5)
**Путь на сервере:** `/opt/beget/bit-technolog/`
**Порт:** 8081 (Kapital на 8080, не пересекаемся)
**GitHub:** https://github.com/swzhukov/bit-technolog-prototype

## Структура

| Файл | Что |
|---|---|
| `install.sh` | Первый деплой: клонирует репо, ставит venv, supervisor, nginx |
| `deploy.sh` | Обновление из GitHub: pull + restart |
| `serve.sh` | Запуск uvicorn (использует supervisor) |
| `supervisor-bit.conf` | supervisor unit → `/etc/supervisor/conf.d/bit-technolog.conf` |
| `nginx-bit.conf` | nginx vhost → `/etc/nginx/sites-enabled/bit-technolog.conf` |
| `backup.sh` | cron: ежедневный бэкап БД + drawings + RAG |
| `.env.vps.example` | Шаблон .env для прода |

## Пошаговый деплой (после получения пароля)

### 0. Сохранить пароль (sandbox wipe переживёт)
```bash
# В /root/.mavis/secrets/beget_ssh:
printf '%s' 'СЕРГЕЙ_ДАСТ_ПАРОЛЬ' > /root/.mavis/secrets/beget_ssh
chmod 600 /root/.mavis/secrets/beget_ssh
```

### 1. SSH + sanity checks
```bash
/workspace/.vps-helper.sh "python3.11 --version; df -h /opt; free -h; uname -a"
/workspace/.vps-helper.sh "which supervisorctl; which nginx; which certbot"
/workspace/.vps-helper.sh "systemctl status supervisor --no-pager 2>&1 | head -3"
```

### 2. Залить файлы (с локалки)
```bash
scp /workspace/bit-technolog-deploy/install.sh root@seefeesnahurid.beget.app:/workspace/bit-technolog-deploy/
scp /workspace/bit-technolog-deploy/deploy.sh root@seefeesnahurid.beget.app:/workspace/bit-technolog-deploy/
scp /workspace/bit-technolog-deploy/serve.sh root@seefeesnahurid.beget.app:/workspace/bit-technolog-deploy/
scp /workspace/bit-technolog-deploy/supervisor-bit.conf root@seefeesnahurid.beget.app:/workspace/bit-technolog-deploy/
scp /workspace/bit-technolog-deploy/nginx-bit.conf root@seefeesnahurid.beget.app:/workspace/bit-technolog-deploy/
scp /workspace/bit-technolog-deploy/backup.sh root@seefeesnahurid.beget.app:/workspace/bit-technolog-deploy/
scp /workspace/bit-technolog-deploy/.env.vps.example root@seefeesnahurid.beget.app:/workspace/bit-technolog-deploy/
```

### 3. SSH + install
```bash
/workspace/.vps-helper.sh "bash /workspace/bit-technolog-deploy/install.sh"
```

### 4. Заполнить .env
```bash
/workspace/.velper.sh "nano /opt/beget/bit-technolog/.env"
# Заполнить LLM_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

### 5. Старт + verify
```bash
/workspace/.vps-helper.sh "supervisorctl restart bit-technolog"
/workspace/.vps-helper.sh "sleep 5; curl -s http://127.0.0.1:8081/health"
```

### 6. nginx + домен
**Без домена (пока IP):**
```bash
/workspace/.vps-helper.sh "cp /workspace/bit-technolog-deploy/nginx-bit.conf /etc/nginx/sites-enabled/bit-technolog.conf"
/workspace/.vps-helper.sh "nginx -t && systemctl reload nginx"
# Теперь: http://217.114.7.5/bit-technolog/  (НЕТ — у нас / на 8081 проксируется)
# Или: http://217.114.7.5:8081/ напрямую (если открыть 8081 в firewall)
```

**С поддоменом `bit.beget.tech` (бесплатно на Бегете):**
1. В панели Бегета: Домены → добавить `bit.beget.tech` (поддомен бесплатно)
2. DNS A-запись: `bit.beget.tech` → 217.114.7.5
3. certbot --nginx -d bit.beget.tech
4. Раскомментировать `server { listen 443 ... }` в `nginx-bit.conf`
5. nginx -t && systemctl reload nginx

## SSL (HTTPS)

**В России Cloudflare блокируется, поэтому план без него.**

**Для пилота 27 июля: HTTP без шифрования** (на порту 8081, доступ через IP-адрес VPS).
- Баранов/Голубев подключаются: `http://217.114.7.5:8081` (логин `user:pass` из Basic Auth)
- Безопасно для внутренней сети Техинкома
- ФИО/чертежи передаются по plain — это риск для production, но для пилота 3-5 человек внутри сети ок

**Если нужен HTTPS внутри РФ (3 варианта):**

| Вариант | Стоимость | Время | Подводные |
|---|---|---|---|
| **Nginx reverse proxy на VPS** | Бесплатно | 10 мин | Свой домен в зоне .ru, Let's Encrypt DNS-01 challenge |
| **VPN-туннель** (WireGuard) | Бесплатно | 30 мин | На каждом клиенте ставить WireGuard |
| **Самоподписанный сертификат** | Бесплатно | 5 мин | Браузер ругается, неудобно |

**Рекомендация для пилота:** пока `http://217.114.7.5:8081`. На production (после пилота) — WireGuard или nginx+Let's Encrypt с российским доменом.

## Backup
```bash
# Установить cron
echo "0 3 * * * /opt/beget/bit-technolog/backup.sh >> /var/log/bit-technolog-backup.log 2>&1" | crontab -
```

## Мониторинг
```bash
# Логи
tail -f /var/log/bit-technolog.log
tail -f /var/log/bit-technolog.err.log

# Restart
supervisorctl restart bit-technolog

# Health
curl -s http://127.0.0.1:8081/health | python3 -m json.tool
```

## Что НЕ встанет (out of scope)

- Watcher папки КОМПАС-3D (нужен on-premise у Техинкома)
- Прямая интеграция 1С:ERP через COM (только REST)
- DNS-имя для production (пока поддомен `bit.beget.tech` для пилота)

## Лимиты Beget shared VPS

- 5-10 ГБ диск (наша БД ~150 КБ + RAG ~1 МБ + drawings — следить)
- 1-2 ГБ RAM (uvicorn с workers=1 ест ~150 МБ — ок)
- 1-2 CPU ядра (sklearn TF-IDF на 100+ деталей — ок)
- Лимиты на исходящие API-запросы (YandexGPT — ок, Telegram — ок)
