# app/llm.py
import os, json, subprocess, shlex
from dotenv import load_dotenv
load_dotenv()

BACKEND = os.getenv("LLM_BACKEND", "ollama").lower()  # ollama | openai | offline
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

_SYSTEM = """
You are a registered dietitian & nutrition coach.
You MUST return exactly one JSON object with keys: speak (string), done (bool), actions (array).
Never return anything other than this JSON object. No preamble or explanations.

For food logging, return structured actions with these exact fields:
- For "log X food": return log_meal action with items containing name and qty
- For "add X food": return add_food action first, then log_meal

Required action formats:
- set_goal: {"action": "set_goal", "args": {"calories": number, "protein_g": number, "carbs_g": number, "fat_g": number}}
- add_food: {"action": "add_food", "args": {"name": "food_name", "serving_desc": "description", "cal": number, "protein": number, "carbs": number, "fat": number, "provenance": "llm_estimate"}}
- log_meal: {"action": "log_meal", "args": {"date": "YYYY-MM-DD", "items": [{"name": "food_name", "qty": number}]}}
- day_summary: {"action": "day_summary", "args": {"date": "YYYY-MM-DD"}}

Behavioral rules:
1) For food logging (e.g., "log 2 eggs", "add 1 leg quarter and rice meal"):
   - Parse quantities and food names carefully
   - For "log X food": assume food exists, just log it
   - For "add X food": add food to database first, then log it
   - ALWAYS use today's date: 2025-09-14
   - ALWAYS provide a helpful speak message describing what you're doing

2) For goal setting:
   - Compute daily calorie target using Mifflin-St Jeor equation
   - Apply activity multiplier and goal adjustment
   - Split macros: protein 1.6-2.2 g/kg, fat 20-30% calories, rest carbs

3) Always provide realistic macro estimates for foods
4) Use proper food names (singular form)
5) Never say "recorded" without actions
6) ALWAYS include a meaningful speak message - never leave it empty
7) CRITICAL: Always use date "2025-09-14" for all log_meal actions
"""


# ---------- OFFLINE (fallback) ----------
def _offline_chat(history):
    last = (history[-1]["content"] if history else "").lower()
    if "total" in last or ("show" in last and "today" in last):
        return json.dumps({"speak":"Here are today's totals.","done":False,"actions":[{"action":"day_summary","args":{}}]})
    if "set goal" in last:
        nums = [w for w in last.replace(",", " ").split() if w.replace(".", "", 1).isdigit()]
        if len(nums) >= 4:
            c, p, car, f = map(float, nums[:4])
            return json.dumps({"speak":"Goal saved.","done":False,"actions":[{"action":"set_goal","args":{"calories":c,"protein_g":p,"carbs_g":car,"fat_g":f}}]})
        return json.dumps({"speak":"Give four numbers: calories protein carbs fat.","done":False,"actions":[]})
    if last.startswith("log") or last.startswith("add"):
        toks = last.split()
        qty = 1.0
        name = toks[-1] if len(toks) > 1 else "item"
        if len(toks) >= 3 and toks[1].replace(".", "", 1).isdigit():
            qty = float(toks[1]); name = toks[2]
        if name.endswith("s"): name = name[:-1]
        
        from datetime import date
        today = "2025-09-14"  # Use today's date
        
        # Generate realistic macros for common foods
        macros = {
            "apple": {"cal": 95, "protein": 0.3, "carbs": 25, "fat": 0.3},
            "egg": {"cal": 70, "protein": 6, "carbs": 0.6, "fat": 5},
            "banana": {"cal": 105, "protein": 1.3, "carbs": 27, "fat": 0.4},
            "rice": {"cal": 206, "protein": 4.3, "carbs": 45, "fat": 0.4}
        }
        
        food_macros = macros.get(name, {"cal": 50, "protein": 1, "carbs": 10, "fat": 1})
        
        actions = []
        if last.startswith("add"):
            # Add food first, then log
            actions.append({
                "action": "add_food",
                "args": {
                    "name": name,
                    "serving_desc": f"1 {name}",
                    "cal": food_macros["cal"],
                    "protein": food_macros["protein"],
                    "carbs": food_macros["carbs"],
                    "fat": food_macros["fat"],
                    "provenance": "llm_estimate"
                }
            })
        
        actions.append({
            "action": "log_meal",
            "args": {
                "date": today,
                "items": [{"name": name, "qty": qty}]
            }
        })
        
        return json.dumps({
            "speak": f"Added and logged {qty:g} {name} for today!",
            "done": False,
            "actions": actions
        })
    return json.dumps({"speak":"(offline) Try: 'set goal 1800 140 170 60', 'log 2 eggs', 'show today totals'","done":False,"actions":[]})

def _offline_estimate(name:str):
    presets = {
        "egg":{"serving_desc":"1 large","cal":70,"protein":6,"carbs":0,"fat":5},
        "chicken":{"serving_desc":"100 g cooked","cal":165,"protein":31,"carbs":0,"fat":3.6},
        "rice":{"serving_desc":"1 cup cooked","cal":206,"protein":4.3,"carbs":45,"fat":0.4},
        "wrap":{"serving_desc":"1 tortilla","cal":110,"protein":10,"carbs":12,"fat":2},
    }
    m = presets.get(name.lower(), {"serving_desc":"1 serving","cal":100,"protein":5,"carbs":5,"fat":3})
    return json.dumps({"speak":f"(offline) Using average nutrition for {name}.","done":False,"actions":[{"action":"add_food","args":{"name":name.lower(),**m,"provenance":"llm_estimate"}}]})

# ---------- OLLAMA (local, free) ----------
def _ollama(prompt: str) -> str:
    cmd = f"ollama run {shlex.quote(OLLAMA_MODEL)} {shlex.quote(prompt)}"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else res.stderr.strip()

def _ollama_json(prompt: str) -> str:
    # wrap system + user into a single prompt; many local models prefer this style
    full = f"{_SYSTEM}\n\nUSER:\n{prompt}\n\nASSISTANT (JSON only):"
    out = _ollama(full)
    # try to extract JSON if model adds text around it
    start = out.find("{"); end = out.rfind("}")
    if start != -1 and end != -1 and end > start:
        return out[start:end+1]
    return out  # hope it's already JSON

def _ollama_chat(history):
    user = history[-1]["content"] if history else "Hello"
    return _ollama_json(user)

def _ollama_estimate(name:str):
    prompt = f"User mentioned '{name}' which is not in DB. Return ONE JSON object with exactly one add_food action for best-average macros and a short 'speak'. Set provenance='llm_estimate'."
    return _ollama_json(prompt)

# ---------- OPENAI (paid/credits) ----------
def _openai_chat(history):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    messages = [{"role":"system","content":_SYSTEM}] + history
    r = client.chat.completions.create(
        model=os.getenv("MODEL","gpt-4o-mini"),
        temperature=0,
        messages=messages
    )
    return r.choices[0].message.content

def _openai_estimate(name:str):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    messages = [
        {"role":"system","content":_SYSTEM},
        {"role":"user","content": f"User mentioned '{name}' which is not in DB. Return ONE JSON object with exactly one add_food action for best-average macros and a short 'speak'. Set provenance='llm_estimate'."}
    ]
    r = client.chat.completions.create(
        model=os.getenv("MODEL","gpt-4o-mini"),
        temperature=0,
        messages=messages
    )
    return r.choices[0].message.content

# ---------- PUBLIC API ----------
def chat_once(history):
    if BACKEND == "ollama":
        return _ollama_chat(history)
    if BACKEND == "openai":
        return _openai_chat(history)
    return _offline_chat(history)

def estimate_food(name: str):
    if BACKEND == "ollama":
        return _ollama_estimate(name)
    if BACKEND == "openai":
        return _openai_estimate(name)
    return _offline_estimate(name)

def repair_with_errors(raw_json: str, errors: list[str]) -> str:
    """
    Ask the model to fix its last JSON given explicit error messages.
    Must return ONE corrected JSON object (no prose).
    """
    if BACKEND == "offline":
        # in offline mode just echo raw; controller will bail or continue
        return raw_json

    err_bullets = "\n".join(f"- {e}" for e in errors)
    if BACKEND == "ollama":
        prompt = (
            f"{_SYSTEM}\n\nYour previous JSON had these problems:\n{err_bullets}\n\n"
            "Return ONLY a corrected JSON object that fixes all issues. No extra text."
        )
        return _ollama_json(prompt)

    if BACKEND == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        messages = [
            {"role":"system","content":_SYSTEM},
            {"role":"user","content": f"Your previous JSON had these problems:\n{err_bullets}\n\nReturn ONLY the corrected JSON."},
        ]
        r = client.chat.completions.create(
            model=os.getenv("MODEL","gpt-4o-mini"),
            temperature=0,
            messages=messages
        )
        return r.choices[0].message.content

    return raw_json
