"""
seed_tech_cards.py — генерирует тестовые ТК из эталонов.

Для каждого эталона создаёт tech_card (is_approved=1) + operations.
Используется для демонстрации светофора норм в UI.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from repositories import db


def seed_tech_cards_from_etalons(verbose: bool = True) -> int:
    """Создать ТК из каждого эталона (для demo)."""
    db.init_db()
    loaded = 0
    etalons = db.rows_to_dicts(db.query("SELECT * FROM etalons WHERE is_published = 1"))

    for et in etalons:
        # Найти item по designation
        item = db.query_one("SELECT id FROM items WHERE designation = ?", (et["designation"],))
        if not item:
            if verbose:
                print(f"⚠️  Item {et['designation']} не найден в items, пропускаю")
            continue

        # Проверим, есть ли уже ТК
        existing = db.query_one("""
            SELECT id FROM tech_cards WHERE item_id = ? AND version = 1
        """, (item["id"],))
        if existing:
            continue

        content = et.get("content_json") or {}
        if isinstance(content, str):
            content = json.loads(content)

        # Создать ТК
        tc_id = db.insert_and_get_id("tech_cards", {
            "item_id": item["id"],
            "version": 1,
            "status": "approved",
            "author": "Демо-эталон (ВП 3237)",
            "approver_chief": "Главный технолог",
            "approver_prod": "Начальник производства",
            "approved_at": et.get("approved_date"),
            "llm_provider_id": None,
            "llm_model": "mock-1",
            "is_approved": 1,
            "ref_1c": None,
        })

        # Загрузим справочники
        workshops = {r["code"]: r["id"] for r in db.query("SELECT id, code FROM workshops")}
        professions = {r["code"]: r["id"] for r in db.query("SELECT id, code FROM professions")}
        equipment_list = list(db.query("SELECT id, name FROM equipment LIMIT 100"))

        # Создать операции
        for op in content.get("operations", []):
            op_num = op.get("op_number", 0)
            if not op_num:
                continue
            workshop_code = op.get("workshop_code", "01")
            prof_code = op.get("profession_code", "С-4")

            # Время — если не указано, ставим дефолт
            tpu = op.get("time_per_unit_min", 0) or 0
            if tpu == 0:
                tpu = 10.0

            # Материалы
            mats = op.get("materials", [])
            mat_codes = [m.get("code", "") for m in mats if m.get("code")]

            db.insert_and_get_id("operations", {
                "tech_card_id": tc_id,
                "op_number": op_num,
                "name": op.get("name", "Без названия")[:200],
                "workshop_id": workshops.get(workshop_code),
                "equipment_id": equipment_list[0]["id"] if equipment_list else None,
                "profession_id": professions.get(prof_code),
                "time_setup_min": op.get("time_setup_min", 0) or 0,
                "time_per_unit_min": tpu,
                "time_total_min": (op.get("time_setup_min", 0) or 0) + tpu,
                "source": "factory_data",  # Эталоны — это factory_data
                "evidence_json": json.dumps({"from_etalon": et["id"]}, ensure_ascii=False),
                "ref_1c": None,
                "notes": None,
            })

        if verbose:
            n_ops = db.query_one("SELECT COUNT(*) AS n FROM operations WHERE tech_card_id = ?", (tc_id,))["n"]
            print(f"✅ ТК {et['designation']} v1 — {n_ops} операций (эталон, source=factory_data)")
        loaded += 1

    return loaded


if __name__ == "__main__":
    n = seed_tech_cards_from_etalons()
    print(f"\nСоздано ТК: {n}")
