"""
seed_items.py — загрузить номенклатуру (items) из реальных PDF.

Из 2 PDF:
- ЛМША.301712.000 (Растяжка пружинная) — главная деталь
- ЛМША.301314.010 (Упор продольный) — главная деталь
- Их составные (пружины, шайбы, проушины, втулки)
- АЦ-8,0-40 (модель изделия)
- КАМАЗ-43118 (шасси)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from repositories import db


# Шасси
CHASSIS = [
    ("КАМАЗ-43118", "КАМАЗ-43118 6×6", "ПАО «КАМАЗ»", "6×6", 10400, 7000),
    ("УРАЛ-4320", "УРАЛ-4320 6×6", "ОАО «АЗ УРАЛ»", "6×6", 8400, 12000),
]

# Модели изделий
PRODUCT_MODELS = [
    ("АЦ-8,0-40", "Автоцистерна пожарная 8 м³ на шасси КАМАЗ-43118", "АЦ", "КАМАЗ-43118", "ТУ 4854-001-..."),
    ("УМК-3,0-40", "Установка комбинированная 3 м³ на шасси КАМАЗ-43118", "УМК", "КАМАЗ-43118", "ТУ 4854-002-..."),
]

# Главные детали (из 2 PDF)
ITEMS = [
    {
        "designation": "ЛМША.301314.010",
        "name": "Упор продольный",
        "level": "detail",
        "type": "сборочная единица",
        "mass_kg": 12.5,
        "sourcing": "make",
    },
    {
        "designation": "ЛМША.301712.000",
        "name": "Растяжка пружинная",
        "level": "detail",
        "type": "сборочная единица",
        "mass_kg": 8.3,
        "sourcing": "make",
    },
]

# Составные (из К/М)
COMPOSITE = [
    ("ЛМША.304142.010", "Втулка", 0.8, "make"),
    ("ЛМША.304142.010-01", "Втулка (модификация)", 0.8, "make"),
    ("ЛМША.304142.010-04", "Втулка (модификация -04)", 0.8, "make"),
    ("ЛМША.304339.010", "Проушина", 1.2, "make"),
    ("ЛМША.304339.010-01", "Проушина (модификация)", 1.2, "make"),
    ("ЛМША.304590.001", "Пружина тарельчатая", 0.05, "buy"),  # покупное!
    ("ЛМША.301624.003", "Шайба", 0.02, "make"),
    ("ЛМША.301624.002", "Шайба (модификация)", 0.02, "make"),
    ("ЛМША.301614.001", "Шпилька", 0.05, "make"),
    ("ЛМША.301614.004", "Шпилька (модификация)", 0.05, "make"),
    ("Св-08Г2С-О", "Проволока сварочная 0,8 мм", 0.0, "buy"),
    ("Спрей антипригарный Auscon Wpre!", "Спрей антипригарный", 0.0, "buy"),
]

# Цеха (5 из техинкома)
WORKSHOPS = [
    ("01", "Заготовительный"),
    ("02", "Сварочный"),
    ("03", "Сборочный"),
    ("04", "Окрасочный"),
    ("05", "Контроль качества"),
]

# Профессии
PROFESSIONS = [
    ("Р-3", "Резчик", "рабочий", 3, 250.0),
    ("С-4", "Слесарь-сборщик", "рабочий", 4, 300.0),
    ("Э-5", "Электросварщик", "рабочий", 5, 380.0),
    ("Г-4", "Гибщик", "рабочий", 4, 290.0),
    ("К-3", "Контролёр ОТК", "рабочий", 3, 270.0),
    ("М-5", "Маляр", "рабочий", 5, 320.0),
]

# Материалы
MATERIALS = [
    ("09Г2С", "Сталь 09Г2С листовая", "лист", "ГОСТ 19281-2014", "кг", 95.0),
    ("Св-08Г2С-О", "Проволока сварочная Св-08Г2С-О 0,8 мм", "проволока", "ГОСТ Р ИСО 14175-2010", "кг", 145.0),
    ("Спрей антипригарный", "Спрей антипригарный Auscon Wpre!", "вспомогательные", "—", "л", 850.0),
]


def seed_all(verbose: bool = True) -> int:
    db.init_db()
    loaded = 0

    # Шасси
    for code, name, manuf, formula, curb, payload in CHASSIS:
        existing = db.query_one("SELECT id FROM chassis WHERE designation = ?", (code,))
        if existing:
            continue
        db.insert_and_get_id("chassis", {
            "designation": code,
            "name": name,
            "manufacturer": manuf,
            "wheel_formula": formula,
            "curb_weight_kg": curb,
            "payload_kg": payload,
        })
        loaded += 1
        if verbose:
            print(f"✅ chassis: {code}")

    # Модели изделий
    for code, name, ptype, chassis_des, tu in PRODUCT_MODELS:
        existing = db.query_one("SELECT id FROM product_models WHERE designation = ?", (code,))
        if existing:
            continue
        chassis_row = db.query_one("SELECT id FROM chassis WHERE designation = ?", (chassis_des,))
        chassis_id = chassis_row["id"] if chassis_row else None
        db.insert_and_get_id("product_models", {
            "designation": code,
            "name": name,
            "product_type": ptype,
            "chassis_id": chassis_id,
            "tu_doc": tu,
        })
        loaded += 1
        if verbose:
            print(f"✅ product_model: {code}")

    # Цеха
    for code, name in WORKSHOPS:
        existing = db.query_one("SELECT id FROM workshops WHERE code = ?", (code,))
        if existing:
            continue
        db.insert_and_get_id("workshops", {
            "code": code,
            "name": name,
        })
        loaded += 1
        if verbose:
            print(f"✅ workshop: {code} {name}")

    # Профессии
    for code, name, cat, grade, rate in PROFESSIONS:
        existing = db.query_one("SELECT id FROM professions WHERE code = ?", (code,))
        if existing:
            continue
        db.insert_and_get_id("professions", {
            "code": code,
            "name": name,
            "category": cat,
            "grade": grade,
            "hourly_rate": rate,
        })
        loaded += 1
        if verbose:
            print(f"✅ profession: {code} {name}")

    # Материалы
    for code, name, cat, grade, unit, price in MATERIALS:
        existing = db.query_one("SELECT id FROM materials WHERE code = ?", (code,))
        if existing:
            continue
        db.insert_and_get_id("materials", {
            "code": code,
            "name": name,
            "category": cat,
            "grade": grade,
            "unit": unit,
            "price_per_unit": price,
        })
        loaded += 1
        if verbose:
            print(f"✅ material: {code}")

    # Главные items (2 PDF)
    for spec in ITEMS:
        existing = db.query_one("SELECT id FROM items WHERE designation = ?", (spec["designation"],))
        if existing:
            continue
        db.insert_and_get_id("items", spec)
        loaded += 1
        if verbose:
            print(f"✅ item: {spec['designation']} «{spec['name']}»")

    # Составные
    for des, name, mass, sourcing in COMPOSITE:
        existing = db.query_one("SELECT id FROM items WHERE designation = ?", (des,))
        if existing:
            continue
        db.insert_and_get_id("items", {
            "designation": des,
            "name": name,
            "level": "purchased" if sourcing == "buy" else "detail",
            "type": "деталь",
            "mass_kg": mass,
            "sourcing": sourcing,
        })
        loaded += 1
        if verbose:
            print(f"✅ item: {des} «{name}» ({sourcing})")

    # Привязка к модели АЦ-8,0-40
    pm_id = db.query_one("SELECT id FROM product_models WHERE designation = 'АЦ-8,0-40'")
    if pm_id:
        for des in ["ЛМША.301314.010", "ЛМША.301712.000"]:
            item = db.query_one("SELECT id FROM items WHERE designation = ?", (des,))
            if item:
                db.execute("UPDATE items SET product_model_id = ? WHERE id = ?", (pm_id["id"], item["id"]))

    return loaded


if __name__ == "__main__":
    n = seed_all()
    print(f"\nЗагружено записей: {n}")
