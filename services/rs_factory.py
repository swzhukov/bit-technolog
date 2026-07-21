"""
rs_factory.py — детерминированный алгоритм расчёта РС.

ADR-0011 Принцип П8: РС-фабрика — детерминированный алгоритм по 8 осям.
LLM НЕ используется в слое 2 (расчёт). Только в слое 1 (генерация черновика ТК).

8 осей (разбор v2):
1. stage_resolution: by_workshop | by_site | by_room | by_route | single
2. op_granularity: full | aggregated | stages_only
3. norms: setup_per_piece | piece_only | total | none
4. materials: per_op | per_stage | per_spec
5. labor: per_op | summary | none
6. nesting: multi | flat
7. cooperation: stage_coop | purchased_semi
8. export_format: xml_1c | json_1c | csv

Вход: утверждённая ТК (operations) + профиль РС
Выход: OneCResourceSpec (готов к экспорту)

Каждая строка РС имеет аудит-цепочку:
"строка X ← правило Y ← операция Z (ТП)"
Это ОБЯЗАТЕЛЬНО — чтобы технолог мог проверить, откуда взялась цифра.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from gateways.one_c_gateway import OneCResourceSpec

logger = logging.getLogger(__name__)


# ============================================================
# DTO — СТРОКА РС + АУДИТ-ЦЕПОЧКА
# ============================================================

@dataclass
class RSAudit:
    """Аудит-цепочка для одной строки РС."""
    rule: str                              # "by_workshop" | "aggregate_by_profession" | ...
    source_operation_id: Optional[int]     # FK на operations.id (если применимо)
    source_op_number: Optional[int]        # 5, 10, 15...
    explanation: str                       # "4.35 н/ч = 0.10 + 0.15 + 0.12 + ... (sum of operations 015+020+025)"


@dataclass
class RSRow:
    """Одна строка ресурсной спецификации."""
    stage: str                             # "01/01" (цех/участок) или "" если агрегировано
    op_number: int                         # 0 если нет конкретной операции (агрегат)
    name: str                              # "Сборка под сварку" или "Этап: Сварочный"
    profession: str = ""                   # "Р-3" или "С-4, Э-5"
    equipment: str = ""                    # "НГ-6,3"
    qty: float = 1.0                       # Количество
    time_setup_min: float = 0.0            # Тпз
    time_per_unit_min: float = 0.0         # Тшт
    material_code: str = ""
    material_qty: float = 0.0
    material_unit: str = "кг"
    audit: Optional[RSAudit] = None        # Аудит-цепочка

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class RSReport:
    """Полный отчёт расчёта РС."""
    item_designation: str
    tech_card_id: Optional[int]
    profile_code: str
    profile_axes: Dict[str, str]
    rows: List[RSRow] = field(default_factory=list)
    summary: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_designation": self.item_designation,
            "tech_card_id": self.tech_card_id,
            "profile_code": self.profile_code,
            "profile_axes": self.profile_axes,
            "rows": [r.to_dict() for r in self.rows],
            "summary": self.summary,
            "warnings": self.warnings,
        }


# ============================================================
# ПРОФИЛЬ ПО УМОЛЧАНИЮ (для Техинкома)
# ============================================================

DEFAULT_PROFILE = {
    "stage_resolution": "by_workshop",   # по цехам (01, 02, 03...)
    "op_granularity": "full",             # все операции отдельно
    "norms": "setup_per_piece",           # Тпз + Тшт раздельно
    "materials": "per_op",                # материалы по операциям
    "labor": "per_op",                    # труд по операциям
    "nesting": "flat",                    # плоский (без вложенности)
    "cooperation": "stage_coop",          # этап-кооперация
    "export_format": "xml_1c",            # XML для 1С
}


# ============================================================
# РС-ФАБРИКА
# ============================================================

def build_rs(
    item_designation: str,
    operations: List[Dict[str, Any]],
    profile: Optional[Dict[str, str]] = None,
    tech_card_id: Optional[int] = None,
) -> RSReport:
    """Построить РС из операций ТК и профиля.

    Args:
        item_designation: Обозначение изделия
        operations: Список операций (с полями: op_number, name, workshop_code, equipment,
                    profession_code, time_setup_min, time_per_unit_min, materials[])
        profile: 8 осей (если None — DEFAULT_PROFILE)
        tech_card_id: ID техкарты (для аудита)
    """
    profile = profile or DEFAULT_PROFILE
    report = RSReport(
        item_designation=item_designation,
        tech_card_id=tech_card_id,
        profile_code=profile.get("code", "default"),
        profile_axes=profile,
    )

    if not operations:
        report.warnings.append("Нет операций для расчёта РС")
        return report

    # 1. Стадия 1: разбивка по stage_resolution
    stages = _group_by_stage(operations, profile["stage_resolution"])

    # 2. Стадия 2: фильтрация по op_granularity
    if profile["op_granularity"] == "stages_only":
        # Оставляем только строки этапов (агрегаты)
        for stage_key, ops in stages.items():
            row = _build_stage_row(item_designation, stage_key, ops, profile)
            report.rows.append(row)
    elif profile["op_granularity"] == "aggregated":
        # Агрегируем по профессиям
        for stage_key, ops in stages.items():
            for prof_code, prof_ops in _group_by_profession(ops).items():
                row = _build_aggregated_row(item_designation, stage_key, prof_code, prof_ops, profile)
                report.rows.append(row)
    else:
        # full: одна строка на операцию
        for stage_key, ops in stages.items():
            for op in sorted(ops, key=lambda o: o.get("op_number", 0)):
                row = _build_op_row(item_designation, stage_key, op, profile)
                report.rows.append(row)

    # 3. Кооперация
    if profile["cooperation"] == "stage_coop":
        for op in operations:
            if op.get("is_coop_step"):
                row = RSRow(
                    stage=f"{op.get('workshop_code', '??')}/{op.get('site_code', '??')}",
                    op_number=op.get("op_number", 0),
                    name=f"Передача в кооперацию: {op.get('coop_note', '')}",
                    profession="",
                    equipment="",
                    qty=1,
                    time_setup_min=op.get("time_setup_min", 0),
                    time_per_unit_min=0,
                    audit=RSAudit(
                        rule="stage_coop",
                        source_operation_id=op.get("id"),
                        source_op_number=op.get("op_number"),
                        explanation=f"Кооперационная операция: {op.get('coop_note', '')}",
                    ),
                )
                report.rows.append(row)

    # 4. Summary
    total_setup = sum(r.time_setup_min for r in report.rows)
    total_per_unit = sum(r.time_per_unit_min for r in report.rows)
    total_materials = sum(r.material_qty for r in report.rows if r.material_qty)
    report.summary = {
        "total_setup_min": total_setup,
        "total_per_unit_min": total_per_unit,
        "total_time_min": total_setup + total_per_unit,
        "total_time_hours": round((total_setup + total_per_unit) / 60, 3),
        "operations_count": len(operations),
        "rows_count": len(report.rows),
        "materials_count": sum(1 for r in report.rows if r.material_code),
    }

    # 5. Warnings
    if any(r.time_per_unit_min == 0 for r in report.rows if r.op_number > 0):
        report.warnings.append("Есть операции без Тшт (0 н/ч) — проверьте ввод")
    if not any(r.material_code for r in report.rows):
        report.warnings.append("В РС нет материалов — проверьте, нужны ли")

    return report


# ============================================================
# ВНУТРЕННИЕ ФУНКЦИИ (правила)
# ============================================================

def _group_by_stage(operations: List[Dict[str, Any]], resolution: str) -> Dict[str, List[Dict]]:
    """Группировка операций по этапам согласно оси stage_resolution."""
    if resolution == "single":
        return {"all": operations}
    if resolution == "by_workshop":
        return _group_by(operations, lambda o: o.get("workshop_code", "??"))
    if resolution == "by_site":
        return _group_by(operations, lambda o: f"{o.get('workshop_code', '??')}/{o.get('site_code', '??')}")
    if resolution == "by_room":
        return _group_by(operations, lambda o: f"{o.get('workshop_code', '??')}/{o.get('site_code', '??')}/{o.get('workplace', '??')}")
    if resolution == "by_route":
        # Группируем по типам операций (заготовительные/сборочные/сварочные/контроль)
        return _group_by(operations, _route_group)
    return _group_by(operations, lambda o: o.get("workshop_code", "??"))


def _route_group(op: Dict) -> str:
    name = (op.get("name") or "").lower()
    if any(k in name for k in ["резк", "заготовительн", "раскрой", "гибк", "вальц"]):
        return "Заготовительные"
    if any(k in name for k in ["сварк", "наплавк"]):
        return "Сварочные"
    if any(k in name for k in ["сборк", "установк", "правк", "зачистк"]):
        return "Сборочные"
    if any(k in name for k in ["контрол", "осмотр", "испыта"]):
        return "Контроль"
    if "окраск" in name or "грунтов" in name or "покраск" in name:
        return "Окраска"
    return "Прочие"


def _group_by(items: List, key_fn) -> Dict:
    out = {}
    for it in items:
        k = key_fn(it)
        out.setdefault(k, []).append(it)
    return out


def _group_by_profession(operations: List[Dict]) -> Dict[str, List[Dict]]:
    """Группировка по профессии."""
    return _group_by(operations, lambda o: o.get("profession_code", "") or "?")


def _build_op_row(
    item_designation: str,
    stage_key: str,
    op: Dict,
    profile: Dict,
) -> RSRow:
    """Создать строку РС для одной операции (full granularity)."""
    op_num = op.get("op_number", 0)
    op_name = op.get("name", "")
    materials = op.get("materials", [])

    # Берём первый материал (для flat — одна строка на операцию)
    mat = materials[0] if materials else {}

    return RSRow(
        stage=stage_key,
        op_number=op_num,
        name=op_name,
        profession=op.get("profession_code", ""),
        equipment=op.get("equipment_name", ""),
        qty=1,
        time_setup_min=op.get("time_setup_min", 0) or 0,
        time_per_unit_min=op.get("time_per_unit_min", 0) or 0,
        material_code=mat.get("code", ""),
        material_qty=mat.get("qty", 0) or 0,
        material_unit=mat.get("unit", "кг"),
        audit=RSAudit(
            rule="op_to_row",
            source_operation_id=op.get("id"),
            source_op_number=op_num,
            explanation=f"Операция {op_num:03d} {op_name} → строка РС 1:1",
        ),
    )


def _build_stage_row(
    item_designation: str,
    stage_key: str,
    operations: List[Dict],
    profile: Dict,
) -> RSRow:
    """Строка РС = один этап (stages_only)."""
    total_setup = sum(o.get("time_setup_min", 0) or 0 for o in operations)
    total_per_unit = sum(o.get("time_per_unit_min", 0) or 0 for o in operations)
    op_nums = [o.get("op_number", 0) for o in operations]
    op_names = " + ".join(f"{o.get('op_number', 0):03d}" for o in operations[:5])
    if len(operations) > 5:
        op_names += f" + {len(operations) - 5} ещё"

    return RSRow(
        stage=stage_key,
        op_number=0,
        name=f"Этап: {stage_key} ({len(operations)} оп.)",
        profession=", ".join(set(o.get("profession_code", "") for o in operations if o.get("profession_code"))),
        equipment=", ".join(set(o.get("equipment_name", "") for o in operations if o.get("equipment_name")))[:50],
        qty=1,
        time_setup_min=round(total_setup, 3),
        time_per_unit_min=round(total_per_unit, 3),
        audit=RSAudit(
            rule="aggregate_by_stage",
            source_operation_id=operations[0].get("id") if operations else None,
            source_op_number=op_nums[0] if op_nums else None,
            explanation=f"Этап {stage_key} = сумма {len(operations)} операций ({op_names}). "
                        f"Тпз={total_setup:.2f}, Тшт={total_per_unit:.2f} мин",
        ),
    )


def _build_aggregated_row(
    item_designation: str,
    stage_key: str,
    prof_code: str,
    operations: List[Dict],
    profile: Dict,
) -> RSRow:
    """Строка РС = агрегат по профессии в этапе."""
    total_setup = sum(o.get("time_setup_min", 0) or 0 for o in operations)
    total_per_unit = sum(o.get("time_per_unit_min", 0) or 0 for o in operations)
    op_nums = ", ".join(f"{o.get('op_number', 0):03d}" for o in operations)

    return RSRow(
        stage=stage_key,
        op_number=0,
        name=f"{stage_key} • {prof_code}",
        profession=prof_code,
        equipment="",
        qty=1,
        time_setup_min=round(total_setup, 3),
        time_per_unit_min=round(total_per_unit, 3),
        audit=RSAudit(
            rule="aggregate_by_profession",
            source_operation_id=operations[0].get("id") if operations else None,
            source_op_number=operations[0].get("op_number", 0) if operations else None,
            explanation=f"Агрегат по профессии {prof_code} в {stage_key} = {op_nums}. "
                        f"Тпз={total_setup:.2f}, Тшт={total_per_unit:.2f} мин",
        ),
    )


# ============================================================
# ЭКСПОРТ В OneCResourceSpec
# ============================================================

def to_one_c_spec(report: RSReport, item_ref_1c: str = "", tech_card_ref: str = "", version: int = 1, change_reason: str = "") -> OneCResourceSpec:
    """Конвертировать отчёт РС-фабрики в OneCResourceSpec для экспорта в 1С."""
    return OneCResourceSpec(
        ref_1c=None,  # Будет присвоен 1С при импорте
        item_ref=item_ref_1c or report.item_designation,
        tech_card_ref=tech_card_ref,
        version=version,
        profile_code=report.profile_code,
        rows=[r.to_dict() for r in report.rows],
        change_reason=change_reason,
    )


# ============================================================
# ДЕТЕРМИНИЗМ (важно для тестов)
# ============================================================

def is_deterministic(operations: List[Dict], profile: Dict, runs: int = 10) -> bool:
    """Проверить, что РС детерминированная (одинаковая при N запусках)."""
    reports = [build_rs("test", operations, profile) for _ in range(runs)]
    first = reports[0].to_dict()
    for r in reports[1:]:
        if r.to_dict() != first:
            return False
    return True
