"""
tp_parser.py — парсер техпроцессов (из OCR или ручного ввода).

Поддерживает 2 формата:
1. Из OCR PDF комплекта документов (ГОСТ 3.1105)
2. Из табличного ввода (CSV / ручная форма)

Извлекает:
- designation (обозначение)
- name (название)
- operations (операции с Тшт+Тпз)
- materials (материалы операций)
- equipment (оборудование)
- professions (профессии)
- docs_used (КК, КЭ, ОК, ИОТ)

Возвращает dict, готовый для записи в etalons.content_json.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# DTO
# ============================================================

@dataclass
class TPOperation:
    op_number: int                  # 10, 15, 20, ...
    name: str                        # "Подготовительная", "Сварка Трубы"
    workshop_code: str = ""          # "01"
    site_code: str = ""              # "01"
    workplace: str = ""              # "04"
    equipment_name: str = ""         # "Полуавтомат сварочный"
    profession_code: str = ""        # "Э-5"
    profession_name: str = ""        # "Электросварщик"
    time_setup_min: float = 0.0      # Тпз
    time_per_unit_min: float = 0.0   # Тшт
    materials: List[Dict[str, Any]] = field(default_factory=list)
    docs: List[str] = field(default_factory=list)  # "КК лист 3", "ИОТ №001"


@dataclass
class TPComposite:
    """Структура ТП для записи в etalons.content_json."""
    designation: str = ""
    name: str = ""
    product_type: str = ""
    source_doc: str = ""
    pages: int = 0
    operations: List[TPOperation] = field(default_factory=list)
    materials: List[Dict[str, Any]] = field(default_factory=list)  # общая К/М
    equipment: List[str] = field(default_factory=list)
    docs_used: List[str] = field(default_factory=list)
    approved_by: str = ""
    approved_date: str = ""
    parse_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "designation": self.designation,
            "name": self.name,
            "product_type": self.product_type,
            "source_doc": self.source_doc,
            "pages": self.pages,
            "operations": [asdict(op) for op in self.operations],
            "materials": self.materials,
            "equipment": self.equipment,
            "docs_used": self.docs_used,
            "approved_by": self.approved_by,
            "approved_date": self.approved_date,
            "parse_warnings": self.parse_warnings,
        }


# ============================================================
# РЕГУЛЯРКИ
# ============================================================

# Обозначение: ЛМША.301314.010 / ЛМША.301712.000
RE_DESIGNATION = re.compile(r"[ЛM][МM][ШШ][АA]\.\d{6}\.\d{3}")

# Операции в формате МК/ОК:
#   "А 01 01 04 010 9043, Подготовительная" (цех 01, уч 01, РМ 04, оп 010)
#   "А 01 01 04 015 9043, Сборка под сварку"
RE_OPERATION = re.compile(
    r"^[АA]\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{3})\s*[\d,]*\s*,?\s*([А-Яа-я][А-Яа-я\s,]+?)(?=\s{2,}|КК|КЭ|ОК|ИОТ|$)",
    re.MULTILINE,
)

# Материалы:
#   "м 13 01 01 04 015 — _ Спрей антипригарный ... 0,23"
#   "м 18 | 1 01 04 010 | - Проволока 0,8 Св-08Г2С-0"
RE_MATERIAL = re.compile(
    r"^[МM]\s+\d+[\s|]+[\d\s|]+(\d{3})[\s|]+.*?([А-Яа-я][А-Яа-я0-9\-\.\s]+?)\s+([А-Я][А-Яа-я0-9\-\.]+?)(?:\s+[А-Я]+)?\s+(\d+[,\.]?\d*)\s*$",
    re.MULTILINE,
)

# Общее кол-во материала (из К/М):
#   "11 Пружина тарельчатая ЛМША.304590.001 —- — 1 72"
RE_COMPOSITE_ITEM = re.compile(
    r"^\d+\s+([А-Яа-я][А-Яа-я\s]+?)\s+(ЛМША\.\d{6}\.\d{3})\s+.*?\s+(\d+)\s*$",
    re.MULTILINE,
)

# Согласовано/Утверждаю:
RE_APPROVED = re.compile(r"(СОГЛАСОВАНО|УТВЕРЖДАЮ)", re.IGNORECASE)
RE_APPROVER = re.compile(r"(Начальник\s+\w+\s+[А-Я][а-я]+\s+[А-Я]\.[А-Я]\.?)")


# ============================================================
# ПАРСЕР
# ============================================================

def _preprocess_ocr(text: str) -> str:
    """Убрать OCR-мусор: |, _."""
    import re as _re
    text = _re.sub(r"\s*\|\s*", " ", text)
    text = _re.sub(r"_+", " ", text)
    return text


def parse_tp_text(text: str, source_doc: str = "") -> TPComposite:
    """Парсит текст техпроцесса (из OCR или ручного ввода)."""
    text = _preprocess_ocr(text)
    tp = TPComposite(source_doc=source_doc)

    # 1. Обозначение (в заголовке)
    m = re.search(r"[ЛM][МM][ШШ][АA]\.\s*\d{6}\.\s*\d{3}", text)
    if m:
        tp.designation = _normalize_designation(m.group(0).replace(" ", ""))

    # 2. Название (ищем "КОМПЛЕКТ ДОКУМЕНТОВ ... ИМЯ_ДЕФЕКТА")
    m2 = re.search(
        r"КОМПЛЕКТ\s+ДОКУМЕНТОВ[^А-Яа-я]*([А-Яа-я][А-Яа-я\s]+?)(?:\s*ЛМША|\s*КД)",
        text, re.IGNORECASE
    )
    if m2:
        name = m2.group(1).strip()
        # Убираем служебные слова
        for stop in ["технологический процесс", "сборки", "и сварки", "процесс"]:
            name = re.sub(stop, "", name, flags=re.IGNORECASE).strip()
        if name and len(name) > 3:
            tp.name = name[:200]
    if not tp.name and tp.designation:
        # Fallback: ищем по обозначению
        m3 = re.search(r"ЛМША\.\d{6}\.\d{3}\s*\n?\s*([А-Яа-я][А-Яа-я\s]+)", text)
        if m3:
            tp.name = m3.group(1).strip().split("\n")[0][:200]

    # 3. Продукт
    if "АЦ-" in text or "пожарн" in text.lower() or "цистерн" in text.lower():
        tp.product_type = "АЦ"
    elif "УМК" in text or "Установк" in text:
        tp.product_type = "УМК"
    elif "ПСС" in text:
        tp.product_type = "ПСС"

    # 4. Операции (более гибкая регулярка)
    # Ищем строки вида: "А 01 01 04 010 0108, Подготовительная КК ..."
    op_re = re.compile(
        r"\b[АA]\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{3})\b\s*"
        r"[А-Яа-яЁё0-9\s,]*?[\.,]?\s*"
        r"([А-Яа-яЁё][А-Яа-яЁё\s]+?)"
        r"(?=\s+(?:КК|КЭ|ОК|ИОТ|ВО|ОКК|$))",
        re.MULTILINE,
    )
    for m in op_re.finditer(text):
        op = TPOperation(
            op_number=int(m.group(4)),
            name=_clean_op_name(m.group(5)),
            workshop_code=m.group(1).zfill(2),
            site_code=m.group(2).zfill(2),
            workplace=m.group(3).zfill(2),
        )
        # Дедупликация
        if any(o.op_number == op.op_number for o in tp.operations):
            continue
        tp.operations.append(op)

    # 4. Материалы операций
    for m in RE_MATERIAL.finditer(text):
        op_num = int(m.group(1))
        mat_name = m.group(2).strip()
        mat_code = m.group(3).strip()
        mat_qty = m.group(4).replace(",", ".")
        # Найти операцию
        for op in tp.operations:
            if op.op_number == op_num:
                op.materials.append({
                    "name": mat_name,
                    "code": mat_code,
                    "qty": float(mat_qty) if mat_qty else 0.0,
                    "unit": "кг",
                })
                break

    # 5. Состав (из К/М)
    for m in RE_COMPOSITE_ITEM.finditer(text):
        tp.materials.append({
            "name": m.group(1).strip(),
            "designation": m.group(2).strip(),
            "qty": int(m.group(3)),
        })

    # 6. Согласующие
    approver_match = re.search(r"Начальник\s+\w+\s+([А-Я][а-я]+\s+[А-Я]\.[А-Я]\.?)", text)
    if approver_match:
        tp.approved_by = approver_match.group(1).strip()

    # 7. Оборудование (ищем по словарю)
    equipment_keywords = [
        "Полуавтомат сварочный", "Пресс", "Гильотинные ножницы",
        "Стенд сборочный", "УШМ", "Стол", "Сварочный стол",
    ]
    for kw in equipment_keywords:
        if kw in text:
            tp.equipment.append(kw)

    # 8. Документы
    for pattern, label in [
        (r"ИОТ\s*№\s*\d+", "ИОТ"),
        (r"КК\s*\(?ЛИСТ\s*\d+\)?", "КК"),
        (r"КЭ\s*\(?ЛИСТ\s*\d+\)?", "КЭ"),
        (r"ОК\s*\(?ЛИСТ\s*\d+\)?", "ОК"),
        (r"ВП\s+\d+\s+\w+\s+\w+", "ВП"),
    ]:
        matches = re.findall(pattern, text)
        for m in matches:
            tp.docs_used.append(m)

    # 9. Предупреждения
    if not tp.designation:
        tp.parse_warnings.append("Не найдено обозначение детали (формат ЛМША.XXXXXX.XXX)")
    if not tp.operations:
        tp.parse_warnings.append("Не найдено ни одной операции (формат: А 01 01 04 010)")
    if not tp.materials and not any(op.materials for op in tp.operations):
        tp.parse_warnings.append("Не найдено материалов")

    # 10. Сортировка операций
    tp.operations.sort(key=lambda o: o.op_number)

    return tp


def _clean_op_name(name: str) -> str:
    """Очистить название операции от мусора."""
    name = name.strip().rstrip(",").strip()
    # Убрать хвост с цифрами (OCR-артефакты)
    import re as _re
    name = _re.sub(r"\s+\d+[\d\s]*$", "", name)
    name = _re.sub(r"\s+[АA]\s*$", "", name)
    # Убрать двойные пробелы
    name = _re.sub(r"\s+", " ", name)
    return name[:200]


def _normalize_designation(des: str) -> str:
    """ЛМША → ЛМША (OCR может путать Л/М, Ш/Щ, А/Я)."""
    return (des
            .replace("M", "М").replace("m", "м")
            .replace("Ш", "Ш").replace("щ", "щ")
            .replace("A", "А").replace("a", "а"))


# ============================================================
# ВЕРИФИКАЦИЯ ПАРСЕРА
# ============================================================

def validate_parsed_tp(tp: TPComposite) -> List[str]:
    """Проверить корректность распарсенного ТП. Возвращает список проблем."""
    issues = []
    if not tp.designation:
        issues.append("❌ Нет обозначения")
    if not tp.operations:
        issues.append("❌ Нет операций")
    if tp.operations and len(tp.operations) < 2:
        issues.append(f"⚠️  Только {len(tp.operations)} операция — необычно мало")
    # Проверим непрерывность нумерации
    nums = [op.op_number for op in tp.operations]
    if nums:
        expected = list(range(min(nums), max(nums) + 1, 5))
        if nums != expected:
            issues.append(f"⚠️  Пропуски в нумерации: {nums}")
    # Проверим материалы
    no_mat = [op.op_number for op in tp.operations if not op.materials and "Сварка" in op.name]
    if no_mat:
        issues.append(f"⚠️  Операции без материалов: {no_mat} (сварка требует проволоку)")
    return issues


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m services.tp_parser <ocr_text_file>")
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    tp = parse_tp_text(text, source_doc=sys.argv[1])
    print(f"Обозначение: {tp.designation}")
    print(f"Название:    {tp.name}")
    print(f"Продукт:     {tp.product_type}")
    print(f"Согласовано: {tp.approved_by}")
    print(f"Операций:    {len(tp.operations)}")
    for op in tp.operations:
        print(f"  {op.op_number:03d} [{op.workshop_code}/{op.site_code}/{op.workplace}] {op.name} ({len(op.materials)} материалов)")
    print(f"Материалов (К/М): {len(tp.materials)}")
    print(f"Оборудование: {', '.join(tp.equipment)}")
    print(f"Предупреждения: {tp.parse_warnings}")
    issues = validate_parsed_tp(tp)
    if issues:
        print(f"Проверка: {issues}")
    else:
        print("Проверка: OK")
