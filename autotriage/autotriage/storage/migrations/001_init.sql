PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
  id TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
  ingest_id TEXT PRIMARY KEY,
  idempotency_key TEXT NOT NULL UNIQUE,
  received_at TEXT NOT NULL,
  vendor TEXT,
  raw_json TEXT NOT NULL,
  normalized_json TEXT,
  status TEXT NOT NULL,
  updated_at TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  processing_started_at TEXT,
  processed_at TEXT,
  last_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_alerts_received_at ON alerts(received_at);
CREATE INDEX IF NOT EXISTS idx_alerts_status_received ON alerts(status, received_at);

CREATE TABLE IF NOT EXISTS fingerprints (
  ingest_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  strategy TEXT NOT NULL,
  fp_hash TEXT NOT NULL,
  window_start TEXT NOT NULL,
  PRIMARY KEY (ingest_id),
  FOREIGN KEY (ingest_id) REFERENCES alerts(ingest_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fingerprints_hash_window ON fingerprints(fp_hash, window_start);
