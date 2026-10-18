import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tradutor import juntar_linhas  # noqa: E402


# mesmos casos de TradutorTest.kt (android)
class JuntarLinhasTest(unittest.TestCase):
    def test_quebra_simples_vira_espaco(self):
        self.assertEqual("has a whole host of advantages", juntar_linhas("has a whole\nhost of advantages"))

    def test_hifen_no_fim_da_linha_junta_palavra(self):
        self.assertEqual("associated with distributed systems", juntar_linhas("associated with dis-\ntributed systems"))

    def test_hifen_antes_de_maiuscula_fica(self):
        self.assertEqual("Monolith-To", juntar_linhas("Monolith-\nTo"))

    def test_linha_em_branco_separa_paragrafos(self):
        self.assertEqual("um dois\n\ntres", juntar_linhas("um\ndois\n\n\ntres"))

    def test_crlf_e_espacos_na_quebra(self):
        self.assertEqual("a b c", juntar_linhas("a  \r\n  b\r\nc"))


if __name__ == "__main__":
    unittest.main()
