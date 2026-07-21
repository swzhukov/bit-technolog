# HANDOFF — точка входа для новой сессии Mavis

> **Дата:** 2026-07-21
> **Версия:** v0.8.5
> **Пилот:** 27 июля 2026 (через 6 дней)
> **Production:** http://217.114.7.5:8081/

Этот файл — **единственный источник истины для новой сессии**. Вся критичная информация для продолжения работы собрана здесь. Прочитай его первым делом.

---

## 1. Что за проект

**БИТ.Технолог** — AI-помощник технолога для ООО «ПК Техинком-Центр» (производство пожарной техники).
Генерирует черновики техкарт по свойствам детали за 30-60 минут вместо 4-8 часов.

**Ключевые принципы:**
- **On-premise** (данные не покидают завод, ГОЗ)
- **1С:ERP ready** (XML ресурсные спецификации)
- **«Норма с доказательством»** — каждая операция имеет source (ГОСТ/аналог/правило) + светофор уверенности (зелёный/жёлтый/красный) + топ-3 аналога — **КИЛЛЕР-ФИЧА**
- **5 ролей** (technologist / main_technologist / workshop_chief / tech_admin / llm_admin)
- **UI для 50+ технолога** — НИКАКИХ emoji, символов, непонятных терминов

**Стек:** Python 3.11+ / FastAPI / SQLite (WAL) / Jinja2 / OpenAI-compatible LLM (YandexGPT в проде) / собственный TF-IDF RAG / pytest + Playwright.

---

## 2. Архитектура v0.8 (clean architecture)

```
bit-technolog-prototype/
├── app.py                  (1028 строк, 28 routes, тонкий FastAPI)
├── domain/                 ← бизнес-логика
│   ├── llm_provider.py     (LLMProvider + 3 реализации: OpenAI / Mock / OneC)
│   ├── prompts.py          (8 специализированных промтов: welding, electrical, hydraulic, paint, ...)
│   └── few_shot.py         (динамический few-shot: FEW_SHOT_4C85941A)
├── gateways/               ← внешние интеграции
│   └── one_c_gateway.py    (OneCGateway интерфейс + File + Http заглушка)
├── services/               ← прикладная логика (10 файлов)
│   ├── auth.py            (5 ролей, Fernet-шифрование)
│   ├── rs_factory.py      (РС-фабрика, 8 осей, детерминированная)
│   ├── rag.py             (RAG v2: TF-IDF + material/equipment)
│   ├── evidence.py        (светофор, топ-3 аналога)
│   ├── notices.py         (извещения по ГОСТ 2.503)
│   ├── tp_parser.py       (OCR → структурированный ТП)
│   ├── one_c_loader.py    (загрузка XML из 1С)
│   ├── generate_one_c_mock.py (эмуляция 1С:ERP)
│   ├── metrics.py         (Sprint 9: b и c)
│   └── text_utils.py      (синонимы, Jaccard, морфология)
├── repositories/db.py      (33 таблицы, generic CRUD)
├── migrations/001_v0_8_init.sql
├── seeds/                  (6 seed скриптов)
├── templates/              (15 используемых Jinja2)
├── test/                   (91 pytest: 78 unit + 13 e2e)
├── graphify-out/GRAPH_REPORT.md  (1648 nodes / 3264 edges / 236 communities)
├── archive/                (мёртвый код v0.4, не удалять на всякий случай)
├── attachments/            (46 файлов данных Техинкома, 12M, см. INDEX.md)
├── deploy/                 (Beget деплой скрипты)
├── docs/                   (11 актуальных + adr/ + versions/v0.4/ + legacy-context/)
└── .master_key             (Fernet master key для шифрования секретов, НЕ в git)
```

**Полная архитектура:** [`docs/21-v0.8-design.md`](docs/21-v0.8-design.md), [`docs/adr/0011-v0.8-architecture.md`](docs/adr/0011-v0.8-architecture.md)

---

## 3. Что задеплоено и работает

| | |
|---|---|
| **Production URL** | http://217.114.7.5:8081/ |
| **Версия** | v0.8.5 |
| **Items в БД** | 51 |
| **Эталонов в RAG** | 14 (2 PDF + 5 синтетических + 7 недавних) |
| **Mock LLM** | активен (`is_mock_mode: true`) |
| **Тестов** | 91/91 passing (78 unit + 13 e2e) |
| **Systemd** | `bit-technolog.service` (Beget VPS, root@seefeesnahurid.beget.app) |
| **Health** | `GET /health` → `{"status":"ok","version":"0.8.5",...}` |

**Все 9 экранов работают (200 OK):** `/`, `/products`, `/knowledge`, `/login`, `/metrics`, `/notices`, `/items/{id}/generate`, `/detail/{id}`, `/llm-admin`, `/settings` (303 redirect для анонима).

---

## 4. Ключевые файлы (прочитай в этом порядке)

| # | Файл | Зачем |
|---|---|---|
| 1 | **Этот файл** | Точка входа |
| 2 | [`README.md`](README.md) | Что это, как запустить |
| 3 | [`MISTAKES.md`](MISTAKES.md) | Извлечённые уроки (push ≠ репо, PAT workflow scope, ...) |
| 4 | [`CHANGELOG.md`](CHANGELOG.md) | История по спринтам (v0.4 → v0.8.5) |
| 5 | [`docs/21-v0.8-design.md`](docs/21-v0.8-design.md) | Архитектура v0.8 |
| 6 | [`docs/adr/`](docs/adr/) | 11 ADR, все актуальны |
| 7 | [`graphify-out/GRAPH_REPORT.md`](graphify-out/GRAPH_REPORT.md) | Карта модулей (community hubs) |
| 8 | [`attachments/INDEX.md`](attachments/INDEX.md) | Что в данных Техинкома |
| 9 | [`USER_GUIDE.md`](USER_GUIDE.md) | Гайд для технолога (UI) |

**Скилл Mavis** для архитектурных запросов: `/workspace/.skills/graphify-bit/SKILL.md` (BFS по графу).

---

## 5. Что НЕ сделано (риски для пилота 27.07)

| Что | Статус | Что нужно |
|---|---|---|
| **LLM-ключ Сергея** | НЕ введён | Сергей вводит через `/settings` (Fernet-шифрование) |
| **Login-форма** | Работает (cookie), но тестировалась только с mock | Проверить с реальным пользователем в проде |
| **HttpGateway 1С:ERP** | Заглушка (FileGateway работает) | Реальная интеграция после пилота |
| **Inline-edit операций** | Работает, но не тестировался Playwright в бою | Проверить в браузере перед пилотом |
| **Sprint 9 dashboard метрики** | Показывают реальные цифры только после первого замера | Сделать 1-2 замера на тестовой ТК |
| **50-100 реальных PDF ТП** | Сейчас 14 (2 PDF + 5 синт. + 7 недавних) | Нужно до пилота, иначе RAG будет бедным |
| **КОМПАС-3D Watcher** | Не начат (Phase 3) | После пилота |
| **GitHub Actions CI** | PAT без `workflow` scope | Запросить новый PAT или GitHub App |

---

## 6. Чеклист до пилота 27.07

```
[ ] Сергей ввёл LLM-ключ через /settings
[ ] Login работает с реальным паролем (не mock)
[ ] /metrics показывает реальные цифры (b и c) после 1-2 замеров
[ ] /items/{id}/generate для ЛМША.301314.010 (Упор продольный) end-to-end
[ ] Все 5 табов в /detail открываются без 500
[ ] Inline-edit операций работает (Enter/Esc, автофокус)
[ ] Светофор + подтверждение через /api/operations/{id}/confirm
[ ] Экспорт в 1С через /api/items/{id}/export-to-1c пишет XML в data/one_c_exchange/out/
[ ] /notices/new → /notices/{id} → resolve работает end-to-end
[ ] /llm-admin показывает провайдеры + назначения
[ ] /health → 200 OK, version 0.8.5
[ ] 91/91 тестов зелёных (pytest)
[ ] 16/16 кнопок работают (check_all_buttons.py через Playwright)
[ ] Бэкап prod БД (cp data/bit_technolog_v0_8.db backups/)
[ ] Документация обновлена (USER_GUIDE, README)
```

---

## 7. Правила работы (от Сергея)

**Извлечены из реальных правок. НАРУШАТЬ = получить отпор.**

1. **НЕ выдумывать имена людей.** Если в коде/wiki/чатах нет — спросить. Не предполагать "А = Б".
2. **Цитировать дословно** с пометкой источника (файл, commit, gptunnel).
3. **Противоречия разрешать голосом Сергея**, не додумыванием.
4. **Прямая критика — настаивает.** Спорить, давать другой взгляд, понимать главную цель.
5. **UI для 50+ технолога**: НИКАКИХ emoji, символов, непонятных терминов. Кириллица.
6. **Все тесты зелёные** перед коммитом. После изменений ВСЕГДА `python -m pytest test/`.
7. **Push ≠ репо доступно.** Всегда проверять через API (`git ls-remote origin main` → SHA последнего коммита).
8. **PAT workflow scope** — нельзя push'ить `.github/workflows/*` с PAT без `workflow` scope. Решение: `git rm -r --cached .github/` + .gitignore.
9. **Не давать Сергею команды по распаковке** (tar, Expand-Archive). Только команды которые запускают код в уже распакованной папке.
10. **153-ФЗ / 152-ФЗ** — не логировать ФИО/персданные в открытом виде. audit_logins хранит IP/UA (это ОК).

**Стиль общения с LLM** (Сергей):
- Префикс «ты — лучший в мире [роль]» (опционально)
- Часто «покритикуй», «задавай вопросы», «что я делаю не так?»
- Длинные структурированные промты с контекстом
- Главные LLM: Mavis (основной) > Claude (для крутых задач) >> DeepSeek (раньше активно)

---

## 8. Ключевые факты о Сергее (для контекста)

- **ФИО:** Жуков Сергей Владимирович, 48 лет
- **Семья:** жена Наталья, дочь Алиса (19), сын Глеб (16)
- **Мать:** Жукова Лидия Викторовна, 76 лет, MSA-P (мультисистемная атрофия)
- **Работа:** «Первый БИТ», офис Спортивная (Москва). Руководитель проектного департамента + дирекции по маркетплейсам.
- **Прямой руководитель:** Кирилл Заболотный
- **Продукты свои:** БИТ.УМ, BIT CRM, локализация BITIS
- **Спорт:** бокс (активно), зал
- **Психолог:** работает (тревога/депрессия/выгорание — постоянные)
- **Карьера:** не хочет руководителем офиса, хочет стабилизации и прибыли. Думает об уходе из Бита "почти каждую неделю", но "не очень планирует".
- **Жизненный баланс:** "Жизнь = работа + спорт + семья". "Что такое время на личную жизнь — не сильно понимаю".

Полный профиль: `/workspace/wiki/` (если есть в окружении сессии) или спросить у Сергея.

---

## 9. Что в репо (для новой сессии)

**Клонирование (если нужно):**
```bash
git clone https://github.com/swzhukov/bit-technolog-prototype.git
cd bit-technolog-prototype
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PILOT_AUTH_DISABLED=true python app.py
```

**Тесты:**
```bash
source venv/bin/activate
PILOT_AUTH_DISABLED=true python -m pytest test/ -v
```

**Деплой на prod (если нужны изменения):**
```bash
# 1) Сделай изменения локально, commit, push
# 2) SSH на Beget
sshpass -p "$BEGET_SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@seefeesnahurid.beget.app
# 3) Бэкап + клон
cd /opt/beget
mv bit-technolog bit-technolog-OLD-backup
git clone --depth=1 https://github.com/swzhukov/bit-technolog-prototype.git bit-technolog-new
mv bit-technolog-new bit-technolog
cp -r bit-technolog-OLD-backup/venv bit-technolog/
cp bit-technolog-OLD-backup/.env bit-technolog/
cp bit-technolog-OLD-backup/.master_key bit-technolog/
cp -r bit-technolog-OLD-backup/data bit-technolog/
# 4) Restart
systemctl restart bit-technolog
curl http://localhost:8081/health
```

**Пароль Beget:** в env `$BEGET_SSH_PASSWORD` (или `/workspace/.ssh_beget_pass`).

---

## 10. Что НЕ делать в новой сессии

- ❌ Не удалять `graphify-out/` (GRAPH_REPORT.md — в git, не regenerable)
- ❌ Не удалять `archive/` (там мёртвый код v0.4 на всякий случай, 514K)
- ❌ Не удалять `attachments/` (это реальные данные Техинкома)
- ❌ Не менять схему БД без миграции в `migrations/`
- ❌ Не выдумывать людей/факты. Если в коде/wiki/чатах нет — спросить.
- ❌ Не вводить эмодзи/символы в UI (для 50+ технолога)
- ❌ Не заливать новые PDF/PNG/Office в `attachments/` без понимания что это
- ❌ Не менять prod конфиги (`.env`, `.master_key`) без явного запроса Сергея
- ❌ Не коммитить `.env`, `.master_key`, `data/*.db`, `venv/`, `.github/workflows/*`

---

## 11. Git workflow (правила)

- **Branch:** `main` (PRIVATE репо, только Сергей + Mavis)
- **Commit format:** `M35: что сделано — детали` или `Sprint 9: что — детали`
- **Push:** `git push origin main`
- **Проверка push:** `git ls-remote origin main` → SHA последнего коммита
- **Перед commit:** `python -m pytest test/` → 91/91 passing
- **PAT:** без `workflow` scope, workflows держать локально + .gitignore

---

## 12. Список спринтов (для CHANGELOG)

```
M34 (commit 5481175) — v0.8: полная переделка архитектуры (33 таблицы, 4 слоя)
Sprint 5 (commit 55ec8be) — «Норма с доказательством» (светофор + топ-3 аналога)
Sprint 6 (commit 87c8998) — Извещения end-to-end (ГОСТ 2.503)
Sprint 7 (commit 6a90a57) — Эмуляция 1С:ERP + RAG v2
Sprint 8 (commit 9c65027) — Login-форма + cookie + /settings + HttpGateway
Sprint 9 (commit 43f706c) — Метрики пилота (b+c) + inline-edit + UI полировка
Audit 1+2 (commit ba816b3) — 17 проблем → исправлено (Playwright, кнопки, табы)
REPO_AUDIT (commit 811dc09) — прочитал все 430 файлов, классифицировал
M35 (commit 87a4da2) — REPO_CLEANUP (attachments 222→46, мёртвый код в archive/)
M35b (commit 27199f4) — MISTAKES: PAT workflow scope fix
M35c (commit dc48a40) — Graphify rebuild (1648 nodes, 3264 edges, 236 communities)
```

Полный changelog: [`CHANGELOG.md`](CHANGELOG.md).

---

## 13. Следующая сессия: что делать

**Минимум до пилота 27.07 (по приоритету):**

1. **Прочитать `HANDOFF.md` (этот файл)** — точка входа.
2. **Проверить prod:** `curl http://217.114.7.5:8081/health` → 200 OK v0.8.5.
3. **Пройти чеклист §6** — каждый пункт должен быть ✓.
4. **Если есть вопросы — спросить Сергея, не выдумывать.**
5. **Любые изменения через репо** (commit + push + деплой по §9).

**После пилота 27.07:**
- Сбор метрик b и c за неделю
- Анализ feedback от технологов
- Реальная интеграция HttpGateway с 1С:ERP
- 50-100 реальных PDF ТП → эталоны
- КОМПАС-3D Watcher (Phase 3)

---

**Готов к работе. Если что-то непонятно — спроси Сергея, не додумывай.**

*— Mavis, 2026-07-21*
