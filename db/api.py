import sqlite3, pathlib, datetime

BASE = pathlib.Path(__file__).resolve().parents[1]
DB_PATH = BASE / "db" / "tracker.db"
SCHEMA = BASE / "db" / "schema.sql"

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("PRAGMA foreign_keys=ON;")
    return c

def run_schema():
    sql = SCHEMA.read_text(encoding="utf-8")
    with _conn() as c:
        for stmt in [s.strip()+";" for s in sql.split(";") if s.strip()]:
            c.execute(stmt)

def set_default_goal(calories, protein_g, carbs_g, fat_g):
    with _conn() as c:
        c.execute("""
          INSERT INTO goals(goal_date, cal, protein, carbs, fat)
          VALUES (NULL, ?, ?, ?, ?)
          ON CONFLICT(goal_date) DO UPDATE SET
            cal=excluded.cal, protein=excluded.protein,
            carbs=excluded.carbs, fat=excluded.fat
        """, (calories, protein_g, carbs_g, fat_g))

def lookup_food_id(name:str):
    with _conn() as c:
        r = c.execute("SELECT id FROM foods WHERE name=?", (name,)).fetchone()
        return r[0] if r else None

def add_food(name, serving_desc, cal, protein, carbs, fat, provenance="user"):
    with _conn() as c:
        c.execute("""
          INSERT OR REPLACE INTO foods(name, serving_desc, cal, protein, carbs, fat, provenance)
          VALUES (?,?,?,?,?,?,?)
        """, (name, serving_desc, cal, protein, carbs, fat, provenance))

def _ensure_log_id(c, date_str):
    c.execute("INSERT OR IGNORE INTO logs(log_date) VALUES (?)", (date_str,))
    return c.execute("SELECT id FROM logs WHERE log_date=?", (date_str,)).fetchone()[0]

def insert_log_item(date=None, food_id=None, qty=1.0):
    if not date:
        date = datetime.date.today().isoformat()
    with _conn() as c:
        log_id = _ensure_log_id(c, date)
        c.execute("INSERT INTO log_items(log_id, food_id, qty) VALUES (?,?,?)",
                  (log_id, int(food_id), float(qty)))

def day_summary(date=None):
    if not date:
        date = datetime.date.today().isoformat()
    with _conn() as c:
        r = c.execute("""
          SELECT COALESCE(SUM(f.cal*li.qty),0),
                 COALESCE(SUM(f.protein*li.qty),0),
                 COALESCE(SUM(f.carbs*li.qty),0),
                 COALESCE(SUM(f.fat*li.qty),0)
          FROM logs lg
          JOIN log_items li ON li.log_id=lg.id
          JOIN foods f ON f.id=li.food_id
          WHERE lg.log_date=?
        """, (date,)).fetchone()
        return {"date": date, "cal": r[0] or 0, "protein": r[1] or 0, "carbs": r[2] or 0, "fat": r[3] or 0}
