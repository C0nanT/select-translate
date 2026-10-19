import json
import os

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")


def carregar(nome):
    with open(os.path.join(RAIZ, "casos", nome), encoding="utf-8") as f:
        return json.load(f)
