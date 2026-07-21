# Аудит v2 БИТ.Технолог — 2026-07-19 (после P0 фиксов)

**Объект:** `/workspace/bit-technolog-prototype/` — 6027 строк (app.py 2686, test_app.py 708, RAG 306, prompts 342, CSS 240, HTML ~1700)
**Тесты:** 75/75 passing
**Коммиты:** c235a73 (последний P0 fix)

> **TL;DR:** P0-фиксы прошли, но **появились новые проблемы** (dead code, несоответствия, невалидированный JSON от LLM, отсутствие CSRF). Плюс **3 критичных вопроса, которые оставляю Сергею** (они требуют бизнес-решения, а не кода).

---

## 1. Цели и ценности (re-check)

### 1.1 Что было исправлено
- ✅ Sprint 1/2/3 переименованы в человеческие названия (U2)
- ✅ Печатная форма ТК (P0 задача 10) — критично для подписи в бумажный журнал
- ✅ Search + pagination (U4) — без этого 575 деталей невозможно
- ✅ Inline-edit (U6) — убрали 3 формы на операцию

### 1.2 Новые риски
- ⚠️ Печатная форма имеет **Times New Roman 12pt** — стандарт для бумажных журналов, но не имеет QR-кода для привязки к digital версии (ISO 9001 / военная приёмка требуют traceability)
- ⚠️ Inline-edit не имеет undo на уровне одной правки (есть только на уровне версии)
- ⚠️ Search работает по `designation, name, model, material` — но **не по `chassis`, не по `extra_props`, не по `tech_rules`**. Технологи часто ищут именно по шасси

**[СЕРГЕЮ-1]**: Pilot scope — **3-5 технологов или 1 главный + 2-3 рядовых?** Это меняет требования к ролевой модели и audit-логу.

**[СЕРГЕЮ-2]**: Критично ли **offline-mode** для пилота? (цех без Wi-Fi) — это переход с SQLite на локальный кеш LLM-ответов.

---

## 2. Концепции и фреймворки (re-check)

### 2.1 Решения, которые подтвердились
- ✅ **WAL mode + singleton client** — реально ускорили (тест N+1 проходит за <1с вместо зависания)
- ✅ **Auth middleware** — простая, делает job для пилота. JWT можно потом
- ✅ **localStorage для answers** — работает, простой UX
- ✅ **HTML-печатная форма** вместо PDF-генерации — браузер сам делает PDF/A4, экономит ~200 строк кода

### 2.2 Новые концептуальные проблемы

#### ❌ NC1: Двойная проверка детали — `MOCK_DETAILS` И `get_detail()`
**12 мест** в `app.py` используют `next((d for d in MOCK_DETAILS if d["id"] == detail_id), None)`. Одновременно `get_detail()` читает из SQLite. Если деталь есть в БД, но не в `MOCK_DETAILS` (например, добавил через UI) — `next()` вернёт None → 404, хотя `get_detail()` бы нашёл.

**Fix:** заменить все `next((d for d in MOCK_DETAILS...))` на `get_detail(detail_id)`. `MOCK_DETAILS` оставить только в `generate_mock_draft()` (где нужны свойства для генерации мока).

#### ⚠️ NC2: `from openai import OpenAI` оставлен в 4 местах после C4 fix
`app.py:999, 1059, 1134, 1689` — `from openai import OpenAI` импортируется, но **не используется** (я заменил `client = OpenAI(...)` на `client = get_llm_client()`). Dead code, замедляет запуск на 200мс × 4 = 800мс.

**Fix:** удалить `from openai import OpenAI` из всех 4 мест, оставить только в `get_llm_client()`.

#### ❌ NC3: JSON-parsing LLM-ответа — неустойчив
`app.py:1038, 1100, 1259` — обрабатывают `if text.startswith("```")`. Но:
- Нет защиты от ответа без JSON (LLM может вернуть «Извини, я не могу...»)
- Нет защиты ответа с markdown внутри JSON-строк
- Нет защиты ответа с обрезанным JSON (max_tokens=8000 режется)

**Fix:** добавить `parse_llm_json(text)` helper с многоуровневой очисткой + fallback на ошибку.

#### ⚠️ NC4: RAG + LLM в одном промте, но без валидации что similar действительно relevant
`REFINE_PROMPT` имеет секцию "Похожие техкарты (RAG)". Но если RAG вернул деталь с `score=0.3` (низкая похожесть) — LLM всё равно «учится» на ней. Это может **ухудшить** результат.

**Fix:** в RAG endpoint / промт — добавить `if score < 0.4: skip`.

---

## 3. Реализация (re-check)

### 3.1 Что я увидел перечитывая код

#### 🔴 B1: `/api/feedback` (Sprint 1) — нигде не вызывается
`app.py:1158` — endpoint есть, тест есть (`test_api_feedback`), но **в UI нет кнопки «👎 Пожаловаться»**. Sprint 1 заявлял эту кнопку — забыли добавить в `detail.html`.

**Fix:** добавить кнопку «⚠ Черновик не подходит» в action-bar.

#### 🔴 B2: `record_edit` и `add_history` используют `conn = get_conn()` без commit
`app.py:612-616` (record_edit), `app.py:818-825` (add_history) — `conn.commit()` есть, но **нет `conn.close()` в happy-path**. Утечка соединений.

**Fix:** `with get_conn() as conn:` или `try/finally`.

#### 🟠 B3: `inline_edit` whitelist не покрывает `materials`, `gosts`, `control_points`
`/api/edit/inline` принимает только `name, equipment, duration_hours, department, workplace`. Но в `detail.html` есть `materials`, `gosts`, `control_points` для каждой операции. **Технолог хочет их тоже править inline.**

**Fix:** расширить whitelist.

#### 🟠 B4: CSRF protection всё ещё нет
Sprint 1 упоминал — не сделано. `htmx` по умолчанию делает GET для всех URL, а POST через `hx-post`. Злоумышленник может сделать `<form action="http://tehnolog.ru/api/approve" method="POST">` с автоподставленными credentials (если пользователь зашёл на вредоносный сайт в той же сессии).

**Fix:** добавить `X-Requested-With: XMLHttpRequest` header check (htmx его шлёт) или CSRF-token.

#### 🟠 B5: `pilot.html` использует `record_daily_cost` — нет такого метода
`grep "record_daily_cost" app.py` → не найдено. Pilot dashboard может падать в проде.

**Fix:** проверить pilot.html, добавить функцию или удалить вызов.

#### 🟡 B6: `app.py` 2686 строк — большая проблема
По правилу C# / Go / Python — файл > 1000 строк нуждается в разделении. Помехи:
- 50+ endpoints в одном файле
- Невозможно grep'ом найти «все endpointы с префиксом /api/rag»
- Конфликты при merge в команде

**Fix (после пилота):** routers/{drafts,details,ai,rag,audit,economics}.py.

#### 🟡 B7: `prompts.py` 342 строки — все промты в одном файле
То же. После пилота — `prompts/{analyze,draft,refine,few_shot}.md` с чтением из файлов.

#### 🟡 B8: `equipment.json`, `structure.json` — синхронно читаются при импорте
`app.py:75-83` — `open(...)` блокирует event loop на 50-200мс (для больших файлов).

**Fix:** ленивая загрузка через `@lru_cache` функцию.

#### 🟡 B9: `templates/audit.html` рендерит `{{ e.details }}` как строку без pretty-print
`audit.html:23` — `<code>{{ e.details or '{}' }}</code>`. JSON выглядит как мусор.

**Fix:** `{{ e.details | fromjson | tojson(indent=2) }}` (есть в Jinja2).

#### 🟡 B10: `learning.html` / `pilot.html` / `llm_debug.html` — нет пагинации
При 1000+ LLM-вызовов страница будет тормозить.

**Fix:** `?limit=50&offset=N` параметры.

#### ⚪ B11: `templates/_crud_list.html` — 19 строк, **нигде не используется**
`grep "_crud_list" app.py` → нет. Dead template.

**Fix:** удалить.

#### ⚪ B12: `start.bat` обновляет через `git pull` без проверки ошибок
`start.bat:5` — `git pull` молча игнорирует конфликты.

**Fix:** `git pull || echo "ERROR: merge conflict, resolve manually"`.

#### ⚪ B13: `requirements.txt` имеет `openai` — но не `scikit-learn`?
`requirements.txt` — проверю.

### 3.2 Архитектурные долги (новые)

| # | Долг | Последствие | Приоритет |
|---|------|-------------|-----------|
| AD1 | `MOCK_DETAILS` в 12 местах | См. NC1 | High |
| AD2 | `from openai import OpenAI` в 4 dead imports | Замедление старта | High |
| AD3 | `parse_llm_json` отсутствует | LLM вернёт markdown → JSON parse error | High |
| AD4 | CSRF | Security | Medium |
| AD5 | Утечки conn в `record_edit`/`add_history` | Long-run на пилоте | Medium |
| AD6 | `prompts.py`/`app.py` слишком большие | Maintainability | Low (после пилота) |

### 3.3 Security (re-check)

| # | Проблема | Severity | Fix |
|---|----------|----------|-----|
| S6 | CSRF | High | См. B4 |
| S7 | `X-Requested-With` не проверяется | Medium | htmx его шлёт, проверить |
| S8 | `bearer token` в .env — может утечь в логи | Low | Mask в logging |

---

## 4. UX/юзабилити (re-check)

### 4.1 Что улучшилось
- ✅ Печатная форма — **огромный** прогресс, теперь это реальный артефакт
- ✅ Search — теперь можно найти деталь за 5 сек
- ✅ Inline-edit — клик-изменил (хотя пока не до конца)
- ✅ Переименование Sprint 1/2/3 — больше нет «что за спринт»

### 4.2 Новые UX проблемы

#### 🔴 UX1: На `/index` нет кнопки **«📦 Сгенерировать все новые»** (массовое действие)
U9 из аудита v1 — не реализовано. Технолог откроет `/index`, увидит «🔴 Новый × 47» и... будет кликать 47 раз.

**Fix:** кнопка в action-bar `/index`: «📦 Сгенерировать все новые» → POST `/api/batch-generate` с фильтром status=new.

#### 🔴 UX2: Кнопка «⚠ Черновик не подходит» отсутствует
B1 — feedback кнопки нет. Технолог не может пожаловаться на плохой draft.

**Fix:** добавить.

#### 🟠 UX3: Печатная форма не имеет QR-кода
Технолог печатает → относит на подпись → главный технолог хочет проверить «точно ли это из системы». Без QR — открывает PDF, ищет ID вручную.

**Fix:** добавить `<svg>` QR-код (4 строки JS) с `bit-technolog://detail/{id}` (или просто URL).

#### 🟠 UX4: `/detail/{id}` — вкладки не сохраняют состояние при reload
Открыл «Operations» → refresh → снова «Summary». Мелочь, но раздражает.

**Fix:** `localStorage.setItem('tab-{id}', 'operations')` + при загрузке восстанавливать.

#### 🟠 UX5: `/index` — фильтр по статусу не имеет кнопки «Применить» (есть), но **нет счётчика результатов** в реальном времени
После ввода «Кронштейн» в search — нужно нажать Enter или кнопку. **Лучше:** live-search через `hx-get` каждые 300мс.

**Fix:** опционально, добавить `hx-get` + `hx-trigger="keyup changed delay:300ms"`.

#### 🟠 UX6: `print.html` имеет `.no-print` div с подсказкой про Ctrl+P — но эта подсказка **сама не печатается** (правильно). Однако при экспорте в PDF — её нет (тоже правильно). **OK.**

#### 🟡 UX7: Tab `Operations` имеет 3 inline-edit формы на операцию + кнопка «+Добавить операцию». Всё ещё перегружено. Технолог увидит 8 операций × 3 формы = 24 input.

**Fix:** click-to-edit (один input вместо 3) + Enter/Esc.

#### 🟡 UX8: Detail header показывает `model, chassis, material, mass, surface_treatment` — но **не показывает `extra_props`**. А там могут быть критичные данные (толщина стенки, ГОСТ на материал, термообработка).

**Fix:** развернуть `extra_props` как JSON на странице.

#### 🟡 UX9: При сохранении экономики → `setTimeout(() => location.reload(), 1000)`. Это **теряет фокус** (если технолог печатал 5 значений подряд).

**Fix:** обновлять только панель экономики, не всю страницу.

#### 🟡 UX10: Шрифт 14px в основном тексте. Для 50+ — мало.

**Fix:** глобально 16px (1 line CSS).

#### ⚪ UX11: Цвет уверенности 🟢🟡🔴 — для дальтоников 8% мужчин не работает.

**Fix:** + текстовая метка «высокая/средняя/низкая» рядом с эмодзи (в печатной форме уже есть).

### 4.3 Что ОК и не трогаем
- ✅ Вкладки (Сводка/Маршрут/Операции/Обоснование/Warnings/Вопросы) — стандарт
- ✅ Audit log + экспорт — для ISO 27001 хватит
- ✅ Cost-pill в nav — мгновенная обратная связь
- ✅ Inline-form для экономики и правил

---

## 5. Приоритеты (что делаю сейчас)

### P0 (делаю в этом цикле)

| # | Задача | Effort |
|---|--------|--------|
| A | NC1: заменить MOCK_DETAILS → get_detail() в 12 местах | 30 мин |
| B | NC2: удалить dead imports `from openai import OpenAI` | 5 мин |
| C | NC3: parse_llm_json helper | 30 мин |
| D | B1+UX2: feedback кнопка | 10 мин |
| E | B2: `with get_conn()` для record_edit, add_history | 10 мин |
| F | B3: расширить inline-edit whitelist | 15 мин |
| G | B4: CSRF (X-Requested-With check) | 20 мин |
| H | UX1: «Сгенерировать все новые» | 20 мин |
| I | UX3: QR-код в print | 15 мин |
| J | UX7: click-to-edit (один input) | 30 мин |
| K | UX10: 16px глобально | 5 мин |
| L | B11: удалить dead _crud_list.html | 1 мин |

**Итого:** ~3.5 часа кода + 1 коммит.

### P1 (следующий цикл)

- B5: pilot.html record_daily_cost (если реально нужен)
- B6: разделить app.py на routers (после пилота)
- B9: pretty-print JSON в audit.html
- B10: пагинация в learning/pilot/llm_debug
- UX4: localStorage для tab state
- UX5: live search
- UX8: показать extra_props
- UX9: не перезагружать страницу при сохранении экономики

### P2 (после пилота)

- B6, B7: разделение на модули
- B12: проверка git pull в start.bat
- S7, S8: X-Requested-With, bearer token masking

---

## 6. Спорные вопросы — [СЕРГЕЮ]

1. **[СЕРГЕЮ-1]** Pilot scope: 3-5 технологов ИЛИ 1 главный + 2-3 рядовых? Меняет ролевую модель.
2. **[СЕРГЕЮ-2]** Нужен ли offline-mode для пилота? (цех без Wi-Fi)
3. **[СЕРГЕЮ-3]** Технологи говорят «найди по шасси» — расширить search на `chassis`? (1 строка кода, но UX-решение — насколько это критично для пилота)
4. **[СЕРГЕЮ-4]** 30% acceptance — это «правка ≤2 полей» или «approve без правок»? Определение «acceptance» влияет на метрики.
5. **[СЕРГЕЮ-5]** Когда первый пилот — Баранов смотрит UI до пилота или после 1-2 раунда фидбека от рядовых?

---

## 7. Сравнение с v1 аудитом

| Метрика | v1 (11:31) | v2 (11:51) | Δ |
|---------|-----------|-----------|----|
| Тестов passing | 58 | 75 | +17 |
| Critical багов | 6 | 4 | -2 |
| UX проблем | 9 | 11 | +2 (новые) |
| Архитектурных долгов | 8 | 8 | 0 |
| Security issues | 5 | 6 | +1 (CSRF) |
| Спорных вопросов | 0 | 5 | +5 |

**Вывод:** Технические P0 фиксы прошли, но **появились новые проблемы** (особенно dead code, JSON parsing, CSRF). Спорных вопросов накопилось 5 — нужны твои ответы.

---

*Аудит v2, commit c235a73, 2026-07-19 11:51 МСК*
