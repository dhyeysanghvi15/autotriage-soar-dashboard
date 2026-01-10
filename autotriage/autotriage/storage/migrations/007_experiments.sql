CREATE TABLE IF NOT EXISTS experiments (
  experiment_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  since TEXT NOT NULL,
  until TEXT NOT NULL,
  overrides_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_results (
  experiment_id TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  before_value REAL,
  after_value REAL,
  details_json TEXT NOT NULL,
  PRIMARY KEY (experiment_id, metric_name),
  FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_experiments_time ON experiments(created_at);

