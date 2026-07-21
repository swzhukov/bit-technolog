"""
OCR чертежей Техинкома — извлечение текста для LLM.
Использует pdftoppm + tesseract (русский).
"""
import os, sys, subprocess, json, time
from pathlib import Path

ATTACH = Path('/workspace/attachments')
OUT = Path('/workspace/attachments/ocr_output')
OUT.mkdir(exist_ok=True)
TEMP = Path('/tmp/ocr_temp')
TEMP.mkdir(exist_ok=True)

pdfs = sorted(ATTACH.glob('*.pdf'))
print(f"Total PDFs: {len(pdfs)}")

results = {}
total_start = time.time()

for i, pdf in enumerate(pdfs, 1):
    print(f"\n[{i}/{len(pdfs)}] {pdf.name}")
    pdf_start = time.time()
    pdf_id = pdf.stem.split('__')[0]
    out_dir = TEMP / pdf_id
    out_dir.mkdir(exist_ok=True)

    # 1. pdftoppm → images
    subprocess.run([
        'pdftoppm', '-r', '300', '-gray',
        str(pdf), str(out_dir / 'page'),
        '-png'
    ], check=True, capture_output=True)

    pages = sorted(out_dir.glob('page-*.png'))
    print(f"  {len(pages)} pages converted in {time.time()-pdf_start:.1f}s")

    # 2. tesseract на каждую страницу
    page_texts = []
    for p in pages:
        result = subprocess.run([
            'tesseract', str(p), '-', '-l', 'rus+eng',
            '--psm', '6',  # assume a single uniform block of text
            '-c', 'preserve_interword_spaces=1',
        ], capture_output=True, text=True, timeout=180)
        page_texts.append(result.stdout.strip())

    full_text = '\n--- PAGE BREAK ---\n'.join(page_texts)

    # 3. Сохраняем
    out_file = OUT / f"{pdf_id}.txt"
    out_file.write_text(full_text, encoding='utf-8')

    elapsed = time.time() - pdf_start
    print(f"  OCR done in {elapsed:.1f}s, saved to {out_file}")
    print(f"  Text length: {len(full_text)} chars, {len(full_text.split())} words")

    results[pdf_id] = {
        'pdf': pdf.name,
        'pages': len(pages),
        'time_sec': round(elapsed, 1),
        'text_len': len(full_text),
    }

total_elapsed = time.time() - total_start
print(f"\n=== TOTAL: {total_elapsed:.1f}s for {len(pdfs)} PDFs ===")

# Сохраняем summary
with open(OUT / 'summary.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Summary: {OUT / 'summary.json'}")
