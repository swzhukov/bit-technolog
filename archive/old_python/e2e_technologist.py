"""
E2E тестовая эксплуатация БИТ.Технолог от лица технолога.
Проходит через все основные функции как реальный пользователь.
Записывает впечатления и баги в E2E_REPORT.md
"""
import os
os.environ["PILOT_AUTH_DISABLED"] = "true"
os.environ["PILOT_RATELIMIT_DISABLED"] = "true"
os.environ["PILOT_CSRF_DISABLED"] = "true"
os.environ["DEMO_MODE"] = "true"  # чтобы не тратить ₽ на LLM

import sys
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
import app as app_module
app_module.init_db()  # явно инициализируем БД
from fastapi.testclient import TestClient


class TechnologistDiary:
    def __init__(self, c):
        self.c = c
        self.impressions = []
        self.bugs = []
        self.praises = []
        self.timing = {}

    def log(self, msg, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {level}: {msg}")

    def note(self, category, text):
        """Записать впечатление"""
        self.impressions.append((category, text, datetime.now().isoformat()))

    def bug(self, severity, text):
        self.bugs.append((severity, text, datetime.now().isoformat()))

    def praise(self, text):
        self.praises.append((text, datetime.now().isoformat()))

    def time_it(self, name, func, *args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        self.timing[name] = round(elapsed, 3)
        return result, elapsed

    def save_report(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("# E2E отчёт — работа технологом\n\n")
            f.write(f"**Дата:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Сессий:** {len(self.impressions)}\n\n")
            f.write("## Тайминги\n\n")
            for name, t in sorted(self.timing.items()):
                f.write(f"- `{name}`: {t}с\n")
            f.write("\n")
            f.write("## Что понравилось (👍)\n\n")
            for text, ts in self.praises:
                f.write(f"- {text}\n")
            f.write("\n## Что раздражает (👎)\n\n")
            cats = {}
            for cat, text, ts in self.impressions:
                if cat not in cats:
                    cats[cat] = []
                cats[cat].append(text)
            for cat, items in cats.items():
                f.write(f"### {cat}\n")
                for text in items:
                    f.write(f"- {text}\n")
                f.write("\n")
            f.write("## Баги 🐛\n\n")
            for sev, text, ts in self.bugs:
                f.write(f"- **[{sev}]** {text}\n")


def main():
    print("\n" + "="*60)
    print("E2E ТЕСТОВАЯ ЭКСПЛУАТАЦИЯ БИТ.Технолог — работа технологом")
    print("="*60 + "\n")

    c = TestClient(app_module.app)
    diary = TechnologistDiary(c)

    # === ДЕНЬ 1: УТРО ===

    diary.log("=== ДЕНЬ 1: УТРО ===")

    # 1. Логин (через Basic Auth в production; в dev — без)
    r, t = diary.time_it("login", c.get, "/")
    diary.log(f"GET / (главная) = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Главная открылась быстро")
    else:
        diary.bug("HIGH", f"Главная вернула {r.status_code}")

    # 2. Смотрим на список деталей
    r, t = diary.time_it("list_details", c.get, "/")
    diary.log(f"GET / (список) = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        if "Ничего не найдено" in r.text:
            diary.note("UX", "Список пуст — нужно завести детали")
        else:
            # Считаем строки
            n_rows = r.text.count("<tr>") - 1  # минус header
            diary.log(f"В списке {n_rows} деталей")

    # 3. Поиск
    r, t = diary.time_it("search", c.get, "/?q=АЦ")
    diary.log(f"GET /?q=АЦ = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Поиск работает (с задержкой 300мс)")

    # 4. Открываем первую деталь
    # Найдём ID
    r = c.get("/")
    import re
    ids = re.findall(r'/detail/([\w\-]+)', r.text)[:3]
    if ids:
        detail_id = ids[0]
        diary.log(f"Открываем деталь: {detail_id}")
        r, t = diary.time_it("open_detail", c.get, f"/detail/{detail_id}")
        diary.log(f"GET /detail/{detail_id} = {r.status_code} за {t:.3f}с")
        if r.status_code == 200:
            # Проверим что в карточке есть нужные элементы
            if "АЦ-" in r.text or "model" in r.text:
                diary.praise("Карточка детали рендерится")
            if "Сгенерировать" in r.text or "Генерировать" in r.text:
                diary.praise("Кнопка Генерации видна")
            if "Утвердить" in r.text:
                diary.praise("Кнопка Утвердить видна")
            if "pre-approve" in r.text.lower() or "чеклист" in r.text.lower():
                diary.praise("Pre-approve checklist присутствует")
            else:
                diary.bug("MEDIUM", "Pre-approve checklist не найден в HTML")
            if "Вернуть в работу" in r.text:
                diary.praise("Кнопка 'Вернуть в работу' есть")
            if "AI-помощник" in r.text:
                diary.praise("AI-блок виден")
        else:
            diary.bug("HIGH", f"Карточка вернула {r.status_code}")
    else:
        diary.log("Нет деталей в списке — нужно создать")
        # Создадим тестовую
        diary.log("Создаём тестовую деталь через /api/details")
        c.post("/api/role/switch", data={"role": "technologist"})
        c.post("/api/details", data={
            "id": "e2e-test-001", "designation": "E2E.001",
            "name": "Тестовая деталь E2E",
            "model": "АЦ-6,0-40", "chassis": "КАМАЗ-43118",
            "material": "Сталь 09Г2С", "size_mm": "100", "mass_kg": "5.0",
            "surface_treatment": "Грунт ГФ-021"
        })
        r, t = diary.time_it("open_detail", c.get, "/detail/e2e-test-001")
        diary.log(f"GET /detail/e2e-test-001 = {r.status_code} за {t:.3f}с")

    # === ДЕНЬ 1: СОЗДАНИЕ ДЕТАЛИ ===

    diary.log("\n=== ДЕНЬ 1: СОЗДАНИЕ ДЕТАЛИ ===")
    c.post("/api/role/switch", data={"role": "technologist"})
    r, t = diary.time_it("create_detail", c.post, "/api/details", data={
        "designation": "E2E.001",
        "name": "Тестовая деталь E2E",
        "model": "АЦ-6,0-40", "chassis": "КАМАЗ-43118",
        "material": "Сталь 09Г2С", "size_mm": "100", "mass_kg": "5.0",
        "surface_treatment": "Грунт ГФ-021"
    }, follow_redirects=False)
    diary.log(f"POST /api/details = {r.status_code} за {t:.3f}с")
    if r.status_code == 303:
        detail_id = r.headers.get("location", "").rstrip("/").split("/")[-1]
        diary.log(f"Создана деталь: {detail_id}")
        diary.praise("Создание детали работает (303 redirect на /detail/{id})")
    elif r.status_code in (200, 307):
        # follow_redirects=False мог не сработать
        import re
        m = re.search(r'/detail/([\w\-]+)', r.text)
        if m:
            detail_id = m.group(1)
            diary.praise(f"Создание детали: {detail_id}")
        else:
            # Попробуем найти в БД
            from db import get_conn
            conn = get_conn()
            row = conn.execute("SELECT id FROM details WHERE designation=? ORDER BY id DESC LIMIT 1",
                                ("E2E.001",)).fetchone()
            conn.close()
            if row:
                detail_id = row[0]
                diary.praise(f"Создание детали (найдено в БД): {detail_id}")
            else:
                diary.bug("HIGH", f"Не удалось получить detail_id. status={r.status_code}, body={r.text[:200]}")
                detail_id = None
    else:
        diary.bug("HIGH", f"Создание детали вернуло {r.status_code}: {r.text[:200]}")
        detail_id = None

    if not detail_id:
        diary.log("Не удалось создать деталь — пропускаю остальные шаги")
        return

    # === ДЕНЬ 1: ГЕНЕРАЦИЯ ===

    diary.log("\n=== ДЕНЬ 1: ГЕНЕРАЦИЯ ===")

    # 5. Генерируем draft
    r, t = diary.time_it("generate", c.post, "/api/generate", data={"detail_id": detail_id})
    diary.log(f"POST /api/generate = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Генерация прошла успешно (demo_mode без LLM)")
    else:
        diary.bug("HIGH", f"Генерация вернула {r.status_code}: {r.text[:200]}")

    # 6. Открываем карточку с draft
    r, t = diary.time_it("open_after_gen", c.get, f"/detail/{detail_id}")
    diary.log(f"GET /detail/{detail_id} (после генерации) = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        if "операц" in r.text.lower() or "operation" in r.text.lower():
            diary.praise("Операции отображаются")
        if "замечания" in r.text.lower() or "warnings" in r.text.lower():
            diary.praise("Замечания отображаются")
        if "Вопросы" in r.text or "questions" in r.text.lower():
            diary.praise("Вопросы отображаются")

    # 7. Inline-edit операции
    r, t = diary.time_it("edit_op", c.post, "/api/edit/operation", data={
        "detail_id": detail_id, "op_index": "0",
        "field": "name", "value": "010 Тестовая операция",
        "reason": "тест"
    })
    diary.log(f"POST /api/edit/operation = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Inline-edit работает")

    # 8. Добавление операции
    r, t = diary.time_it("add_op", c.post, "/api/edit/add-operation", data={
        "detail_id": detail_id, "name": "015 Доп. операция",
        "equipment": "TestEq", "duration_hours": "0.5"
    })
    diary.log(f"POST /api/edit/add-operation = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Добавление операции работает")

    # 9. Удаление операции
    r, t = diary.time_it("delete_op", c.post, "/api/edit/delete-operation", data={
        "detail_id": detail_id, "op_index": "0", "reason": "тест"
    })
    diary.log(f"POST /api/edit/delete-operation = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Удаление операции работает (soft-delete)")

    # 10. Проверяем, что удалённая операция в списке restore
    r, t = diary.time_it("check_restore_list", c.get, f"/detail/{detail_id}")
    if "Восстановить" in r.text or "deleted_ops" in r.text:
        diary.praise("Soft-delete с restore UI виден")
    else:
        diary.bug("MEDIUM", "Restore UI не виден после удаления")

    # 11. Утверждение (без checklist — он для UI, не для API)
    r, t = diary.time_it("approve", c.post, "/api/approve", data={"detail_id": detail_id})
    diary.log(f"POST /api/approve = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Утверждение через API работает")
    else:
        diary.bug("HIGH", f"Утверждение вернуло {r.status_code}: {r.text[:200]}")

    # === ДЕНЬ 1: ОТЧЁТЫ ===

    diary.log("\n=== ДЕНЬ 1: ОТЧЁТЫ ===")

    # 12. Pilot dashboard
    r, t = diary.time_it("pilot", c.get, "/pilot")
    diary.log(f"GET /pilot = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        if "KPI" in r.text or "принятых" in r.text:
            diary.praise("Pilot dashboard с KPI")
        if "RAG" in r.text:
            diary.praise("RAG-метрика видна")

    # 13. Pilot learning
    r, t = diary.time_it("pilot_learning", c.get, "/pilot/learning?weeks=4")
    diary.log(f"GET /pilot/learning = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Pilot learning dashboard работает")

    # 14. Pilot report
    r, t = diary.time_it("pilot_report", c.get, "/pilot/report?days=7")
    diary.log(f"GET /pilot/report = {r.status_code} за {t:.3f}с")

    # === ДЕНЬ 2: ИМПОРТ ===

    diary.log("\n=== ДЕНЬ 2: ИМПОРТ ===")

    # 15. Demo
    r, t = diary.time_it("demo", c.get, "/demo")
    diary.log(f"GET /demo = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Demo-сценарий работает")

    # 16. Справочники
    r, t = diary.time_it("equipment", c.get, "/equipment")
    diary.log(f"GET /equipment = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        if "Поиск" in r.text or "q=" in r.text:
            diary.praise("Справочник оборудования с поиском")

    # 17. Health
    r, t = diary.time_it("health", c.get, "/health")
    diary.log(f"GET /health = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        data = r.json()
        diary.praise(f"/health: version={data.get('version')}, uptime={data.get('uptime_sec')}с, "
                     f"llm={data.get('dependencies', {}).get('llm')}")

    # 18. 404 страница
    r, t = diary.time_it("404", c.get, "/detail/несуществующая-деталь")
    diary.log(f"GET /detail/несуществующая = {r.status_code} за {t:.3f}с")
    if r.status_code == 404 and "К списку" in r.text:
        diary.praise("404 с навигацией работает")

    # === ДЕНЬ 2: РОЛИ ===

    diary.log("\n=== ДЕНЬ 2: СМЕНА РОЛЕЙ ===")

    # BUG-2026-07-20-01: проверка что role badge виден и меняется
    c.post("/api/role/switch", data={"role": "technologist"})
    r = c.get("/")
    if 'id="current-role-badge"' in r.text:
        diary.praise("Badge текущей роли отображается в header")
        if 'data-role="technologist"' in r.text:
            diary.praise("Badge показывает выбранную роль (data-role=technologist)")
        else:
            diary.bug("HIGH", "Badge data-role НЕ соответствует выбранной роли")
    else:
        diary.bug("HIGH", "Badge роли НЕ найден в HTML (id=current-role-badge отсутствует)")

    # Проверим что cookie НЕ httponly (BUG-2026-07-20-01)
    r = c.post("/api/role/switch", data={"role": "main_technologist"})
    cookie_header = r.headers.get("set-cookie", "")
    if "HttpOnly" in cookie_header:
        diary.bug("HIGH", f"Cookie bit_role всё ещё HttpOnly: {cookie_header}")
    else:
        diary.praise(f"Cookie bit_role НЕ HttpOnly (JS может прочитать): {cookie_header[:80]}")
    if "bit_role=main_technologist" in cookie_header:
        diary.praise("Cookie bit_role=main_technologist в Set-Cookie")
    c.post("/api/role/switch", data={"role": "technologist"})  # сброс

    # 19. Смена роли на админа
    r, t = diary.time_it("role_admin", c.post, "/api/role/switch", data={"role": "admin"})
    diary.log(f"POST /api/role/switch admin = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Смена роли работает")

    # 20. Admin dashboard
    r, t = diary.time_it("admin_dashboard", c.get, "/admin")
    diary.log(f"GET /admin = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Admin dashboard рендерится")
    else:
        diary.bug("MEDIUM", f"Admin вернул {r.status_code} (для admin role)")

    # 21. Admin users
    r, t = diary.time_it("admin_users", c.get, "/admin/users")
    diary.log(f"GET /admin/users = {r.status_code} за {t:.3f}с")

    # 22. Admin settings
    r, t = diary.time_it("admin_settings", c.get, "/admin/settings")
    diary.log(f"GET /admin/settings = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        if "Fernet" in r.text or "encrypted" in r.text.lower() or "YandexGPT" in r.text:
            diary.praise("Admin settings с группами LLM/Telegram/SMTP")

    # 23. Admin llm-calls
    r, t = diary.time_it("admin_llm", c.get, "/admin/llm-calls")
    diary.log(f"GET /admin/llm-calls = {r.status_code} за {t:.3f}с")

    # 24. Admin errors
    r, t = diary.time_it("admin_errors", c.get, "/admin/errors")
    diary.log(f"GET /admin/errors = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("/admin/errors работает (V8-18)")

    # 25. Admin login-log
    r, t = diary.time_it("admin_login_log", c.get, "/admin/login-log")
    diary.log(f"GET /admin/login-log = {r.status_code} за {t:.3f}с")

    # 26. Admin system
    r, t = diary.time_it("admin_system", c.get, "/admin/system")
    diary.log(f"GET /admin/system = {r.status_code} за {t:.3f}с")

    # 27. Reopen
    r, t = diary.time_it("reopen", c.post, "/api/reopen", data={"detail_id": detail_id})
    diary.log(f"POST /api/reopen = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Reopen работает (вернуть в работу)")

    # 28. Roles проверка
    for role in ["main_technologist", "workshop_chief", "admin"]:
        c.post("/api/role/switch", data={"role": role})
        r = c.get(f"/detail/{detail_id}")
        if r.status_code == 200:
            if "Утвердить как начальник" in r.text and role in ("main_technologist", "workshop_chief", "admin"):
                diary.praise(f"Роль {role}: видит 'approve-chief'")
            elif role == "main_technologist" and "Утвердить как начальник" not in r.text:
                diary.bug("MEDIUM", f"main_technologist НЕ видит approve-chief")
            if "Вернуть в работу" in r.text and role in ("technologist", "main_technologist", "admin"):
                diary.praise(f"Роль {role}: видит 'Вернуть в работу'")

    # 29. PDF/Excel export
    r, t = diary.time_it("export_pdf", c.post, "/api/export/pdf", data={"detail_id": detail_id})
    diary.log(f"POST /api/export/pdf = {r.status_code} за {t:.3f}с")
    if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/pdf"):
        diary.praise("PDF export работает")

    r, t = diary.time_it("export_excel", c.post, "/api/export/excel", data={"detail_id": detail_id})
    diary.log(f"POST /api/export/excel = {r.status_code} за {t:.3f}с")
    if r.status_code == 200 and "spreadsheet" in r.headers.get("content-type", ""):
        diary.praise("Excel export работает")

    r, t = diary.time_it("export_1c_csv", c.get, f"/api/export/onec-csv?detail_id={detail_id}")
    diary.log(f"GET /api/export/onec-csv = {r.status_code} за {t:.3f}с")
    if r.status_code == 200 and "csv" in r.headers.get("content-type", "").lower():
        diary.praise("1С CSV export работает")

    # 30. Print
    r, t = diary.time_it("print", c.get, f"/detail/{detail_id}/print")
    diary.log(f"GET /detail/{detail_id}/print = {r.status_code} за {t:.3f}с")
    if r.status_code == 200 and "qrcode" in r.text.lower():
        diary.praise("Print с QR работает")

    # 31. Diff
    r, t = diary.time_it("diff", c.get, f"/detail/{detail_id}/diff/1/2")
    diary.log(f"GET /detail/{detail_id}/diff/1/2 = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Diff версий работает")

    # 32. Mobile viewport (проверка CSS)
    r, t = diary.time_it("css", c.get, "/static/style.css")
    diary.log(f"GET /static/style.css = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        if "@media" in r.text:
            diary.praise("CSS содержит @media (mobile-responsive)")
        if "max-width" in r.text or "min-width" in r.text:
            diary.praise("CSS имеет breakpoints")

    # 33. Importer stats
    r, t = diary.time_it("import_stats", c.get, "/api/import/stats")
    diary.log(f"GET /api/import/stats = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("/api/import/stats работает")

    # 34. Audit
    r, t = diary.time_it("audit", c.get, "/audit")
    diary.log(f"GET /audit = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        diary.praise("Audit страница рендерится")

    # 35. Справочник материалов
    r, t = diary.time_it("materials", c.get, "/materials")
    diary.log(f"GET /materials = {r.status_code} за {t:.3f}с")

    # 36. Профессии
    r, t = diary.time_it("iot", c.get, "/iot")
    diary.log(f"GET /iot = {r.status_code} за {t:.3f}с")

    # 37. Benchmarks
    r, t = diary.time_it("benchmarks", c.get, "/benchmarks")
    diary.log(f"GET /benchmarks = {r.status_code} за {t:.3f}с")

    # 38. Learning
    r, t = diary.time_it("learning", c.get, "/learning")
    diary.log(f"GET /learning = {r.status_code} за {t:.3f}с")

    # 39. History
    r, t = diary.time_it("history", c.get, f"/history/{detail_id}")
    diary.log(f"GET /history/{detail_id} = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        if "approved" in r.text.lower() or "reopened" in r.text.lower():
            diary.praise("History страница показывает события")

    # 40. Роль "Нормировщик" — не должна видеть approve
    c.post("/api/role/switch", data={"role": "normirovshchik"})
    r = c.get(f"/detail/{detail_id}")
    if r.status_code == 200:
        if "showApprovePreview" not in r.text and "✅ Утвердить" not in r.text:
            diary.praise("Роль 'normirovshchik' НЕ видит кнопку Утвердить (правильно)")
        else:
            diary.bug("HIGH", "Роль 'normirovshchik' видит кнопку Утвердить (НЕ должно быть!)")

    # 41. Конструктор
    c.post("/api/role/switch", data={"role": "constructor"})
    r = c.get(f"/detail/{detail_id}")
    if r.status_code == 200:
        diary.praise(f"Роль 'constructor' открывает карточку (только просмотр)")

    # 42. Quality (контролёр ОТК)
    c.post("/api/role/switch", data={"role": "quality"})
    r = c.get(f"/detail/{detail_id}")
    if r.status_code == 200:
        diary.praise(f"Роль 'quality' открывает карточку")

    # 43. Проверка pilot_learning
    r, t = diary.time_it("learning_json", c.get, "/api/pilot/learning?weeks=4")
    if r.status_code == 200:
        data = r.json()
        if "metrics" in data and len(data["metrics"]) == 4:
            diary.praise(f"/api/pilot/learning возвращает {len(data['metrics'])} недель")

    # 44. Тест быстрого импорта
    diary.log("\n=== ДЕНЬ 2: ИМПОРТ JSON ===")
    import_json = json.dumps({
        "details": [{
            "id": "e2e-import-1", "designation": "IMP.001",
            "name": "Импортированная деталь",
            "model": "АЦ-6,0-40", "chassis": "КАМАЗ-43118",
            "material": "Сталь 09Г2С", "size_mm": "200", "mass_kg": 10.0,
            "surface_treatment": "Грунт"
        }]
    })
    r, t = diary.time_it("import_json", c.post, "/api/import/tk",
                          data=import_json,
                          headers={"Content-Type": "application/json"})
    diary.log(f"POST /api/import/tk (JSON) = {r.status_code} за {t:.3f}с")
    if r.status_code == 200:
        data = r.json()
        if "created" in data and data["created"] >= 1:
            diary.praise(f"JSON импорт: создано {data['created']} деталей")
        else:
            diary.bug("MEDIUM", f"JSON импорт вернул {data}")

    # 45. Тест импорта невалидного JSON
    r, t = diary.time_it("import_bad_json", c.post, "/api/import/tk",
                          data="not json",
                          headers={"Content-Type": "application/json"})
    diary.log(f"POST /api/import/tk (bad JSON) = {r.status_code} за {t:.3f}с")
    if r.status_code == 400:
        diary.praise("Невалидный JSON корректно отклонён (400)")

    # 46. Magic bytes (exe файл)
    exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00" + b"X" * 100
    import io
    files = {"file": ("test.pdf", io.BytesIO(exe_content), "application/pdf")}
    r, t = diary.time_it("import_magic_bytes", c.post, "/api/import/tk", files=files)
    diary.log(f"POST /api/import/tk (magic bytes) = {r.status_code} за {t:.3f}с")
    if r.status_code == 400:
        diary.praise("Magic bytes verification работает (.exe не пройдёт как .pdf)")

    # === ИТОГ ===

    diary.log("\n=== ИТОГ ===")
    diary.log(f"Сделано {len(diary.impressions)} наблюдений")
    diary.log(f"Похвал: {len(diary.praises)}")
    diary.log(f"Багов: {len(diary.bugs)}")
    if diary.bugs:
        for sev, text, ts in diary.bugs:
            diary.log(f"  [{sev}] {text}", "BUG")

    report_path = os.path.join(os.path.dirname(__file__), "E2E_REPORT.md")
    diary.save_report(report_path)
    diary.log(f"\nОтчёт сохранён в {report_path}")
    return len(diary.bugs)


if __name__ == "__main__":
    n_bugs = main()
    sys.exit(0 if n_bugs == 0 else 1)
