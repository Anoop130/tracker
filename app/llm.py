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

Allowed actions and required fields:
- set_goal {calories, protein_g, carbs_g, fat_g}
- add_food {name, serving_desc, cal, protein, carbs, fat, provenance?}
- log_meal {date?, items:[{name, qty}]}
- day_summary {date?}

Behavioral rules:
1) If the user provides stats (age, sex, height, weight, body fat, activity, goal: lean bulk/bulk/cut/maintain):
   - Compute daily calorie target using a standard method (e.g., Mifflin-St Jeor), apply an activity multiplier, then:
       lean_bulk: +10~15%, bulk: +15~20%, cut: -15~25%, maintain: 0%.
   - Split macros (default): protein 1.6–2.2 g/kg body weight, fat 20–30% of calories, rest carbs.
   - Emit a single set_goal action with numbers.
   - In speak, summarize the numbers briefly.

2) For food logging:
   - Parse free-form input (quantities, plurals) and emit ONE log_meal action with items.
   - Use date=today unless user says otherwise.

3) If a food isn't in the DB:
   - Emit one add_food action first with average macros for a typical serving (set provenance="llm_estimate"),
     then emit log_meal that references it by name.

4) Never say “recorded” without actions. If nothing to write, ask a concise follow-up question in 'speak' and set actions=[].
"""


# ---------- OFFLINE (fallback) ----------
def _offline_chat(history):
    last = (history[-1]["content"] if history else "").lower()
    if "total" in last or ("show" in last and "today" in last):
        return json.dumps({"speak":"Here are today’s totals.","done":False,"actions":[{"action":"day_summary","args":{}}]})
    if "set goal" in last:
        nums = [w for w in last.replace(",", " ").split() if w.replace(".", "", 1).isdigit()]
        if len(nums) >= 4:
            c, p, car, f = map(float, nums[:4])
            return json.dumps({"speak":"Goal saved.","done":False,"actions":[{"action":"set_goal","args":{"calories":c,"protein_g":p,"carbs_g":car,"fat_g":f}}]})
        return json.dumps({"speak":"Give four numbers: calories protein carbs fat.","done":False,"actions":[]})
    if last.startswith("log"):
        toks = last.split()
        qty = 1.0
        name = toks[-1] if len(toks) > 1 else "item"
        if len(toks) >= 3 and toks[1].replace(".", "", 1).isdigit():
            qty = float(toks[1]); name = toks[2]
        if name.endswith("s"): name = name[:-1]
        return json.dumps({"speak":f"Logging {qty:g} {name}.","done":False,"actions":[{"action":"log_meal","args":{"items":[{"name":name,"qty":qty}]}}]})
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
