"""
seed_test_ai_tc.py — тестовая ТК с AI-нормами (без эталона).

Для демонстрации светофора в UI:
- 1 операция похожа на эталон (Сварка трубы) → 🟡 жёлтый
- 1 операция совершенно новая → 🔴 красный
- 1 операция тип "Контроль" → аналог в эталоне → 🟡

Создаёт новый item ЛМША.301555.020 (Кронштейн боковой) +
tech_card v1 (status=draft, source=ai_guess) +
5 операций с типовыми AI-нормами.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from repositories import db


TEST_TC = {
    "item": {
        "designation": "ЛМША.301555.020",
        "name": "Кронштейн боковой",
        "level": "detail",
        "type": "сборочная единица",
        "mass_kg": 4.5,
        "sourcing": "make",
    },
    "tech_card": {
        "version": 1,
        "status": "draft",
        "author": "AI (mock)",
        "llm_model": "mock-1",
        "is_approved": 0,
    },
    "operations": [
        {
            "op_number": 5,
            "name": "Резка листа",
            "workshop_code": "01",
            "site_code": "01",
            "workplace": "04",
            "profession_code": "Р-3",
            "time_setup_min": 6.0,
            "time_per_unit_min": 12.0,  # Аналогия с эталоном
            "source": "ai_guess",  # изначально догадка
        },
        {
            "op_number": 10,
            "name": "Гибка заготовки",
            "workshop_code": "01",
            "site_code": "01",
            "workplace": "02",
            "profession_code": "Г-4",
            "time_setup_min": 8.0,
            "time_per_unit_min": 18.0,
            "source": "ai_guess",
        },
        {
            "op_number": 15,
            "name": "Сварка",
            "workshop_code": "02",
            "site_code": "01",
            "workplace": "04",
            "profession_code": "Э-5",
            "time_setup_min": 12.0,
            "time_per_unit_min": 35.0,
            "source": "ai_guess",
        },
        {
            "op_number": 20,
            "name": "Зачистка швов",
            "workshop_code": "02",
            "site_code": "01",
            "workplace": "01",
            "profession_code": "С-4",
            "time_setup_min": 4.0,
            "time_per_unit_min": 15.0,
            "source": "ai_guess",
        },
        {
            "op_number": 25,
            "name": "Контроль качества",
            "workshop_code": "04",
            "site_code": "01",
            "workplace": "01",
            "profession_code": "К-3",
            "time_setup_min": 5.0,
            "time_per_unit_min": 8.0,
            "source": "ai_guess",
        },
    ],
}


def seed_test_ai_tc(verbose: bool = True) -> int:
    """Создать тестовую ТК с AI-нормами."""
    db.init_db()

    # 1. Создать item
    item_spec = TEST_TC["item"]
    existing_item = db.query_one("SELECT id FROM items WHERE designation = ?", (item_spec["designation"],))
    if existing_item:
        item_id = existing_item["id"]
        if verbose:
            print(f"⏭  Item {item_spec['designation']} уже есть (id={item_id})")
    else:
        item_id = db.insert_and_get_id("items", item_spec)
        if verbose:
            print(f"✅ Создан item {item_spec['designation']} (id={item_id})")

    # 2. Создать tech_card
    tc_spec = TEST_TC["tech_card"]
    existing_tc = db.query_one("SELECT id FROM tech_cards WHERE item_id = ? AND version = ?", (item_id, tc_spec["version"]))
    if existing_tc:
        tc_id = existing_tc["id"]
        if verbose:
            print(f"⏭  ТК уже есть (id={tc_id})")
    else:
        tc_id = db.insert_and_get_id("tech_cards", {
            "item_id": item_id,
            "version": tc_spec["version"],
            "status": tc_spec["status"],
            "author": tc_spec["author"],
            "llm_model": tc_spec["llm_model"],
            "is_approved": tc_spec["is_approved"],
        })
        if verbose:
            print(f"✅ Создана ТК (id={tc_id})")

    # 3. Создать операции (если нет)
    existing_ops = db.query_one("SELECT COUNT(*) AS n FROM operations WHERE tech_card_id = ?", (tc_id,))["n"]
    if existing_ops > 0:
        if verbose:
            print(f"⏭  Операции уже есть ({existing_ops})")
    else:
        workshops = {r["code"]: r["id"] for r in db.query("SELECT id, code FROM workshops")}
        professions = {r["code"]: r["id"] for r in db.query("SELECT id, code FROM professions")}
        equipment_list = list(db.query("SELECT id FROM equipment LIMIT 10"))
        eq_id = equipment_list[0]["id"] if equipment_list else None

        for op in TEST_TC["operations"]:
            db.insert_and_get_id("operations", {
                "tech_card_id": tc_id,
                "op_number": op["op_number"],
                "name": op["name"],
                "workshop_id": workshops.get(op["workshop_code"]),
                "equipment_id": eq_id,
                "profession_id": professions.get(op["profession_code"]),
                "time_setup_min": op["time_setup_min"],
                "time_per_unit_min": op["time_per_unit_min"],
                "time_total_min": op["time_setup_min"] + op["time_per_unit_min"],
                "source": op["source"],
            })
        if verbose:
            print(f"✅ Создано операций: {len(TEST_TC['operations'])}")

    return tc_id


if __name__ == "__main__":
    tc_id = seed_test_ai_tc()
    print(f"\nТК id={tc_id} (для UI: /detail/{db.query_one('SELECT id FROM items WHERE designation = ?', ('ЛМША.301555.020',))['id']})")
