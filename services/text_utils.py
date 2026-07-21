"""Утилиты для обработки текста (морфология, синонимы, сходство).

Извлечено из старого rag.py (Sprint 2) — нужно для services/rag.py (RAG v2 Sprint 5).
"""
import re
from typing import List, Set


# ============================================================
# СЛОВАРЬ СИНОНИМОВ (для workshop_context + rag)
# ============================================================

SYNONYMS = {
    "сварка": ["сваривание", "сварочные работы", "сварит"],
    "зачистка": ["зачистка швов", "зачистные", "зачищать", "очистка"],
    "сборка": ["собирать", "сборка узлов", "сборочные"],
    "прихватка": ["прихватывать", "прихватки"],
    "шлифовка": ["шлифовать", "шлифовальные"],
    "токарная": ["токарь", "токарные", "точение"],
    "фрезерная": ["фрезеровать", "фрезерные"],
    "сверление": ["сверлить", "сверловочные"],
    "гибка": ["гнуть", "гибочные"],
    "резка": ["резать", "отрезка", "раскрой"],
    "окраска": ["красить", "малярные", "покраска"],
    "контроль": ["проверка", "ОТК", "осмотр"],
}


def apply_synonyms(text: str) -> str:
    """Раскрыть синонимы — 'сварка' → 'сварка сваривание сварочные работы'."""
    out = text
    for word, syns in SYNONYMS.items():
        if word in out.lower():
            out = out + " " + " ".join(syns)
    return out


# ============================================================
# МОРФОЛОГИЯ (опционально pymorphy2)
# ============================================================

def get_morph():
    """Ленивая загрузка pymorphy2 (может быть не установлен)."""
    try:
        import pymorphy2
        return pymorphy2.MorphAnalyzer()
    except ImportError:
        return None


def lemmatize_text(text: str) -> str:
    """Лемматизация (нормальная форма слов). Если pymorphy2 нет — просто lower()."""
    morph = get_morph()
    if not morph:
        return text.lower()
    words = re.findall(r"\b\w+\b", text)
    lemmas = []
    for w in words:
        p = morph.parse(w)[0]
        lemmas.append(p.normal_form)
    return " ".join(lemmas)


# ============================================================
# СХОДСТВО МНОЖЕСТВ (для equipment/material)
# ============================================================

def jaccard(a: Set, b: Set) -> float:
    """Коэффициент Жаккара: |A ∩ B| / |A ∪ B|. 0 = нет пересечения, 1 = идентичны."""
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def equipment_set(draft_output: dict) -> Set[str]:
    """Извлечь множество equipment из draft_output."""
    if not draft_output:
        return set()
    eqs = draft_output.get("equipment", [])
    if isinstance(eqs, str):
        eqs = [eqs]
    return {e.lower().strip() for e in eqs if e}


def material_set(draft_output: dict) -> Set[str]:
    """Извлечь множество материалов из draft_output."""
    if not draft_output:
        return set()
    mats = draft_output.get("materials", [])
    if isinstance(mats, str):
        mats = [mats]
    return {m.lower().strip() for m in mats if m}
