import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from nucleo import Cronometro  # noqa: E402


# espelha android/.../CronometroTest.kt
class CronometroTest(unittest.TestCase):
    def test_conta_ate_zero(self):
        c = Cronometro(15_000)
        c.iniciar(1_000)
        self.assertEqual(10_000, c.descontar(6_000))
        self.assertFalse(c.acabou)
        self.assertEqual(0, c.descontar(16_000))
        self.assertTrue(c.acabou)

    def test_pausa_e_retomada_nao_perdem_nem_ganham_tempo(self):
        c = Cronometro(15_000)
        c.iniciar(0)
        c.pausar(4_000)
        self.assertEqual(11_000, c.descontar(60_000))
        c.retomar(60_000)
        self.assertEqual(8_000, c.descontar(63_000))

    def test_reiniciar_enquanto_pausado_nao_corre(self):
        c = Cronometro(15_000)
        c.iniciar(0)
        c.pausar(2_000)
        c.iniciar(5_000)
        self.assertEqual(15_000, c.descontar(50_000))
        self.assertEqual(1.0, c.fracao)
        c.retomar(50_000)
        self.assertEqual(14_000, c.descontar(51_000))

    def test_parado_nao_desconta_e_pausar_retomar_nao_inicia(self):
        c = Cronometro(15_000)
        self.assertEqual(15_000, c.descontar(99_000))
        c.pausar(100_000)
        c.retomar(200_000)
        self.assertEqual(15_000, c.descontar(300_000))
        self.assertFalse(c.acabou)

    def test_reiniciar_volta_ao_total(self):
        c = Cronometro(15_000)
        c.iniciar(0)
        c.descontar(10_000)
        c.iniciar(10_000)
        self.assertEqual(15_000, c.descontar(10_000))

    def test_fracao_da_barra(self):
        c = Cronometro(10_000)
        self.assertEqual(1.0, c.fracao)
        c.iniciar(0)
        c.descontar(2_500)
        self.assertEqual(0.75, c.fracao)
        c.descontar(20_000)
        self.assertEqual(0.0, c.fracao)

    def test_parar_volta_ao_estado_parado_do_carregamento(self):
        c = Cronometro(15_000)
        self.assertFalse(c.iniciado)
        c.iniciar(0)
        c.descontar(5_000)
        self.assertTrue(c.iniciado)
        c.parar()
        self.assertFalse(c.iniciado)
        self.assertEqual(15_000, c.descontar(99_000))
        self.assertFalse(c.acabou)

    def test_resultado_com_mouse_em_cima_depois_de_carregar_so_corre_ao_sair(self):
        c = Cronometro(15_000)
        c.parar()
        c.pausar(1_000)
        c.iniciar(8_000)
        self.assertEqual(15_000, c.descontar(30_000))
        c.retomar(30_000)
        self.assertEqual(13_000, c.descontar(32_000))


if __name__ == "__main__":
    unittest.main()
