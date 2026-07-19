# БИТ.Технолог — прототип

**AI-помощник технолога для ООО «ПК Техинком-Центр»** (производство пожарной техники).
Генерирует черновики техкарт по свойствам детали за 30-60 минут вместо 4-8 часов.

> 🎯 **v0.4 готов к пилоту на 85%.** Блокирующее: 50-100 исторических ТК Техинкома для RAG.

## Что это

Деталь от конструктора (материал, масса, шасси) → AI генерирует черновик технологической карты:
- Список операций с оборудованием и временем
- Указание источника оценки (ГОСТ / аналог / правило)
- Уверенность по каждой операции (зелёный/жёлтый/красный)
- Warnings с цитатами (что смущает)
- Вопросы к технологу с вариантами
- Обоснование решений (для руководства)

## Быстрый старт

```powershell
# Windows PowerShell
cd C:\Projects\MiniMax\BIT_Tech
.\start.bat
```

Открыть `http://localhost:8000`. Логин/пароль по умолчанию — без (для DEMO).

## Тесты

```powershell
.\venv\Scripts\python -m pytest test_app.py -v
```

**Текущий статус:** 87/87 passing.

## Документация

Вся документация в [`docs/`](docs/README.md):
- Что строим и зачем — [01-product-design.md](docs/01-product-design.md)
- Как устроен прототип — [02-architecture.md](docs/02-architecture.md)
- Как AI обучается — [03-training-architecture.md](docs/03-training-architecture.md)
- План пилота — [04-pilot-roadmap.md](docs/04-pilot-roadmap.md)
- Контекст Техинком-Центр — [05-techinkom-context.md](docs/05-techinkom-context.md)
- UX-сценарии — [06-ux-flow.md](docs/06-ux-flow.md)
- 5 циклов аудита — [07-audit-log.md](docs/07-audit-log.md)
- Анализ конкурентов — [08-competitors.md](docs/08-competitors.md)
- **9 открытых вопросов по продукту** — [09-open-questions.md](docs/09-open-questions.md)

## Стек

- **Backend:** Python 3.11+ / FastAPI / SQLite (WAL mode)
- **Frontend:** Jinja2 + HTMX + vanilla CSS (16px базовый шрифт)
- **AI:** YandexGPT (или OpenAI-совместимый) через `openai` SDK
- **RAG:** TF-IDF + cosine + hybrid scoring (scikit-learn, on-prem)
- **Безопасность:** HTTP Basic Auth + CSRF (X-Requested-With)
- **Тесты:** pytest (87 тестов)

## Структура

```
bit-technolog-prototype/
├── app.py                    # 2793 строк — FastAPI endpoints
├── rag.py                    # 306 строк — RAG-индекс
├── prompts.py                # 342 строки — промты для LLM
├── mock_data.py              # 4 mock-детали (для DEMO)
├── few_shot.py               # Примеры для LLM
├── equipment.json            # Справочник оборудования
├── structure.json            # Структура ТК
├── test_app.py               # 798 строк — pytest тесты
├── requirements.txt          # httpx, scikit-learn, openai, fastapi
├── start.bat                 # Запуск (Windows)
├── update.bat                # git pull
├── init-git.bat              # Первичная инициализация
├── templates/                # Jinja2 шаблоны
│   ├── base.html
│   ├── index.html            # Список деталей + search + pagination
│   ├── detail.html           # Карточка детали (8 вкладок)
│   ├── print.html            # Печатная форма ТК (A4)
│   ├── audit.html            # Журнал действий
│   ├── learning.html         # Правила + правки + метрики
│   ├── llm_debug.html        # Лог LLM-вызовов
│   ├── pilot.html            # Дашборд KPI пилота
│   ├── equipment_list.html
│   ├── materials_list.html
│   └── iot_list.html
├── static/
│   ├── style.css             # 241 строка
│   └── htmx.min.js
├── docs/                     # Документация
│   ├── README.md
│   ├── 01-product-design.md
│   ├── 02-architecture.md
│   ├── 03-training-architecture.md
│   ├── 04-pilot-roadmap.md
│   ├── 05-techinkom-context.md
│   ├── 06-ux-flow.md
│   ├── 07-audit-log.md
│   ├── 08-competitors.md
│   └── 09-open-questions.md
├── .env.example              # Шаблон переменных окружения
├── .gitignore
├── bit_technolog.db          # SQLite (создаётся автоматически)
└── .rag/                     # Pickle-файлы RAG-индекса
    ├── vectorizer.pkl
    ├── tfidf_matrix.pkl
    ├── ids.pkl
    └── metadata.pkl
```

## Ключевые эндпоинты

**Основные:**
- `GET /` — список деталей с search + pagination
- `GET /detail/{id}` — карточка детали (8 вкладок)
- `GET /detail/{id}/print` — печатная форма (A4, для подписи)
- `POST /api/generate` — генерация черновика через LLM
- `POST /api/approve` — утверждение (auto-index в RAG)
- `POST /api/edit/inline` — inline-редактирование операции

**AI-помощник (3-step flow):**
- `POST /api/analyze` — AI задаёт 3-5 уточняющих вопросов
- `POST /api/draft-fast` — быстрый draft (3 операции, ~1₽)
- `POST /api/refine` — полный маршрут с учётом уточнений

**RAG (Sprint 2):**
- `GET /api/rag/similar/{id}?top_k=5` — top-5 похожих техкарт
- `POST /api/rag/rebuild` — перестроить индекс
- `GET /api/rag/status` — статус индекса

**Альтернативы (Sprint 3):**
- `POST /api/alternatives` — 2-3 варианта маршрута
- `POST /api/apply-similar` — 1-click применить похожую ТК
- `POST /api/batch-generate` — пакетная генерация (до 20 деталей)
- `POST /api/batch-generate-new` — сгенерировать все new-детали

**Экспорт:**
- `GET /api/export/onec-csv?detail_id=...` — CSV для 1С:ERP
- `GET /api/audit/export` — audit log в JSON
- `GET /api/export/all` — вся БД в JSON

**Управление:**
- `GET /audit` — страница audit log
- `GET /pilot` — дашборд KPI пилота
- `GET /llm-debug` — лог LLM-вызовов
- `GET /learning` — правила + правки
- `GET /health` — статус БД + RAG

## Лицензия

Internal prototype for «Первый БИТ» / «ПК Техинком-Центр».
Не для публичного распространения.

## Контакты

- **Разработка:** Mavis (AI-ассистент)
- **Заказчик:** Сергей Жуков
- **Завод:** ПК «Техинком-Центр» (Москва)

---

*Версия: v0.4. Коммит: aa8e0c4. Дата: 2026-07-19.*
