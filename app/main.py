#!/usr/bin/env python3
import json
from datetime import date
from app.llm import chat_once, estimate_food
from db import api
from dotenv import load_dotenv

load_dotenv() 


# ---- minimal JSON checks (no pydantic) ----
def parse_turn(raw: str) -> dict:
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        # If the model drifted, show raw and fail softly
        print("[warn] LLM returned non-JSON. Raw reply:\n", raw)
        return {"speak": "Sorry—please try again.", "done": False, "actions": []}
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
