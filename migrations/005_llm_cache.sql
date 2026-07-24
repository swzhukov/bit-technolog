-- Sprint 7 D10: LLM extraction cache
-- Избегает повторных вызовов LLM для одинаковых OCR текстов

CREATE TABLE IF NOT EXISTS llm_extraction_cache (
    ocr_hash TEXT PRIMARY KEY,
    ocr_text_preview TEXT,  -- первые 100 символов (для отладки)
    llm_data TEXT NOT NULL,  -- JSON
    is_fallback INTEGER DEFAULT 0,  -- 1 = regex fallback
    hits_count INTEGER DEFAULT 1,  -- сколько раз использовали
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_llm_cache_hits ON llm_extraction_cache(hits_count DESC);
CREATE INDEX IF NOT EXISTS idx_llm_cache_last_used ON llm_extraction_cache(last_used_at);
