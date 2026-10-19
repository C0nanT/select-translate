import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def load_cases(name):
    with open(os.path.join(ROOT, "cases", name), encoding="utf-8") as f:
        return json.load(f)
