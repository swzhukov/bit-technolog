"""
Sprint 7 D3: LLM extraction из OCR text чертежа.

Sprint 7 D10: SQLite-based cache для избежания повторных LLM вызовов
- key = hash(ocr_text)
- value = llm_data (JSON)
- is_fallback = 1 если regex fallback (тоже кешируется)
- hits_count = сколько раз использовали
"""
import json
import logging
import re
import time
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Промт для LLM
EXTRACTION_PROMPT = """Ты — инженер-технолог машиностроительного завода. Проанализируй текст с чертежа детали и извлеки структурированные данные.

Текст с чертежа (OCR):
---
{ocr_text}
---

Извлеки ТОЛЬКО следующие поля (верни валидный JSON, без markdown-обёрток, без пояснений):

{{
  "designation": "обозначение по ГОСТ 2.201 (например, 03-ТВ.30.119.01). Если не найдено — null",
  "name": "наименование детали (например, Кронштейн). Если не найдено — null",
  "level": "тип: detail | assembly | standard_item. По умолчанию detail",
  "material": "материал (например, Труба 60х40х3.0 ГОСТ 8645-68, Сталь 35Х, ...). Если не найдено — null",
  "gost": "ГОСТ на материал (если указан). null если не указан",
  "dimensions": "габаритные размеры в мм (например, 200x100x50). null если не найдено",
  "mass_kg": "масса в кг (число, например, 0.45). null если не указана",
  "surface_treatment": "покрытие/обработка поверхности (если указано). null если нет",
  "raw_components": [
    {{"designation": "...", "name": "...", "quantity": 1, "material": "..."}}
  ],
  "author": "ФИО разработчика (если указано). null если нет",
  "drawing_date": "дата чертежа (YYYY-MM-DD если возможно). null если нет",
  "notes": "любые дополнительные заметки (допуски, шероховатость, и т.п.). null если нет"
}}

Правила:
1. Если поле не найдено в тексте — ставь null
2. Не выдумывай данных, которых нет в тексте
3. Обозначение обычно содержит точки, цифры, иногда буквы (например, "03-ТВ.30.119.01")
4. Наименование — короткое слово или 2-3 слова (Кронштейн, Заглушка, Труба, Вал, и т.п.)
5. Материал обычно указан как "Материал: ..." или в графе "Материал"
6. Размеры могут быть в формате "L=200мм" или "200×100" или "Ø50"
7. raw_components — это составные части сборочного чертежа (если это сборочный)
"""


def _get_db_path() -> str:
    """Получить путь к БД (Sprint 6+: SQLite WAL)."""
    return "/app/data/bit_technolog_v0_8.db"


def _ocr_hash(ocr_text: str) -> str:
    """SHA256 hash от нормализованного OCR text.
    
    Нормализация: strip + lowercase (для устойчивости к разному OCR шуму).
    """
    norm = re.sub(r'\s+', ' ', ocr_text.strip().lower())
    return hashlib.sha256(norm.encode('utf-8')).hexdigest()[:32]  # 32 hex = 128 bit


def _cache_lookup(ocr_text: str) -> Optional[Tuple[Dict[str, Any], bool]]:
    """Поиск в кеше. Возвращает (llm_data, is_fallback) или None."""
    import sqlite3
    h = _ocr_hash(ocr_text)
    try:
        conn = sqlite3.connect(_get_db_path(), timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        cur = conn.cursor()
        cur.execute(
            "SELECT llm_data, is_fallback, hits_count FROM llm_extraction_cache WHERE ocr_hash = ?",
            (h,)
        )
        row = cur.fetchone()
        if row:
            llm_data_str, is_fallback, hits = row
            # Increment hits
            cur.execute(
                "UPDATE llm_extraction_cache SET hits_count = hits_count + 1, last_used_at = CURRENT_TIMESTAMP WHERE ocr_hash = ?",
                (h,)
            )
            conn.commit()
            conn.close()
            return json.loads(llm_data_str), bool(is_fallback)
        conn.close()
    except Exception as e:
        logger.warning(f"cache lookup failed: {e}")
    return None


def _cache_store(ocr_text: str, llm_data: Dict[str, Any], is_fallback: bool = False) -> None:
    """Сохранить в кеш."""
    import sqlite3
    h = _ocr_hash(ocr_text)
    try:
        conn = sqlite3.connect(_get_db_path(), timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        cur = conn.cursor()
        cur.execute(
            """INSERT OR REPLACE INTO llm_extraction_cache (ocr_hash, ocr_text_preview, llm_data, is_fallback, hits_count, last_used_at)
               VALUES (?, ?, ?, ?, COALESCE((SELECT hits_count FROM llm_extraction_cache WHERE ocr_hash=?), 0) + 1, CURRENT_TIMESTAMP)""",
            (h, ocr_text[:100], json.dumps(llm_data, ensure_ascii=False), 1 if is_fallback else 0, h)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"cache store failed: {e}")


def llm_extract(ocr_text: str, use_cache: bool = True) -> Tuple[bool, Dict[str, Any], str]:
    """Извлечь структурированные данные из OCR text через LLM.
    
    Sprint 7 D10: использует SQLite кеш. Если ocr_text уже обработан —
    возьмёт результат из кеша (hit) вместо LLM вызова.
    
    Returns: (success, data_dict, error_message)
    """
    if not ocr_text or not ocr_text.strip():
        return False, {}, "empty OCR text"
    
    # 1. Cache lookup
    if use_cache:
        cached = _cache_lookup(ocr_text)
        if cached is not None:
            llm_data, is_fallback = cached
            suffix = " (regex fallback)" if is_fallback else ""
            return True, llm_data, f"cache_hit{suffix}"
    
    # 2. LLM call
    from domain.llm_provider import call_llm
    
    prompt = EXTRACTION_PROMPT.format(ocr_text=ocr_text[:3000])  # limit 3000 chars
    
    try:
        result = call_llm(
            task_type="ocr_pdf",
            prompt=prompt,
            temperature=0.0,
            max_tokens=1000,
        )
        
        text = result.get("text", "").strip() if isinstance(result, dict) else str(result).strip()
        
        # Чистим markdown-обёртки
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()
        
        # Парсим JSON
        try:
            data = json.loads(text)
        except json.JSONDecodeError as je:
            logger.warning(f"LLM returned invalid JSON, falling back to regex: {je}, text: {text[:200]}")
            data = extract_with_regex(ocr_text)
            _cache_store(ocr_text, data, is_fallback=True)
            return True, data, f"json_fallback: {je}"
        
        if not isinstance(data, dict):
            return False, {}, f"LLM returned non-dict: {type(data)}"
        
        # Cache successful LLM result
        _cache_store(ocr_text, data, is_fallback=False)
        return True, data, ""
        
    except json.JSONDecodeError as e:
        logger.error(f"LLM returned invalid JSON: {e}, text: {text[:200]}")
        return False, {}, f"invalid JSON: {e} (raw: {text[:100]})"
    except Exception as e:
        logger.exception("LLM extraction failed")
        return False, {}, f"LLM error: {e}"


def cache_stats() -> Dict[str, Any]:
    """Статистика кеша (для monitoring / debugging)."""
    import sqlite3
    try:
        conn = sqlite3.connect(_get_db_path(), timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), SUM(hits_count), SUM(is_fallback) FROM llm_extraction_cache")
        total, total_hits, total_fallback = cur.fetchone()
        conn.close()
        return {
            "unique_entries": total or 0,
            "total_hits": total_hits or 0,
            "fallback_entries": total_fallback or 0,
        }
    except Exception as e:
        return {"error": str(e)}


def extract_with_regex(ocr_text: str) -> Dict[str, Any]:
    """Fallback: regex-парсинг для простых случаев (когда LLM недоступна)."""
    result = {
        "designation": None,
        "name": None,
        "level": "detail",
        "material": None,
        "gost": None,
        "dimensions": None,
        "mass_kg": None,
        "surface_treatment": None,
        "raw_components": [],
        "author": None,
        "drawing_date": None,
        "notes": None,
    }
    
    if not ocr_text:
        return result
    
    # Designation: pattern like XX-XX.XX.XXX or XX.XXXXX.XXX
    desig_match = re.search(r"\b(\d{2,3}[-.]?[А-Яа-я]{1,3}[-.]\d{2,3}[-.]\d{2,4}[-.]\d{2,3})\b", ocr_text)
    if desig_match:
        result["designation"] = desig_match.group(1).replace(" ", "")
    
    # ГОСТ
    gost_match = re.search(r"ГОСТ\s*(\d+[-.]?\d*[-.]?\d*)", ocr_text, re.IGNORECASE)
    if gost_match:
        result["gost"] = "ГОСТ " + gost_match.group(1)
    
    # Размеры: L=200мм или 200x100x50
    dim_match = re.search(r"[L=L]\s*=?\s*(\d+)\s*(мм|mm)?", ocr_text, re.IGNORECASE)
    if dim_match:
        result["dimensions"] = f"{dim_match.group(1)}мм"
    
    return result
