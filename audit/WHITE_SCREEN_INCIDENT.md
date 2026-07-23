# 🚨 WHITE SCREEN INCIDENT — RESOLVED (2026-07-23)

## Что произошло
Сергей зашёл на `http://217.114.7.5:8081/` (без https, на 8081) — белый экран.
Мои тесты: 200 OK + валидный HTML на `https://...:8081/`. Что не так?

## Диагноз
`uvicorn` слушал **только** `https://0.0.0.0:8081/`. HTTP (порт 8081) не обслуживался.
→ `curl http://217.114.7.5:8081/` → `ERR_EMPTY_RESPONSE` → браузер показывает **белый экран** без деталей.

Сергей не пробовал `https://...:8081/` явно — http:// — белый экран.

## Что я делал неправильно
1. Поднял `http_redirect.py` на **порте 8082** (потому что 8080 занят `newton-api.py` от n8n).
2. Не обновил деплой так, чтобы **8081** тоже работал как HTTP→HTTPS redirect.
3. Сергей зашёл на 8081 — белый экран — расстроился.

## Fix (v8.1.1, commit a60a970)
- `uvicorn` теперь на `8443` (https).
- `http_redirect.py` теперь на `8081` (http) → 301 → `https://...:8443/`.
- Схема:  
  ```
  217.114.7.5:8081 (http)  →  301 Moved Permanently  →  https://217.114.7.5:8443/
  217.114.7.5:8443 (https) →  uvicorn (рабочий endpoint)
  ```
- Сергей заходит на 8081 — **автоматически** попадает на 8443 (https).

## Verify
```bash
$ curl -sk -m 5 -i http://217.114.7.5:8081/ 
HTTP/1.0 301 Moved Permanently
Location: https://217.114.7.5:8443/

$ curl -sk -m 5 -i https://217.114.7.5:8443/health
HTTP/1.1 200 OK

$ curl -sk -m 5 -i -X POST -d "username=techadmin&password=demo" https://217.114.7.5:8443/login
HTTP/1.1 303 See Other
set-cookie: session_id=...
```

Playwright test (headless Chromium):
- `http://...:8081/` → redirect → `https://...:8443/login?next=/` (Title: "Вход — БИТ.Технолог")
- Login (techadmin/demo) → 200, "Мои задачи" (Title: "Мои задачи — БИТ.Технолог")
- Body: "Добрый день, коллега. Вы вошли как: techadmin"
- Скриншоты: `/workspace/v8_final.png`, `/workspace/v8_logged_in.png`

## Скриншоты

### v8_final.png — после redirect, login form
![v8_final](file:///workspace/v8_final.png) — login form "Вход", демо-учётки видны

### v8_logged_in.png — после логина, dashboard
![v8_logged_in](file:///workspace/v8_logged_in.png) — "Добрый день, коллега", статистика, извещения

## Что должен делать Сергей
**Просто зайди на `http://217.114.7.5:8081/` в инкогнито.**

Браузер покажет:
1. **Сертификат** — "Принять риск / Продолжить" (self-signed)
2. После accept: 301 redirect → `https://217.114.7.5:8443/`
3. **Снова** "Принять риск" (если сертификат хоста)
4. **Login form** — "Вход", "Введите логин и пароль"
5. Login `techadmin / demo` → дашборд "Мои задачи"

## Lessons
1. **Проверять своими руками** — не только curl, а реальный browser flow с http:// редиректом
2. **Когда http:// — белый экран** → сразу проверять `curl -v http://...:port/` и искать `Connection reset` / `Empty response`
3. **Redirect на другой порт** — плохо UX. Делать сразу на тот же порт
4. **Сергей имеет право** сразу злиться. Я должен был проверить ВСЕ варианты URL (http 8081, http 8082, https 8081, https 8443)

## Production state after fix
- HEAD: `a60a970` (v8.1.1)
- uvicorn workers=1, port 8443 (https)
- http_redirect port 8081 → https://...:8443
- systemd: `bit-technolog.service`, `bit-technolog-http-redirect.service`
- TR.py / UI_SMOKE / TECHNOLOGIST_SESSIONS — должны быть все зелёные
