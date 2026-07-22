# M37-#7: Load Test Report (50 users, 60s)

**Дата:** 2026-07-22, 12:27-12:28
**Host:** https://217.114.7.5:8081 (prod, TLS, v1.0.0)
**Сценарий:** 50 пользователей, spawn rate 10/сек
**Длительность:** 60 сек

## Результаты

### Throughput
- **Total requests:** 1346
- **Requests/sec:** 22.7 (avg), 22.9 (last 10s)

### Latency (p50 / p95 / p99 / max)
- **Aggregated:** 180ms / 370ms / 640ms / 850ms
- **GET /** (dashboard): 170ms / 190ms / 280ms / 412ms
- **GET /detail/3:** 220ms / 300ms / 400ms / 540ms
- **POST /login:** 600ms / 690ms / 850ms (создание session, bcrypt)

### Errors
- **Total errors:** 78 / 1346 = 5.79%
- **Все ошибки 403** на /settings, /llm-admin (RBAC — non-admin юзеры, корректно)
- **0× 5xx** — приложение стабильно под нагрузкой

### Endpoint breakdown
| Endpoint | Requests | Fails | p50 | p95 |
|----------|----------|-------|-----|-----|
| GET / | 238 | 0 | 170 | 190 |
| GET /detail/3 | 446 | 0 | 220 | 300 |
| GET /products | 294 | 0 | 180 | 260 |
| GET /profiles | 133 | 0 | 160 | 190 |
| GET /metrics | 62 | 0 | 180 | 190 |
| POST /login | 50 | 0 | 600 | 690 |
| GET /llm-admin | 61 | 35 (403) | 140 | 200 |
| GET /settings | 62 | 43 (403) | 140 | 190 |

## Выводы

1. **Стабильно** — 50 одновременных пользователей не роняют приложение
2. **Latency OK** — p95=370мс (бюджет 1 сек для UI отклика)
3. **0× 5xx** — внутренние ошибки отсутствуют
4. **RBAC работает** — 78 ошибок все 403, не 500
5. **Login медленнее** — 600мс из-за bcrypt hash. До пилота: кэшировать.

## Что НЕ тестировалось

- Реальные LLM-вызовы (semaphore 5, очередь до 10) — 50 юзеров
  одновременно жмут "Сгенерировать" → первые 5 идут, остальные ждут.
  Это by design.
- SQLite concurrent writes — WAL mode должен справиться.

## Что добавить в load test v2

- Тестировать POST /items/{id}/generate (LLM вызов) — но 24 сек на
  вызов, не влезет в 60s
- POST /api/operations/{id}/update (inline-edit)
- Тестировать 100+ юзеров (с запасом)
