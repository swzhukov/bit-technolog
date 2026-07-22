-- M35j: добавить таблицу pilot_runs (отсутствовала в v0.8 init)
-- Зачем: services/metrics.py::start_tc_generation() пишет в pilot_runs,
--        но таблица не была создана в 001_v0_8_init.sql → /items/{id}/generate падал с 500
-- Обнаружено: 2026-07-22 при smoke-test чеклиста пилота
-- Fix: CREATE TABLE pilot_runs + индексы по item_id/user

CREATE TABLE IF NOT EXISTS pilot_runs (
  id                  INTEGER PRIMARY KEY,
  kind                TEXT NOT NULL DEFAULT 'tc_generation',
  item_id             INTEGER NOT NULL REFERENCES items(id),
  user                TEXT NOT NULL,
  started_at          TIMESTAMP NOT NULL,
  finished_at         TIMESTAMP,
  duration_sec        REAL,
  tc_id               INTEGER REFERENCES tech_cards(id),
  notes               TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_runs_item ON pilot_runs(item_id);
CREATE INDEX IF NOT EXISTS idx_runs_user ON pilot_runs(user);
CREATE INDEX IF NOT EXISTS idx_runs_started ON pilot_runs(started_at);
