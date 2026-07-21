# HOW TO BOOTSTRAP — инструкция для новой сессии Mavis

> **КРИТИЧНО:** В новой сессии у тебя НЕТ ни проекта, ни git credentials, ни prod-доступа.
> Sandbox чистый. Этот файл — инструкция как всё поднять.

## Шаг 1: Клонируй проект

```bash
cd /workspace
git clone https://github.com/swzhukov/bit-technolog-prototype.git
cd bit-technolog-prototype
```

**Почему это работает:** репо временно открыто как PUBLIC (сделано 2026-07-21). Никаких токенов не нужно. После поднятия попроси Сергея вернуть PRIVATE.

## Шаг 2: Прочитай HANDOFF.md

```bash
cat HANDOFF.md
```

Это **12K точка входа** — статус, архитектура, чеклист, правила.

Также прочитай:
- `README.md` (v0.8.5)
- `MISTAKES.md` (уроки)
- `CHANGELOG.md` (история)
- `graphify-out/GRAPH_REPORT.md` (карта модулей)

## Шаг 3: Подними окружение

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Шаг 4: Проверь тесты

```bash
PILOT_AUTH_DISABLED=true python -m pytest test/ -v
```

Ожидаемо: **91/91 passing** (78 unit + 13 e2e).

## Шаг 5: Запусти локально

```bash
PILOT_AUTH_DISABLED=true python app.py
```

Открой `http://localhost:8080/`.

## Шаг 6: Prod (если нужно)

**Prod URL:** http://217.114.7.5:8081/

**SSH на Beget** — НЕ настроен в твоей сессии. Если нужны изменения в prod:
1. Попроси Сергея дать тебе `$BEGET_SSH_PASSWORD`
2. `sshpass -p "$BEGET_SSH_PASSWORD" ssh root@seefeesnahurid.beget.app`
3. Или попроси Сергея сделать деплой сам

## Что в репо

- 51 items, 14 эталонов, v0.8.5 задеплоена
- Все 9 экранов работают
- MockLLMProvider активен (Сергей ещё не ввёл реальный ключ)
- Тестов 91/91

## Что НЕ в репо (и не должно быть)

- `.env` (секреты prod)
- `.master_key` (Fernet master key)
- `data/*.db` (БД — есть на сервере Beget)
- `venv/` (зависимости)
- `.rag/` (кэш RAG)

## Когда поднимешь — скажи Сергею

Он:
1. Вернёт репо PRIVATE (важно для безопасности)
2. Даст тебе SSH доступ к prod если нужен
3. Расскажет какая задача сейчас актуальна

---

*— Создано 2026-07-21 в спешке, чтобы новая сессия не тупила*
