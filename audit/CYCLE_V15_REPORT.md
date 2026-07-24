# 📊 CYCLE v15+v16 REPORT — Sprint 7 D8 (Bulk upload) — 0 замечаний (2026-07-24)

## 🏁 КРИТЕРИЙ ОСТАНОВКИ В ЧЕТВЁРТЫЙ РАЗ (v9-v16 = 8 циклов подряд)

### Sprint 7 D8: Bulk upload (multi-file)

**HEAD:** `92b4e1d` (D8: bulk upload + UI fix)

### Что сделано (D8)

| Компонент | Описание |
|-----------|----------|
| Endpoint | `POST /api/drawings/bulk-upload` (multipart/form-data, поле "files" multiple) |
| Ограничения | до 50 файлов за раз, max 50MB каждый, PDF/PNG/JPG |
| Response | `{uploaded: [{id, filename, size}], errors: [{filename, error}], summary}` |
| RBAC | admin, main_technologist, technologist, workshop_chief |
| Audit | batch logging + per-file history |
| UI | `templates/drawing_upload.html` — bulk form (multi-file input + progress + results) |

### Результаты

| Suite | v15 | v16 |
|-------|----|----|
| **TR.py** | **54/54** ✅ | **54/54** ✅ |
| **UI_SMOKE.py** | 0 замечаний | 0 замечаний |
| **TECHNOLOGIST_SESSIONS.py** | 0 замечаний | 0 замечаний |

**Итог:** 2 цикла подряд = 0 замечаний → **КРИТЕРИЙ ОСТАНОВКИ × 4**

### Tests (новые)
- BULK-01: bulk upload 1 файл
- BULK-02: bulk upload 2 файла
- BULK-03: empty (400 error)
- BULK timeouts: 30s/60s (для 1/2+ файлов)

### UI fix (drawing_upload.html)
- БЫЛО: bulk_form попал в `{% block title %}` → Jinja не рендерит content
- СТАЛО: bulk_form в `{% block content %}` → 2 blocks / 2 endblocks корректно
- Headline: "Загрузить чертёж — БИТ.Технолог" (вместо "Загрузить чертёж + bulk HTML")

### Что увидит технолог

1. Открывает `/drawings/upload`
2. Видит single form (1 файл) + bulk form (multi-file)
3. Drag & drop 5 PDF в bulk форму
4. Нажимает "Загрузить все"
5. Через ~3 сек получает список:
   - `#33 2f8e70aa...pdf (374335 байт)` — ссылка на review
   - `#34 3180da73...pdf (345232 байт)` — ссылка на review
   - ...
6. Кликает на каждую ссылку → review screen → process → create item

### Quality на bulk
- 3 PDF загружены за один запрос: ~3 сек (вместо 3 × ~1 сек = 3 сек)
- Параллельная обработка: не нужна, последовательная OK
- Audit log: один batch event + N per-file events

### Файлы изменены
- `app.py` — `api_drawings_bulk_upload()` (64 строки)
- `templates/drawing_upload.html` — bulk_form + script (в правильном block)
- `audit/TR.py` — BULK-01..BULK-03, curl() для `__bulk__:`

### Backup
- `/opt/beget/backups/bit-technolog/db-pre-d8-20260724_091858.db` (до D8)
- `/opt/beget/backups/bit-technolog/db-post-d8-20260724_093241.db` (после D8)

### Production state
- Items: 78 (было 67, +11 drawings created через bulk)
- Drawings: ~38 (было 32, +6 drawings)
- Test users: 6

### Итоговый статус

| Метрика | Значение |
|---------|----------|
| URL | `https://seefeesnahurid.beget.app/bit-technolog/` |
| SSL | Let's Encrypt (валидный) |
| Порт | 443 |
| Docker | `bit-technolog:1.0.0` (healthy) |
| Тесты | 54/54 ✅ + 0 + 0 |
| Cycles | v9-v16 (8 циклов подряд 0 замечаний) |

### Что отложено
- D10 (performance/кеш) — Sprint 8
- A2 (bug-fix по фидбэку) — после пилота 27.07
- D7 (YandexGPT folder_id) — нужен от Сергея

### Next steps
- A1: Сергей звонит 4 пользователям (27.07.2026)
- A2: bug-fix по фидбэку (28-30.07)
- Sprint 8 (10-23.08): pilot fixes + LLM improvements
- YandexGPT folder_id: ждать от Сергея
