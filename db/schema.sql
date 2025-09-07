PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS foods (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  serving_desc TEXT DEFAULT '1 serving',
  cal REAL NOT NULL,
  protein REAL NOT NULL,
  carbs REAL NOT NULL,
  fat REAL NOT NULL,
  provenance TEXT DEFAULT 'user' -- 'user' | 'llm_estimate'
);

CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY,
  log_date TEXT NOT NULL UNIQUE -- YYYY-MM-DD
);

CREATE TABLE IF NOT EXISTS log_items (
  id INTEGER PRIMARY KEY,
  log_id INTEGER NOT NULL,
  food_id INTEGER NOT NULL,
  qty REAL NOT NULL DEFAULT 1,
  FOREIGN KEY (log_id) REFERENCES logs(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS goals (
  id INTEGER PRIMARY KEY,
  goal_date TEXT,  -- NULL = default
  cal REAL NOT NULL,
  protein REAL NOT NULL,
  carbs REAL NOT NULL,
  fat REAL NOT NULL,
  UNIQUE(goal_date)
);
