import json
from datetime import datetime
from pathlib import Path


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def load_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {path}. Copy config.json and fill in your keys.")
    with open(p) as f:
        return json.load(f)
