import json
import os
import sys
import unittest

RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, RAIZ)
from tradutor import juntar_linhas  # noqa: E402

with open(os.path.join(RAIZ, "casos", "juntar_linhas.json"), encoding="utf-8") as f:
    CASOS = json.load(f)


# os casos moram em casos/juntar_linhas.json e valem tambem para o Android (TradutorTest.kt)
class JuntarLinhasTest(unittest.TestCase):
    def test_casos_compartilhados(self):
        self.assertTrue(CASOS)
        for caso in CASOS:
            with self.subTest(caso=caso["nome"]):
                self.assertEqual(caso["esperado"], juntar_linhas(caso["entrada"]),
                                 "caso quebrado: " + caso["nome"])


if __name__ == "__main__":
    unittest.main()
