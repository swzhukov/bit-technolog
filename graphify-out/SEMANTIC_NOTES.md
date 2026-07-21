# SEMANTIC_NOTES — обогащение knowledge graph моими словами

> Написано Mavis 2026-07-21. Это **семантический слой** над AST-графом graphify.
> Graphify даёт связи (кто кого вызывает), я даю **смысл** (зачем, как работает, на что обратить внимание).
> Читать после `GRAPH_REPORT.md` — сначала граф, потом мои заметки.

## Главные модули (что есть в проекте)

### `app.py` (5000+ строк) — главный бэкенд
**Что:** Все endpoints, middleware, lifespan, импорты, роутинг. Это сердце приложения.
**Где смотреть:**
- 70: `get_llm_client()` — инициализация YandexGPT/OpenAI клиента
- 145: `now_msk()` — все timestamp'ы в Moscow time
- 220: `_lifespan()` — старт/стоп приложения, init БД
- 266: `RoleStateMiddleware` — переключение ролей (технолог/нач.цеха/гл.технолог/admin)
- 304: `err()` — единый формат ошибок
- 309: `safe_call()` — try/except обёртка для LLM
- 324: `check_auth()` — Basic Auth
- 358: `auth_middleware` — CSRF + session
- 441: `api_save_answers` — backup для 3-step flow (localStorage)
- 529: `_check_rate_limit` — защита от спама
- 1618: `api_import_drawing` — загрузка чертежа (M28)
- 1682: `api_drawing_recognize` — OCR endpoint
- 2580: `api_analyze` — быстрый черновик (3-step)
- 2651: `api_draft_fast` — **главная кнопка "Сгенерировать ТК"**
- 2734: `api_refine` — доработка черновика до полной ТК
- 2851: `generate` — полная генерация через TECH_CARD_PROMPT
- 3151: `approve` — утверждение ТК (триггерит RAG индексацию)
- 3194: `api_pilot_session_start` — старт пилота
**Важно:** это монолит. Если добавляешь endpoint — клади в `app.py`. Если он большой (>50 строк логики) — выноси в отдельный модуль и импортируй.
**Подводный камень:** `api_draft_fast` (M27 fix) ДОЛЖЕН вызывать `save_draft()` — иначе операции не сохраняются, toast "Готово" но пусто.

### `db.py` — БД
**Что:** SQLite, 19 таблиц, миграции через `CREATE TABLE IF NOT EXISTS`. Seed-данные при инициализации.
**Где смотреть:**
- 15: `get_conn()` — все обращения к БД идут через эту функцию (WAL mode, autocommit off)
- 32: `init_db()` — все CREATE TABLE
- 275: `get_detail()` — загрузка одной детали
- 284: `get_all_details()` — список с фильтрами + пагинация
- 343: `save_draft()` — **сохранение черновика ТК** (JSON в `llm_output`)
- 370: `get_versions()` — история версий для отката
**Важно:** миграции только additive (`IF NOT EXISTS`). Если меняешь схему — ALTER TABLE с обработкой `except`.
**Подводный камень:** DB_PATH может быть относительным — `os.path.dirname(DB_PATH) or "."` (M27 fix).

### `admin.py` — админка
**Что:** Все endpoints для админа: пользователи, логи входов, настройки, LLM-вызовы, errors, system, backup, RAG.
**Где смотреть:**
- 41: `_get_templates_db_path_roles()` — **tuple unpacking**, берите `DB_PATH` 2-м элементом
**Endpoints:** /admin, /admin/users, /admin/login-log, /admin/llm-calls, /admin/settings, /admin/errors, /admin/system, /admin/backup, /admin/rag
**Подводный камень:** `/admin/backup` 500 если не распаковать tuple правильно (M27 fix).

### `rag.py` — RAG
**Что:** TF-IDF + cosine similarity, **on-prem** без внешних API. Лемматизация pymorphy2 + синонимы для русского.
**Где смотреть:**
- 39: `_get_morph()` — lazy-init pymorphy2
- 83: `_apply_synonyms()` — маппинг синонимов (Ст3/сталь3, MIG/полуавтсварка, лист/листовой)
- 118: `_ensure_index_dir()` — создание `.rag/`
- 122: `_build_text()` — что индексируется из detail
- 320: `rebuild_from_db()` — пересборка индекса
- 384: `rag_index_detail()` — добавить деталь в индекс
**Где хранится:** `.rag/vectorizer.pkl`, `.rag/tfidf_matrix.pkl`, `.rag/ids.pkl`, `.rag/metadata.pkl` (в .gitignore)
**Синонимы — это золото:** если LLM говорит "Ст3" а в индексе "сталь3" — они мапаются. Без этого TF-IDF не находит.
**Подводный камень:** pymorphy2 может не установиться (зависимость от pypi). Тогда лемматизация off, fallback работает.

### `llm.py` — LLM-клиент
**Что:** YandexGPT через OpenAI-совместимый SDK, логирование вызовов, расчёт стоимости.
**Где смотреть:**
- 70: `get_llm_client()` — singleton клиент
- 92: `log_llm_call()` — запись в `llm_calls` для аналитики
- 99: `parse_llm_json()` — вытаскивает JSON из LLM-ответа (часто LLM оборачивает в markdown)
**Модели:** `gpt://b1gj791m9sc92argfa0q/yandexgpt/latest` (default)
**Дневной лимит:** 200₽ / 500₽ (settings) — `DAILY_COST_LIMIT_RUB`
**Подводный камень:** `auth_error` если LLM_API_KEY в settings битый — нужно переввести через `/admin/settings`.

### `prompts.py` — все системные промты
**Что:** 7 типов: WELDING, ELECTRICAL, HYDRAULIC, PAINT, TECH_CARD, CLARIFICATION, REFINE.
**Размер:** ~700 строк, по 100 на каждый промт.
**Структура каждого:** контекст производства → переменные ($properties, $equipment, $workshops_context) → задача → формат JSON → требования.
**Когда менять:** если AI генерирует не то, что нужно — сначала смотри сюда. 80% проблем = неправильный промт.
**Параметры шаблона:** `properties_json`, `equipment_json`, `structure_json`, `few_shot_json`, `tech_rules`, `rules_block`, `workshops_context`, `draft_json`, `answers_json`, `similar_block`.

### `auth.py` — авторизация
**Что:** HTTP Basic Auth, CSRF, rate limit, security headers (CSP, HSTS).
**Подводный камень:** **CSRF обязателен** для всех POST fetch в JS (`X-Requested-With: XMLHttpRequest` + `credentials: 'same-origin'`).

### `economics.py` — стоимость ТК
**Что:** Process-based pricing (CADDi-стиль) — раскладка по этапам маршрута: материалы, зарплата, накладные, итого.
**Стиль:** функции `calc_cost_estimate(detail_id)` возвращают dict со всеми breakdown.
**Дефолты:** cost_per_hour=800₽ (после M27 fix), overhead=15%, material cost = из детали.

### `learning.py` — метрики
**Что:** Сбор метрик с пилота: sessions, time-to-card, edits, acceptance.
**Где смотреть:** `compute_acceptance_from_versions` — считает процент правок технолога.

### `drawing_recognize.py` — OCR (M28)
**Что:** pdftoppm + tesseract (rus+eng) + regex-извлечение полей.
**Pipeline:** PDF → PNG (300 dpi gray) → tesseract → text → regex → fields dict.
**Извлекает:** designation, material, material_grade, dimensions, thickness_mm, mass_kg, blank_type.
**На Beget:** нужны `poppler-utils` + `tesseract-ocr-rus` (не установлены по умолчанию).

### `workshops_tehinkom.py` — реальные цеха (M28)
**Что:** 5 цехов, 36 операций Техинкома в формате для LLM system prompt.
**Размер:** 2190 символов.
**Подключение:** `from workshops_tehinkom import TECHINKOM_WORKSHOPS_CONTEXT` → подставляется в `prompts.py` через `$workshops_context`.
**Когда менять:** когда Сергей присылает обновлённый список цехов/операций.

### `pilot_report.py` — отчёт пилота
**Что:** PDF + Markdown отчёт по пилоту: графики (matplotlib), метрики, статистика.
**Где смотреть:** `/pilot/report` — endpoint, `generate_pilot_report()` — функция.

---

## Подводные камни (top-10 из MISTAKES.md)

1. **CSRF обязателен** для всех POST fetch в JS — иначе 403
2. **DB_PATH relative** — `os.path.dirname(DB_PATH) or "."` для `/backups`
3. **Парсер DOCX workshops** — workshop name может быть в cell[0] ИЛИ cell[1]
4. **PDF = скан** — pdftotext пустой, нужен tesseract rus+eng
5. **На Beget нет pdftoppm/tesseract** — apt install
6. **`{% if %}` баланс** в Jinja — scripts с функциями НЕ внутри if-block
7. **Race condition** в тестах — `c.post("/api/role/switch")` в начале
8. **Lazy `_get_templates_db_path_roles()`** — распаковывай tuple правильно
9. **Inline styles** запрещены (M22) — только CSS variables
10. **Перед UI-рефактором** — опиши workflow словами, потом рисуй

---

## "Сюрпризы" в коде (что может пойти не так)

1. **`api_draft_fast` НЕ сохранял draft в БД** (M27 bug) — был toast "Готово" но операции 0. **Фикс:** вызывать `save_draft()` + adapter route→operations.
2. **`cost_per_hour=0` у всех 26 деталей** (M27 bug) — UPDATE на production. **Фикс:** `cost_per_hour=800` default.
3. **404 в навигации** (`/hierarchy`, `/admin/backup`, `/admin/rag`) — шаблоны не созданы. **Фикс:** templates/*.html + endpoints.
4. **Дубль в materials select** (8 опций вместо 6) — хардкод в `detail_form.html`. **Фикс:** убрать хардкод.
5. **`data-op-id=""` пустой** (M26 bug) — op.id=None в LLM данных → editOp не работал. **Фикс:** `op_id = op.op_index`.

---

## Где искать для типичных задач

| Задача | Файл | Функция/строка |
|--------|------|----------------|
| "Сгенерируй ТК для детали X" | app.py:2651 | `api_draft_fast` |
| "Измени логику утверждения" | app.py:3151 | `approve` |
| "Подключи новый LLM" | llm.py:70 | `get_llm_client` |
| "Улучши промт для сварки" | prompts.py:5 | `WELDING_PROMPT` |
| "Добавь endpoint /api/foo" | app.py | новый @app.post |
| "Найди баг в RAG" | rag.py:320 | `rebuild_from_db` |
| "Меняю UI карточки детали" | templates/detail.html | весь файл |
| "Добавь стиль для кнопки" | static/design-system.css | BEM-класс |
| "OCR не работает на PDF" | drawing_recognize.py:79 | `_pdf_to_text` |
| "Поднять лимит LLM" | admin.py | `/admin/settings` |
