"""
Загрузка workshop данных Техинкома в RAG production.
- Один workshop -> один RAG chunk
- Операции сгруппированы внутри chunk
"""
import json, base64

with open('/workspace/attachments/tehinkom_workshops.json', 'r', encoding='utf-8') as f:
    workshops = json.load(f)

# Сгенерируем SQL для INSERT в rag_documents (или подобную таблицу)
# Сначала надо посмотреть схему RAG

# Создадим Python скрипт для загрузки через SSH
PY = '''
import sqlite3, json
conn = sqlite3.connect('/opt/beget/bit-technolog/bit_technolog.db')
cur = conn.cursor()

# Сначала проверим какие таблицы связаны с RAG
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE 'rag%' OR name LIKE 'document%' OR name LIKE 'chunk%')")
tables = [r[0] for r in cur.fetchall()]
print("RAG TABLES:", tables)

# Прочитаем workshops
with open("/tmp/tehinkom_workshops.json", "r", encoding="utf-8") as f:
    workshops = json.load(f)
print(f"Workshops: {len(workshops)}")

# Проверим схему первой RAG-таблицы
if tables:
    first = tables[0]
    cur.execute(f"PRAGMA table_info({first})")
    for col in cur.fetchall():
        print(f"  {col}")
'''

with open('/tmp/workshops.json', 'w', encoding='utf-8') as f:
    json.dump(workshops, f, ensure_ascii=False)

print(f"Workshops: {len(workshops)}")
total_ops = sum(len(w['operations']) for w in workshops)
print(f"Total operations: {total_ops}")
