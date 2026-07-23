# 🗺️ ROADMAP 2026 — БИТ.Технолог

## Сейчас (Sprint 6, 2026-07)

✅ **v9 + v10 = 0 замечаний × 2 цикла (критерий остановки)**
- URL: `https://seefeesnahurid.beget.app/bit-technolog/`
- Docker + Traefik + Let's Encrypt
- 42 теста ✅
- 4 роли × 16 проверок ✅
- 5 сценариев технолога ✅

## Q3 2026 (июль-сентябрь)

### 27.07 - 09.08: Sprint 7 — Распознавание деталей с чертежей
- D1-D10 (см. SPRINT_7_PLAN.md)
- Загрузка PDF/PNG → автоматическое создание item
- **Killer feature** для технолога: 5-10 мин → 30 сек

### 10.08 - 23.08: Sprint 8 — Pilot fixes + LLM improvements
- A2: bug-fix по фидбэку 4 пользователей (после пилота 27.07)
- D7 (Sprint 6): YandexGPT fallback (нужен folder_id)
- Расширение workshop_context.md
- Улучшение LLM промпта на основе work_history

### 24.08 - 06.09: Sprint 9 — Auto-generate ТК
- На основе распознанного чертежа → генерация ТК
- Auto-suggest операций (материал + размеры)
- Workshop assignment (УОМ/ПКТ/ПВТ)

## Q4 2026 (октябрь-декабрь)

### 07.09 - 20.09: Sprint 10 — 1C integration
- Импорт из 1С (items + materials)
- Экспорт в 1С (item + ТК + РС)
- Sync изменений

### 21.09 - 04.10: Sprint 11 — Pilot 2.0
- Подключение 10+ технологов
- Нагрузочное тестирование (50+ users, 1000+ items)
- Метрики: время генерации ТК, % зелёных, ошибки

### Октябрь-Ноябрь: Sprint 12-13 — Production rollout
- Подключение всех 50+ технологов
- Backup + DR
- Мониторинг + алерты
- SLA 99.5%

### Декабрь: Sprint 14 — Year-end review
- Анализ метрик за Q4
- Roadmap 2027
- Закрытие года

## Q1 2027 (план)

### Multi-tenant
- Подключение других заводов (не только Техинком)
- Per-tenant настройки (workshops, equipment, materials)

### Advanced features
- 3D-модели (STEP/IGES) вместо PDF
- Голосовой ввод для технолога
- Mobile app (iOS/Android)
- Offline mode

### AI improvements
- Fine-tuned модель на work_history
- RAG 2.0 с embeddings
- Multi-modal (вид сбоку + чертёж)

## Ключевые метрики 2026

| Метрика | Сейчас (07.2026) | Q3 цель | Q4 цель | 2027 цель |
|---------|------------------|---------|---------|-----------|
| Технологов в системе | 4 (demo) | 4-10 | 50 | 200 |
| Изделий в БД | 196 | 300 | 1000 | 5000 |
| ТК сгенерировано | 50 | 100 | 500 | 2000 |
| Среднее время создания ТК | ~10 мин | ~5 мин | ~2 мин | ~30 сек |
| % зелёных ТК (без правок) | 7.4% | 20% | 40% | 60% |
| Uptime | n/a | 95% | 99% | 99.5% |
| LLM calls / месяц | 261 | 500 | 2000 | 10000 |

## Что нужно от Сергея

| Сейчас | Q3 | Q4 |
|--------|-----|-----|
| YandexGPT folder_id | Доступ к 1С (read) | Production data |
| A1 (звонки 4 user) | Расширение pilot | Подключение 50+ user |
| D2 (multi-worker) | Backup DR | Multi-region |
| Folder_id для D7 | Yandex Cloud account | Mobile app (iOS/Android) |

