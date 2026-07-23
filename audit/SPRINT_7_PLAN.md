# 🚀 SPRINT 7 PLAN — Распознавание деталей с чертежей (2026-07-27 → 2026-08-09)

## Контекст

**Сергей:** "а как распознать деталь с чертежа? ни черта нет."

**Сейчас:** Технолог получает PDF/PNG чертёж от конструктора → вручную переписывает
обозначение, наименование, материал, размеры в форму создания item → ждёт ~5-10 мин.

**Цель Sprint 7:** Технолог загружает чертёж → система за 10-30 сек
**автоматически создаёт draft item** с предзаполненными полями. Технолог правит
только неточности → экономия 80% времени.

## Что уже есть (наследие Sprint 6)

| Ресурс | Где | Статус |
|--------|-----|--------|
| 12 PDF чертежей деталей | `attachments/*.pdf` (одностраничные) | ✅ |
| 20 PNG сканов чертежей | `attachments/*.png` | ✅ |
| 2 PDF эталона ТП (41+31 стр) | `attachments/5c6e1e30__, cd9db5eb__` | ✅ (OCR в `wiki/tehinkom/ocr/`) |
| tesseract-ocr + tesseract-ocr-rus | Docker image | ✅ |
| poppler-utils (pdftoppm) | Docker image | ✅ (доустановил) |
| LLM (1bitai.ru) | domain/llm_provider.py | ✅ |
| workshop_context.md | `seed/workshop_context.md` | ✅ |
| items.drawing_no, items.drawing_pdf | schema | ✅ (поля готовы) |
| equipment Техинкома (57 единиц) | БД | ✅ |

**Proof of concept (2026-07-23):** OCR на `2f8e70aa_*.pdf` распознал
обозначение `03-ТВ.30.119.00 СБ`, детали `Кронштейн`, `Заглушка`, `Труба`,
материал `60х40х3.0`, ГОСТ `8645-68`, длину `L=200мм`. **Качество ~85%**.

## Задачи Sprint 7 (10 задач, 2 недели)

### D1. Drawing upload endpoint (1 день)
**Что:** `POST /api/drawings/upload` (multipart, PDF/PNG/JPG, max 50MB)
**Где:** `app.py` + `services/drawing_storage.py`
**RBAC:** all roles
**Storage:** `/opt/beget/bit-technolog/data/drawings/{uuid}.pdf`
**Table:** `drawings` (id, item_id NULL, file_path, format, uploaded_by, uploaded_at, ocr_status, ocr_text, llm_extracted_json)

### D2. PDF→PNG + OCR pipeline (2 дня)
**Что:** `services/ocr_pipeline.py`
- PDF: `pdftoppm -r 300 -png` → page-1.png
- PNG/JPG: прямой
- OCR: `tesseract page-1.png out -l rus` → out.txt
- Сохранить в `drawings.ocr_text`

### D3. LLM extraction (2 дня)
**Что:** `domain/drawing_extractor.py`
**Промт:** "Извлеки из текста чертежа: designation, name, material, dimensions,
mass, surface_treatment, gost. Верни JSON."
**Fallback:** regex parser для простых случаев
**Output:** `drawings.llm_extracted_json`

### D4. Auto-create draft item (1 день)
**Что:** `POST /api/drawings/{id}/process` → создаёт item в БД
- `designation` из LLM
- `name` из LLM
- `material_id` lookup или NULL
- `drawing_pdf` → file_path
- `drawing_no` → designation
- `level='detail'`, status='draft'

### D5. UI upload form (2 дня)
**Что:** `templates/details_new.html` (расширить)
- Кнопка "📎 Загрузить чертёж" (но без emoji — у нас 50+ технологов 40+)
- Drag & drop зона
- Progress bar при OCR+LLM (10-30 сек)
- Redirect на review screen

### D6. Review screen (2 дня)
**Что:** `templates/drawing_review.html`
- Превью PDF (первая страница как PNG)
- Распознанные поля в форме (можно править)
- Кнопки "Принять" / "Перегенерировать" / "Отклонить"
- При "Принять" — создаётся item с подтверждёнными полями

### D7. RBAC (0.5 дня)
- All roles: upload, review
- Только admin/main_tech: подтверждение item в БД
- workshop_chief: только просмотр распознанных

### D8. Bulk upload (1 день)
- Drag & drop нескольких файлов
- Queue processing (показывать прогресс)
- Failure handling (один не распознался — остальные ОК)

### D9. Тесты (2 дня)
- 9 тестов в `TR.py` (DRAW-01..DRAW-09):
  - D1: upload PDF → 201, drawing row created
  - D2: upload PNG → 201
  - D3: upload JPG → 201
  - D4: upload >50MB → 413
  - D5: upload без auth → 401/403
  - D6: process drawing → item создан с правильными полями
  - D7: process несуществующего → 404
  - D8: process уже processed → 409
  - D9: bulk upload 3 PDF → 201+201+201
- `TECHNOLOGIST_SESSIONS.py`: сценарий T6 — "Распознать деталь с чертежа"
- `UI_SMOKE.py`: проверка upload form

### D10. Performance + cache (1 день)
- OCR кеш (если чертёж уже распознан → быстрый путь)
- Background task (не блокировать UI при долгом OCR+LLM)
- Метрики: время OCR, % успешных распознаваний, поля которые часто ошибочны

**ИТОГО: ~12.5 дней, 2 недели (есть буфер на 1.5 дня)**

## Roadmap до конца 2026

### Sprint 7 (27.07 - 09.08) — Drawing recognition
- D1-D10 как выше
- **Цель:** Технолог загружает PDF → item создан автоматически

### Sprint 8 (10.08 - 23.08) — Pilot fixes + LLM improvements
- A2: bug-fixes по фидбэку 4 пользователей
- D7 (Sprint 6): YandexGPT fallback (нужен folder_id)
- Перевод workshop_context.md на 2-3 цеха
- Улучшение LLM промпта на основе work_history (Sprint 6 E1)

### Sprint 9 (24.08 - 06.09) — Auto-generate ТК
- Расширение D1-D10: на основе распознанного чертежа → генерация ТК
- Auto-suggest операций на основе material + dimensions
- LLM: "Какие операции нужны для трубы 60х40х3.0 длиной 200мм?"
- Workshop assignment (УОМ/ПКТ/ПВТ)

### Sprint 10 (07.09 - 20.09) — 1C integration
- Импорт из 1С (items + materials)
- Экспорт в 1С (item + ТК + РС)
- Sync изменений

### Sprint 11+ (Q4 2026) — Production rollout
- Подключение всех 50+ технологов
- Нагрузочное тестирование
- Backup + DR
- Мониторинг + алерты

## Open questions для Сергея

1. **Качество OCR:** для каких ещё чертежей кроме 03-ТВ.30.119 нужно распознавание?
   Размеры, материал, шероховатость, допуски, покрытие?
2. **YandexGPT folder_id** — для D7 (Sprint 6) — fallback когда 1bitai.ru недоступен
3. **Pilot сценарий 6 (D9):** готов ли ты дать пользователям доступ к upload-у?
   Или оставить только для admin/main_tech?
4. **Хранилище чертежей:** текущий `/data/drawings/` — 12 PDF × 1MB = 12MB.
   За год может быть 50+ технологов × 100 чертежей = 5000 файлов. Хватит ли места?
5. **Очистка:** удалять ли чертежи после создания item? Или хранить навсегда?

## Definition of Done для Sprint 7

- [ ] Все 10 задач (D1-D10) merged в main
- [ ] TR.py: DRAW-01..DRAW-09 все зелёные
- [ ] UI_SMOKE.py: проверка upload form
- [ ] TECHNOLOGIST_SESSIONS.py: T6 сценарий "Распознать деталь с чертежа"
- [ ] Playwright manual: загрузка 12 PDF → 12 items созданы с правильными полями (≥80%)
- [ ] 0 замечаний × 2 цикла (v11 + v12)
- [ ] Документация обновлена: USER_GUIDE.md, CARTE_v10.md

## Rollback

Sprint 7 изменения ограничены:
- Новый endpoint `/api/drawings/*` — легко отключить
- Новая таблица `drawings` — можно не заполнять
- Изменения в `details_new.html` — additive (старая форма работает)

**Если что-то критичное:**
```bash
git revert <sprint-7-merge-commit>
docker compose build && docker compose up -d
```

## Связь с пилотом 27.07

Sprint 7 СТАРТУЕТ сразу после пилота. Если в пилоте выяснится, что upload
критичен — приоритет D1+D5+D6 (минимальный upload) поднимем на пилот.
