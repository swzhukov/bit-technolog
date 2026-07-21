# Аудит v3 БИТ.Технолог — 2026-07-19 (после v2 фиксов)

**Объект:** `/workspace/bit-technolog-prototype/` — 5861 строк (app.py 2763, test 798, RAG 306, prompts 342, CSS 241, HTML ~1700)
**Тесты:** 81/81 passing
**Коммиты:** f7d62b4 (последний v2 fix)

> **TL;DR:** v2-фиксы прошли. Появились **новые наблюдения** про долгосрочную надёжность (observability, error handling, code style). По CSRF и UI нашёл ещё тонкости. Спорных вопросов накопилось 8 — начну выделять «фатальные» (блокируют пилот) vs «косметика».

---

## 1. Цели и ценности (re-check)

### ✅ Без изменений
Все P0 цели закрыты. Один новый сигнал — **на печатной форме QR-код через Google Chart API** — это **внешний запрос** (CDN). На пилоте с on-prem это может не работать без интернета.

**[СЕРГЕЮ-6]**: критично ли что QR использует внешний CDN (api.qrserver.com)? Если на заводе закрытый контур — нужно рисовать QR клиентом (qrcode.js ~5KB) без сети.

---

## 2. Концепции (re-check)

### ✅ Подтвердились
- `parse_llm_json` — теперь 4 парсера единообразные, устойчивые
- CSRF middleware — htmx шлёт X-Requested-With автоматически
- Inline-edit whitelist с list-полями — теперь можно править materials/gosts через UI

### ⚠️ Новые концептуальные вопросы

#### NC5: 40+ `except Exception` — нет наблюдаемости
`grep "except Exception" app.py` → 40+ вхождений. По правилам SRE — каждый catch должен либо:
- (a) логировать (`log.exception(...)`)
- (b) возвращать осмысленную ошибку пользователю
- (c) re-raise

Сейчас половина просто проглатывает. На пилоте что-то упадёт в `/api/generate` — никто не узнает.

**Fix:** централизованный `log.error()` через `log = logging.getLogger("bit-technolog")` (уже есть) + helper `_safe_call(name, fn, *args)`.

#### NC6: `f"SELECT * FROM {t}"` в `/api/export/all` — table name из локального list, **не SQL injection**, но непереносимо
`app.py:1789` — `tables = ["details", "drafts", ...]`. Это **внутренний** list, не user input. Безопасно. Но если когда-то попадёт user input — дыра. Добавить whitelist.

#### NC7: Дублирование error JSONResponse
30+ мест с `return JSONResponse({"error": "..."}, status_code=...)`. Можно упростить через helper:
```python
def err(msg, code=400, **extra): return JSONResponse({"error": msg, **extra}, status_code=code)
```

---

## 3. Реализация (re-check)

### 3.1 Новые баги

#### 🔴 R1: CSRF блокирует **формы без htmx**
Сейчас middleware требует `X-Requested-With` или same-origin Referer. Но:
- **Печатная форма** `/detail/{id}/print` — это GET, не POST. OK.
- **`/api/export/excel`** — это POST через `<form action="/api/export/excel" method="post">` (видно в `detail.html`). Браузер шлёт Referer = `http://localhost:8000/detail/{id}`. Same-origin. **OK.**
- **Однако** есть формы без htmx в `index.html` пагинация (`<a href="?page=...">`) — это GET, OK.
- **CSRF в тестах** — `PILOT_CSRF_DISABLED=true` обходит, OK.

**[СЕРГЕЮ-7]**: ok что я добавил CSRF с opt-out через env? Или это лишнее для пилота (там 3-5 доверенных человек)?

#### 🟠 R2: `record_edit` / `add_history` try/finally — но **в happy-path не тестируется**
Тест `test_record_edit_no_leak` создаёт 50 записей. Но на пилоте 1000+ вызовов — нужна реальная нагрузка. **Пока ОК, но добавлю нагрузочный тест.**

#### 🟠 R3: `pilot.html` — что показывает при пустой БД?
Не проверял. Возможно падает или показывает мусор. Запущу — посмотрю.

#### 🟠 R4: `learning.html` — 7 раскрывающихся секций `<details>` на одной странице
`templates/learning.html:1-100` (101 строка, много раскрывашек). Длинная страница, нужен tabs.

#### 🟡 R5: 3 search endpoint'а — `/`, `/equipment`, `/materials`, `/iot` — **equipment/materials/iot НЕ имеют search**
В `index.html` я добавил search, но в `equipment_list.html` / `materials_list.html` / `iot_list.html` — фильтрация только клиентом (нет `<form method="get">`).

#### 🟡 R6: SQL f-string с WHERE-конструкцией — потенциально `where_sql` пустая или с AND
`app.py:962` — `f"SELECT COUNT(*) FROM details {where_sql}"` где `where_sql = ""` или `"WHERE x AND y"`. **OK** в текущем коде, но `""` + `LIMIT ? OFFSET ?` — должно работать.

#### ⚪ R7: `index.html:46` — кнопка "📦 Сгенерировать все новые" ссылается на GET `/api/batch-generate-new`, но я сделал POST. **Bug в HTML.**

```html
<a href="/api/batch-generate-new" ...>📦 Сгенерировать все новые</a>
```
Должна быть `<form method="post" action="/api/batch-generate-new">` или `<button hx-post=...>`.

**Fix:** изменить на форму + `hx-post`.

### 3.2 Observability

| # | Проблема | Severity | Fix |
|---|----------|----------|-----|
| OB1 | `except Exception` без логирования | High | helper `_safe_call` + `log.exception` |
| OB2 | Нет метрик времени ответа | Medium | FastAPI middleware с timing |
| OB3 | Нет healthcheck БД (только `details_count`) | Medium | `SELECT 1` в `/health` |
| OB4 | Логи в stderr без JSON | Low | `python-json-logger` |

### 3.3 Code style

- Нет `black`/`ruff`/`mypy` — но `requirements.txt` имеет `httpx<0.28`, что показывает заботу о версиях
- `app.py:2763` — всё ещё большой, но **rx-разделение не критично до пилота**

### 3.4 Security (re-check)

- ✅ CSRF добавлен
- ✅ Auth middleware
- ✅ Bearer token в .env (нет утечек в коде)
- ⚠️ **Нет HTTPS** — но на пилоте это вопрос reverse proxy (nginx), не FastAPI

---

## 4. UX (re-check)

### 4.1 Новые находки

#### 🔴 UX12: Кнопка "📦 Сгенерировать все новые" не работает (R7)
Это ссылка `<a>`, но endpoint POST. **Сломано.**

#### 🟠 UX13: В `detail.html` появилось 4 раскрывающихся секции (AI-помощник, Похожие, Другие маршруты, Правила, Экономика) — **5 details** на одной странице
Всё ещё много. U1 из v1 — не сделано полностью. Нужен **tabs-style** для AI-блоков.

#### 🟠 UX14: Печатная форма через Google Chart API для QR
Работает только с интернетом. На on-prem — нет.

#### 🟡 UX15: Шрифт 16px — уже OK. Но **в таблице `/index`** остался мелкий (12-13px). На 50+ — трудно читать.

#### 🟡 UX16: Feedback кнопки 👍/👎 — `hx-confirm="Что не так?"` — но **не имеют input для reason**
`hx-vals='{"detail_id": "...", "reason": "draft не подходит"}'` — reason хардкод. Нужен prompt.

**Fix:** использовать inline form как для экономики.

#### ⚪ UX17: Audit log — `{{ e.details }}` показывает JSON как строку (B9 не сделан)
Не критично, но некрасиво.

### 4.2 Где улучшения
- ✅ QR-код в печатной форме
- ✅ Click-to-edit расширен (materials/gosts)
- ✅ Шрифт 16px

---

## 5. Сравнение v1 → v2 → v3

| Метрика | v1 | v2 | v3 | Δ v1→v3 |
|---------|----|----|----|---------|
| Тестов passing | 58 | 75 | 81 | +23 |
| Critical багов | 6 | 4 | 1 (R7 broken button) | -5 |
| UX проблем | 9 | 11 | 6 (новый приоритет) | -3 |
| Архитектурных долгов | 8 | 8 | 8 | 0 |
| Security | 5 | 6 | 5 | 0 |
| Наблюдаемость | 0 | 0 | 0 | 0 (новый) |
| Спорных | 0 | 5 | 3 (новых) | 3 |

---

## 6. Приоритеты (что делаю сейчас в v3)

### P0 (исправляю в этом цикле)

| # | Задача | Effort |
|---|--------|--------|
| A | R7: починить кнопку "Сгенерировать все новые" (POST форма) | 5 мин |
| B | NC5: helper `_safe_call(name, fn, *args)` + `log.exception` | 30 мин |
| C | OB3: `/health` проверяет SELECT 1 | 10 мин |
| D | NC7: helper `err(msg, code, **extra)` | 15 мин |
| E | UX13: AI-блоки в tabs вместо 3 details | 30 мин |
| F | UX16: feedback form с reason input | 15 мин |
| G | R3: проверить pilot.html при пустой БД | 10 мин |
| H | UX15: таблица /index — 14px | 5 мин |

**Итого:** ~2 часа.

### P1 (следующий цикл)

- UX14: QR через локальный qrcode.js без CDN
- R4: learning.html → tabs
- R5: search в /equipment, /materials, /iot
- B9: pretty-print JSON в audit.html
- B10: пагинация в learning/pilot/llm_debug

### P2 (после пилота)

- Code style: black + ruff
- Observability: timing middleware
- Разделение app.py на routers

---

## 7. Спорные вопросы — обновлено

1. **[СЕРГЕЮ-1]** Pilot scope: 3-5 технологов ИЛИ 1 главный + 2-3 рядовых? (из v2)
2. **[СЕРГЕЮ-2]** Нужен ли offline-mode для пилота? (из v2)
3. **[СЕРГЕЮ-3]** Search по chassis? (из v2)
4. **[СЕРГЕЮ-4]** 30% acceptance — определение? (из v2)
5. **[СЕРГЕЮ-5]** Pilot flow: Баранов до пилота или после 1-2 раунда? (из v2)
6. **[СЕРГЕЮ-6]** QR через CDN — критично? on-prem контур?
7. **[СЕРГЕЮ-7]** CSRF нужен или overkill для 3-5 человек?
8. **[СЕРГЕЮ-8]** Когда первый пилот — **до UX-фидбека от Баранова** или после? (новый)

---

## 8. Что ОК и НЕ трогаем

- ✅ Auth (Basic) — для пилота достаточно
- ✅ RAG (TF-IDF) — для 50-100 ТК хватит
- ✅ 3-step flow — UX-тестирование покажет
- ✅ Print form — критично и работает
- ✅ Inline-edit + list-поля
- ✅ WAL mode + singleton LLM

---

*Аудит v3, commit f7d62b4, 2026-07-19 12:05 МСК*
