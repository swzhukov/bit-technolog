# БИТ.Технолог

**AI-помощник технолога для ООО «ПК Техинком-Центр»** (производство пожарной техники).
Генерирует черновики техкарт по свойствам детали за 30-60 минут вместо 4-8 часов.

> **Рабочий релиз, пилот 27 июля 2026.**
> **Текущая версия:** 1.0.0, **122/122 теста passing** (78 unit + 44 e2e), развёрнут на Beget VPS.
> Архитектура: domain / gateways / services / repositories (clean architecture).

## Для кого это

| Кто | Что делает с системой | Документация |
|---|---|---|
| **Технолог** (рядовой) | Генерирует проект ТК, правит, отправляет на проверку | `docs/11-tehnolog-guide.md` |
| **Гл. технолог** | Утверждает, записывает в 1С, смотрит метрики | `docs/11-tehnolog-guide.md` |
| **Нач. цеха** | Утверждает как начальник, смотрит что в работе | `docs/11-tehnolog-guide.md` |
| **Tech admin** | Управляет LLM провайдерами, эталонной базой | `docs/12-admin-guide.md` |
| **LLM admin** | Назначает модели на задачи | `docs/12-admin-guide.md` |
| **Разработчик** (Mavis) | Развивает, фиксит баги, рефакторит | `docs/adr/0001-architecture.md` + `MISTAKES.md` + `CHANGELOG.md` |

**Ключевые принципы:**
- **On-premise** — данные не покидают завод (ГОЗ, оборонка)
- **1С:ERP ready** — XML ресурсные спецификации
- **Учится на правках** — каждая правка = сигнал для RAG
- **«Норма с доказательством»** — каждая норма имеет источник (ГОСТ / аналог / правило) + уверенность (светофор)

## Что это

Деталь от конструктора (материал, масса, шасси) → AI генерирует проект ТК:
- **Список операций** с оборудованием и временем (от РС-фабрики)
- **Указание источника** оценки (ГОСТ / аналог / правило) — **КИЛЛЕР-ФИЧА**
- **Светофор уверенности** (зелёный/жёлтый/красный) с топ-3 аналогами
- **Извещения по ГОСТ 2.503** — AI diff между версиями
- **Экспорт РС в 1С:ERP** (XML)
- **Метрики пилота** — b (время генерации) + c (% норм зелёного)

## Быстрый старт (production на Beget)

```
http://217.114.7.5:8081
```

1. `/login` → вход (cookie-сессии)
2. `/products` — список деталей (51 items, 14 эталонов)
3. `/detail/{id}` — карточка детали (5 табов: Операции/РС/Состав/Параметры/История)
4. `/metrics` — метрики пилота (b и c)

## Быстрый старт (локально)

```bash
cd /workspace/bit-technolog
source venv/bin/activate
PILOT_AUTH_DISABLED=true python app.py
```

Открыть `http://localhost:8080`.

## Тесты

```bash
source venv/bin/activate
PILOT_AUTH_DISABLED=true python -m pytest test/ -v
```

**Текущий статус:** **91/91 passing** (78 unit + 13 e2e Playwright).

## Архитектура (1.0.0)

Clean architecture, 4 слоя:

```
bit-technolog/
├── app.py                  (1028 строк, 28 routes, тонкий FastAPI)
├── domain/                 ← бизнес-логика
│   ├── llm_provider.py     (LLMProvider + 3 реализации)
│   ├── prompts.py          (8 специализированных промтов)
│   └── few_shot.py         (динамический few-shot)
├── gateways/               ← внешние интеграции
│   └── one_c_gateway.py    (OneCGateway + File + Http)
├── services/               ← прикладная логика
│   ├── auth.py            (5 ролей, Fernet)
│   ├── rs_factory.py      (РС-фабрика, 8 осей, детерминированная)
│   ├── rag.py             (RAG v2: TF-IDF + material/equipment)
│   ├── evidence.py        (светофор, топ-3 аналога)
│   ├── notices.py         (извещения по ГОСТ 2.503)
│   ├── tp_parser.py       (OCR → структурированный ТП)
│   ├── one_c_loader.py    (загрузка XML)
│   ├── generate_one_c_mock.py (эмуляция 1С:ERP)
│   ├── metrics.py         (Sprint 9: b и c)
│   └── text_utils.py      (синонимы, морфология, Jaccard)
├── repositories/db.py      (33 таблицы, generic CRUD)
├── migrations/001_init.sql
├── seeds/                  (6 seed скриптов)
├── templates/              (15 используемых Jinja2)
├── test/                   (91 pytest теста)
└── static/
```

## Возможности (1.0.0)

### Sprint 5-9 (после M34)
- ✅ **«Норма с доказательством»** — каждая операция имеет source (ГОСТ/аналог/правило) + confidence
- ✅ **RAG v2** — TF-IDF по эталонным ТП с бонусом material_id/equipment_id
- ✅ **Светофор** — зелёный/жёлный/красный + inline-edit для подтверждения
- ✅ **Топ-3 аналога** в карточке операции (обогащённые)
- ✅ **Извещения** end-to-end (ГОСТ 2.503) + AI diff
- ✅ **Эмуляция 1С:ERP** — 6 XML, 113 записей НСИ
- ✅ **Login-форма** + cookie-сессии + /settings для LLM ключа (Fernet)
- ✅ **HttpGateway** — заглушка для реального 1С:ERP
- ✅ **Метрики пилота** (Sprint 9) — b (время генерации ТК) + c (% норм зелёного)
- ✅ **Inline-edit** (Enter/Esc, автофокус, без prompt())
- ✅ **UI полировка** — Jinja фильтры `ru_level`, `ru_sourcing`

### РС-фабрика (8 осей, детерминированная)
1. `stage_resolution` — что в каждом этапе
2. `op_granularity` — насколько детально
3. `norms` — откуда берём нормы (ГОСТ/аналог/правило)
4. `materials` — ведомость материалов
5. `labor` — трудоёмкость
6. `nesting` — раскладка
7. `cooperation` — кооперация
8. `export_format` — формат вывода

### 5 ролей
- 👨‍🔧 Технолог
- 👑 Гл. технолог
- 🏭 Нач. цеха
- 🛡 Tech admin (LLM провайдеры, эталонная база)
- 🤖 LLM admin (назначения моделей)

### Безопасность
- **Cookie сессии** через `PILOT_USERS` (.env) или БД-pilot_users (bcrypt)
- **CSRF** через `PILOT_CSRF_ENABLED=true`
- **Fernet (AES-128 + HMAC)** для всех секретов в БД
- **WAL mode** SQLite с busy_timeout
- **Path traversal protection** при загрузке файлов
- **152-ФЗ** — audit_logins (compliance для ПДн)

## Ключевые эндпоинты

**Основные:**
- `GET /` — Dashboard (5 counters + tasks + извещения + метрики)
- `GET /products` — 51 items + поиск `?q=` + фильтр `?level=`
- `GET /detail/{id}` — карточка детали (5 табов: #ops, #rs, #bom, #params, #history)
- `GET /items/{id}/generate` + `POST` — генерация ТК
- `GET /notices` + `GET /notices/new` + `POST` — извещения по ГОСТ 2.503
- `GET /knowledge` — 14 эталонов (синтетические помечены)
- `GET /profiles` — 8 осей профиля
- `GET /llm-admin` — провайдеры + назначения
- `GET /settings` (admin) + `POST /settings/llm` (Fernet)
- `GET /login` + `POST /login` + `GET /logout`
- `GET /metrics` + `POST /metrics/record-green`
- `GET /health`

**API (JSON):**
- `POST /api/tech-cards/{id}/regenerate` — перегенерация
- `POST /api/tech-cards/{id}/approve` — утверждение (TC.is_approved=1)
- `POST /api/items/{id}/export-to-1c` — экспорт РС в 1С:ERP
- `GET /api/tech-cards/{id}/rs-preview?profile_code=default` — превью РС
- `GET /api/tech-cards/{id}/evidence` — доказательства норм
- `POST /api/operations/{id}/confirm?new_time=...` — подтверждение с inline

## Стек

- **Backend:** Python 3.11+ / FastAPI / SQLite (WAL mode)
- **Frontend:** Jinja2 + vanilla CSS (inline v8-brand) + server-side HTML
- **AI:** YandexGPT через OpenAI-совместимый SDK (или mock)
- **RAG:** собственный TF-IDF (без sklearn), cosine similarity, hybrid scoring
- **Security:** cookie Auth + Fernet (AES-128) + bcrypt
- **Deploy:** systemd + Beget VPS, backup cron 03:00
- **Тесты:** pytest + Playwright (91 теста)

## Учтено для России

- **YandexGPT** (российский LLM, не западный)
- **ГОСТ 3.1105-2011, 3.1702-79, 23594-79, 12.3.006-75, 25129-82** в промтах
- **ЕТС** коды профессий (19905 Сварщик, 19861 Электромонтажник)
- **Рубли** во всей экономике
- **on-premise архитектура** (можно развернуть у Техинкома)
- **152-ФЗ** — audit_logins
- **Без Cloudflare** (в РФ блокируется)
- **Без западных CDN** — всё локально
- **Beget** (российский хостинг)
- **Открытые либы** (MIT/BSD) — FastAPI, openai

## Структура

```
bit-technolog/
├── app.py                    # 1028 строк — FastAPI endpoints
├── domain/                   # бизнес-логика
├── gateways/                 # интеграции (1С, LLM)
├── services/                 # прикладная логика (10 файлов)
├── repositories/db.py        # 33 таблицы
├── migrations/               # SQL миграции
├── seeds/                    # seed скрипты
├── templates/                # 15 Jinja2 шаблонов
├── static/                   # inline CSS
├── test/                     # 91 pytest теста
├── check_all_buttons.py      # Playwright чекер
├── archive/                  # архив мёртвого кода (v0.4)
├── attachments/              # данные Техинкома (46 файлов, 12M)
│   └── INDEX.md              # описание каждого файла
├── deploy/                   # Beget деплой скрипты
└── docs/                     # документация (25 файлов)
    └── adr/                  # Architecture Decision Records
```

## Документация

Вся документация в [`docs/`](docs/README.md):
- [01-product-design.md](docs/01-product-design.md)
- [02-architecture.md](docs/02-architecture.md)
- [11-tehnolog-guide.md](docs/11-tehnolog-guide.md)
- [12-admin-guide.md](docs/12-admin-guide.md)
- [21-1.0.0-design.md](docs/21-1.0.0-design.md) — текущий
- [MISTAKES.md](MISTAKES.md) — извлечённые уроки
- [adr/](docs/adr/) — Architecture Decision Records

## Лицензия

Working release for «Первый БИТ» / «ПК Техинком-Центр».
Не для публичного распространения.

## Контакты

- **Разработка:** Mavis (AI-ассистент)
- **Заказчик:** Сергей Жуков
- **Завод:** ПК «Техинком-Центр» (Москва)

---

*Версия: 1.0.0. Дата: 2026-07-21. Тесты: 91/91. Pilot: 27 июля 2026.*
