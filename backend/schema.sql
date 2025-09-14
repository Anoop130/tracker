PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Updated foods table with user_id
CREATE TABLE IF NOT EXISTS foods (
  id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  name TEXT NOT NULL,
  serving_desc TEXT DEFAULT '1 serving',
  cal REAL NOT NULL,
  protein REAL NOT NULL,
  carbs REAL NOT NULL,
  fat REAL NOT NULL,
  provenance TEXT DEFAULT 'user', -- 'user' | 'llm_estimate'
  UNIQUE(user_id, name)
);

-- Updated logs table with user_id
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  log_date TEXT NOT NULL, -- YYYY-MM-DD
  UNIQUE(user_id, log_date)
);

-- Log items table (no changes needed)
CREATE TABLE IF NOT EXISTS log_items (
  id INTEGER PRIMARY KEY,
  log_id INTEGER NOT NULL,
  food_id INTEGER NOT NULL,
  qty REAL NOT NULL DEFAULT 1,
  FOREIGN KEY (log_id) REFERENCES logs(id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
);

-- Updated goals table with user_id
CREATE TABLE IF NOT EXISTS goals (
  id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  goal_date TEXT, -- NULL = default
  cal REAL NOT NULL,
  protein REAL NOT NULL,
  carbs REAL NOT NULL,
  fat REAL NOT NULL,
  UNIQUE(user_id, goal_date)
);

-- Insert demo user for testing
INSERT OR IGNORE INTO users (id, email, password_hash) 
VALUES (1, 'demo@example.com', 'dem0123');
