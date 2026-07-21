"""
БИТ.Технолог v0.8 — FastAPI приложение (тонкое).

Архитектура (ADR-0011):
- presentation: этот файл (routes + templates)
- services: rs_factory, notices, learning, tp_parser, auth
- repositories: db (25 таблиц)
- domain: llm_provider, yandexgpt, mock_llm
- gateways: one_c_gateway (FileGateway, HttpGateway)

8 экранов (v0.8 дизайн):
1. /dashboard       — Мои задачи
2. /products        — Изделия
3. /detail/{id}     — Карточка ТК (5 табов)
4. /notices         — Извещения
5. /profiles        — Профили РС
6. /knowledge       — База знаний
7. /llm-admin       — Управление LLM
8. /help            — Помощь
"""
import base64
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# === Jinja2 filter: from_json ===

# === Пути ===
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# === Модули ===
from repositories import db  # noqa
from domain.llm_provider import (  # noqa
    get_registry, call_llm, parse_llm_json_safe,
)
from services.auth import (  # noqa
    authenticate, ROLES, has_permission, User, seed_users,
    hash_password, verify_password,
)
from services.rs_factory import (  # noqa
    build_rs, to_one_c_spec, DEFAULT_PROFILE, is_deterministic,
)
from services.tp_parser import parse_tp_text, validate_parsed_tp
from gateways.one_c_gateway import get_gateway, OneCResourceSpec  # noqa

# === Инициализация ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="БИТ.Технолог", version="0.8.0")
templates = Jinja2Templates(directory=str(ROOT / "templates"))

# Jinja2 filters
def from_json(value):
    import json as _json
    if not value:
        return {}
    try:
        return _json.loads(value)
    except (ValueError, TypeError):
        return {}

templates.env.filters["from_json"] = from_json

app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

# Инициализация БД + сидинг
db.init_db()
seed_users(verbose=False)


# ============================================================
# AUTH (Basic)
# ============================================================

def get_current_user(request: Request) -> Optional[User]:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Basic "):
        # Для UI — попробуем cookie
        return None
    try:
        creds = base64.b64decode(auth[6:]).decode()
        username, password = creds.split(":", 1)
        return authenticate(username, password)
    except Exception:
        return None


def get_user_from_request(request: Request) -> Optional[User]:
    """Получить user (из Basic Auth или form)."""
    user = get_current_user(request)
    if user:
        return user
    # TODO: из cookie / session
    return None


def require_user(request: Request) -> User:
    user = get_user_from_request(request)
    if not user:
        raise HTTPException(401, "Authentication required",
                            headers={"WWW-Authenticate": 'Basic realm="bit-technolog"'})
    return user


# ============================================================
# CONTEXT для всех шаблонов
# ============================================================

def get_template_context(request: Request, user: Optional[User] = None) -> Dict[str, Any]:
    """Общий контекст для всех шаблонов."""
    registry = get_registry()
    # Счётчик открытых извещений (нужен в nav)
    n_open_notices = db.query_one("SELECT COUNT(*) AS n FROM change_notices WHERE status IN ('open','in_progress')")["n"]
    return {
        "request": request,
        "current_user": user,
        "is_mock_mode": registry.is_mock_mode(),
        "daily_cost": registry.daily_cost_estimate(),
        "cost_budget": 500.0,
        "app_version": "0.8.0",
        "app_env": "ПРОТОТИП",
        "ROLES": ROLES,
        "counters": {"notices": n_open_notices},  # для nav
    }


# ============================================================
# ROUTES — 8 ЭКРАНОВ
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_user_from_request(request)
    ctx = get_template_context(request, user)

    # Счётчики
    counters = {
        "drafts": db.query_one("SELECT COUNT(*) AS n FROM tech_cards WHERE status='draft'")["n"],
        "review": db.query_one("SELECT COUNT(*) AS n FROM tech_cards WHERE status='review'")["n"],
        "notices": db.query_one("SELECT COUNT(*) AS n FROM change_notices WHERE status='open'")["n"],
        "ai_questions": 3,  # Заглушка
        "evidence_green_pct": 61,  # Из метрик
    }

    # Задачи (последние 5)
    tasks = db.query("""
        SELECT tc.id AS tech_card_id, i.designation, i.name,
               tc.status, tc.version,
               p.designation AS product_model
        FROM tech_cards tc
        JOIN items i ON i.id = tc.item_id
        LEFT JOIN product_models p ON p.id = i.product_model_id
        ORDER BY tc.updated_at DESC
        LIMIT 5
    """)
    tasks = [db.row_to_dict(t) for t in tasks]

    # Извещения
    notices = db.query("""
        SELECT * FROM change_notices
        WHERE status IN ('open', 'in_progress')
        ORDER BY date DESC LIMIT 3
    """)
    notices = [db.row_to_dict(n) for n in notices]

    ctx.update({
        "counters": counters,
        "tasks": tasks,
        "notices": notices,
    })
    return templates.TemplateResponse("dashboard.html", ctx)


@app.get("/products", response_class=HTMLResponse)
async def products(request: Request):
    user = get_user_from_request(request)
    ctx = get_template_context(request, user)
    items = db.rows_to_dicts(db.query("""
        SELECT i.*, p.designation AS product_model_designation
        FROM items i
        LEFT JOIN product_models p ON p.id = i.product_model_id
        ORDER BY i.designation
        LIMIT 100
    """))
    ctx["items"] = items
    return templates.TemplateResponse("products.html", ctx)


@app.get("/detail/{item_id}", response_class=HTMLResponse)
async def detail(request: Request, item_id: int):
    user = get_user_from_request(request)
    ctx = get_template_context(request, user)

    item = db.get_item_with_bom(item_id)
    if not item:
        raise HTTPException(404, "Item not found")

    # Текущая ТК
    tc = db.query_one("""
        SELECT * FROM tech_cards
        WHERE item_id = ?
        ORDER BY version DESC LIMIT 1
    """, (item_id,))
    if tc:
        tc_full = db.get_tech_card_full(tc["id"])
    else:
        tc_full = {}

    # Эталоны (для обоснования)
    etalons = db.get_etalons_for_rag(product_type=item.get("product_type") or "", limit=5)

    ctx.update({
        "item": item,
        "tech_card": tc_full,
        "etalons": etalons,
    })
    return templates.TemplateResponse("detail.html", ctx)


@app.get("/notices", response_class=HTMLResponse)
async def notices(request: Request):
    user = get_user_from_request(request)
    ctx = get_template_context(request, user)
    n = db.rows_to_dicts(db.query("""
        SELECT * FROM change_notices ORDER BY date DESC LIMIT 50
    """))
    ctx["notices"] = n
    return templates.TemplateResponse("notices.html", ctx)


@app.get("/profiles", response_class=HTMLResponse)
async def profiles(request: Request):
    user = get_user_from_request(request)
    ctx = get_template_context(request, user)
    profiles_list = db.rows_to_dicts(db.query("SELECT * FROM rs_output_profiles"))
    ctx["profiles"] = profiles_list
    ctx["default_profile"] = DEFAULT_PROFILE
    return templates.TemplateResponse("profiles.html", ctx)


@app.get("/knowledge", response_class=HTMLResponse)
async def knowledge(request: Request):
    user = get_user_from_request(request)
    ctx = get_template_context(request, user)
    etalons = db.rows_to_dicts(db.query("SELECT * FROM etalons ORDER BY approved_date DESC"))
    ctx["etalons"] = etalons
    return templates.TemplateResponse("knowledge.html", ctx)


@app.get("/llm-admin", response_class=HTMLResponse)
async def llm_admin(request: Request):
    user = get_user_from_request(request)
    if user and not has_permission(user.role, "manage_llm_providers"):
        raise HTTPException(403, "Requires llm_admin role")
    ctx = get_template_context(request, user)
    providers = db.rows_to_dicts(db.query("SELECT * FROM llm_providers"))
    assignments = db.rows_to_dicts(db.query("""
        SELECT ma.*, p.display_name AS provider_display
        FROM llm_model_assignments ma
        JOIN llm_providers p ON p.id = ma.llm_provider_id
    """))
    recent_calls = db.rows_to_dicts(db.query("""
        SELECT * FROM llm_calls ORDER BY ts DESC LIMIT 20
    """))
    ctx.update({
        "providers": providers,
        "assignments": assignments,
        "recent_calls": recent_calls,
    })
    return templates.TemplateResponse("llm_admin.html", ctx)


@app.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    user = get_user_from_request(request)
    ctx = get_template_context(request, user)
    return templates.TemplateResponse("help.html", ctx)


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/health")
async def health():
    """Health check."""
    try:
        # Проверим БД
        result = db.query_one("SELECT COUNT(*) AS n FROM items")
        n_items = result["n"] if result else 0
        result = db.query_one("SELECT COUNT(*) AS n FROM etalons")
        n_etalons = result["n"] if result else 0
        return {
            "status": "ok",
            "version": "0.8.0",
            "db": "ok",
            "items": n_items,
            "etalons": n_etalons,
            "is_mock_mode": get_registry().is_mock_mode(),
        }
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)


@app.get("/api/items")
async def api_items(
    level: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
):
    items = db.list_items(level=level, search=search, limit=limit)
    return {"items": items, "total": len(items)}


@app.get("/api/tech-cards/{tech_card_id}/rs-preview")
async def api_rs_preview(tech_card_id: int, profile_code: str = "default"):
    """Предпросмотр РС по ТК + профилю (детерминированный расчёт)."""
    tc = db.get_tech_card_full(tech_card_id)
    if not tc:
        raise HTTPException(404, "Tech card not found")

    # Профиль
    if profile_code == "default":
        profile = DEFAULT_PROFILE
    else:
        row = db.query_one("SELECT * FROM rs_output_profiles WHERE code = ?", (profile_code,))
        profile = json.loads(row["axes_json"]) if row else DEFAULT_PROFILE

    report = build_rs(
        item_designation=tc.get("item_designation", "?"),
        operations=tc.get("operations", []),
        profile=profile,
        tech_card_id=tech_card_id,
    )
    return report.to_dict()


@app.post("/api/tech-cards/{tech_card_id}/regenerate")
async def api_regenerate(tech_card_id: int, request: Request):
    """Перегенерировать ТК через LLM (mock)."""
    user = get_user_from_request(request)
    if not user:
        raise HTTPException(401)
    tc = db.get_tech_card_full(tech_card_id)
    if not tc:
        raise HTTPException(404)
    # Mock
    result = call_llm("tech_card_generation",
                      prompt=f"Сгенерируй ТК для {tc.get('item_designation')}",
                      system="Ты — главный технолог")
    return {"status": "ok", "llm_response": result.parse_json(), "model": result.model}


@app.post("/api/tech-cards/{tech_card_id}/approve")
async def api_approve(tech_card_id: int, request: Request):
    """Утвердить ТК → добавить в эталоны (петля обратной связи)."""
    user = get_user_from_request(request)
    if not user:
        raise HTTPException(401)
    tc = db.get_tech_card_full(tech_card_id)
    if not tc:
        raise HTTPException(404)

    # Получить операции как dict
    operations = tc.get("operations", [])

    # Создаём эталон из текущей ТК
    etalon_id = db.insert_and_get_id("etalons", {
        "designation": tc.get("designation", "?"),
        "name": tc.get("name", ""),
        "product_type": "",
        "source_doc": f"Утверждена {user.username} из ТК v{tc.get('version', 1)}",
        "source_pages": 0,
        "approved_by": user.display_name,
        "approved_date": None,
        "is_approved": 1,
        "is_published": 1,  # Сразу публикуем
        "content_json": json.dumps({
            "operations": [
                {
                    "op_number": op.get("op_number"),
                    "name": op.get("name"),
                    "time_setup_min": op.get("time_setup_min", 0),
                    "time_per_unit_min": op.get("time_per_unit_min", 0),
                    "profession_code": op.get("profession_code", ""),
                    "equipment_name": op.get("equipment_name", ""),
                }
                for op in operations
            ],
        }, ensure_ascii=False),
    })
    return {"status": "ok", "etalon_id": etalon_id, "message": "ТК утверждена и добавлена в эталоны"}


@app.post("/api/change-notices/{notice_id}/process")
async def api_process_notice(notice_id: int, request: Request):
    """Обработать извещение: AI diff + пересчёт РС."""
    user = get_user_from_request(request)
    if not user:
        raise HTTPException(401)
    notice = db.query_one("SELECT * FROM change_notices WHERE id = ?", (notice_id,))
    if not notice:
        raise HTTPException(404)

    # Mock AI diff
    result = call_llm("notice_diff", prompt=f"Извещение {notice['number']}: {notice.get('reason', '')}")
    return {
        "status": "ok",
        "notice_id": notice_id,
        "ai_diff": result.parse_json(),
    }


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup_event():
    """При старте — логируем состояние."""
    n_etalons = db.query_one("SELECT COUNT(*) AS n FROM etalons")["n"]
    n_items = db.query_one("SELECT COUNT(*) AS n FROM items")["n"]
    n_users = db.query_one("SELECT COUNT(*) AS n FROM pilot_users")["n"]
    logger.info(f"v0.8 startup: etalons={n_etalons}, items={n_items}, users={n_users}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
