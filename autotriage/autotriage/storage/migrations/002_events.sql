CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  stage TEXT NOT NULL,
  ingest_id TEXT,
  case_id TEXT,
  payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_time ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_case ON events(case_id, created_at);

