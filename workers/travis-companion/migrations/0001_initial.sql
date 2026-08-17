PRAGMA foreign_keys = ON;

CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  course_id TEXT NOT NULL,
  lesson_id TEXT NOT NULL,
  state TEXT NOT NULL,
  draft_version INTEGER NOT NULL DEFAULT 1,
  draft_json TEXT NOT NULL,
  primary_track_asset_id TEXT,
  current_published_revision TEXT,
  workflow_instance_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE media_assets (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  kind TEXT NOT NULL,
  file_name TEXT NOT NULL,
  content_type TEXT NOT NULL,
  declared_size INTEGER NOT NULL,
  actual_size INTEGER,
  expected_sha256 TEXT,
  actual_sha256 TEXT,
  duration_ms INTEGER,
  r2_key TEXT NOT NULL UNIQUE,
  upload_id TEXT,
  status TEXT NOT NULL,
  label TEXT,
  is_primary INTEGER NOT NULL DEFAULT 0,
  visible_to_learners INTEGER NOT NULL DEFAULT 0,
  downloadable INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX media_assets_project_idx ON media_assets(project_id, kind);

CREATE TABLE edit_events (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  from_version INTEGER NOT NULL,
  to_version INTEGER NOT NULL,
  editor_email TEXT NOT NULL,
  summary TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX edit_events_project_idx ON edit_events(project_id, created_at);

CREATE TABLE published_revisions (
  project_id TEXT NOT NULL REFERENCES projects(id),
  revision TEXT NOT NULL,
  content_sha256 TEXT NOT NULL,
  artifact_key TEXT NOT NULL,
  pdf_key TEXT NOT NULL,
  published_by TEXT NOT NULL,
  published_at TEXT NOT NULL,
  PRIMARY KEY (project_id, revision)
);

CREATE TABLE analysis_jobs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  workflow_instance_id TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL,
  attempt INTEGER NOT NULL DEFAULT 0,
  lease_token_hash TEXT,
  lease_expires_at TEXT,
  video_asset_id TEXT NOT NULL REFERENCES media_assets(id),
  primary_track_asset_id TEXT NOT NULL REFERENCES media_assets(id),
  result_key TEXT,
  error TEXT,
  retryable INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX analysis_jobs_claim_idx ON analysis_jobs(status, lease_expires_at, created_at);

CREATE TABLE oauth_states (
  state_hash TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  return_origin TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  used_at TEXT
);

CREATE TABLE embed_codes (
  code_hash TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  subject TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  used_at TEXT
);

CREATE INDEX embed_codes_project_idx ON embed_codes(project_id, expires_at);
