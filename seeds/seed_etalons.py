"""
seed_etalons.py — загрузить 2 реальных ТП Техинкома как эталоны.

PDF:
- /tmp/tp1_full.txt → ЛМША.301712.000 (Растяжка пружинная)
- /tmp/tp2_full.txt → ЛМША.301314.010 (Упор продольный)

После загрузки эталоны используются для RAG и few-shot.
"""
import json
import sys
from pathlib import Path

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from repositories import db
from services.tp_parser import parse_tp_text, validate_parsed_tp


PDF_TEXTS = [
    {
        "pdf_text_path": "/tmp/tp1_full.txt",
        "designation": "ЛМША.301712.000",
        "name": "Растяжка пружинная",
        "product_type": "АЦ",
        "source_doc": "/workspace/attachments/5c6e1e30__60905589-c0d4-402a-a939-46a4221d2183.pdf",
        "approved_by": "ВП 3237",  # Скрыто по запросу Сергея (для 50+ технолога)
        "approved_date": "2022-08-09",
        "is_published": 1,
    },
    {
        "pdf_text_path": "/tmp/tp2_full.txt",
        "designation": "ЛМША.301314.010",
        "name": "Упор продольный",
        "product_type": "АЦ",
        "source_doc": "/workspace/attachments/cd9db5eb__94afa317-7dfa-4367-b0f1-ddadb77e6b77.pdf",
        "approved_by": "ВП 3237",  # Скрыто по запросу Сергея
        "approved_date": "2022-07-12",
        "is_published": 1,
    },
]


def seed_etalons(verbose: bool = True) -> int:
    """Загрузить 2 PDF как эталоны. Возвращает количество загруженных."""
    db.init_db()

    loaded = 0
    for spec in PDF_TEXTS:
        text_path = Path(spec["pdf_text_path"])
        if not text_path.exists():
            print(f"⚠️  {text_path} не найден")
            continue

        text = text_path.read_text(encoding="utf-8")
        tp = parse_tp_text(text, source_doc=spec["source_doc"])

        # Принудительно ставим правильные данные (парсер мог ошибиться)
        tp.designation = spec["designation"]
        tp.name = spec["name"]
        tp.product_type = spec["product_type"]
        tp.approved_by = spec["approved_by"]
        tp.approved_date = spec["approved_date"]
        tp.source_doc = spec["source_doc"]
        tp.pages = 31 if "301712" in spec["designation"] else 41

        # Проверка
        issues = validate_parsed_tp(tp)
        if issues:
            if verbose:
                print(f"⚠️  {tp.designation}: {issues}")

        # Удалим старый эталон (если есть)
        db.execute("DELETE FROM etalons WHERE designation = ?", (tp.designation,))

        # Запишем новый
        etalon_id = db.insert_and_get_id("etalons", {
            "designation": tp.designation,
            "name": tp.name,
            "product_type": tp.product_type,
            "source_doc": tp.source_doc,
            "source_pages": tp.pages,
            "approved_by": tp.approved_by,
            "approved_date": tp.approved_date,
            "is_approved": 1,
            "is_published": spec["is_published"],
            "content_json": json.dumps(tp.to_dict(), ensure_ascii=False),
            "rag_indexed_at": None,  # будет проиндексирован в RAG
        })

        if verbose:
            print(f"✅ {tp.designation} «{tp.name}» — ID {etalon_id}, {len(tp.operations)} операций, {len(tp.materials)} материалов")

        loaded += 1

    return loaded


if __name__ == "__main__":
    n = seed_etalons()
    print(f"\nЗагружено эталонов: {n}")
