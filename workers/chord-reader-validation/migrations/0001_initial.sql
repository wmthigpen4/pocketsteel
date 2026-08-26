PRAGMA foreign_keys = ON;

CREATE TABLE review_sessions (
  id TEXT PRIMARY KEY,
  reviewer_hash TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE track_feedback (
  session_id TEXT NOT NULL REFERENCES review_sessions(id),
  track_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (session_id, track_id)
);

CREATE INDEX track_feedback_updated_idx
  ON track_feedback(session_id, updated_at);
