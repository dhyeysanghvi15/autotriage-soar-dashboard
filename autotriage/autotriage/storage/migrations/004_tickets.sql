CREATE TABLE IF NOT EXISTS tickets (
  ticket_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  url TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tickets_case ON tickets(case_id);

