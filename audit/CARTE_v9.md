# 🗺️ CARTE v9 — Карта prod-системы БИТ.Технолог (2026-07-23)

## 🌐 Production URLs

| URL | Описание |
|-----|----------|
| **`https://seefeesnahurid.beget.app/bit-technolog/`** | **PROD (основной)** — Let's Encrypt, Docker |
| ~~`https://217.114.7.5:8081/`~~ | ❌ DEPRECATED — IP+self-signed, Kaspersky режет |
| ~~`http://217.114.7.5:8082/`~~ | ❌ DEPRECATED — IP+http, нестандартный порт |

## 🏗️ Архитектура (v9)

```
                    Internet (https://...)
                            |
                ┌───────────▼────────────┐
                │  Traefik 3.6.5 (443)   │
                │  - Let's Encrypt       │
                │  - PathPrefix rules    │
                └───────────┬────────────┘
                            │
                ┌───────────┴────────────┐
                │                        │
       ┌────────▼─────────┐    ┌─────────▼─────────┐
       │ bit-technolog    │    │ n8n-n8n-1         │
       │ :8081 (Docker)   │    │ :5678 (Docker)    │
       │ FastAPI+uvicorn  │    │                   │
       │ root_path=/bt    │    │                   │
       └────────┬─────────┘    └─────────┬─────────┘
                │                        │
       ┌────────▼─────────┐    ┌─────────▼─────────┐
       │ /opt/beget/bit-  │    │ n8n-postgres      │
       │ technolog/       │    │ n8n-redis         │
       │ - data/app.db    │    └───────────────────┘
       │ - .master_key    │
       │ - .env (LLM)     │
       │ - seed/          │
       │ - attachments/   │
       │ - templates/     │
       │ - static/        │
       └──────────────────┘
```

## 📦 Docker

- **Image:** `bit-technolog:1.0.0`
- **Container:** `bit-technolog` (healthy)
- **Networks:** `n8n_net` (external)
- **Volumes:**
  - `/opt/beget/bit-technolog/data:/app/data:rw` — БД SQLite
  - `/opt/beget/bit-technolog/.master_key:/app/.master_key:rw` — Fernet
  - `/opt/beget/bit-technolog/.env:/app/.env:ro` — LLM
  - `/opt/beget/bit-technolog/seed:/app/seed:ro` — workshop_context.md
  - `/opt/beget/bit-technolog/attachments:/app/attachments:ro` — Техинком
  - `/opt/beget/bit-technolog/templates:/app/templates:rw` — Jinja2 (live reload)
  - `/opt/beget/bit-technolog/static:/app/static:ro` — CSS/JS

## 🔐 Traefik Labels

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.bt.rule=Host(`seefeesnahurid.beget.app`) && PathPrefix(`/bit-technolog`)"
  - "traefik.http.routers.bt.entrypoints=websecure"
  - "traefik.http.routers.bt.tls=true"
  - "traefik.http.routers.bt.tls.certresolver=mytlschallenge"
  - "traefik.http.routers.bt.middlewares=bt-strip"
  - "traefik.http.middlewares.bt-strip.stripprefix.prefixes=/bit-technolog"
  - "traefik.http.services.bt.loadbalancer.server.port=8081"
```

## 📡 Endpoints (42 + 4 новых)

### Public (no auth)
- `GET /health` — health check (JSON)
- `GET /login` — login form
- `POST /login` — login (CSRF: X-Requested-With или Origin)
- `GET /logout` — logout

### Authenticated (any role)
- `GET /` — dashboard
- `GET /products` — список деталей
- `GET /products?level=...&q=...` — фильтры
- `GET /detail/{id}` — карточка детали
- `GET /notices` — извещения
- `GET /notices/{id}` — карточка извещения
- `GET /notices/new` — форма создания
- `POST /notices/new` — создание
- `GET /knowledge` — база знаний
- `GET /help` — помощь
- `GET /rs` — выгрузка РС
- `GET /details/new` — форма создания детали
- `POST /details/new` — создание детали

### Admin / Main Tech
- `GET /settings` — настройки
- `GET /llm-admin` — LLM провайдеры
- `GET /metrics` — метрики
- `GET /profiles` — профили
- `GET /audit` — журнал аудита (3 таба: logins, history, llm)
- `GET /audit?tab=logins&user=...&date_from=...&date_to=...&limit=...`
- `GET /audit?tab=history&...`
- `GET /audit?tab=llm&...`

### API
- `GET /api/rs/list` — список XML
- `GET /api/rs/download/{filename}` — скачать XML
- `POST /api/items/{id}/export-to-1c` — экспорт в 1С
- `POST /api/operations/{id}/update` — inline-edit (field: name|time_per_unit_min|workshop_id|...)
- `POST /api/operations/{id}/confirm` — подтвердить норму
- `POST /api/tech-cards/{id}/approve` — утвердить ТК
- `GET /api/tech-cards/{id}/diff` — diff версий
- `POST /api/change-notices/{id}/process` — решение (accept_ai|manual_review|reject)

## 🗄️ БД (33 таблицы, 177 items)

```
items: 177
etalons: 19
tech_cards: 49
equipment: 57
operations: 231
resource_specs: 96
change_notices: 99
materials: 18
professions: 12
workshops: 5
history: 597
edits: 349
llm_calls: 261
audit_logins: 5206
sessions: 1635
pilot_metrics: 209
pilot_runs: 3
pilot_users: 6
```

## 👥 Пользователи (6 demo)

| Login | Роль | Права |
|-------|------|-------|
| `techadmin` | admin | всё |
| `llmadmin` | admin | LLM-управление |
| `vorobyev` | main_technologist | создание, approve, извещения |
| `baranov` | main_technologist | создание, approve, извещения |
| `tarrietsky` | technologist | создание, без approve |
| `golubev` | workshop_chief | read-only |

Пароль для всех: `demo`

## 🔄 Rollback (если что-то не так)

```bash
ssh root@seefeesnahurid.beget.app
cd /opt/beget/bit-technolog
docker compose down
systemctl start bit-technolog
# → вернётся старый URL https://217.114.7.5:8081/
```

## 📊 Тесты (v9+v10 = 42/42 + 0 + 0)

| Suite | Результат |
|-------|-----------|
| `TR.py` | 42/42 ✅ (A11 теперь dynamic) |
| `UI_SMOKE.py` | 0 замечаний |
| `TECHNOLOGIST_SESSIONS.py` | 0 замечаний |
