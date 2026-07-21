"""Метрики пилота.

Две ключевые метрики:
- b (время генерации ТК): от нажатия "Сгенерировать ТК" до утверждения
- c (% норм зелёного уровня): на текущий момент по всем ТК в работе
"""
from datetime import datetime
from repositories import db


def record_metric(code: str, value: float, label: str = "", notes: str = "") -> int:
    """Записать метрику. Один code может иметь много измерений (история)."""
    today = datetime.now().strftime("%Y-%m-%d")
    return db.insert_and_get_id("pilot_metrics", {
        "metric_code": code,
        "metric_value": value,
        "metric_label": label,
        "measured_at": today,
        "notes": notes,
    })


def start_tc_generation(item_id: int, user: str) -> int:
    """Начать замер генерации. Возвращает run_id для последующего finish."""
    return db.insert_and_get_id("pilot_runs", {
        "kind": "tc_generation",
        "item_id": item_id,
        "user": user,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "finished_at": None,
        "duration_sec": None,
    })


def finish_tc_generation(run_id: int, tc_id: int, notes: str = ""):
    """Закончить замер, записать в pilot_metrics."""
    row = db.query_one("SELECT started_at FROM pilot_runs WHERE id = ?", (run_id,))
    if not row or not row["started_at"]:
        return
    start = datetime.fromisoformat(row["started_at"])
    duration = (datetime.now() - start).total_seconds()
    db.execute(
        "UPDATE pilot_runs SET finished_at = ?, duration_sec = ?, tc_id = ?, notes = ? WHERE id = ?",
        (datetime.now().isoformat(timespec="seconds"), duration, tc_id, notes, run_id),
    )
    record_metric("b_tc_generation_sec", duration,
                 label=f"Генерация ТК для item_id={row.get('item_id') if hasattr(row, 'get') else ''}",
                 notes=f"run_id={run_id} tc_id={tc_id}")
    return duration


def get_metric_history(code: str, limit: int = 30) -> list:
    """История измерений метрики."""
    return db.rows_to_dicts(db.query(
        "SELECT * FROM pilot_metrics WHERE metric_code = ? ORDER BY measured_at DESC, id DESC LIMIT ?",
        (code, limit),
    ))


def calc_green_pct(scope: str = "all") -> dict:
    """% норм зелёного уровня (метрика c).
    
    scope: 'all' — все ТК, 'last_7_days' — за неделю, 'last_30_days' — за месяц
    """
    if scope == "last_7_days":
        where = "WHERE tc.created_at >= datetime('now', '-7 days')"
    elif scope == "last_30_days":
        where = "WHERE tc.created_at >= datetime('now', '-30 days')"
    else:
        where = ""
    
    sql = f"""
        SELECT 
            COUNT(o.id) AS total,
            SUM(CASE WHEN o.source = 'factory_data' THEN 1 ELSE 0 END) AS green,
            SUM(CASE WHEN o.source = 'ai_guess' THEN 1 ELSE 0 END) AS red
        FROM operations o
        JOIN tech_cards tc ON tc.id = o.tech_card_id
        {where}
    """
    row = db.query_one(sql)
    total = row["total"] or 0
    green = row["green"] or 0
    red = row["red"] or 0
    pct = (green * 100 / total) if total > 0 else 0
    return {
        "total": total,
        "green": green,
        "yellow": total - green - red,  # аналоги/оценка
        "red": red,
        "green_pct": round(pct, 1),
    }


def record_green_pct(scope: str = "all") -> int:
    """Записать текущее значение метрики c."""
    data = calc_green_pct(scope)
    return record_metric(
        "c_green_pct", data["green_pct"],
        label=f"% зелёных норм ({scope})",
        notes=f"total={data['total']} green={data['green']} yellow={data['yellow']} red={data['red']}"
    )


def get_dashboard_metrics() -> dict:
    """Сводка метрик для dashboard."""
    return {
        "green_pct_all": calc_green_pct("all"),
        "green_pct_7d": calc_green_pct("last_7_days"),
        "green_pct_30d": calc_green_pct("last_30_days"),
        "gen_history": get_metric_history("b_tc_generation_sec", 10),
        "green_history": get_metric_history("c_green_pct", 10),
    }
