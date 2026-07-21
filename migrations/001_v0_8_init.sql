-- ============================================================
-- БИТ.Технолог v0.8 — полная переделка БД
-- Дата: 2026-07-21
-- ADR-0011: https://.../docs/adr/0011-v0.8-architecture.md
-- ============================================================
-- Принципы:
--   1. Один факт — одно место (model+chassis больше не тексты в details)
--   2. ref_1c у каждой сущности с двойником в 1С
--   3. items универсальная (level: detail/assembly/product)
--   4. bom_links MANY-TO-MANY
--   5. ext_attributes для extension-атрибутов
--   6. 8 осей профиля РС
--   7. ML/LLM лестница: etalons + work_history + rag
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- СПРАВОЧНИКИ (read-only, ссылаются на 1С через ref_1c)
-- ============================================================

CREATE TABLE IF NOT EXISTS chassis (
  id              INTEGER PRIMARY KEY,
  designation     TEXT NOT NULL UNIQUE,           -- КАМАЗ-43118, УРАЛ-4320, и т.д.
  name            TEXT NOT NULL,
  manufacturer    TEXT,                            -- ПАО «КАМАЗ», ОАО «АЗ УРАЛ»
  wheel_formula   TEXT,                            -- 6×6, 4×4
  curb_weight_kg  REAL,
  payload_kg      REAL,
  ref_1c          TEXT                             -- UUID в 1С
);

CREATE TABLE IF NOT EXISTS professions (
  id              INTEGER PRIMARY KEY,
  code            TEXT NOT NULL UNIQUE,           -- Р-3, С-4, Э-5
  name            TEXT NOT NULL,                  -- "Резчик"
  category        TEXT,                            -- "рабочий", "ИТР"
  grade           INTEGER,                         -- 3, 4, 5
  hourly_rate     REAL,                            -- руб/час
  ref_1c          TEXT
);

CREATE TABLE IF NOT EXISTS workshops (
  id              INTEGER PRIMARY KEY,
  code            TEXT NOT NULL,                  -- 01, 02, 03
  name            TEXT NOT NULL,                  -- "Заготовительный"
  parent_id       INTEGER REFERENCES workshops(id),
  ref_1c          TEXT
);

CREATE TABLE IF NOT EXISTS equipment (
  id              INTEGER PRIMARY KEY,
  inventory_no    TEXT NOT NULL UNIQUE,
  name            TEXT NOT NULL,
  type            TEXT,                            -- "сварочное", "металлорежущее"
  workshop_id     INTEGER REFERENCES workshops(id),
  power_kw        REAL,
  ref_1c          TEXT
);

CREATE TABLE IF NOT EXISTS materials (
  id              INTEGER PRIMARY KEY,
  code            TEXT NOT NULL UNIQUE,           -- "09Г2С", "Св-08Г2С-О"
  name            TEXT NOT NULL,
  category        TEXT,                            -- "лист", "проволока", "крепеж"
  grade           TEXT,                            -- марка
  unit            TEXT DEFAULT 'кг',              -- кг, м, шт
  price_per_unit  REAL,                            -- руб/кг
  ref_1c          TEXT
);

-- ============================================================
-- РС-ПРОФИЛИ (нужны ДО product_models из-за FK)
-- ============================================================

CREATE TABLE IF NOT EXISTS rs_output_profiles (
  id                  INTEGER PRIMARY KEY,
  code                TEXT NOT NULL UNIQUE,        -- "tehinkom_v1", "spec_1c"
  name                TEXT NOT NULL,
  product_type        TEXT,                          -- "АЦ", "УМК", "ПСС"
  version             INTEGER DEFAULT 1,
  is_active           INTEGER DEFAULT 1,
  -- 8 ОСЕЙ (ADR-0011, T1)
  axes_json           TEXT NOT NULL,
  description         TEXT,
  ref_1c              TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- LLM ПРОВАЙДЕРЫ (нужны ДО tech_cards из-за FK)
-- ============================================================

CREATE TABLE IF NOT EXISTS llm_providers (
  id                  INTEGER PRIMARY KEY,
  name                TEXT NOT NULL UNIQUE,        -- "yandexgpt", "gigachat", "deepseek", "mock"
  display_name        TEXT NOT NULL,
  endpoint            TEXT,                          -- "gpt://b1gj.../yandexgpt/latest"
  api_key_enc         TEXT,                          -- Fernet-encrypted
  cost_per_1k_input   REAL DEFAULT 0,
  cost_per_1k_output  REAL DEFAULT 0,
  is_active           INTEGER DEFAULT 1,
  supports_tasks      TEXT,                          -- JSON-массив: ["generation","ocr","embedding"]
  notes               TEXT,
  ref_1c              TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- ИЗДЕЛИЯ И НОМЕНКЛАТУРА
-- ============================================================

-- product_models: модель изделия (АЦ-8,0-40, УМК, ПСС)
CREATE TABLE IF NOT EXISTS product_models (
  id                     INTEGER PRIMARY KEY,
  designation            TEXT NOT NULL UNIQUE,     -- "АЦ-8,0-40"
  name                   TEXT NOT NULL,            -- "Автоцистерна пожарная 8 м³ на шасси КАМАЗ-43118"
  product_type           TEXT,                      -- "АЦ", "УМК", "ПСС"
  chassis_id             INTEGER REFERENCES chassis(id),
  tu_doc                 TEXT,                      -- ТУ 4854-001-...
  default_rs_profile_id  INTEGER REFERENCES rs_output_profiles(id),
  ref_1c                 TEXT
);

-- product_configurations: исполнение (зав.№144, №147)
CREATE TABLE IF NOT EXISTS product_configurations (
  id                  INTEGER PRIMARY KEY,
  product_model_id    INTEGER NOT NULL REFERENCES product_models(id),
  internal_number     TEXT NOT NULL,              -- "144", "147"
  contract            TEXT,                        -- договор
  order_date          DATE,
  customer            TEXT,                        -- заказчик
  base_diffs_json     TEXT,                        -- отличия от базовой модели (JSON)
  ref_1c              TEXT,
  UNIQUE(product_model_id, internal_number)
);

-- items: УНИВЕРСАЛЬНАЯ номенклатура (деталь/узел/сборка/покупное/полуфабрикат)
-- ЗАМЕНЯЕТ details, assemblies, purchased — ОДНА таблица для всех
CREATE TABLE IF NOT EXISTS items (
  id                  INTEGER PRIMARY KEY,
  designation         TEXT NOT NULL UNIQUE,       -- "ЛМША.301314.010"
  name                TEXT NOT NULL,
  level               TEXT NOT NULL CHECK(level IN ('detail','assembly','product','purchased','semi')),
  type                TEXT,                        -- "деталь", "узел", "сборочная единица"
  parent_item_id      INTEGER REFERENCES items(id),  -- иерархия
  product_model_id    INTEGER REFERENCES product_models(id),
  configuration_id    INTEGER REFERENCES product_configurations(id),
  mass_kg             REAL,
  material_id         INTEGER REFERENCES materials(id),
  drawing_no          TEXT,                        -- "ЛМША.301314.010 СБ"
  drawing_pdf         TEXT,                        -- путь к PDF
  -- Кооперация (ПРИНЦИП П10)
  sourcing            TEXT DEFAULT 'make' CHECK(sourcing IN ('make','buy','coop_da','coop_full')),
  coop_partner_id     INTEGER,
  coop_partner_name   TEXT,
  coop_what_we_send   TEXT,                        -- "заготовка трубы", "лист"
  coop_what_we_get    TEXT,                        -- "пружина тарельчатая 72шт"
  coop_deadline_days  INTEGER,
  --
  ref_1c              TEXT,
  source_type         TEXT DEFAULT 'manual' CHECK(source_type IN ('manual','ai','etalon','imported_1c')),
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_items_parent ON items(parent_item_id);
CREATE INDEX IF NOT EXISTS idx_items_product_model ON items(product_model_id);
CREATE INDEX IF NOT EXISTS idx_items_configuration ON items(configuration_id);
CREATE INDEX IF NOT EXISTS idx_items_sourcing ON items(sourcing);
CREATE INDEX IF NOT EXISTS idx_items_ref_1c ON items(ref_1c);

-- bom_links: MANY-TO-MANY состав (parent → child + qty)
CREATE TABLE IF NOT EXISTS bom_links (
  id                  INTEGER PRIMARY KEY,
  parent_item_id      INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  child_item_id       INTEGER NOT NULL REFERENCES items(id),
  qty                 REAL NOT NULL DEFAULT 1,
  configuration_id    INTEGER REFERENCES product_configurations(id), -- NULL = базовый состав
  ref_1c              TEXT,
  UNIQUE(parent_item_id, child_item_id, configuration_id)
);

CREATE INDEX IF NOT EXISTS idx_bom_parent ON bom_links(parent_item_id);
CREATE INDEX IF NOT EXISTS idx_bom_child ON bom_links(child_item_id);
CREATE INDEX IF NOT EXISTS idx_bom_config ON bom_links(configuration_id);

-- ============================================================
-- ТЕХНОЛОГИЧЕСКИЕ КАРТЫ (ТК)
-- ============================================================

-- tech_cards: ТК (одна на изделие, много версий)
CREATE TABLE IF NOT EXISTS tech_cards (
  id                  INTEGER PRIMARY KEY,
  item_id             INTEGER NOT NULL REFERENCES items(id),
  version             INTEGER NOT NULL DEFAULT 1,
  status              TEXT DEFAULT 'draft' CHECK(status IN ('draft','review','approved','archived')),
  author              TEXT,
  approver_chief      TEXT,                        -- главный технолог
  approver_prod       TEXT,                        -- начальник производства
  approved_at         TIMESTAMP,
  llm_provider_id     INTEGER REFERENCES llm_providers(id),
  llm_model           TEXT,                        -- "gpt://.../yandexgpt/latest"
  llm_meta_json       TEXT,                        -- generation_params, cost, prompt_version
  is_approved         INTEGER DEFAULT 0,           -- 0/1
  ref_1c              TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(item_id, version)
);

CREATE INDEX IF NOT EXISTS idx_tech_cards_item ON tech_cards(item_id);
CREATE INDEX IF NOT EXISTS idx_tech_cards_status ON tech_cards(status);

-- operations: операции ТК
CREATE TABLE IF NOT EXISTS operations (
  id                  INTEGER PRIMARY KEY,
  tech_card_id        INTEGER NOT NULL REFERENCES tech_cards(id) ON DELETE CASCADE,
  op_number           INTEGER NOT NULL,            -- 010, 015, 020, ...
  name                TEXT NOT NULL,                -- "Приварка ножей к основанию"
  workshop_id         INTEGER REFERENCES workshops(id),
  equipment_id        INTEGER REFERENCES equipment(id),
  profession_id       INTEGER REFERENCES professions(id),
  time_setup_min      REAL DEFAULT 0,               -- Тпз
  time_per_unit_min   REAL DEFAULT 0,               -- Тшт
  time_total_min      REAL,                          -- (Тпз + Тшт) — вычисляется в API
  -- Источник нормы (СВЕТОФОР)
  source              TEXT DEFAULT 'ai_guess' CHECK(source IN ('factory_data','analog_estimate','ai_guess','manual')),
  evidence_json       TEXT,                          -- аналоги, ссылки на эталоны
  -- Кооперация
  is_coop_step        INTEGER DEFAULT 0,
  coop_note           TEXT,
  ref_1c              TEXT,
  -- Доп. параметры
  labor_category      TEXT,                          -- "основная", "вспомогательная"
  notes               TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(tech_card_id, op_number)
);

CREATE INDEX IF NOT EXISTS idx_operations_tech_card ON operations(tech_card_id);
CREATE INDEX IF NOT EXISTS idx_operations_workshop ON operations(workshop_id);
CREATE INDEX IF NOT EXISTS idx_operations_source ON operations(source);

-- operation_materials: материалы операции (для РС)
CREATE TABLE IF NOT EXISTS operation_materials (
  id                  INTEGER PRIMARY KEY,
  operation_id        INTEGER NOT NULL REFERENCES operations(id) ON DELETE CASCADE,
  material_id         INTEGER NOT NULL REFERENCES materials(id),
  qty                 REAL NOT NULL,
  unit                TEXT DEFAULT 'кг',
  ref_1c              TEXT,
  is_waste            INTEGER DEFAULT 0,            -- отходы
  notes               TEXT
);

CREATE INDEX IF NOT EXISTS idx_op_mats_op ON operation_materials(operation_id);

-- ============================================================
-- РЕСУРСНЫЕ СПЕЦИФИКАЦИИ (РС) — Трек B
-- ============================================================

-- resource_specs: РС в 1С:ERP
CREATE TABLE IF NOT EXISTS resource_specs (
  id                  INTEGER PRIMARY KEY,
  item_id             INTEGER NOT NULL REFERENCES items(id),
  tech_card_id        INTEGER REFERENCES tech_cards(id),
  tech_card_version   INTEGER,
  rs_profile_id       INTEGER REFERENCES rs_output_profiles(id),
  status              TEXT DEFAULT 'draft' CHECK(status IN ('draft','exported','accepted_1c','rejected_1c','conflict')),
  ref_1c              TEXT,                          -- UUID в 1С
  version_1c          TEXT,                          -- версия в 1С
  change_reason       TEXT,                          -- "И-2026-014"
  content_json        TEXT NOT NULL,                 -- сериализованная РС (см. rs_factory)
  exported_at         TIMESTAMP,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rs_item ON resource_specs(item_id);
CREATE INDEX IF NOT EXISTS idx_rs_tech_card ON resource_specs(tech_card_id);
CREATE INDEX IF NOT EXISTS idx_rs_status ON resource_specs(status);

-- ============================================================
-- ИЗВЕЩЕНИЯ (change_notices) — ГОСТ 2.503
-- ============================================================

CREATE TABLE IF NOT EXISTS change_notices (
  id                  INTEGER PRIMARY KEY,
  number              TEXT NOT NULL UNIQUE,        -- "И-2026-014"
  date                DATE NOT NULL,
  author              TEXT NOT NULL,
  status              TEXT DEFAULT 'open' CHECK(status IN ('open','in_progress','resolved','cancelled')),
  foundation_doc      TEXT,                          -- "Решение главного конструктора №..."
  reason              TEXT,                          -- "Замена материала"
  description         TEXT,
  -- Затронутые items (после автопоиска через bom_links)
  affected_items_json TEXT,                          -- JSON-массив {item_id, impact_type, ai_diff}
  user_decision       TEXT,                          -- "accept_ai" | "manual_review" | "reject"
  decided_at          TIMESTAMP,
  decided_by          TEXT,
  ref_1c              TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_change_notices_status ON change_notices(status);
CREATE INDEX IF NOT EXISTS idx_change_notices_date ON change_notices(date);

-- ============================================================
-- РАСШИРЕНИЯ (ext_attributes) — extension-атрибуты
-- ============================================================

CREATE TABLE IF NOT EXISTS ext_attributes (
  id                  INTEGER PRIMARY KEY,
  entity_type         TEXT NOT NULL,                -- "item" | "operation" | "tech_card" | "rs"
  ref_1c              TEXT NOT NULL,                -- UUID сущности в 1С
  attr_code           TEXT NOT NULL,                -- "weld_length_mm" | "wall_thickness" | "coating"
  value               TEXT NOT NULL,                -- JSON или строка
  unit                TEXT,
  used_in             TEXT,                          -- "rs_calc" | "witness" | "logging"
  source              TEXT DEFAULT 'manual',
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(entity_type, ref_1c, attr_code)
);

CREATE INDEX IF NOT EXISTS idx_ext_attr_lookup ON ext_attributes(entity_type, ref_1c);

-- ============================================================
-- ИСТОРИЯ РАБОТ (work_history) — для петли обратной связи
-- ============================================================

CREATE TABLE IF NOT EXISTS work_history (
  id                  INTEGER PRIMARY KEY,
  item_designation    TEXT NOT NULL,                -- "ЛМША.301314.010"
  operation_name      TEXT NOT NULL,                -- "Приварка ножей"
  source_type         TEXT NOT NULL CHECK(source_type IN ('work_log','time_sheet','card_575','narjad','akt')),
  time_min            REAL,                          -- фактическое время
  n_observations      INTEGER DEFAULT 1,             -- сколько раз наблюдалось
  source_doc          TEXT,                          -- путь к файлу/источнику
  worker              TEXT,
  date                DATE,
  notes               TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wh_item ON work_history(item_designation);
CREATE INDEX IF NOT EXISTS idx_wh_source ON work_history(source_type);

-- ============================================================
-- ЭТАЛОНЫ (etalons) — реальные ТП Техинкома
-- ============================================================

CREATE TABLE IF NOT EXISTS etalons (
  id                  INTEGER PRIMARY KEY,
  designation         TEXT NOT NULL UNIQUE,        -- "ЛМША.301314.010"
  name                TEXT NOT NULL,
  product_type        TEXT,                          -- "АЦ", "УМК", "ПСС"
  source_doc          TEXT,                          -- путь к PDF
  source_pages        INTEGER,                       -- сколько страниц
  approved_by         TEXT,                          -- "Воробьев И.Ф. (ВП 3237)"
  approved_date       DATE,
  is_approved         INTEGER DEFAULT 1,            -- всегда 1 для эталонов
  is_published        INTEGER DEFAULT 0,            -- опубликован для RAG
  content_json        TEXT NOT NULL,                 -- сериализованный ТП (операции+материалы)
  rag_indexed_at      TIMESTAMP,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_etalons_published ON etalons(is_published);
CREATE INDEX IF NOT EXISTS idx_etalons_product_type ON etalons(product_type);

-- ============================================================
-- ПРАВИЛА ТЕХНОЛОГА (tech_rules)
-- ============================================================

CREATE TABLE IF NOT EXISTS tech_rules (
  id                  INTEGER PRIMARY KEY,
  name                TEXT NOT NULL,
  description         TEXT,
  -- Условие (jsonLogic)
  condition_json      TEXT NOT NULL,
  -- Действие
  action              TEXT NOT NULL,                 -- "set_time" | "set_material" | "set_profession"
  action_params_json  TEXT,
  priority            INTEGER DEFAULT 100,
  is_active           INTEGER DEFAULT 1,
  source              TEXT DEFAULT 'tech_lead',     -- "tech_lead" | "ai_learned" | "dse_575"
  source_doc          TEXT,                          -- откуда правило (наряд, ведомость)
  created_by          TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- ПРАВКИ (edits) — петля обратной связи
-- ============================================================

CREATE TABLE IF NOT EXISTS edits (
  id                  INTEGER PRIMARY KEY,
  draft_id            INTEGER,
  tech_card_id        INTEGER REFERENCES tech_cards(id),
  operation_id        INTEGER REFERENCES operations(id),
  field               TEXT NOT NULL,                 -- "time_per_unit_min"
  old_value           TEXT,
  new_value           TEXT,
  user                TEXT NOT NULL,
  reason              TEXT,                          -- "по аналогу ЛМША.301314.020"
  ts                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_edits_tech_card ON edits(tech_card_id);
CREATE INDEX IF NOT EXISTS idx_edits_op ON edits(operation_id);

-- (llm_providers создана выше, до product_models)

-- llm_model_assignments: какая модель на какой задаче
CREATE TABLE IF NOT EXISTS llm_model_assignments (
  id                  INTEGER PRIMARY KEY,
  task_type           TEXT NOT NULL CHECK(task_type IN (
    'tech_card_generation',
    'tech_card_refinement',
    'clarification_question',
    'notice_diff',
    'ocr_pdf',
    'evidence_search',
    'general_chat'
  )),
  llm_provider_id     INTEGER NOT NULL REFERENCES llm_providers(id),
  model_name          TEXT NOT NULL,
  temperature         REAL DEFAULT 0.2,
  max_tokens          INTEGER DEFAULT 4000,
  is_active           INTEGER DEFAULT 1,
  updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by          TEXT,
  UNIQUE(task_type, is_active)
);

-- llm_calls: журнал вызовов
CREATE TABLE IF NOT EXISTS llm_calls (
  id                  INTEGER PRIMARY KEY,
  task_type           TEXT,
  llm_provider_id     INTEGER REFERENCES llm_providers(id),
  model_name          TEXT,
  prompt_hash         TEXT,
  prompt_tokens       INTEGER,
  completion_tokens   INTEGER,
  cost_rub            REAL,
  duration_ms         INTEGER,
  user                TEXT,
  status              TEXT,                          -- "ok" | "error" | "fallback"
  error_message       TEXT,
  ts                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_llm_calls_ts ON llm_calls(ts);
CREATE INDEX IF NOT EXISTS idx_llm_calls_task ON llm_calls(task_type);

-- ============================================================
-- ПОЛЬЗОВАТЕЛИ И АУТЕНТИФИКАЦИЯ
-- ============================================================

CREATE TABLE IF NOT EXISTS pilot_users (
  id                  INTEGER PRIMARY KEY,
  username            TEXT NOT NULL UNIQUE,
  password_hash       TEXT NOT NULL,                 -- bcrypt
  role                TEXT NOT NULL CHECK(role IN (
    'technologist',          -- технолог (Баранов, Голубев, Воробьев)
    'main_technologist',     -- главный технолог
    'workshop_chief',        -- начальник цеха
    'tech_admin',            -- технический администратор (настройка профилей РС, не LLM)
    'llm_admin'              -- LLM-администратор (назначение моделей)
  )),
  display_name        TEXT NOT NULL,
  email               TEXT,
  is_active           INTEGER DEFAULT 1,
  ref_1c              TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login          TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logins (
  id                  INTEGER PRIMARY KEY,
  username            TEXT NOT NULL,
  ip                  TEXT,
  user_agent          TEXT,
  success             INTEGER NOT NULL,              -- 0/1
  reason              TEXT,                          -- "wrong_password" | "ok" | "inactive"
  ts                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logins_username ON audit_logins(username);
CREATE INDEX IF NOT EXISTS idx_audit_logins_ts ON audit_logins(ts);

-- ============================================================
-- НАСТРОЙКИ (Fernet-encrypted)
-- ============================================================

CREATE TABLE IF NOT EXISTS app_settings (
  key                 TEXT PRIMARY KEY,
  value_enc           TEXT NOT NULL,                 -- Fernet-encrypted
  description         TEXT,
  updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by          TEXT
);

-- ============================================================
-- ПИЛОТНЫЕ МЕТРИКИ
-- ============================================================

CREATE TABLE IF NOT EXISTS pilot_metrics (
  id                  INTEGER PRIMARY KEY,
  metric_code         TEXT NOT NULL,
  metric_value        REAL,
  metric_label        TEXT,
  measured_at         DATE NOT NULL,
  notes               TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metrics_code ON pilot_metrics(metric_code);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON pilot_metrics(measured_at);

-- ============================================================
-- ЧЕРНОВИКИ (drafts) + ВЕРСИИ (draft_versions)
-- ============================================================

CREATE TABLE IF NOT EXISTS drafts (
  id                  INTEGER PRIMARY KEY,
  item_id             INTEGER NOT NULL REFERENCES items(id),
  status              TEXT DEFAULT 'in_progress' CHECK(status IN ('in_progress','submitted','approved','rejected')),
  assigned_to         TEXT,
  last_activity       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS draft_versions (
  id                  INTEGER PRIMARY KEY,
  draft_id            INTEGER NOT NULL REFERENCES drafts(id) ON DELETE CASCADE,
  version             INTEGER NOT NULL,
  content_json        TEXT NOT NULL,
  created_by          TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(draft_id, version)
);

-- ============================================================
-- ИСТОРИЯ (history) — общая
-- ============================================================

CREATE TABLE IF NOT EXISTS history (
  id                  INTEGER PRIMARY KEY,
  entity_type         TEXT NOT NULL,
  entity_id           INTEGER NOT NULL,
  action              TEXT NOT NULL,                  -- "create" | "update" | "delete" | "approve" | "export"
  user                TEXT,
  details_json        TEXT,
  ts                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_history_entity ON history(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_history_ts ON history(ts);

-- ============================================================
-- КОМПАС-3D Watcher (F12, заглушка для будущего)
-- ============================================================

CREATE TABLE IF NOT EXISTS kompas_events (
  id                  INTEGER PRIMARY KEY,
  file_path           TEXT NOT NULL,
  event_type          TEXT,                          -- "modified" | "created" | "deleted"
  drawing_no          TEXT,
  detected_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  processed           INTEGER DEFAULT 0
);

-- ============================================================
-- IOT (заглушка)
-- ============================================================

CREATE TABLE IF NOT EXISTS iot (
  id                  INTEGER PRIMARY KEY,
  device_id           TEXT,
  metric              TEXT,
  value               REAL,
  ts                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- BENCHMARKS (бенчмарки для тестов)
-- ============================================================

CREATE TABLE IF NOT EXISTS benchmarks (
  id                  INTEGER PRIMARY KEY,
  test_name           TEXT NOT NULL,
  duration_ms         REAL,
  metadata_json       TEXT,
  ts                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
