CREATE TABLE IF NOT EXISTS deadletter (
  ingest_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  attempts INTEGER NOT NULL,
  error TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

