#!/usr/bin/env python3
import json
from datetime import date
from app.llm import chat_once, estimate_food
from db import api
from dotenv import load_dotenv


import os
DEBUG_RAW = os.getenv("DEBUG_RAW", "0") == "1"

load_dotenv() 
    
# ---- minimal JSON checks (no pydantic) ----
def parse_turn(raw: str) -> dict:
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        # If the model drifted, show raw and fail softly
        print("[warn] LLM returned non-JSON. Raw reply:\n", raw)
        return {"speak": "Sorry—please try again.", "done": False, "actions": []}
    
    # Use validator to check and fix the output
    from app.validator import validate_payload
    is_valid, errors = validate_payload(obj)
    
    if not is_valid:
        print(f"[warn] LLM output validation failed: {errors}")
        # Try to fix common issues
        obj = _fix_common_issues(obj, errors)
        is_valid, errors = validate_payload(obj)
        
        if not is_valid:
            return {"speak": f"Sorry, I had trouble understanding that. Errors: {'; '.join(errors[:3])}", "done": False, "actions": []}
    
    # enforce keys with defaults
    speak = obj.get("speak", "")
    done = bool(obj.get("done", False))
    actions = obj.get("actions", []) or []
    
    # make sure actions are list of dicts with 'action'
    safe_actions = []
    for a in actions:
        if isinstance(a, dict) and "action" in a:
            safe_actions.append({"action": a["action"], "args": a.get("args", {}) or {}})
    
    return {"speak": str(speak), "done": done, "actions": safe_actions}

def _fix_common_issues(obj, errors):
    """Try to fix common validation issues"""
    # Fix missing date in log_meal
    for action in obj.get("actions", []):
        if action.get("action") == "log_meal" and "date" not in action.get("args", {}):
            from datetime import date
            action["args"]["date"] = date.today().isoformat()
    
    return obj

# ---- dispatch ----
def dispatch(act: dict):
    name = act["action"]
    args = act.get("args", {}) or {}
    if name == "set_goal":
        required(args, ["calories","protein_g","carbs_g","fat_g"])
        api.set_default_goal(args["calories"], args["protein_g"], args["carbs_g"], args["fat_g"])
    elif name == "add_food":
        required(args, ["name","serving_desc","cal","protein","carbs","fat"])
        api.add_food(args["name"], args["serving_desc"], args["cal"], args["protein"], args["carbs"], args["fat"], args.get("provenance","user"))
    elif name == "log_meal":
        _log_meal_with_estimates(args)
    elif name == "day_summary":
        totals = api.day_summary(args.get("date"))
        print(f"[Totals {totals['date']}] kcal {totals['cal']:.0f} | P {totals['protein']:.0f} | C {totals['carbs']:.0f} | F {totals['fat']:.0f}")
    else:
        print(f"[ignored unknown action: {name}]")

def required(d, keys):
    missing = [k for k in keys if k not in d]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

def generate_sql_commands(actions):
    """Generate SQL commands based on validated actions"""
    sql_commands = []
    
    for action in actions:
        action_type = action["action"]
        args = action.get("args", {})
        
        if action_type == "add_food":
            sql = f"""INSERT INTO foods (user_id, name, serving_desc, cal, protein, carbs, fat, provenance) 
                     VALUES (1, '{args["name"]}', '{args["serving_desc"]}', {args["cal"]}, {args["protein"]}, {args["carbs"]}, {args["fat"]}, 'llm_estimate')"""
            sql_commands.append({
                "sql": sql,
                "description": f"Add food: {args['name']}"
            })
            
        elif action_type == "log_meal":
            from datetime import date
            date = args.get("date", date.today().isoformat())  # Use today's date
            # First create log entry
            log_sql = f"INSERT INTO logs (user_id, log_date) VALUES (1, '{date}') ON CONFLICT DO NOTHING"
            sql_commands.append({
                "sql": log_sql,
                "description": f"Create log entry for {date}"
            })
            
            # Then add each food item
            for item in args.get("items", []):
                food_name = item["name"]
                qty = item["qty"]
                log_item_sql = f"""INSERT INTO log_items (log_id, food_id, qty) 
                                 VALUES ((SELECT id FROM logs WHERE user_id=1 AND log_date='{date}'), 
                                        (SELECT id FROM foods WHERE name='{food_name}' AND user_id=1), {qty})"""
                sql_commands.append({
                    "sql": log_item_sql,
                    "description": f"Log {qty} {food_name}"
                })
                
        elif action_type == "set_goal":
            sql = f"""INSERT OR REPLACE INTO goals (user_id, calories, protein_g, carbs_g, fat_g) 
                     VALUES (1, {args["calories"]}, {args["protein_g"]}, {args["carbs_g"]}, {args["fat_g"]})"""
            sql_commands.append({
                "sql": sql,
                "description": f"Set nutrition goals"
            })
    
    return sql_commands

def execute_sql_command(sql: str, description: str = ""):
    """Execute a SQL command and return the result"""
    try:
        with api._conn() as conn:
            cursor = conn.execute(sql)
            conn.commit()
            if description:
                print(f"[SQL] {description}: {sql}")
            return {"success": True, "description": description}
    except Exception as e:
        print(f"[SQL ERROR] {description}: {sql} - Error: {e}")
        return {"success": False, "error": str(e), "description": description}

def _log_meal_with_estimates(args):
    d = args.get("date") or date.today().isoformat()
    items = args.get("items", [])
    if not isinstance(items, list) or not items:
        raise ValueError("log_meal requires non-empty items list")
    for it in items:
        name = it.get("name")
        qty  = float(it.get("qty", 1))
        if not name:
            raise ValueError("log_meal item missing 'name'")
        fid = api.lookup_food_id(name)
        if not fid:
            # ask LLM for average profile
            est_raw = estimate_food(name)
            est = parse_turn(est_raw)
            # expect one add_food action
            for a in est["actions"]:
                if a["action"] == "add_food":
                    a["args"].setdefault("provenance","llm_estimate")
                    dispatch(a)  # reuse normal add_food path
            fid = api.lookup_food_id(name)
            if not fid:
                raise RuntimeError(f"Failed to add estimated food: {name}")
        api.insert_log_item(d, fid, qty)

# ---- REPL ----
def run_chat():
    api.run_schema()  # idempotent
    history = []
    print("Diet coach ready. Type your request (e.g., 'log 2 eggs'). Ctrl+C to exit.")
    while True:
        try:
            user = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not user:
            continue
        history.append({"role":"user","content":user})
        raw = chat_once(history)
        turn = parse_turn(raw)
        print(turn["speak"])
        
        # Generate and execute SQL commands based on validated actions
        sql_commands = generate_sql_commands(turn["actions"])
        for sql_cmd in sql_commands:
            result = execute_sql_command(sql_cmd["sql"], sql_cmd.get("description", ""))
            if not result["success"]:
                print(f"[SQL Error] {result['error']}")
        
        # Execute regular actions (for display/logging)
        for act in turn["actions"]:
            try:
                dispatch(act)
            except Exception as e:
                print(f"[error] {e}")
        history.append({"role":"assistant","content":turn["speak"]})
        if turn["done"]:
            break

if __name__ == "__main__":
    run_chat()
