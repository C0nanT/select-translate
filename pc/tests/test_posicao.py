import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from nucleo import Pos, Tamanho, ajustar_posicao  # noqa: E402

TELA = Tamanho(1000, 600)
JANELA = Tamanho(400, 100)


# espelha android/.../PosicaoTest.kt
class PosicaoTest(unittest.TestCase):
    def test_dentro_da_tela_nao_muda(self):
        self.assertEqual(Pos(20, 30), ajustar_posicao(Pos(20, 30), TELA, JANELA, centrada_x=False))

    def test_canto_superior_esquerdo_nao_passa_da_borda_direita_nem_de_baixo(self):
        self.assertEqual(Pos(600, 500), ajustar_posicao(Pos(900, 580), TELA, JANELA, centrada_x=False))
        self.assertEqual(Pos(0, 0), ajustar_posicao(Pos(-50, -5), TELA, JANELA, centrada_x=False))

    def test_centrada_x_mede_desvio_do_centro(self):
        self.assertEqual(Pos(300, 500), ajustar_posicao(Pos(900, 700), TELA, JANELA, centrada_x=True))
        self.assertEqual(Pos(-300, 0), ajustar_posicao(Pos(-900, -10), TELA, JANELA, centrada_x=True))

    def test_janela_maior_que_a_tela_fica_no_canto(self):
        pequena = Tamanho(300, 80)
        self.assertEqual(Pos(0, 0), ajustar_posicao(Pos(50, 50), pequena, JANELA, centrada_x=True))
        self.assertEqual(Pos(0, 0), ajustar_posicao(Pos(50, 50), pequena, JANELA, centrada_x=False))


if __name__ == "__main__":
    unittest.main()
