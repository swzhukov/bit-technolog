"""
Скрипт загрузки 27 единиц оборудования Техинкома в production БД.
Запускается на Beget через SSH (pexpect).
"""
import os, sys, sqlite3, tempfile, base64

# Файл с оборудованием
EQUIPMENT_FILE = '/workspace/attachments/equipment_tehinkom.txt'

# Маппинг workshops (цеха) -> production
WORKSHOP_TO_PRODUCTION = {
    'УОМ': 'Заготовительное производство',
    'ПВТ': 'Производство высотной техники',
    'ПКТ': 'Производство кузовной техники',
    'УОМ(резерв)': 'Заготовительное производство',
    'ПВТ(резерв)': 'Производство высотной техники',
}

# Маппинг "производство" -> department code
PRODUCTION_CODE = {
    'Заготовительное производство': 'ZP',
    'Производство высотной техники': 'PVT',
    'Производство кузовной техники': 'PKT',
    'Мелкосерийное производство': 'MSP',
}

def parse_equipment(path):
    """Парсит equipment_tehinkom.txt в список словарей."""
    items = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 5: continue
            name, year, workshop, inv, eq_type = parts[:5]
            try:
                inv = int(inv)
                year = int(year)
            except ValueError:
                continue
            production = WORKSHOP_TO_PRODUCTION.get(workshop, workshop)
            ext_id = f"{PRODUCTION_CODE.get(production, 'XX')}-{inv}"
            items.append({
                'name': name,
                'type': eq_type,
                'code': inv,  # code = инвентарный
                'year': year,
                'workshop': workshop,
                'production': production,
                'external_id': ext_id,
                'inv': inv,
            })
    return items

def sql_insert_equipment():
    """Возвращает SQL для INSERT всех единиц."""
    items = parse_equipment(EQUIPMENT_FILE)
    print(f"Parsed {len(items)} equipment items")
    for it in items[:3]:
        print(f"  {it['external_id']}: {it['name']} ({it['year']}, {it['workshop']})")
    return items

# Запуск без БД — просто генерим SQL
if __name__ == '__main__':
    items = sql_insert_equipment()
    print(f"\nTotal: {len(items)}")

    # Генерим SQL скрипт
    sql_lines = ["-- Equipment loader for Tehinkom 27 units"]
    sql_lines.append("BEGIN TRANSACTION;")
    for it in items:
        name = it['name'].replace("'", "''")
        notes = f"Год: {it['year']}, Цех: {it['workshop']}, Инв.№: {it['inv']}"
        sql_lines.append(
            f"INSERT INTO equipment (name, type, code, source, external_id, notes) "
            f"VALUES ('{name}', '{it['type']}', '{it['code']}', 'tehinkom_docx_2025', '{it['external_id']}', '{notes}');"
        )
    sql_lines.append("COMMIT;")
    sql_lines.append(f"SELECT 'Inserted {len(items)} equipment', COUNT(*) FROM equipment;")

    with open('/tmp/load_equipment.sql', 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    print("\nSQL script saved to /tmp/load_equipment.sql")
    print(f"  {len(sql_lines)} lines")
