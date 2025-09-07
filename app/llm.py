import os
from openai import OpenAI

_SYSTEM = """You are a registered dietitian & nutrition coach.
Always respond with ONE JSON object: { "speak": string, "done": bool, "actions": [] }.
- Ask concise questions when inputs are missing; apply sensible defaults (date=today, serving="1 serving").
- Emit actions ONLY when ready to update or read the DB.
- Allowed actions:
  - set_goal {calories, protein_g, carbs_g, fat_g}
  - add_food {name, serving_desc, cal, protein, carbs, fat, provenance?}
  - log_meal {date?, items:[{name, qty}]}
  - day_summary {date?}
Never include SQL. Never include extra top-level keys.
"""

def _client():
    return OpenAI()  # uses OPENAI_API_KEY

def chat_once(history):
    messages = [{"role":"system","content":_SYSTEM}] + history
    r = _client().chat.completions.create(
        model=os.getenv("MODEL","gpt-4o-mini"),
        temperature=0,
        messages=messages
    )
    return r.choices[0].message.content

def estimate_food(name:str):
    """Ask the model for a best-average profile & return an add_food action JSON."""
    messages = [
        {"role":"system","content":_SYSTEM},
        {"role":"user","content": f"User mentioned '{name}' which is not in DB. Provide ONE JSON reply that includes exactly one add_food action with average macros for a typical serving. Set provenance='llm_estimate'. Speak a short confirmation."}
    ]
    r = _client().chat.completions.create(
        model=os.getenv("MODEL","gpt-4o-mini"),
        temperature=0,
        messages=messages
    )
    return r.choices[0].message.content
