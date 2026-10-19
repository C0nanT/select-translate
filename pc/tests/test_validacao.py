import json
import os
import sys
import unittest

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(RAIZ, "pc"))
from nucleo import (Erro, ErroHttp, GrandeDemais, SemLetras, Traducao,  # noqa: E402
                    Vazio, traduzir, validar)

with open(os.path.join(RAIZ, "casos", "validacao.json"), encoding="utf-8") as f:
    CASOS = json.load(f)

BASE = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=pt&dt=t&q="


def resp(*partes):
    return json.dumps([[[p, "x"] for p in partes], None, "en"])


# os casos moram em casos/validacao.json e valem tambem para o Android (TradutorTest.kt)
class ValidacaoTest(unittest.TestCase):
    def test_casos_compartilhados(self):
        self.assertTrue(CASOS)
        for caso in CASOS:
            with self.subTest(caso=caso["nome"]):
                urls = []

                def busca(url):
                    urls.append(url)
                    return resp("ok")

                vezes = caso.get("vezes", 1)
                r = traduzir(caso["entrada"] * vezes, busca)
                esp = caso["esperado"]
                if esp["tipo"] == "ok":
                    self.assertEqual(Traducao("ok"), r)
                    self.assertEqual([BASE + esp["q"] * vezes], urls)
                    continue
                self.assertEqual([], urls, "nao deve chamar a busca")
                if esp["tipo"] == "grande_demais":
                    self.assertEqual(GrandeDemais(esp["n"]), r)
                else:
                    self.assertIs({"vazio": Vazio, "sem_letras": SemLetras}[esp["tipo"]], r)


class ResultadosTest(unittest.TestCase):
    def test_mensagem_de_grande_demais(self):
        self.assertEqual("Texto grande demais (3001 caracteres)", GrandeDemais(3001).mensagem)

    def test_validar_nao_chama_rede_e_devolve_none_se_ok(self):
        self.assertIs(Vazio, validar("  "))
        self.assertIs(SemLetras, validar("42"))
        self.assertEqual(GrandeDemais(3001), validar("a" * 3001))
        self.assertIsNone(validar("hello"))

    def test_erros_da_busca(self):
        def erro(e):
            def busca(_):
                raise e
            return traduzir("x", busca)

        self.assertEqual(Erro("Tempo esgotado"), erro(TimeoutError()))
        self.assertEqual(Erro("Sem conexão com a internet"), erro(ConnectionError("x")))
        self.assertEqual(Erro("Erro do servidor (HTTP 503)"), erro(ErroHttp(503)))
        self.assertEqual(Erro("boom"), erro(OSError("boom")))



if __name__ == "__main__":
    unittest.main()
