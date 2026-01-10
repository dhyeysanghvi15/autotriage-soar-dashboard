CREATE TABLE IF NOT EXISTS cases (
  case_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  severity INTEGER NOT NULL,
  confidence REAL NOT NULL,
  decision TEXT NOT NULL,
  queue TEXT NOT NULL,
  summary TEXT NOT NULL,
  score_json TEXT NOT NULL,
  routing_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS case_entities (
  case_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_value TEXT NOT NULL,
  PRIMARY KEY (case_id, entity_type, entity_value),
  FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS case_edges (
  case_id TEXT NOT NULL,
  src_type TEXT NOT NULL,
  src_value TEXT NOT NULL,
  dst_type TEXT NOT NULL,
  dst_value TEXT NOT NULL,
  edge_type TEXT NOT NULL,
  PRIMARY KEY (case_id, src_type, src_value, dst_type, dst_value, edge_type),
  FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cases_time ON cases(created_at);
CREATE INDEX IF NOT EXISTS idx_cases_sev ON cases(severity, created_at);

