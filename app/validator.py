# app/validator.py
from typing import List, Dict, Any, Tuple

ALLOWED_ACTIONS = {"set_goal", "add_food", "log_meal", "day_summary"}

def validate_payload(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    # top-level
    if not isinstance(payload, dict):
        return False, ["payload must be a JSON object"]

    if "speak" not in payload or not isinstance(payload.get("speak", ""), str):
        errors.append('missing or invalid "speak" (string)')

    if "done" not in payload or not isinstance(payload.get("done", False), bool):
        errors.append('missing or invalid "done" (bool)')

    actions = payload.get("actions", [])
    if actions is None:
        actions = []
    if not isinstance(actions, list):
        errors.append('"actions" must be an array')

    # each action
    for i, a in enumerate(actions):
        if not isinstance(a, dict):
            errors.append(f"actions[{i}] is not an object")
            continue

        # canonicalize alternate forms like {"set_goal": {...}}
        if "action" not in a:
            for k in list(a.keys()):
                if k in ALLOWED_ACTIONS:
                    a["action"], a["args"] = k, a[k]
                    break

        name = a.get("action")
        args = a.get("args", {})
        if name not in ALLOWED_ACTIONS:
            errors.append(f'actions[{i}].action must be one of {sorted(ALLOWED_ACTIONS)}')
            continue

        if not isinstance(args, dict):
            errors.append(f"actions[{i}].args must be an object")
            continue

        # per-action required args
        if name == "set_goal":
            for k in ["calories", "protein_g", "carbs_g", "fat_g"]:
                if k not in args or not _is_number(args[k]) or float(args[k]) < 0:
                    errors.append(f'actions[{i}].args.{k} missing or invalid (>=0 number)')
        elif name == "add_food":
            for k in ["name", "serving_desc", "cal", "protein", "carbs", "fat"]:
                if k not in args or (k in {"cal","protein","carbs","fat"} and (not _is_number(args[k]) or float(args[k]) < 0)) or (k in {"name","serving_desc"} and not isinstance(args[k], str)):
                    errors.append(f'actions[{i}].args.{k} missing or invalid')
        elif name == "log_meal":
            items = args.get("items")
            if not isinstance(items, list) or not items:
                errors.append(f'actions[{i}].args.items must be a non-empty array')
            else:
                for j, it in enumerate(items):
                    if not isinstance(it, dict) or "name" not in it or not isinstance(it["name"], str):
                        errors.append(f'actions[{i}].args.items[{j}].name missing/invalid')
                    if "qty" in it and (not _is_number(it["qty"]) or float(it["qty"]) <= 0):
                        errors.append(f'actions[{i}].args.items[{j}].qty must be > 0 number if present')
        elif name == "day_summary":
            # no required fields
            pass

    return (len(errors) == 0), errors


def _is_number(x) -> bool:
    try:
        float(x)
        return True
    except Exception:
        return False
