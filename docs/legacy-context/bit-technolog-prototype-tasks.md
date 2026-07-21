# БИТ.Технолог — Задачи для MiniMax Code

> **Дата:** 2026-07-16
> **Назначение:** пошаговые задачи для MiniMax Code (или разработчика). Что делать, в каком порядке.
> **Контекст:** `bit-technolog-prototype-context.md`.

---

## ОБЩАЯ ЗАДАЧА

Создать **прототип** веб-приложения **БИТ.Технолог** — AI-помощник технолога для создания техкарт.

**Стек:** Python 3.11+, FastAPI, Jinja2, HTMX, SQLite, anthropic SDK, PicoCSS.

**Срок:** 1-2 недели.

**Что НЕ делаем:** Docker, PostgreSQL, 1С-интеграцию, Watcher КОМПАС, RAG, аутентификацию.

---

## ЗАДАЧА 1. Структура проекта

Создать директорию `bit-technolog-prototype/` со следующими файлами:

```
bit-technolog-prototype/
├── app.py                      # FastAPI (single file)
├── prompts.py                  # Промт v0.2 (из bit-technolog-prototype-prompt.txt)
├── mock_data.py                # 5-10 mock деталей
├── equipment.json              # Справочник оборудования (8 записей)
├── structure.json              # Структура предприятия (4 производства, 7 участков)
├── few_shot.py                 # Пример 4c85941a (упор продольный)
├── requirements.txt            # Зависимости
├── .env.example                # ANTHROPIC_API_KEY=...
├── README.md                   # Как запустить
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── detail.html
│   └── partials/
│       ├── summary.html
│       ├── route.html
│       ├── operations.html
│       ├── reasoning.html
│       ├── warnings.html
│       └── questions.html
└── static/
    ├── style.css               # PicoCSS
    └── htmx.min.js
```

---

## ЗАДАЧА 2. requirements.txt

```txt
fastapi==0.110.0
uvicorn[standard]==0.27.0
jinja2==3.1.2
python-multipart==0.0.9
python-dotenv==1.0.0
anthropic==0.20.0
openpyxl==3.1.2
reportlab==4.0.7
```

**Установка:** `pip install -r requirements.txt`

---

## ЗАДАЧА 3. equipment.json

8 записей оборудования (из контекста):

```json
[
  {
    "name": "Кедр-300",
    "type": "Сварочный аппарат",
    "group": "Сварка",
    "operations": ["MIG сварка", "MAG сварка", "механизированная сварка"],
    "max_dim_mm": null,
    "department": "Сварочно-сборочный КТ",
    "workplace": "01/01/04",
    "code": 19905,
    "rank": 4
  },
  {
    "name": "Токарный 16К20",
    "type": "Токарный станок",
    "group": "Токарные",
    "operations": ["точение", "сверление", "нарезание резьбы"],
    "max_dim_mm": 400,
    "department": "Механообработка",
    "workplace": null,
    "code": null,
    "rank": null
  },
  ...
]
```

Полный список в `bit-technolog-prototype-data.json`.

---

## ЗАДАЧА 4. structure.json

```json
{
  "productions": [
    {
      "name": "Участок обработки металла (Заготовительное производство)",
      "workshops": [
        {"code": "01", "name": "Уч-к лазерной резки"},
        {"code": "01", "name": "Уч-к механической резки (гильотина)"},
        {"code": "01", "name": "Уч-к гибки"},
        {"code": "01", "name": "Уч-к механообработки"}
      ]
    },
    {
      "name": "Мелкосерийное производство",
      "workshops": [
        {"code": "01", "name": "Уч-к изготовления упоров"},
        {"code": "01", "name": "Уч-к изготовления растяжек"},
        {"code": "01", "name": "Уч-к комплектования и упаковки"}
      ]
    },
    {
      "name": "Производство высотной техники (ПСС)",
      "workshops": [
        {"code": "01", "name": "Сварочно-сборочный уч-к ВТ"},
        {"code": "01", "name": "Сборочный уч-к ВТ"}
      ]
    },
    {
      "name": "Производство кузовной техники (АЦ)",
      "workshops": [
        {"code": "01", "name": "Сварочно-сборочный уч-к КТ"},
        {"code": "01", "name": "Сборочный уч-к КТ"}
      ]
    }
  ]
}
```

---

## ЗАДАЧА 5. mock_data.py

5-10 mock-деталей. Пример:

```python
MOCK_DETAILS = [
    {
        "id": "detail-001",
        "name": "Кронштейн крепления насоса",
        "designation": "КРН-001-АЦ6",
        "material": "Сталь 09Г2С",
        "gost_material": "ГОСТ 19903-2015",
        "mass_kg": 12.5,
        "dimensions_mm": {"x": 250, "y": 180, "z": 80},
        "surface_treatment": "покраска",
        "chassis": "КАМАЗ 43118",
        "model": "АЦ-6-40",
        "status": "new",  # new, draft, approved, in_production
        "created_at": "2026-07-15T10:00:00",
        "file_hash": "sha256:abc123...",
        "file_path": "/mock/konstruktor1/KRN-001-AC6.m3d"
    },
    {
        "id": "detail-002",
        "name": "Рама боковая",
        "designation": "РБ-12-АЦ6",
        "material": "Сталь 09Г2С",
        "gost_material": "ГОСТ 19903-2015",
        "mass_kg": 28.3,
        "dimensions_mm": {"x": 800, "y": 400, "z": 50},
        "surface_treatment": "покраска",
        "chassis": "КАМАЗ 43118",
        "model": "АЦ-6-40",
        "status": "new",
        "created_at": "2026-07-15T10:00:00",
        "file_hash": "sha256:def456...",
        "file_path": "/mock/konstruktor1/RB-12-AC6.m3d"
    },
    {
        "id": "detail-003",
        "name": "Крышка люка",
        "designation": "КЛ-08-АЦ6",
        "material": "Сталь 3",
        "gost_material": "ГОСТ 16523-97",
        "mass_kg": 4.2,
        "dimensions_mm": {"x": 300, "y": 300, "z": 20},
        "surface_treatment": "оцинковка",
        "chassis": "КАМАЗ 43118",
        "model": "АЦ-6-40",
        "status": "new",
        "created_at": "2026-07-15T10:00:00",
        "file_hash": "sha256:ghi789...",
        "file_path": "/mock/konstruktor1/KL-08-AC6.m3d"
    },
    {
        "id": "detail-004",
        "name": "Обтекатель",
        "designation": "ОБ-22-АЦ6",
        "material": "Стекло-пластик",
        "gost_material": null,
        "mass_kg": 6.0,
        "dimensions_mm": {"x": 600, "y": 400, "z": 200},
        "surface_treatment": "покраска",
        "chassis": "КАМАЗ 43118",
        "model": "АЦ-6-40",
        "status": "approved",
        "created_at": "2026-07-10T08:00:00",
        "file_hash": "sha256:jkl012...",
        "file_path": "/mock/konstruktor2/OB-22-AC6.m3d"
    },
    {
        "id": "detail-005",
        "name": "Стрела 22м (нижнее колено)",
        "designation": "СТР-22-НК-ПСС18",
        "material": "Сталь 09Г2С",
        "gost_material": "ГОСТ 19903-2015",
        "mass_kg": 180.0,
        "dimensions_mm": {"x": 5500, "y": 350, "z": 350},
        "surface_treatment": "покраска",
        "chassis": "ГАЗ-C41R13",
        "model": "ПСС-131.18Э",
        "status": "new",
        "created_at": "2026-07-15T10:00:00",
        "file_hash": "sha256:mno345...",
        "file_path": "/mock/konstruktor3/STR-22-NK.m3d"
    },
    {
        "id": "detail-006",
        "name": "Аутригер (выносная опора)",
        "designation": "АУТ-01-ПСС18",
        "material": "Сталь 09Г2С",
        "gost_material": "ГОСТ 19903-2015",
        "mass_kg": 45.0,
        "dimensions_mm": {"x": 1500, "y": 200, "z": 200},
        "surface_treatment": "покраска",
        "chassis": "ГАЗ-C41R13",
        "model": "ПСС-131.18Э",
        "status": "new",
        "created_at": "2026-07-15T10:00:00",
        "file_hash": "sha256:pqr678...",
        "file_path": "/mock/konstruktor3/AUT-01.m3d"
    },
    {
        "id": "detail-007",
        "name": "Бампер с ящиками",
        "designation": "БМР-02-ПСС22",
        "material": "Сталь 09Г2С",
        "gost_material": "ГОСТ 19903-2015",
        "mass_kg": 65.0,
        "dimensions_mm": {"x": 2200, "y": 350, "z": 400},
        "surface_treatment": "покраска",
        "chassis": "ГАЗ-C42R33",
        "model": "ПСС-131.22Э",
        "status": "new",
        "created_at": "2026-07-15T10:00:00",
        "file_hash": "sha256:stu901...",
        "file_path": "/mock/konstruktor4/BMR-02.m3d"
    },
    {
        "id": "detail-008",
        "name": "Колено стрелы (верхнее)",
        "designation": "КС-22-ВК-ПСС18",
        "material": "Сталь 09Г2С",
        "gost_material": "ГОСТ 19903-2015",
        "mass_kg": 95.0,
        "dimensions_mm": {"x": 2800, "y": 350, "z": 350},
        "surface_treatment": "покраска",
        "chassis": "ГАЗ-C41R13",
        "model": "ПСС-131.18Э",
        "status": "draft",
        "created_at": "2026-07-12T14:00:00",
        "file_hash": "sha256:vwx234...",
        "file_path": "/mock/konstruktor3/KS-22-VK.m3d"
    },
    {
        "id": "detail-009",
        "name": "Продольный упор",
        "designation": "ЛМША.301314.010",
        "material": "Сталь 3",
        "gost_material": "ГОСТ 16523-97",
        "mass_kg": 8.5,
        "dimensions_mm": {"x": 600, "y": 100, "z": 50},
        "surface_treatment": "оцинковка",
        "chassis": "various",
        "model": "УМК",
        "status": "new",
        "created_at": "2026-07-15T10:00:00",
        "file_hash": "sha256:yza567...",
        "file_path": "/mock/konstruktor1/LMSHA-301314-010.m3d"
    },
    {
        "id": "detail-010",
        "name": "Пластина",
        "designation": "ПЛ-001-МТБ7",
        "material": "Сталь 09Г2С",
        "gost_material": "ГОСТ 19903-2015",
        "mass_kg": 0.48,
        "dimensions_mm": {"x": 200, "y": 100, "z": 3},
        "surface_treatment": "покраска",
        "chassis": "ГАЗ-C41R13",
        "model": "МТБ-7",
        "status": "new",
        "created_at": "2026-07-15T10:00:00",
        "file_hash": "sha256:bcd890...",
        "file_path": "/mock/konstruktor4/PL-001.m3d"
    }
]
```

---

## ЗАДАЧА 6. few_shot.py

```python
FEW_SHOT_4C85941A = {
    "input": {
        "properties": {
            "name": "Упор продольный",
            "designation": "ЛМША.301314.010",
            "material": "Сталь 3",
            "gost_material": "ГОСТ 16523-97",
            "mass_kg": 8.5,
            "dimensions_mm": {"x": 600, "y": 100, "z": 50},
            "surface_treatment": "оцинковка",
            "chassis": "various"
        }
    },
    "output": {
        "summary": {
            "total_operations": 7,
            "total_hours": 4.2,
            "prep_hours": 0.5,
            "complexity": "средняя",
            "closest_analog": null
        },
        "route": [
            {"step": 1, "operation": "010 Подготовительная", "duration_hours": 0.2},
            {"step": 2, "operation": "015 Установка ножей", "duration_hours": 0.5},
            {"step": 3, "operation": "020 Приварка ножей к основанию", "duration_hours": 0.6},
            {"step": 4, "operation": "025 Установка рёбер", "duration_hours": 0.7},
            {"step": 5, "operation": "030 Приварка рёбер", "duration_hours": 0.6},
            {"step": 6, "operation": "035 Установка настила, уголков, планок", "duration_hours": 0.8},
            {"step": 7, "operation": "040 Сварка", "duration_hours": 0.8}
        ],
        "operations": [
            {
                "name": "010 Подготовительная",
                "equipment": null,
                "duration_hours": 0.2,
                "duration_source": "экспертная оценка",
                "confidence": 75,
                "materials": ["проволока Св-08Г2С-О 1,0 ГОСТ 2246-70", "смесь газовая М21 ГОСТ Р ИСО 14175-2010"],
                "control_points": [],
                "gosts": []
            },
            {
                "name": "015 Установка ножей (сборка под сварку)",
                "equipment": "Кедр-300",
                "duration_hours": 0.5,
                "duration_source": "аналог: ЛМША.301314.020",
                "confidence": 92,
                "materials": [],
                "control_points": ["ОТК визуальный"],
                "gosts": ["ГОСТ 3.1404-86"]
            },
            {
                "name": "020 Приварка ножей к основанию",
                "equipment": "Кедр-300",
                "duration_hours": 0.6,
                "duration_source": "аналог: ЛМША.301314.020",
                "confidence": 92,
                "materials": [],
                "control_points": ["ОТК визуальный", "ОТК измерительный"],
                "gosts": ["ГОСТ 3.1404-86"]
            },
            {
                "name": "025 Установка рёбер и приварка пластин",
                "equipment": "Кедр-300",
                "duration_hours": 0.7,
                "duration_source": "аналог: ЛМША.301314.020",
                "confidence": 85,
                "materials": ["пластина ЛМША.301714.006"],
                "control_points": ["ОТК визуальный"],
                "gosts": ["ГОСТ 3.1404-86"]
            },
            {
                "name": "030 Приварка рёбер к основанию",
                "equipment": "Кедр-300",
                "duration_hours": 0.6,
                "duration_source": "аналог: ЛМША.301314.020",
                "confidence": 85,
                "materials": [],
                "control_points": ["ОТК визуальный"],
                "gosts": ["ГОСТ 3.1404-86"]
            },
            {
                "name": "035 Установка настила, уголков, планок",
                "equipment": "Кедр-300",
                "duration_hours": 0.8,
                "duration_source": "аналог: ЛМША.301314.020",
                "confidence": 80,
                "materials": ["уголок", "планка", "пруток"],
                "control_points": ["ОТК визуальный", "ОТК измерительный"],
                "gosts": ["ГОСТ 3.1404-86"]
            },
            {
                "name": "040 Сварка",
                "equipment": "Кедр-300",
                "duration_hours": 0.8,
                "duration_source": "аналог: ЛМША.301314.020",
                "confidence": 85,
                "materials": [],
                "control_points": ["ОТК визуальный", "ОТК измерительный", "испытания"],
                "gosts": ["ГОСТ 3.1404-86", "ГОСТ 3.1703-79"]
            }
        ],
        "reasoning": {
            "operations_choice": "Операции 015-040 выбраны на основе аналога ЛМША.301314.020 (упор продольный, ближайший аналог). Все сварочные операции выполняются на аппарате Кедр-300 (единственное оборудование для сварки в цехе).",
            "duration_estimates": "Время операций рассчитано по аналогу 020. Коэффициент 1.0 (аналог с тем же материалом и габаритами).",
            "equipment_choice": "Кедр-300 — единственный аппарат механизированной сварки в сварочно-сборочном цехе КТ.",
            "risks": "Операции 025 и 035 имеют пониженную уверенность (80-85%) из-за различий в форме ножей. Требуется проверка технолога."
        },
        "warnings": [
            {
                "type": "missing_data",
                "quote": "surface_treatment: 'оцинковка'",
                "concern": "Не указана толщина цинкового покрытия (обычно 10-25 мкм)",
                "question": "Какая требуется толщина цинкового покрытия? 10, 15, 20 или 25 мкм?"
            },
            {
                "type": "ambiguous",
                "quote": "material: 'Сталь 3'",
                "concern": "Сталь 3 — устаревшее обозначение. Возможно, Ст3сп, Ст3пс, Ст3кп?",
                "question": "Какая марка стали точно? Ст3сп, Ст3пс или Ст3кп?"
            }
        ],
        "questions": [
            {
                "id": "Q1",
                "topic": "оцинковка",
                "question": "Толщина цинкового покрытия?",
                "options": ["10 мкм", "15 мкм", "20 мкм", "25 мкм", "не знаю"],
                "default": "15 мкм",
                "impact_if_changed": "Не влияет на время операций, но влияет на материальные затраты"
            },
            {
                "id": "Q2",
                "topic": "материал",
                "question": "Марка стали (Ст3сп, Ст3пс или Ст3кп)?",
                "options": ["Ст3сп", "Ст3пс", "Ст3кп", "не знаю"],
                "default": "Ст3сп",
                "impact_if_changed": "Может изменить трудоёмкость обработки на ±5-10%"
            }
        ]
    }
}
```

---

## ЗАДАЧА 7. app.py (FastAPI)

Single file. Структура:

```python
# app.py
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import anthropic
from dotenv import load_dotenv
import sqlite3
import io

from prompts import TECH_CARD_PROMPT
from mock_data import MOCK_DETAILS
from equipment import EQUIPMENT
from structure import STRUCTURE
from few_shot import FEW_SHOT_4C85941A

# Load env
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# FastAPI app
app = FastAPI(title="БИТ.Технолог — Прототип")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# SQLite for drafts and history
DB_PATH = "bit_technolog.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS drafts (
            detail_id TEXT PRIMARY KEY,
            llm_output JSON,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            human_edits JSON
        );
        
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            detail_id TEXT,
            action TEXT,
            user TEXT DEFAULT 'technolog',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details JSON
        );
    """)
    conn.close()

init_db()

# Pydantic models
class GenerateRequest(BaseModel):
    detail_id: str
    answers: Optional[dict] = None

class ActionRequest(BaseModel):
    detail_id: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "details": MOCK_DETAILS
    })

@app.get("/detail/{detail_id}", response_class=HTMLResponse)
async def detail(request: Request, detail_id: str):
    detail_obj = next((d for d in MOCK_DETAILS if d["id"] == detail_id), None)
    if not detail_obj:
        raise HTTPException(404, "Detail not found")
    
    # Get draft from DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT llm_output, status FROM drafts WHERE detail_id = ?",
        (detail_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    draft = None
    if row:
        draft = json.loads(row[0]) if row[0] else None
    
    return templates.TemplateResponse("detail.html", {
        "request": request,
        "detail": detail_obj,
        "draft": draft,
        "status": row[1] if row else "new"
    })

@app.post("/api/generate")
async def generate(req: GenerateRequest):
    """Генерирует черновик ТК через Claude"""
    detail_obj = next((d for d in MOCK_DETAILS if d["id"] == req.detail_id), None)
    if not detail_obj:
        raise HTTPException(404, "Detail not found")
    
    # Prepare prompt
    prompt = TECH_CARD_PROMPT.format(
        properties_json=json.dumps(detail_obj, indent=2, ensure_ascii=False),
        equipment_json=json.dumps(EQUIPMENT, indent=2, ensure_ascii=False),
        structure_json=json.dumps(STRUCTURE, indent=2, ensure_ascii=False),
        few_shot_json=json.dumps(FEW_SHOT_4C85941A, indent=2, ensure_ascii=False)
    )
    
    # Add answers context if provided
    if req.answers:
        prompt += f"\n\n# ОТВЕТЫ ТЕХНОЛОГА НА ВОПРОСЫ\n{json.dumps(req.answers, indent=2, ensure_ascii=False)}\n"
    
    # Call Claude
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        llm_output_text = message.content[0].text
        llm_output = json.loads(llm_output_text)
    except Exception as e:
        raise HTTPException(500, f"LLM error: {str(e)}")
    
    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT OR REPLACE INTO drafts (detail_id, llm_output, status, created_at, updated_at)
           VALUES (?, ?, 'draft', ?, ?)""",
        (req.detail_id, json.dumps(llm_output, ensure_ascii=False),
         datetime.now().isoformat(), datetime.now().isoformat())
    )
    conn.execute(
        "INSERT INTO history (detail_id, action, details) VALUES (?, ?, ?)",
        (req.detail_id, "generated", json.dumps({"model": "claude-sonnet-4-5", "tokens": message.usage.input_tokens + message.usage.output_tokens}))
    )
    conn.commit()
    conn.close()
    
    return llm_output

@app.post("/api/approve")
async def approve(req: ActionRequest):
    """Утвердить черновик"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE drafts SET status = 'approved', updated_at = ? WHERE detail_id = ?",
        (datetime.now().isoformat(), req.detail_id)
    )
    conn.execute(
        "INSERT INTO history (detail_id, action) VALUES (?, 'approved')",
        (req.detail_id,)
    )
    conn.commit()
    conn.close()
    return {"status": "approved"}

@app.post("/api/send-to-1c")
async def send_to_1c(req: ActionRequest):
    """MOCK: записать РС в 1С"""
    # В реальной версии — вызов 1С Connector
    # Для прототипа — просто логируем
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO history (detail_id, action, details) VALUES (?, ?, ?)",
        (req.detail_id, "sent_to_1c_mock", json.dumps({"message": "РС записана в 1С:ERP (mock)"}))
    )
    conn.commit()
    conn.close()
    
    return {"status": "sent", "message": "РС записана в 1С:ERP (mock)"}

@app.post("/api/export/excel")
async def export_excel(req: ActionRequest):
    """Экспорт в Excel"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    
    detail_obj = next((d for d in MOCK_DETAILS if d["id"] == req.detail_id), None)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT llm_output FROM drafts WHERE detail_id = ?", (req.detail_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(400, "No draft to export")
    
    draft = json.loads(row[0])
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Техкарта"
    
    # Header
    ws["A1"] = f"Техкарта: {detail_obj['designation']} — {detail_obj['name']}"
    ws["A1"].font = Font(bold=True, size=14)
    ws.merge_cells("A1:E1")
    
    ws["A3"] = "Материал"
    ws["B3"] = detail_obj.get("material", "")
    ws["A4"] = "Масса, кг"
    ws["B4"] = detail_obj.get("mass_kg", "")
    ws["A5"] = "Шасси"
    ws["B5"] = detail_obj.get("chassis", "")
    
    # Operations
    ws["A7"] = "№"
    ws["B7"] = "Операция"
    ws["C7"] = "Оборудование"
    ws["D7"] = "Время, ч"
    ws["E7"] = "Источник"
    for cell in ws[7]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    
    for i, op in enumerate(draft.get("operations", []), 1):
        ws.cell(row=7+i, column=1, value=i)
        ws.cell(row=7+i, column=2, value=op.get("name", ""))
        ws.cell(row=7+i, column=3, value=op.get("equipment", ""))
        ws.cell(row=7+i, column=4, value=op.get("duration_hours", 0))
        ws.cell(row=7+i, column=5, value=op.get("duration_source", ""))
    
    # Save
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={detail_obj['designation']}.xlsx"}
    )

@app.post("/api/export/pdf")
async def export_pdf(req: ActionRequest):
    """Экспорт в PDF (для руководства)"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    detail_obj = next((d for d in MOCK_DETAILS if d["id"] == req.detail_id), None)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT llm_output FROM drafts WHERE detail_id = ?", (req.detail_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(400, "No draft to export")
    
    draft = json.loads(row[0])
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, 28*cm, f"Обоснование: {detail_obj['designation']} — {detail_obj['name']}")
    
    # Reasoning
    c.setFont("Helvetica", 10)
    y = 25*cm
    reasoning = draft.get("reasoning", {})
    for key, value in reasoning.items():
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, y, f"{key}:")
        y -= 0.5*cm
        c.setFont("Helvetica", 10)
        # Wrap text
        for line in wrap_text(value, 90):
            c.drawString(2*cm, y, line)
            y -= 0.5*cm
        y -= 0.3*cm
    
    c.save()
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={detail_obj['designation']}_reasoning.pdf"}
    )

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current += " " + word if current else word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

## ЗАДАЧА 8. templates/base.html

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>БИТ.Технолог — Прототип</title>
    <link rel="stylesheet" href="/static/style.css">
    <script src="/static/htmx.min.js"></script>
</head>
<body>
    <header>
        <nav>
            <a href="/" class="brand">🔧 БИТ.Технолог</a>
            <span class="tag">Прототип v0.1</span>
        </nav>
    </header>
    <main>
        {% block content %}{% endblock %}
    </main>
    <footer>
        <small>ООО «ПК Техинком-Центр» · БИТ.Технолог · 2026</small>
    </footer>
</body>
</html>
```

---

## ЗАДАЧА 9. templates/index.html

```html
{% extends "base.html" %}
{% block content %}
<h1>Детали от конструкторов</h1>

<table>
    <thead>
        <tr>
            <th>Статус</th>
            <th>Деталь</th>
            <th>Модель</th>
            <th>Шасси</th>
            <th>Масса</th>
            <th>Действие</th>
        </tr>
    </thead>
    <tbody>
        {% for d in details %}
        <tr>
            <td>
                {% if d.status == "new" %}🔴
                {% elif d.status == "draft" %}🟡
                {% elif d.status == "approved" %}🟢
                {% else %}⚪{% endif %}
            </td>
            <td>
                <a href="/detail/{{ d.id }}">{{ d.designation }}</a><br>
                <small>{{ d.name }}</small>
            </td>
            <td>{{ d.model }}</td>
            <td>{{ d.chassis }}</td>
            <td>{{ d.mass_kg }} кг</td>
            <td>
                <a href="/detail/{{ d.id }}" class="btn">Открыть</a>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

---

## ЗАДАЧА 10. templates/detail.html

```html
{% extends "base.html" %}
{% block content %}
<div class="breadcrumb">
    <a href="/">← К списку</a>
</div>

<h1>{{ detail.designation }} — {{ detail.name }}</h1>
<p>
    {% if status == "new" %}<span class="badge red">Новый</span>
    {% elif status == "draft" %}<span class="badge yellow">Черновик</span>
    {% elif status == "approved" %}<span class="badge green">Утверждён</span>
    {% endif %}
    · {{ detail.model }} · {{ detail.chassis }} · {{ detail.mass_kg }} кг
</p>

{% if not draft %}
<div class="action-bar">
    <form hx-post="/api/generate" hx-vals='{"detail_id": "{{ detail.id }}"}' hx-ext="json-enc">
        <button type="button" 
                hx-post="/api/generate" 
                hx-vals='{"detail_id": "{{ detail.id }}"}'
                hx-target="#draft-content"
                hx-swap="innerHTML"
                hx-indicator="#loading"
                class="btn primary">
            🤖 Сгенерировать черновик
        </button>
    </form>
    <span id="loading" class="htmx-indicator">⏳ Генерация (≤ 30 сек)...</span>
</div>
{% else %}
<div class="action-bar">
    <button hx-post="/api/approve" 
            hx-vals='{"detail_id": "{{ detail.id }}"}'
            hx-confirm="Утвердить черновик?"
            hx-target="body"
            hx-swap="none"
            class="btn primary">
        ✅ Утвердить
    </button>
    <button hx-post="/api/send-to-1c" 
            hx-vals='{"detail_id": "{{ detail.id }}"}'
            hx-confirm="Записать РС в 1С:ERP?"
            hx-target="#action-result"
            class="btn">
        📤 Записать в 1С
    </button>
    <form action="/api/export/excel" method="post" style="display:inline">
        <input type="hidden" name="detail_id" value="{{ detail.id }}">
        <button type="submit" class="btn">📊 Excel</button>
    </form>
    <form action="/api/export/pdf" method="post" style="display:inline">
        <input type="hidden" name="detail_id" value="{{ detail.id }}">
        <button type="submit" class="btn">📄 PDF</button>
    </form>
    <div id="action-result"></div>
</div>
{% endif %}

<div id="draft-content">
    {% if draft %}
    <div class="tabs">
        <button class="tab active" data-tab="summary">Сводка</button>
        <button class="tab" data-tab="route">Маршрут</button>
        <button class="tab" data-tab="operations">Операции</button>
        <button class="tab" data-tab="reasoning">Обоснование</button>
        <button class="tab" data-tab="warnings">Warnings</button>
        <button class="tab" data-tab="questions">Вопросы</button>
    </div>
    
    <div class="tab-content" id="tab-summary">
        <h2>Сводка</h2>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{{ draft.summary.total_operations }}</div>
                <div class="metric-label">операций</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ draft.summary.total_hours }}</div>
                <div class="metric-label">часов общее</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ draft.summary.prep_hours }}</div>
                <div class="metric-label">часов подг.</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ draft.summary.complexity }}</div>
                <div class="metric-label">сложность</div>
            </div>
        </div>
        
        <h3>Операции</h3>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Операция</th>
                    <th>Время</th>
                    <th>Уверенность</th>
                </tr>
            </thead>
            <tbody>
                {% for op in draft.operations %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ op.name }}</td>
                    <td>{{ op.duration_hours }} ч</td>
                    <td>
                        {% if op.confidence >= 80 %}🟢
                        {% elif op.confidence >= 60 %}🟡
                        {% else %}🔴{% endif %}
                        {{ op.confidence }}%
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div class="tab-content" id="tab-route" style="display:none">
        <h2>Маршрут</h2>
        <div class="route-flow">
            {% for step in draft.route %}
            <div class="route-step">
                <div class="step-num">{{ step.step }}</div>
                <div class="step-name">{{ step.operation }}</div>
                <div class="step-time">{{ step.duration_hours }} ч</div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <div class="tab-content" id="tab-operations" style="display:none">
        <h2>Операции</h2>
        {% for op in draft.operations %}
        <div class="op-card">
            <h3>{{ op.name }}</h3>
            <p><strong>Оборудование:</strong> {{ op.equipment or "—" }}</p>
            <p><strong>Время:</strong> {{ op.duration_hours }} ч</p>
            <p><strong>Источник:</strong> {{ op.duration_source }}</p>
            <p><strong>Уверенность:</strong> {{ op.confidence }}%</p>
            {% if op.materials %}
            <p><strong>Материалы:</strong> {{ op.materials | join(", ") }}</p>
            {% endif %}
            {% if op.control_points %}
            <p><strong>Контроль:</strong> {{ op.control_points | join(", ") }}</p>
            {% endif %}
            {% if op.gosts %}
            <p><strong>ГОСТы:</strong> {{ op.gosts | join(", ") }}</p>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    
    <div class="tab-content" id="tab-reasoning" style="display:none">
        <h2>Обоснование</h2>
        {% for key, value in draft.reasoning.items() %}
        <h3>{{ key }}</h3>
        <p>{{ value }}</p>
        {% endfor %}
    </div>
    
    <div class="tab-content" id="tab-warnings" style="display:none">
        <h2>Warnings</h2>
        {% if draft.warnings %}
            {% for w in draft.warnings %}
            <div class="warning-card">
                <div class="warning-type">{{ w.type }}</div>
                <div class="warning-quote">«{{ w.quote }}»</div>
                <div class="warning-concern">{{ w.concern }}</div>
                <div class="warning-question"><strong>Вопрос:</strong> {{ w.question }}</div>
            </div>
            {% endfor %}
        {% else %}
            <p>Нет warnings</p>
        {% endif %}
    </div>
    
    <div class="tab-content" id="tab-questions" style="display:none">
        <h2>Вопросы к технологу</h2>
        {% if draft.questions %}
            {% for q in draft.questions %}
            <div class="question-card">
                <div class="question-id">{{ q.id }}: {{ q.topic }}</div>
                <div class="question-text">{{ q.question }}</div>
                <div class="question-options">
                    {% for opt in q.options %}
                    <label>
                        <input type="radio" name="{{ q.id }}" value="{{ opt }}"> {{ opt }}
                    </label>
                    {% endfor %}
                </div>
                <div class="question-default"><em>По умолчанию: {{ q.default }}</em></div>
                <div class="question-impact">{{ q.impact_if_changed }}</div>
            </div>
            {% endfor %}
        {% else %}
            <p>Нет вопросов</p>
        {% endif %}
    </div>
    {% endif %}
</div>

<script>
// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
        tab.classList.add('active');
        document.getElementById('tab-' + target).style.display = 'block';
    });
});
</script>
{% endblock %}
```

---

## ЗАДАЧА 11. static/style.css (PicoCSS inline)

```css
:root {
    --primary: #1095c1;
    --green: #22c55e;
    --yellow: #eab308;
    --red: #ef4444;
}

body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }

nav { display: flex; align-items: center; gap: 16px; padding-bottom: 16px; border-bottom: 1px solid #eee; }
nav .brand { font-size: 20px; font-weight: bold; color: var(--primary); text-decoration: none; }
nav .tag { background: #f0f9ff; color: var(--primary); padding: 4px 8px; border-radius: 4px; font-size: 12px; }

table { width: 100%; border-collapse: collapse; margin-top: 16px; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }
th { background: #f9fafb; font-weight: 600; }

.btn { background: #fff; border: 1px solid #d1d5db; padding: 6px 12px; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
.btn:hover { background: #f9fafb; }
.btn.primary { background: var(--primary); color: white; border-color: var(--primary); }

.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.badge.red { background: #fef2f2; color: var(--red); }
.badge.yellow { background: #fefce8; color: var(--yellow); }
.badge.green { background: #f0fdf4; color: var(--green); }

.tabs { display: flex; gap: 4px; border-bottom: 2px solid #e5e7eb; margin-top: 24px; }
.tab { background: none; border: none; padding: 8px 16px; cursor: pointer; font-size: 14px; }
.tab.active { border-bottom: 2px solid var(--primary); color: var(--primary); font-weight: 600; }

.metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 16px 0; }
.metric { background: #f9fafb; padding: 16px; border-radius: 8px; text-align: center; }
.metric-value { font-size: 24px; font-weight: bold; color: var(--primary); }
.metric-label { font-size: 12px; color: #6b7280; margin-top: 4px; }

.op-card, .warning-card, .question-card { background: #f9fafb; padding: 16px; border-radius: 8px; margin: 12px 0; }
.warning-card { background: #fef2f2; }
.question-card { background: #fefce8; }

.htmx-indicator { display: none; color: var(--primary); margin-left: 12px; }
.htmx-request .htmx-indicator { display: inline; }
.htmx-request.htmx-indicator { display: inline; }
```

---

## ЗАДАЧА 12. README.md

```markdown
# БИТ.Технолог — Прототип

AI-помощник технолога для ускорения создания техкарт.

## Что это

Прототип веб-приложения, которое:
- Принимает свойства детали (от конструктора из КОМПАС-3D)
- Генерирует черновик техкарты через Claude Sonnet
- Позволяет технологу править, утверждать, экспортировать
- Демонстрирует, как будет выглядеть продукт

## Как запустить

1. Получите API-ключ Anthropic: https://console.anthropic.com/
2. Скопируйте `.env.example` в `.env` и вставьте ключ
3. Установите зависимости: `pip install -r requirements.txt`
4. Запустите: `python app.py`
5. Откройте http://localhost:8080

## Что можно делать

- Открыть список из 10 mock-деталей
- Кликнуть на любую → увидеть карточку
- Нажать "Сгенерировать черновик" → AI сгенерирует ТК за ≤ 30 сек
- Перейти по 6 вкладкам: Сводка / Маршрут / Операции / Обоснование / Warnings / Вопросы
- Утвердить черновик
- Экспортировать в Excel или PDF

## Что НЕ работает (mock)

- Запись в 1С:ERP (кнопка есть, но это mock)
- Реальный Watcher КОМПАС-3D (детали захардкожены)
- Аутентификация (нет)
- Docker (не нужен)

## Стек

Python 3.11+, FastAPI, Jinja2, HTMX, SQLite, anthropic SDK, PicoCSS.

## Стоимость

~2.7 ₽ за генерацию. 10 тестовых деталей = ~27 ₽.

## Контакты

Сергей Жуков, Первый БИТ.
```

---

## КРИТЕРИИ ПРИЁМКИ ПРОТОТИПА

- [ ] `python app.py` запускает сервер на http://localhost:8080
- [ ] Главная страница показывает 10 mock-деталей
- [ ] Клик на деталь → карточка с 6 вкладками
- [ ] Кнопка "Сгенерировать черновик" → вызов LLM → JSON за ≤ 30 сек
- [ ] Все 7 операций из 4c85941a корректно отображаются
- [ ] Warnings с цитатами
- [ ] Вопросы с вариантами
- [ ] Кнопка "Утвердить" → статус 🟢
- [ ] Кнопка "Экспорт в Excel" → скачивается .xlsx
- [ ] Кнопка "Экспорт в PDF" → скачивается .pdf
- [ ] Бюджет на 10 генераций ≤ 30 ₽
- [ ] README понятен

---

**Версия:** 1.0 (2026-07-16)
**Готов к загрузке в MiniMax Code.**
