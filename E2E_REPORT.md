# E2E отчёт — работа технологом

**Дата:** 2026-07-20T04:24:26.341693

**Сессий:** 0

## Тайминги

- `404`: 0.278с
- `add_op`: 0.5с
- `admin_dashboard`: 0.381с
- `admin_errors`: 0.275с
- `admin_llm`: 0.355с
- `admin_login_log`: 0.342с
- `admin_settings`: 1.119с
- `admin_system`: 10.304с
- `admin_users`: 0.386с
- `approve`: 3.061с
- `audit`: 0.334с
- `benchmarks`: 0.348с
- `check_restore_list`: 0.682с
- `create_detail`: 0.284с
- `css`: 0.172с
- `delete_op`: 0.568с
- `demo`: 0.242с
- `diff`: 0.369с
- `edit_op`: 0.697с
- `equipment`: 0.291с
- `export_1c_csv`: 0.275с
- `export_excel`: 1.136с
- `export_pdf`: 0.528с
- `generate`: 0.797с
- `health`: 0.564с
- `history`: 0.221с
- `import_bad_json`: 0.129с
- `import_json`: 0.294с
- `import_magic_bytes`: 0.166с
- `import_stats`: 0.231с
- `iot`: 0.347с
- `learning`: 0.567с
- `learning_json`: 0.207с
- `list_details`: 0.302с
- `login`: 0.316с
- `materials`: 0.339с
- `open_after_gen`: 0.723с
- `open_detail`: 0.671с
- `pilot`: 0.484с
- `pilot_learning`: 0.331с
- `pilot_report`: 1.335с
- `print`: 0.298с
- `reopen`: 0.357с
- `role_admin`: 0.119с
- `search`: 0.284с

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
- Badge текущей роли отображается в header
- Badge показывает выбранную роль (data-role=technologist)
- Cookie bit_role НЕ HttpOnly (JS может прочитать): bit_role=main_technologist; Max-Age=31536000; Path=/; SameSite=lax
- Cookie bit_role=main_technologist в Set-Cookie
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
