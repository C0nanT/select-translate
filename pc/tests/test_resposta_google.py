import json
import os
import sys
import unittest

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(RAIZ, "pc"))
from nucleo import Erro, Traducao, traduzir  # noqa: E402

with open(os.path.join(RAIZ, "casos", "resposta_google.json"), encoding="utf-8") as f:
    CASOS = json.load(f)


# os casos moram em casos/resposta_google.json e valem tambem para o Android (RespostaGoogleTest.kt)
class RespostaGoogleTest(unittest.TestCase):
    def test_casos_compartilhados(self):
        self.assertTrue(CASOS)
        for caso in CASOS:
            with self.subTest(caso=caso["nome"]):
                esp = caso["esperado"]
                r = traduzir("x", lambda _: caso["corpo"])
                if esp["tipo"] == "traducao":
                    self.assertEqual(Traducao(esp["texto"]), r)
                else:
                    self.assertEqual(Erro(esp["motivo"]), r)


if __name__ == "__main__":
    unittest.main()
