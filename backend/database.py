"""
Database utilities for FastAPI backend
"""
import sqlite3
import pathlib
from typing import Optional, List, Dict, Any

# Database path
BASE = pathlib.Path(__file__).resolve().parents[1]
DB_PATH = BASE / "db" / "tracker.db"
SCHEMA = pathlib.Path(__file__).parent / "schema.sql"

def get_connection():
    """Get database connection with foreign keys enabled"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_database():
    """Initialize database with updated schema"""
    sql = SCHEMA.read_text(encoding="utf-8")
    with get_connection() as conn:
        for stmt in [s.strip() + ";" for s in sql.split(";") if s.strip()]:
            conn.execute(stmt)

def get_user_foods(user_id: int, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get foods for a specific user"""
    with get_connection() as conn:
        if search:
            cursor = conn.execute(
                "SELECT id, name, serving_desc, cal, protein, carbs, fat, provenance FROM foods WHERE user_id = ? AND name LIKE ?",
                (user_id, f"%{search}%")
            )
        else:
            cursor = conn.execute(
                "SELECT id, name, serving_desc, cal, protein, carbs, fat, provenance FROM foods WHERE user_id = ?",
                (user_id,)
            )
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def add_user_food(user_id: int, name: str, serving_desc: str, cal: float, 
                 protein: float, carbs: float, fat: float, provenance: str = "user") -> int:
    """Add food for a specific user"""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT OR REPLACE INTO foods 
               (user_id, name, serving_desc, cal, protein, carbs, fat, provenance)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, name, serving_desc, cal, protein, carbs, fat, provenance)
        )
        return cursor.lastrowid

def get_user_goals(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's current goals"""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT cal, protein, carbs, fat FROM goals WHERE user_id = ? AND goal_date IS NULL",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "calories": row[0],
                "protein_g": row[1],
                "carbs_g": row[2],
                "fat_g": row[3]
            }
        return None

def set_user_goals(user_id: int, calories: float, protein_g: float, carbs_g: float, fat_g: float):
    """Set user's goals"""
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO goals (user_id, goal_date, cal, protein, carbs, fat)
               VALUES (?, NULL, ?, ?, ?, ?)
               ON CONFLICT(user_id, goal_date) DO UPDATE SET
               cal=excluded.cal, protein=excluded.protein,
               carbs=excluded.carbs, fat=excluded.fat""",
            (user_id, calories, protein_g, carbs_g, fat_g)
        )

def get_user_daily_summary(user_id: int, date: str) -> Dict[str, Any]:
    """Get daily nutrition summary for a user"""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT COALESCE(SUM(f.cal*li.qty), 0),
                   COALESCE(SUM(f.protein*li.qty), 0),
                   COALESCE(SUM(f.carbs*li.qty), 0),
                   COALESCE(SUM(f.fat*li.qty), 0)
            FROM logs lg
            JOIN log_items li ON li.log_id = lg.id
            JOIN foods f ON f.id = li.food_id
            WHERE lg.user_id = ? AND lg.log_date = ?
        """, (user_id, date))
        
        row = cursor.fetchone()
        return {
            "date": date,
            "cal": row[0] or 0,
            "protein": row[1] or 0,
            "carbs": row[2] or 0,
            "fat": row[3] or 0
        }
