"""
БИТ.Технолог v0.8 — центральный модуль БД.

Принципы (ADR-0011):
- 25 таблиц по разбору Сергея
- items универсальная (level: detail/assembly/product)
- bom_links MANY-TO-MANY
- ref_1c у каждой сущности с двойником в 1С
- Один факт — одно место
- Миграция: запуск migrations/001_v0_8_init.sql
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

# Путь к БД и SQL-файлу
DB_PATH = Path(__file__).parent.parent / "data" / "bit_technolog_v0_8.db"
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"

# Семафор для SQLite (один поток на запись)
_db_lock = threading.RLock()
_conn: Optional[sqlite3.Connection] = None


def get_connection() -> sqlite3.Connection:
    """Singleton connection. Foreign keys ON, Row factory = Row."""
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
        _conn.execute("PRAGMA journal_mode = WAL")
    return _conn


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """Контекст для транзакции с локом."""
    with _db_lock:
        conn = get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def init_db() -> None:
    """Применить все миграции из migrations/*.sql (по порядку)."""
    conn = get_connection()
    with _db_lock:
        for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            with open(sql_file, encoding="utf-8") as f:
                sql = f.read()
            # executescript сам разбирает SQL на statements с учётом комментариев
            try:
                conn.executescript(sql)
            except sqlite3.OperationalError as e:
                if "already exists" not in str(e):
                    raise
        conn.commit()


def reset_db() -> None:
    """Снести БД и пересоздать (для тестов)."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()


# ============================================================
# GENERIC CRUD
# ============================================================

def query(sql: str, params: tuple = ()) -> List[sqlite3.Row]:
    conn = get_connection()
    with _db_lock:
        return list(conn.execute(sql, params).fetchall())


def query_one(sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
    conn = get_connection()
    with _db_lock:
        return conn.execute(sql, params).fetchone()


def execute(sql: str, params: tuple = ()) -> int:
    """INSERT/UPDATE/DELETE. Возвращает lastrowid для INSERT."""
    conn = get_connection()
    with _db_lock:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def execute_script(sql: str) -> None:
    conn = get_connection()
    with _db_lock:
        conn.executescript(sql)
        conn.commit()


# ============================================================
# HELPERS
# ============================================================

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Row → dict (с распаковкой JSON-полей)."""
    if row is None:
        return {}
    d = dict(row)
    for key, val in d.items():
        if isinstance(val, str) and val.startswith(("{", "[")):
            try:
                d[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def rows_to_dicts(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [row_to_dict(r) for r in rows]


def insert_and_get_id(table: str, data: Dict[str, Any]) -> int:
    """INSERT с заменой dict значений. Возвращает rowid."""
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    values = tuple(
        json.dumps(v) if isinstance(v, (dict, list)) else v
        for v in data.values()
    )
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    return execute(sql, values)


# ============================================================
# ГЛАВНЫЕ ЗАПРОСЫ (для репозиториев)
# ============================================================

def list_items(
    level: Optional[str] = None,
    product_model_id: Optional[int] = None,
    configuration_id: Optional[int] = None,
    sourcing: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Список items (детали/узлы/сборки) с фильтрами."""
    sql = "SELECT * FROM items WHERE 1=1"
    params: list = []
    if level:
        sql += " AND level = ?"
        params.append(level)
    if product_model_id:
        sql += " AND product_model_id = ?"
        params.append(product_model_id)
    if configuration_id:
        sql += " AND configuration_id = ?"
        params.append(configuration_id)
    if sourcing:
        sql += " AND sourcing = ?"
        params.append(sourcing)
    if search:
        sql += " AND (designation LIKE ? OR name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    sql += " ORDER BY designation LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    return rows_to_dicts(query(sql, tuple(params)))


def get_item_with_bom(item_id: int) -> Dict[str, Any]:
    """Item + его состав (bom_links)."""
    item = row_to_dict(query_one("SELECT * FROM items WHERE id = ?", (item_id,)))
    if not item:
        return {}
    children = rows_to_dicts(query("""
        SELECT b.*, i.designation, i.name, i.level, i.mass_kg, i.sourcing
        FROM bom_links b
        JOIN items i ON i.id = b.child_item_id
        WHERE b.parent_item_id = ?
    """, (item_id,)))
    item["children"] = children
    return item


def get_tech_card_full(tech_card_id: int) -> Dict[str, Any]:
    """ТК + операции + материалы операций."""
    tc = row_to_dict(query_one("SELECT * FROM tech_cards WHERE id = ?", (tech_card_id,)))
    if not tc:
        return {}
    operations = rows_to_dicts(query("""
        SELECT o.*,
               w.name AS workshop_name, w.code AS workshop_code,
               e.name AS equipment_name, e.inventory_no,
               p.code AS profession_code, p.name AS profession_name, p.grade
        FROM operations o
        LEFT JOIN workshops w ON w.id = o.workshop_id
        LEFT JOIN equipment e ON e.id = o.equipment_id
        LEFT JOIN professions p ON p.id = o.profession_id
        WHERE o.tech_card_id = ?
        ORDER BY o.op_number
    """, (tech_card_id,)))
    for op in operations:
        op["materials"] = rows_to_dicts(query("""
            SELECT om.*, m.code AS material_code, m.name AS material_name, m.unit AS material_unit
            FROM operation_materials om
            JOIN materials m ON m.id = om.material_id
            WHERE om.operation_id = ?
        """, (op["id"],)))
    tc["operations"] = operations
    return tc


def get_etalons_for_rag(
    product_type: Optional[str] = None,
    operation_name: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Получить эталоны для RAG-поиска аналогов."""
    sql = "SELECT * FROM etalons WHERE is_published = 1"
    params: list = []
    if product_type:
        sql += " AND product_type = ?"
        params.append(product_type)
    sql += " ORDER BY approved_date DESC LIMIT ?"
    params.append(limit)
    return rows_to_dicts(query(sql, tuple(params)))


# ============================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================

if __name__ == "__main__":
    # python -m repositories.db — применить миграции
    print(f"DB: {DB_PATH}")
    print(f"Initializing...")
    init_db()
    print("OK")
    # Проверим таблицы
    rows = query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    print(f"Tables: {len(rows)}")
    for r in rows[:30]:
        print(f"  - {r['name']}")
