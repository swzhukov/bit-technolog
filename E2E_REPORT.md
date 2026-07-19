# E2E отчёт — работа технологом

**Дата:** 2026-07-19T20:48:27.418489

**Сессий:** 0

## Тайминги

- `404`: 0.313с
- `add_op`: 0.544с
- `admin_dashboard`: 0.415с
- `admin_errors`: 0.319с
- `admin_llm`: 0.392с
- `admin_login_log`: 0.351с
- `admin_settings`: 1.254с
- `admin_system`: 11.971с
- `admin_users`: 0.418с
- `approve`: 3.702с
- `audit`: 0.38с
- `benchmarks`: 0.364с
- `check_restore_list`: 0.734с
- `create_detail`: 0.278с
- `css`: 0.19с
- `delete_op`: 0.575с
- `demo`: 0.248с
- `diff`: 0.398с
- `edit_op`: 0.688с
- `equipment`: 0.326с
- `export_1c_csv`: 0.317с
- `export_excel`: 0.576с
- `export_pdf`: 0.376с
- `generate`: 0.815с
- `health`: 0.616с
- `history`: 0.24с
- `import_bad_json`: 0.128с
- `import_json`: 0.299с
- `import_magic_bytes`: 0.188с
- `import_stats`: 0.259с
- `iot`: 0.369с
- `learning`: 0.596с
- `learning_json`: 0.232с
- `list_details`: 0.31с
- `login`: 0.324с
- `materials`: 0.389с
- `open_after_gen`: 0.759с
- `open_detail`: 0.702с
- `pilot`: 0.522с
- `pilot_learning`: 0.359с
- `pilot_report`: 1.437с
- `print`: 0.344с
- `reopen`: 0.357с
- `role_admin`: 0.137с
- `search`: 0.304с

## Что понравилось (👍)

- Главная открылась быстро
- Поиск работает (с задержкой 300мс)
- Карточка детали рендерится
- Кнопка Генерации видна
- Pre-approve checklist присутствует
- Создание детали работает (303 redirect на /detail/{id})
- Генерация прошла успешно (demo_mode без LLM)
- Операции отображаются
- Замечания отображаются
- Вопросы отображаются
- Inline-edit работает
- Добавление операции работает
- Удаление операции работает (soft-delete)
- Утверждение через API работает
- Pilot dashboard с KPI
- RAG-метрика видна
- Pilot learning dashboard работает
- Demo-сценарий работает
- Справочник оборудования с поиском
- /health: version=0.4.9, uptime=0с, llm=demo_mode
- 404 с навигацией работает
- Смена роли работает
- Admin dashboard рендерится
- Admin settings с группами LLM/Telegram/SMTP
- /admin/errors работает (V8-18)
- Reopen работает (вернуть в работу)
- Роль main_technologist: видит 'approve-chief'
- Роль workshop_chief: видит 'approve-chief'
- Роль admin: видит 'approve-chief'
- PDF export работает
- Excel export работает
- 1С CSV export работает
- Print с QR работает
- Diff версий работает
- CSS содержит @media (mobile-responsive)
- CSS имеет breakpoints
- /api/import/stats работает
- Audit страница рендерится
- History страница показывает события
- Роль 'constructor' открывает карточку (только просмотр)
- Роль 'quality' открывает карточку
- /api/pilot/learning возвращает 4 недель
- JSON импорт: создано 1 деталей
- Невалидный JSON корректно отклонён (400)
- Magic bytes verification работает (.exe не пройдёт как .pdf)

## Что раздражает (👎)

## Баги 🐛

- **[MEDIUM]** Restore UI не виден после удаления
- **[HIGH]** Роль 'normirovshchik' видит кнопку Утвердить (НЕ должно быть!)
