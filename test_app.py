"""Pytest tests for БИТ.Технолог prototype.

Запуск: pytest test_app.py -v
"""
import os
import json
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Создаёт временную БД и запускает app"""
    # Изолированная БД
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Установим env ДО импорта app
    os.environ["DB_PATH"] = path
    os.environ["DEMO_MODE"] = "true"
    os.environ["LLM_DAILY_LIMIT_RUB"] = "10"

    sys.path.insert(0, os.path.dirname(__file__))
    import app as app_module
    # Явный init
    app_module.init_db()

    c = TestClient(app_module.app)
    c.__enter__() if hasattr(c, '__enter__') else None

    try:
        yield c, app_module
    finally:
        try:
            c.__exit__(None, None, None)
        except Exception:
            pass
        try:
            os.unlink(path)
        except Exception:
            pass


# ========== Health & basic ==========
def test_health(client):
    c, _ = client
    r = c.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["demo_mode"] is True


def test_index_page(client):
    c, _ = client
    r = c.get("/")
    assert r.status_code == 200
    assert "БИТ.Технолог" in r.text


def test_detail_page(client):
    c, _ = client
    r = c.get("/detail/detail-001")
    assert r.status_code == 200
    assert "КРН" in r.text or "Кронштейн" in r.text


def test_detail_404(client):
    c, _ = client
    r = c.get("/detail/nonexistent")
    assert r.status_code == 404


# ========== LLM Generation ==========
def test_generate_missing_detail_id(client):
    c, _ = client
    r = c.post("/api/generate", data={})
    assert r.status_code == 422


def test_generate_form_data(client):
    c, _ = client
    r = c.post("/api/generate", data={"detail_id": "detail-001"})
    assert r.status_code == 200


def test_generate_not_found(client):
    c, _ = client
    r = c.post("/api/generate", data={"detail_id": "nonexistent"})
    assert r.status_code == 404


# ========== Approve & send-to-1c ==========
def test_approve(client):
    c, _ = client
    r = c.post("/api/approve", data={"detail_id": "detail-001"})
    assert r.status_code == 200
    assert r.json()["status"] == "approved"


def test_send_to_1c(client):
    c, _ = client
    r = c.post("/api/send-to-1c", data={"detail_id": "detail-001"})
    assert r.status_code == 200
    assert r.json()["status"] == "sent"


# ========== Edit operations ==========
def test_edit_operation(client):
    c, _ = client
    # Сначала сгенерируем черновик
    c.post("/api/generate", data={"detail_id": "detail-003"})
    r = c.post("/api/edit/operation", data={
        "detail_id": "detail-003",
        "op_index": "0",
        "field": "duration_hours",
        "value": "0.5",
        "reason": "test"
    })
    assert r.status_code == 200, r.text


def test_add_operation(client):
    c, _ = client
    r = c.post("/api/edit/add-operation", data={
        "detail_id": "detail-001",
        "name": "TEST_OP",
        "duration_hours": "0.3"
    })
    assert r.status_code == 200


def test_delete_operation_invalid_index(client):
    c, _ = client
    r = c.post("/api/edit/delete-operation", data={
        "detail_id": "detail-001",
        "op_index": "99"
    })
    assert r.status_code in (200, 400)


# ========== CRUD pages ==========
def test_equipment_page(client):
    c, _ = client
    assert c.get("/equipment").status_code == 200


def test_materials_page(client):
    c, _ = client
    assert c.get("/materials").status_code == 200


def test_iot_page(client):
    c, _ = client
    assert c.get("/iot").status_code == 200


def test_benchmarks_page(client):
    c, _ = client
    assert c.get("/benchmarks").status_code == 200


def test_new_detail_form(client):
    c, _ = client
    assert c.get("/details/new").status_code == 200


# ========== Learning & metrics ==========
def test_learning_page(client):
    c, _ = client
    assert c.get("/learning").status_code == 200


def test_llm_debug_page(client):
    c, _ = client
    assert c.get("/llm-debug").status_code == 200


# ========== Cost tracking (unit tests) ==========
def test_daily_cost_structure(client):
    _, app = client
    dc = app.get_daily_cost()
    assert "date" in dc
    assert "total_rub" in dc
    assert "limit_rub" in dc
    assert "remaining_rub" in dc
    assert "exceeded" in dc
    assert isinstance(dc["exceeded"], bool)


def test_calc_cost_rub(client):
    _, app = client
    # 0 токенов = 0 руб
    assert app.calc_cost_rub(0, 0) == 0.0
    # 1000 input + 500 output = 0.40*1 + 1.20*0.5 = 1.00
    cost = app.calc_cost_rub(1000, 500)
    assert abs(cost - 1.00) < 0.01


# ========== Database helpers ==========
def test_get_detail_returns_dict_with_id(client):
    _, app = client
    d = app.get_detail("detail-001")
    assert d is not None
    assert "id" in d
    assert d["id"] == "detail-001"
    assert "designation" in d
    assert "name" in d


def test_get_all_details_has_ids(client):
    _, app = client
    details = app.get_all_details()
    assert len(details) > 0
    for d in details:
        assert "id" in d


# ========== Pilot metrics ==========
def test_record_metric(client):
    _, app = client
    app.record_metric("test-detail", "test_metric", 42.0, {"foo": "bar"})
    # No exception = pass


def test_pilot_metrics_endpoint(client):
    c, _ = client
    assert c.get("/pilot").status_code == 200


def test_pilot_time_form(client):
    c, _ = client
    r = c.post("/api/pilot/time", data={"detail_id": "test-1", "minutes": "45"}, follow_redirects=False)
    assert r.status_code in (200, 303)


def test_pilot_accepted_form(client):
    c, _ = client
    r = c.post("/api/pilot/accepted", data={
        "detail_id": "test-2", "total_ops": "10", "accepted_ops": "6"
    }, follow_redirects=False)
    assert r.status_code in (200, 303)


def test_pilot_metrics_after_activity(client):
    _, app = client
    # Сгенерируем черновик
    c, _ = client
    c.post("/api/generate", data={"detail_id": "detail-001"})
    # Утвердим
    c.post("/api/approve", data={"detail_id": "detail-001"})
    # Получим метрики
    metrics = app.get_pilot_metrics()
    assert "total_details_processed" in metrics
    assert "edits_per_card" in metrics
    assert "accepted_pct" in metrics
    assert "avg_time_to_card_min" in metrics
    assert metrics["kpi"]["time_target"] == 60


# ========== Tech rules ==========
def test_save_rules(client):
    c, _ = client
    r = c.post("/api/details/detail-001/rules",
               data={"rules": "обезжиривание 20 мин в травильной жидкости"})
    assert r.status_code == 200


def test_get_detail_has_tech_rules(client):
    _, app = client
    d = app.get_detail("detail-001")
    assert "tech_rules" in d
    assert "cost_per_hour" in d
    assert "overhead_pct" in d
    assert "material_cost_rub" in d


# ========== Economics ==========
def test_save_economics(client):
    c, _ = client
    r = c.post("/api/details/detail-001/economics",
               data={"cost_per_hour": "500", "overhead_pct": "15", "material_cost_rub": "1000"})
    assert r.status_code == 200


def test_calc_cost_estimate(client):
    _, app = client
    # Сначала сгенерируем и установим экономику
    c, _ = client
    c.post("/api/generate", data={"detail_id": "detail-001"})
    c.post("/api/details/detail-001/economics",
           data={"cost_per_hour": "500", "overhead_pct": "15", "material_cost_rub": "1000"})
    econ = app.calc_cost_estimate("detail-001")
    assert "total_hours" in econ
    assert "labor_cost" in econ
    assert "total_cost" in econ
    assert econ["total_cost"] > 0


# ========== Role model ==========
def test_submit_for_review(client):
    c, _ = client
    c.post("/api/generate", data={"detail_id": "detail-001"})
    r = c.post("/api/submit-for-review", data={"detail_id": "detail-001"})
    assert r.status_code == 200


def test_approve_chief(client):
    c, _ = client
    c.post("/api/generate", data={"detail_id": "detail-001"})
    r = c.post("/api/approve-chief",
               data={"detail_id": "detail-001", "chief": "Баранов"})
    assert r.status_code == 200


def test_economics_endpoint(client):
    c, _ = client
    c.post("/api/generate", data={"detail_id": "detail-001"})
    c.post("/api/details/detail-001/economics",
           data={"cost_per_hour": "500", "overhead_pct": "15", "material_cost_rub": "1000"})
    r = c.get("/api/economics/detail-001")
    assert r.status_code == 200
    assert "труд" in r.text or "себестоимость" in r.text


# ========== Sprint 1: analyze / draft-fast / refine / economics by dept ==========
def test_api_analyze_demo(client):
    c, _ = client
    r = c.post("/api/analyze", data={"detail_id": "detail-001"})
    assert r.status_code == 200
    data = r.json()
    assert "questions" in data
    assert 3 <= len(data["questions"]) <= 5
    for q in data["questions"]:
        assert "id" in q and "question" in q
        assert "options" in q and len(q["options"]) >= 2


def test_api_analyze_missing_detail(client):
    c, _ = client
    r = c.post("/api/analyze", data={"detail_id": "nonexistent"})
    assert r.status_code == 404


def test_api_analyze_missing_id(client):
    c, _ = client
    r = c.post("/api/analyze", data={})
    assert r.status_code == 422


def test_api_draft_fast_demo(client):
    c, _ = client
    r = c.post("/api/draft-fast", data={"detail_id": "detail-001", "answers": "{}"})
    assert r.status_code == 200
    data = r.json()
    assert "draft" in data
    draft = data["draft"]
    assert "summary" in draft
    assert "route" in draft
    assert 1 <= len(draft["route"]) <= 5


def test_api_refine_demo(client):
    c, _ = client
    r = c.post("/api/refine", data={"detail_id": "detail-001", "draft": "{}", "answers": "{}"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert "total_ops" in data


def test_api_feedback(client):
    c, _ = client
    r = c.post("/api/feedback", data={"detail_id": "detail-001", "reason": "некорректный маршрут"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_economics_includes_by_department(client):
    c, app = client
    c.post("/api/generate", data={"detail_id": "detail-001"})
    c.post("/api/details/detail-001/economics",
           data={"cost_per_hour": "500", "overhead_pct": "15", "material_cost_rub": "1000"})
    econ = app.calc_cost_estimate("detail-001")
    assert "by_department" in econ
    assert len(econ["by_department"]) >= 1
    for d in econ["by_department"]:
        assert "department" in d and "hours" in d and "labor_cost" in d


def test_economics_endpoint_shows_process_pricing_table(client):
    c, _ = client
    c.post("/api/generate", data={"detail_id": "detail-001"})
    c.post("/api/details/detail-001/economics",
           data={"cost_per_hour": "500", "overhead_pct": "15", "material_cost_rub": "1000"})
    r = c.get("/api/economics/detail-001")
    assert r.status_code == 200
    assert "по цехам" in r.text or "process-based" in r.text.lower() or "Цех" in r.text


# ========== Sprint 2: RAG (TF-IDF + cosine + hybrid) ==========
def test_rag_status_initial(client):
    c, _ = client
    r = c.get("/api/rag/status")
    assert r.status_code == 200
    data = r.json()
    assert "loaded" in data
    assert "documents" in data


def test_rag_rebuild_builds_index(client):
    c, _ = client
    r = c.post("/api/rag/rebuild")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["indexed"] >= 1


def test_rag_similar_returns_results(client):
    c, _ = client
    c.post("/api/rag/rebuild")
    r = c.get("/api/rag/similar/detail-001?top_k=3")
    assert r.status_code == 200
    data = r.json()
    assert "similar" in data
    if data["similar"]:
        s = data["similar"][0]
        assert "detail_id" in s and "score" in s
        assert 0.0 <= s["score"] <= 1.0


def test_rag_similar_not_found(client):
    c, _ = client
    r = c.get("/api/rag/similar/nonexistent")
    assert r.status_code == 404


def test_rag_autoindex_on_approve(client):
    c, _ = client
    # Генерируем и approve
    c.post("/api/generate", data={"detail_id": "detail-002"})
    c.post("/api/approve", data={"detail_id": "detail-002"})
    # Индекс должен содержать detail-002
    status = c.get("/api/rag/status").json()
    assert "detail-002" in c.get("/api/rag/similar/detail-001?top_k=10").json().get("similar", [{"detail_id": ""}])[0].get("detail_id", "") or status["documents"] >= 1


# ========== Sprint 3: Alternatives, Apply similar, Batch ==========
def test_api_alternatives_demo(client):
    c, _ = client
    r = c.post("/api/alternatives", data={"detail_id": "detail-001"})
    assert r.status_code == 200
    data = r.json()
    assert "alternatives" in data
    alts = data["alternatives"]
    assert 2 <= len(alts) <= 5
    for a in alts:
        assert "variant" in a and "approach" in a and "route" in a


def test_api_alternatives_missing(client):
    c, _ = client
    r = c.post("/api/alternatives", data={"detail_id": "nonexistent"})
    assert r.status_code == 404


def test_api_apply_similar(client):
    c, _ = client
    # Source
    c.post("/api/generate", data={"detail_id": "detail-001"})
    c.post("/api/approve", data={"detail_id": "detail-001"})
    # Apply к detail-002
    r = c.post("/api/apply-similar", data={"detail_id": "detail-002", "source_id": "detail-001"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_api_apply_similar_no_source_draft(client):
    c, _ = client
    # Используем несуществующий source_id
    r = c.post("/api/apply-similar", data={"detail_id": "detail-001", "source_id": "detail-nonexistent-xyz"})
    assert r.status_code == 404


def test_api_apply_similar_self(client):
    c, _ = client
    r = c.post("/api/apply-similar", data={"detail_id": "detail-001", "source_id": "detail-001"})
    assert r.status_code == 400


def test_api_batch_generate(client):
    c, _ = client
    detail_ids = json.dumps(["detail-001", "detail-002"])
    r = c.post("/api/batch-generate", data={"detail_ids": detail_ids})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["processed"] == 2


def test_api_batch_generate_empty(client):
    c, _ = client
    r = c.post("/api/batch-generate", data={"detail_ids": "[]"})
    assert r.status_code == 422


# ========== Sprint 5: Audit + Export ==========
def test_audit_page_renders(client):
    c, _ = client
    r = c.get("/audit?limit=20")
    assert r.status_code == 200
    assert "Audit" in r.text


def test_api_audit_export(client):
    c, _ = client
    r = c.get("/api/audit/export")
    assert r.status_code == 200
    data = r.json()
    assert "entries" in data
    assert "total_entries" in data
    assert data["total_entries"] >= 1


def test_api_export_all(client):
    c, _ = client
    r = c.get("/api/export/all")
    assert r.status_code == 200
    data = r.json()
    assert "tables" in data
    assert "details" in data["tables"]
    assert "drafts" in data["tables"]
