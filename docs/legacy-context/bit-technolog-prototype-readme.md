# БИТ.Технолог — Прототип: как загрузить в MiniMax Code

> **Дата:** 2026-07-16
> **Назначение:** инструкция по загрузке контекста в MiniMax Code (https://agent.minimax.io/)

---

## 0. Что у нас есть

Контекст прототипа БИТ.Технолог, готовый к загрузке в MiniMax Code:

| Файл | Назначение | Размер |
|---|---|---|
| `bit-technolog-prototype-context.md` | **Главный контекст** — что, для кого, зачем | 21 КБ |
| `bit-technolog-prototype-tasks.md` | **Задачи** — что делать, в каком порядке | 40 КБ |
| `bit-technolog-prototype-data.json` | **Mock данные** — 10 деталей, 8 станков, структура | 8 КБ |
| `bit-technolog-prototype-prompt.txt` | **Промт v0.2** — для LLM-агента | 6 КБ |

**Итого:** ~75 КБ текста. Это **~25K токенов** — отлично влезает в 1M контекст MiniMax M3.

---

## 1. Что такое MiniMax Code

**MiniMax Code** — AI coding agent от MiniMax, построенный на модели **MiniMax M3** (1M контекст, мультимодальная).

**Возможности:**
- Читает до 1M токенов контекста
- Multi-file edits
- Test-validated repairs
- Agent Teams (multi-agent workflows)
- Skills & memory
- Поддержка MCP tools

**Доступ:**
- **Web:** https://agent.minimax.io/
- **Desktop:** https://agent.minimax.io/download (macOS, Windows)
- **API:** Anthropic-compatible `https://api.minimax.io/anthropic`

---

## 2. Вариант 1: Web-интерфейс (рекомендую)

### Шаг 1. Регистрация
1. Открыть https://agent.minimax.io/
2. Создать аккаунт (бесплатный тариф)
3. Подтвердить email
4. Проверить Token Plan / кредиты

### Шаг 2. Создание проекта
1. Нажать "+ New Project" (или аналогичная кнопка)
2. Назвать проект: `bit-technolog-prototype`
3. Выбрать тип: "Coder" (для кодинга)

### Шаг 3. Загрузка контекста
1. В проекте найти раздел "Files" / "Context"
2. Загрузить файлы:
   - `bit-technolog-prototype-context.md` (главный)
   - `bit-technolog-prototype-tasks.md` (задачи)
   - `bit-technolog-prototype-data.json` (mock данные)
   - `bit-technolog-prototype-prompt.txt` (промт)
3. Подождать пока MiniMax Code проиндексирует

### Шаг 4. Задача для MiniMax Code
Скопировать и вставить в чат:

```
Создай прототип веб-приложения БИТ.Технолог по контексту в файлах
bit-technolog-prototype-*. Это FastAPI-приложение с HTMX-фронтендом,
которое демонстрирует AI-помощника технолога для создания техкарт.

Стек:
- Python 3.11+
- FastAPI
- Jinja2 + HTMX
- SQLite (встроенная)
- anthropic SDK
- PicoCSS

Что нужно сделать:
1. Структура проекта (см. tasks.md → Задача 1)
2. requirements.txt
3. equipment.json + structure.json (взять из data.json)
4. mock_data.py (10 деталей из data.json)
5. few_shot.py (пример 4c85941a из tasks.md)
6. prompts.py (промт из prompt.txt)
7. app.py (FastAPI, single file)
8. templates/*.html (Jinja2 + HTMX)
9. static/style.css (PicoCSS inline)
10. README.md

Не нужно:
- Docker
- PostgreSQL (только SQLite)
- 1С-интеграция (mock)
- Watcher КОМПАС (mock)
- RAG
- Аутентификация
- Аудит
- APScheduler
- Alembic

Критерии приёмки — в конце tasks.md.
```

### Шаг 5. Итерация
- MiniMax Code начнёт создавать файлы
- Ревьюить каждый файл
- Просить правки: "Добавь loading spinner на кнопку генерации"
- Тестировать локально: `cd /path/to/project && python app.py`

### Шаг 6. Деплой
- Локально: `python app.py` → http://localhost:8080
- На сервер Техинкома: через SSH + python

---

## 3. Вариант 2: Desktop app

### Шаг 1. Установка
1. Скачать с https://agent.minimax.io/download
2. Установить (macOS / Windows)
3. Войти в аккаунт

### Шаг 2. Создать проект
1. File → New Project
2. Назвать: `bit-technolog-prototype`
3. Выбрать папку

### Шаг 3. Загрузить файлы
1. Скопировать 4 файла в папку проекта
2. MiniMax Code проиндексирует автоматически

### Шаг 4. Задача
Вставить ту же задачу (см. выше)

---

## 4. Вариант 3: API (для продвинутых)

### Установка
```bash
# Через pip
pip install minimax-ai

# Или через npm
npm install @minimax/ai-sdk
```

### Использование
```python
from minimax import MiniMax

client = MiniMax(
    api_key="sk-...",
    base_url="https://api.minimax.io/anthropic"  # Anthropic-compatible
)

# Отправить задачу с контекстом
with open("bit-technolog-prototype-context.md") as f:
    context = f.read()

with open("bit-technolog-prototype-tasks.md") as f:
    tasks = f.read()

with open("bit-technolog-prototype-prompt.txt") as f:
    prompt = f.read()

with open("bit-technolog-prototype-data.json") as f:
    data = f.read()

response = client.messages.create(
    model="MiniMax-M3",
    max_tokens=16000,
    messages=[{
        "role": "user",
        "content": f"""
Контекст:
{context}

Задачи:
{tasks}

Промт:
{prompt}

Данные:
{data}

ЗАДАЧА: Создай прототип БИТ.Технолог по этим спецификациям.
"""
    }]
)

print(response.content[0].text)
```

---

## 5. Что делать после получения прототипа от MiniMax Code

### Шаг 1. Ревью
- Проверить, что все файлы созданы
- Проверить структуру проекта
- Прочитать README

### Шаг 2. Локальный запуск
```bash
# Перейти в папку проекта
cd bit-technolog-prototype

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Скопировать .env.example в .env и вставить ANTHROPIC_API_KEY
cp .env.example .env
nano .env  # вставить ключ

# Запустить
python app.py
```

### Шаг 3. Открыть в браузере
http://localhost:8080

### Шаг 4. Протестировать
- [ ] Видны 10 mock-деталей
- [ ] Клик на деталь → карточка
- [ ] "Сгенерировать черновик" → работает
- [ ] 6 вкладок отображаются
- [ ] Утвердить → статус меняется
- [ ] Экспорт в Excel → скачивается
- [ ] Стоимость ≤ 30 ₽ за 10 генераций

### Шаг 5. Демонстрация
- Записать видео-демо (3-5 минут)
- Подготовить презентацию для Техинкома
- Подготовить предложение о пилоте

### Шаг 6. Итерация с технологом
- Если есть доступ к Баранову М.А. — показать прототип
- Собрать фидбек
- Итерировать через MiniMax Code

---

## 6. Бюджет

**MiniMax Code (бесплатный тариф):** ограниченное количество запросов.
**MiniMax Code (платный):** ~$20-50/мес.

**Anthropic API (для LLM-агента):**
- 1 генерация ≈ 2.7 ₽
- 10 тестовых деталей = 27 ₽
- 100 генераций = 270 ₽
- 1000 генераций = 2700 ₽

**Итого на прототип:** < 100 ₽ (LLM) + MiniMax Code тариф

---

## 7. Что дальше

### После прототипа
1. Демонстрация Техинкому (Баранов М.А. + Голубев П.В.)
2. Получение обратной связи
3. Согласование пилота
4. Подготовка коммерческого предложения

### Для пилота
1. Реальная интеграция с 1С:ERP (Connector)
2. Реальный Watcher КОМПАС-3D
3. RAG на базе ведомости трудоёмкости
4. Docker Compose для on-premise деплоя
5. PostgreSQL вместо SQLite

### Для тиражирования
1. Multi-tenant архитектура
2. White-label
3. Custdev с другими клиентами Бита
4. Roadmap на год

---

## 8. Контакты

- **MiniMax Code:** https://agent.minimax.io/, support@minimax.io
- **Anthropic API:** https://console.anthropic.com/
- **Продукт БИТ.Технолог:** Сергей Жуков, Первый БИТ

---

**Версия:** 1.0 (2026-07-16)
**Готов к загрузке.**
