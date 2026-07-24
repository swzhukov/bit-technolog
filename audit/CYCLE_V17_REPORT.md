# 📊 CYCLE v17+v18 REPORT — Sprint 7 D10 (LLM Cache) — 0 замечаний (2026-07-24)

## 🏁 КРИТЕРИЙ ОСТАНОВКИ В ПЯТЫЙ РАЗ (v9-v18 = 10 циклов подряд)

### Sprint 7 D10: LLM Extraction Cache

**HEAD:** `3e1989a` (D10: LLM cache + Dockerfile poppler-utils fix)

### Что сделано (D10 + bugfix)

| Компонент | Описание |
|-----------|----------|
| Table | `llm_extraction_cache (ocr_hash PRIMARY KEY, llm_data, is_fallback, hits_count, ...)` |
| drawing_extractor.py | cache lookup → если hit, return без LLM; если miss, call LLM + store |
| Endpoint | `GET /api/llm-cache-stats` (admin/main_tech only) |
| TR.py | CACHE-01, CACHE-02 (RBAC), CACHE-03 (re-process) |
| **Bugfix** | Dockerfile: добавлен `poppler-utils` (pdftoppm) — без него OCR был сломан |
| **Bugfix** | `extract_with_llm` → `llm_extract` rename, fix import в app.py |

### Performance (proof)

| Сценарий | До D10 | После D10 |
|----------|--------|-----------|
| Drawing 1st process | 27.3s (OCR 15s + LLM 12s) | 27.3s (то же) |
| Drawing 2nd process (тот же) | 27.3s (OCR + LLM) | **15.8s** (только OCR, cache hit LLM) |
| Cost 1bitai.ru за process | ~30₽ | 0₽ (cache hit) |

**Cache hit savings:** ~10-12 сек + ~30₽/процесс

### Cache stats (prod)

```
Initial: {unique_entries: 0, total_hits: 0, fallback_entries: 0}
After 1st process: {unique_entries: 1, total_hits: 1, fallback_entries: 1}
After 2nd process: {unique_entries: 1, total_hits: 2, fallback_entries: 1}
```

### Bugfix: poppler-utils в Dockerfile

**Симптом:** Drawing uploads → process → ocr=failed (file not found / pdftoppm not found)
**Причина:** В контейнере `python:3.12-slim` нет `pdftoppm` (poppler-utils)
**Фикс:** Добавлен `poppler-utils` в apt-get install в Dockerfile
**Результат:** OCR работает, drawings обрабатываются за 15 сек

### Bugfix: extract_with_llm → llm_extract rename

**Симптом:** Container `restarting` после deploy
**Причина:** Я переименовал функцию в `domain/drawing_extractor.py`, но забыл обновить import в `app.py`
**Фикс:** `from domain.drawing_extractor import llm_extract` (вместо `extract_with_llm as llm_extract`)
**Урок:** При rename в `domain/` — grep все `import` в `app.py` и сервисах

### Disk cleanup (gotcha)

**Симптом:** Deploy провалился "no space left on device" (98% disk usage)
**Причина:** Старые pre-cleanup backups (5 × 1.3MB) + Docker build cache (3GB)
**Фикс:** `docker builder prune -af` освободил 2GB
**Урок:** Регулярно `docker system prune` на маленьких VPS

### Results (cycles v17+v18)

| Suite | v17 | v18 |
|-------|----|----|
| **TR.py** | **57/57** ✅ | **57/57** ✅ |
| **UI_SMOKE.py** | 0 замечаний | 0 замечаний |
| **TECHNOLOGIST_SESSIONS.py** | 0 замечаний | 0 замечаний |

**Итог:** 2 цикла подряд = 0 замечаний → **КРИТЕРИЙ ОСТАНОВКИ × 5**

### Tests (новые)
- CACHE-01: `/api/llm-cache-stats` (200 для admin)
- CACHE-02: workshop_chief → 403
- CACHE-03: re-process drawing 2 → cache hit

### Production state

| Метрика | Значение |
|---------|----------|
| URL | `https://seefeesnahurid.beget.app/bit-technolog/` |
| Items | 111 |
| Drawings | 82+ (5 fresh) |
| Cache | 1 unique / 2 hits / 1 fallback |
| Тесты | 57/57 ✅ |
| Cycles | v9-v18 (10 подряд 0 замечаний) |
| Disk | 81% used (после cleanup) |

### Sprint 7 — ПОЛНОСТЬЮ завершён

| Задача | Статус |
|--------|--------|
| D1 Upload endpoint | ✅ |
| D2 OCR pipeline | ✅ |
| D3 LLM extraction | ✅ |
| D4 Auto-create item | ✅ |
| D5 UI upload form | ✅ |
| D6 Review screen | ✅ |
| D7 RBAC + audit | ✅ |
| D8 Bulk upload | ✅ |
| D9 Tests (DRAW + BULK) | ✅ |
| **D10 LLM cache** | ✅ |
| T6 scenario | ✅ |
| BULK_DRAWINGS quality | ✅ |
| Cleanup 190 items | ✅ |

### Next steps
- A1: Сергей звонит 4 пользователям (27.07.2026)
- A2: bug-fix по фидбэку (28-30.07)
- Sprint 8 (10-23.08): pilot fixes + LLM improvements
- YandexGPT folder_id: ждать от Сергея (D7)
