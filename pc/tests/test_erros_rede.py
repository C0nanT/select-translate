import json
import os
import socket
import sys
import unittest
import urllib.error
from unittest import mock

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(RAIZ, "pc"))
from nucleo import Erro, ErroRede, traduzir  # noqa: E402
import rede  # noqa: E402

with open(os.path.join(RAIZ, "casos", "erros_rede.json"), encoding="utf-8") as f:
    CASOS = json.load(f)


def falha(d):
    if d["tipo"] == "tempo_esgotado":
        return ErroRede.tempo_esgotado()
    if d["tipo"] == "sem_conexao":
        return ErroRede.sem_conexao()
    if d["tipo"] == "http":
        return ErroRede.http(d["codigo"])
    return ErroRede.outro(d["detalhe"])


# os casos moram em casos/erros_rede.json e valem tambem para o Android (TradutorTest.kt)
class MensagensTest(unittest.TestCase):
    def test_casos_compartilhados(self):
        self.assertTrue(CASOS)
        for caso in CASOS:
            with self.subTest(caso=caso["nome"]):
                def busca(_):
                    raise falha(caso["falha"])
                self.assertEqual(Erro(caso["esperado"]), traduzir("x", busca))

    def test_excecao_desconhecida_vira_outro(self):
        def busca(_):
            raise OSError("boom")
        self.assertEqual(Erro("boom"), traduzir("x", busca))


class ConversaoTest(unittest.TestCase):
    def tipo(self, e):
        r = rede.converter_excecao(e)
        self.assertIsInstance(r, ErroRede)
        return (r.tipo, r.codigo, r.detalhe)

    def test_timeout(self):
        self.assertEqual(("tempo_esgotado", None, None), self.tipo(TimeoutError()))
        self.assertEqual(("tempo_esgotado", None, None), self.tipo(socket.timeout()))
        self.assertEqual(("tempo_esgotado", None, None),
                         self.tipo(urllib.error.URLError(TimeoutError())))

    def test_sem_conexao(self):
        for e in (urllib.error.URLError(socket.gaierror(-2, "Name or service not known")),
                  urllib.error.URLError(ConnectionRefusedError(111, "refused")),
                  urllib.error.URLError(OSError(101, "Network is unreachable")),
                  urllib.error.URLError(OSError(113, "No route to host")),
                  ConnectionResetError()):
            with self.subTest(e=e):
                self.assertEqual(("sem_conexao", None, None), self.tipo(e))

    def test_http(self):
        e = urllib.error.HTTPError("u", 503, "x", {}, None)
        self.assertEqual(("http", 503, None), self.tipo(e))

    def test_resto_vira_outro_com_detalhe(self):
        self.assertEqual(("outro", None, "boom"), self.tipo(ValueError("boom")))
        self.assertEqual(("outro", None, "ValueError"), self.tipo(ValueError()))

    def test_busca_converte_excecoes_do_urllib(self):
        erro = urllib.error.URLError(socket.gaierror(-2, "x"))
        with mock.patch("urllib.request.urlopen", side_effect=erro):
            with self.assertRaises(ErroRede) as c:
                rede.busca("http://x")
        self.assertEqual("sem_conexao", c.exception.tipo)

    def test_status_diferente_de_200_vira_http(self):
        r = mock.MagicMock()
        r.__enter__.return_value = r
        r.status = 204
        with mock.patch("urllib.request.urlopen", return_value=r):
            with self.assertRaises(ErroRede) as c:
                rede.busca("http://x")
        self.assertEqual(("http", 204), (c.exception.tipo, c.exception.codigo))


if __name__ == "__main__":
    unittest.main()
