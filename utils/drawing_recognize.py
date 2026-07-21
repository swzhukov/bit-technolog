"""
Распознавание чертежей (PDF/DXF/PNG/JPG) через OCR.
Использует pdftoppm + tesseract (rus+eng).

Извлекает:
- Полный текст со всех страниц
- Обозначение детали (LMSHA.xxxxxx.xxx)
- Материал (сталь, алюминий, ...)
- Габариты (мм)
- Толщину (мм)
- Массу (кг)
- Заготовку (лист/труба/пруток/отливка/поковка)
"""
import os
import re
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("drawing_recognize")

# Зависимости для OCR
TESSERACT = "/usr/bin/tesseract"
PDFTOPPM = "/usr/bin/pdftoppm"

# Регулярные выражения для извлечения данных
# Обозначение детали: ЛМША.301314.010, 53-ТВ.05.00.00, etc.
RE_DESIGNATION = re.compile(
    r"\b(?:ЛМША|53[-\u00A0]?ТВ|CB|PC|PC\d)[\.\-]\d{4,6}(?:[\.\-]\d{2,4})?\b",
    re.IGNORECASE
)
# Материал: сталь, алюминий, бронза, латунь, ...
RE_MATERIAL = re.compile(
    r"\b(?:сталь|алюминий|бронза|латунь|медь|чугун|титан)"
    r"(?:\s*[а-яА-Яa-zA-Z0-9\-\d]{0,15})?",
    re.IGNORECASE
)
# Конкретные марки: Ст3, 09Г2С, АМг6, etc.
RE_MATERIAL_GRADE = re.compile(
    r"\b(?:Ст[3-9]|09Г2С|09Г2С[-\u2010\u2013]?\d+|[АA][МM][гГ]\d+|[A-Z]+\d+[A-Z]?)\b"
)
# Габариты: 100х50х20 или 100x50x20
RE_DIMENSIONS = re.compile(
    r"\b(\d{2,4})[хxX\*](\d{1,3})[хxX\*](\d{1,3})\s*(мм|mm)?\b"
)
# Толщина: s=2, толщ. 3, t=5
RE_THICKNESS = re.compile(
    r"(?:s\s*=\s*|толщ(?:ина)?\.?\s*|t\s*=\s*)\s*(\d+(?:[.,]\d+)?)\s*(мм|mm)?",
    re.IGNORECASE
)
# Масса: m=1.5, масса 2.3
RE_MASS = re.compile(
    r"(?:m\s*=\s*|масс[аы])\.?\s*(\d+(?:[.,]\d+)?)\s*(кг|kg)?",
    re.IGNORECASE
)
# Заготовка
RE_BLANK_TYPES = re.compile(
    r"\b(лист|труба|пруток|круг|квадрат|полоса|уголок|швеллер|двутавр|отливка|поковка|штампованная)\b",
    re.IGNORECASE
)


def _ocr_image(image_path: str, lang: str = "rus+eng") -> str:
    """OCR одного изображения."""
    try:
        result = subprocess.run(
            [TESSERACT, image_path, "-", "-l", lang,
             "--psm", "6", "-c", "preserve_interword_spaces=1"],
            capture_output=True, text=True, timeout=180
        )
        return result.stdout.strip()
    except Exception as e:
        log.warning(f"OCR failed for {image_path}: {e}")
        return ""


def _pdf_to_text(pdf_path: str, work_dir: str) -> List[Dict]:
    """PDF → список {page, text}."""
    # 1. Конвертируем PDF в PNG (300 dpi)
    prefix = os.path.join(work_dir, "page")
    subprocess.run(
        [PDFTOPPM, "-r", "300", "-gray", pdf_path, prefix, "-png"],
        check=True, capture_output=True, timeout=300
    )
    pages = sorted(Path(work_dir).glob("page-*.png"))
    if not pages:
        log.warning(f"No pages extracted from {pdf_path}")
        return []

    result = []
    for i, p in enumerate(pages, 1):
        text = _ocr_image(str(p))
        result.append({"page": i, "text": text})
        # Удаляем PNG после OCR (экономим место)
        try:
            p.unlink()
        except OSError:
            pass
    return result


def _image_to_text(image_path: str) -> List[Dict]:
    """Один PNG/JPG → [{page: 1, text}]."""
    text = _ocr_image(image_path)
    return [{"page": 1, "text": text}]


def recognize_drawing(file_path: str) -> Dict:
    """
    Распознаёт чертёж (PDF/PNG/JPG) и возвращает структурированный результат.

    Returns:
        {
            "file": filename,
            "format": "pdf"|"png"|"jpg",
            "pages": [{"page": 1, "text": "...", "char_count": N}, ...],
            "full_text": "...",
            "extracted": {
                "designation": "..."|None,
                "material": "сталь Ст3"|None,
                "material_grade": "Ст3"|None,
                "dimensions": "100x50x20"|None,
                "thickness_mm": 2.0|None,
                "mass_kg": 1.5|None,
                "blank_type": "лист"|None,
            },
            "confidence": 0-100,
            "warnings": ["..."]
        }
    """
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        return {"ok": False, "error": f"file not found: {file_path}"}

    suffix = Path(file_path).suffix.lower().lstrip(".")
    filename = os.path.basename(file_path)

    pages = []
    with tempfile.TemporaryDirectory() as work_dir:
        try:
            if suffix == "pdf":
                pages = _pdf_to_text(file_path, work_dir)
            elif suffix in ("png", "jpg", "jpeg"):
                pages = _image_to_text(file_path)
            else:
                return {"ok": False, "error": f"unsupported format: {suffix}"}
        except Exception as e:
            log.error(f"Recognition failed: {e}")
            return {"ok": False, "error": str(e)}

    full_text = "\n--- PAGE BREAK ---\n".join(p["text"] for p in pages)

    extracted = _extract_fields(full_text)
    confidence = _calc_confidence(extracted, len(full_text))
    warnings = _make_warnings(extracted, len(full_text))

    return {
        "ok": True,
        "file": filename,
        "format": suffix,
        "pages": [{"page": p["page"], "text": p["text"], "char_count": len(p["text"])} for p in pages],
        "full_text": full_text,
        "extracted": extracted,
        "confidence": confidence,
        "warnings": warnings,
    }


def _extract_fields(text: str) -> Dict:
    """Извлекает структурированные поля из текста чертежа."""
    if not text:
        return {}

    designation_match = RE_DESIGNATION.search(text)
    designation = designation_match.group(0).upper().replace("\u00A0", "").replace("\u2010", "-") if designation_match else None

    # Материал: ищем самую длинную фразу
    materials = RE_MATERIAL.findall(text)
    material_grade_match = RE_MATERIAL_GRADE.search(text)
    material = None
    if material_grade_match:
        material = material_grade_match.group(0)
    elif materials:
        # Берём первое вхождение + контекст
        idx = RE_MATERIAL.search(text)
        if idx:
            # Берём 30 символов после первого упоминания
            end = min(idx.end() + 20, len(text))
            material = text[idx.start():end].strip().split("\n")[0].strip()

    dimensions_match = RE_DIMENSIONS.search(text)
    dimensions = (
        f"{dimensions_match.group(1)}x{dimensions_match.group(2)}x{dimensions_match.group(3)}"
        if dimensions_match else None
    )

    thickness_match = RE_THICKNESS.search(text)
    thickness = None
    if thickness_match:
        try:
            thickness = float(thickness_match.group(1).replace(",", "."))
        except ValueError:
            pass

    mass_match = RE_MASS.search(text)
    mass = None
    if mass_match:
        try:
            mass = float(mass_match.group(1).replace(",", "."))
        except ValueError:
            pass

    blank_match = RE_BLANK_TYPES.search(text)
    blank_type = blank_match.group(0).lower() if blank_match else None

    return {
        "designation": designation,
        "material": material,
        "material_grade": material_grade_match.group(0) if material_grade_match else None,
        "dimensions": dimensions,
        "thickness_mm": thickness,
        "mass_kg": mass,
        "blank_type": blank_type,
    }


def _calc_confidence(extracted: Dict, text_len: int) -> int:
    """Оценка уверенности (0-100)."""
    if text_len < 50:
        return 0
    if text_len < 200:
        return 20

    score = 0
    weights = {
        "designation": 30, "material": 20, "material_grade": 10,
        "dimensions": 15, "thickness_mm": 10, "mass_kg": 10, "blank_type": 5,
    }
    for field, weight in weights.items():
        if extracted.get(field) is not None:
            score += weight
    return min(100, score)


def _make_warnings(extracted: Dict, text_len: int) -> List[str]:
    """Список предупреждений для технолога."""
    warnings = []
    if text_len < 100:
        warnings.append(f"Очень мало текста ({text_len} символов) — возможно плохое качество скана")
    if not extracted.get("designation"):
        warnings.append("Не удалось извлечь обозначение детали — проверьте основную надпись")
    if not extracted.get("material"):
        warnings.append("Не удалось определить материал — проверьте штамп")
    if not extracted.get("dimensions"):
        warnings.append("Не удалось извлечь габариты — проверьте размерные линии")
    return warnings
