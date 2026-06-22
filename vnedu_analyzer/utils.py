import os
from .config import SUBJECT_TEMPLATES

def safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def ensure_period(s):
    if not s:
        return s
    s = s.strip()
    if s and s[-1] not in [".", "!", "?", "。"]:
        return s + "."
    return s

def load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

def get_subject_template(sub_name):
    if not sub_name:
        return None
    if sub_name in SUBJECT_TEMPLATES:
        return SUBJECT_TEMPLATES[sub_name]
    for key, template in SUBJECT_TEMPLATES.items():
        if key in sub_name or sub_name in key:
            return template
    return None
