ALTER TABLE analysis_jobs ADD COLUMN progress REAL NOT NULL DEFAULT 0;
ALTER TABLE analysis_jobs ADD COLUMN progress_message TEXT;
