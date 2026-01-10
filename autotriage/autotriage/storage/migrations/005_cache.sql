CREATE TABLE IF NOT EXISTS cache (
  enricher TEXT NOT NULL,
  cache_key TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  value_json TEXT NOT NULL,
  PRIMARY KEY (enricher, cache_key)
);

CREATE INDEX IF NOT EXISTS idx_cache_enricher_key ON cache(enricher, cache_key);

