"""
Парсер DOCX v8 — section header может быть в cell[0] (Первые) или в cell[1] (в operations-части).
"""
import zipfile, json
from xml.etree import ElementTree as ET

NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def parse(path):
    with zipfile.ZipFile(path) as z:
        with z.open('word/document.xml') as f:
            tree = ET.parse(f)
    rows = []
    for tr in tree.iter(f'{NS}tr'):
        cells = []
        for tc in tr.iter(f'{NS}tc'):
            text = ''.join(t.text or '' for t in tc.iter(f'{NS}t'))
            cells.append(text.strip())
        if any(cells): rows.append(cells)
    return rows


rows = parse('/workspace/attachments/13bd245e__8f587913-5419-40fa-9b1b-1f01d2d2c143.docx')

# Top-level sections (Участок, Производство, Мелкосерийное)
# Sub-sections (Участок обработки металла, Уч-к лазерной резки, etc.)
# Workshops (Сварочно-сборочный уч-к КТ)
# Operations (1. Сборка цистерны)

top_sections = ('Участок', 'Производство', 'Мелкосерийное')
# 'Заготовительные' — это sub-section внутри "Производство кузовной техники"
# 'Уч-к' — это workshop
# 'Сварочно-сборочный уч-к' / 'Сборочный уч-к' — workshop (с пробелом, не "Уч-к")

current_section = ""
current_workshop_name = ""
by_name = {}

def is_top_section(t):
    return any(t.startswith(s) for s in top_sections)

def is_workshop_name(t):
    """'Уч-к X' или 'Сварочно-сборочный уч-к X' или 'Сборочный уч-к X'"""
    if not t: return False
    if t.startswith('Уч-к') or t.startswith('Сварочно-сборочный уч-к') or t.startswith('Сборочный уч-к'):
        return True
    return False

for row in rows:
    text = row[0] if row[0] else ''
    cell1 = row[1] if len(row) > 1 else ''
    cell2 = row[2] if len(row) > 2 else ''

    # === Section header ===
    # В "оглавлении" — cell[0] = section, cell[1] = пусто
    # В "operations-части" — cell[0] = '' или = число, cell[1] = section name
    section_text = ''
    if is_top_section(text) and not cell1:
        section_text = text
    elif not text and cell1 and is_top_section(cell1) and not cell2:
        section_text = cell1
    if section_text:
        current_section = section_text
        continue

    # === "Заготовительные операции..." — sub-section header внутри "Производство кузовной техники" ===
    if text and 'Заготовительные' in text and not cell1:
        current_section = text
        continue

    # === Workshop declaration ===
    # В "оглавлении" — cell[0] = workshop, cell[1] = пусто
    # В "operations-части" — cell[0] = '', cell[1] = workshop name (но не section!)
    workshop_name = ''
    if is_workshop_name(text) and not cell1:
        workshop_name = text
    elif not text and cell1 and is_workshop_name(cell1) and not cell2:
        workshop_name = cell1
    elif not text and cell1 and is_workshop_name(cell1) and cell2:
        # "Уч-к X | операция 1" в одной строке
        workshop_name = cell1
        if workshop_name not in by_name:
            by_name[workshop_name] = {'section': current_section, 'name': workshop_name, 'operations': []}
        by_name[workshop_name]['operations'].append({'idx': '', 'name': cell2, 'notes': ''})
        current_workshop_name = workshop_name
        continue

    if workshop_name:
        if workshop_name not in by_name:
            by_name[workshop_name] = {'section': current_section, 'name': workshop_name, 'operations': []}
        current_workshop_name = workshop_name
        continue

    # === Операция ===
    # cell[0] = '' или число, cell[1] = название операции
    if current_workshop_name and current_workshop_name in by_name and cell1:
        op_idx = text if text and text.isdigit() else ''
        op_name = cell1
        op_notes = cell2
        by_name[current_workshop_name]['operations'].append({
            'idx': op_idx, 'name': op_name, 'notes': op_notes
        })


final = list(by_name.values())

# Удаляем workshops с 0 операций (это оглавление)
final = [w for w in final if w['operations']]

# Удаляем "мусорные" операции (если первая операция — это section name)
# "Сборочный уч-к КТ" начинается с "Участок обработки металла" — это section header в operations-блоке
# Обработаем: если первая операция workshop-а == название другой секции, удалим её
for w in final:
    if w['operations']:
        first = w['operations'][0]
        if any(first['name'].startswith(s) for s in top_sections):
            w['operations'].pop(0)


with open('/workspace/attachments/tehinkom_workshops.json', 'w', encoding='utf-8') as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

print(f"Workshops (с операциями): {len(final)}")
total_ops = sum(len(w['operations']) for w in final)
print(f"Total operations: {total_ops}\n")
for w in final:
    print(f"[{w['section'][:50]}] {w['name']}: {len(w['operations'])} ops")
    for op in w['operations']:
        notes = op['notes'][:60] + '...' if len(op['notes']) > 60 else op['notes']
        print(f"  {op['idx']:>3}. {op['name']}" + (f" — {notes}" if notes else ""))
    print()
