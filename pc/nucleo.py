"""Nucleo: regras puras, sem GTK e sem rede."""
import re
from collections import namedtuple

MAX_CHARS = 3000


# Copia da juntarLinhas de android/.../Tradutor.kt: manter as duas iguais,
# conferidas pelos casos compartilhados em casos/juntar_linhas.json.
# Texto copiado de PDF traz \n em cada fim de linha (e hifen em palavra cortada);
# junta as linhas, linha em branco continua separando paragrafos.
def juntar_linhas(texto):
    def hifen(m):  # dis-|tributed some o hifen; Monolith-|To fica
        return "" if m.group(1).islower() else "-"

    pars = re.split(r"\n[ \t]*\n\s*", texto.replace("\r\n", "\n"))
    out = []
    for par in pars:
        par = re.sub(r"-[ \t]*\n[ \t]*(?=(.?))", hifen, par)
        par = re.sub(r"[ \t]*\n[ \t]*", " ", par)
        par = re.sub(r"[ \t]{2,}", " ", par)
        out.append(par.strip())
    return "\n\n".join(out)


# Copia do Cronometro.kt: tempo restante do popup. Sem relogio: o "agora" (ms)
# vem em cada chamada. Estados: parado (carregando), correndo, pausado (mouse em cima).
class Cronometro:
    def __init__(self, total_ms):
        self.total_ms = total_ms
        self.restante_ms = total_ms
        self.iniciado = False
        self._pausado = False
        self._ultimo = 0

    @property
    def acabou(self):
        return self.iniciado and self.restante_ms <= 0

    @property
    def fracao(self):
        return min(1.0, max(0.0, self.restante_ms / self.total_ms))

    def iniciar(self, agora):
        # tempo cheio; se pausado, so corre ao retomar
        self.restante_ms = self.total_ms
        self.iniciado = True
        self._ultimo = agora

    def parar(self):
        # volta a "carregando"; a pausa continua valendo
        self.restante_ms = self.total_ms
        self.iniciado = False

    def pausar(self, agora):
        self.descontar(agora)
        self._pausado = True

    def retomar(self, agora):
        if not self._pausado:
            return
        self._pausado = False
        self._ultimo = agora

    def descontar(self, agora):
        if self.iniciado and not self._pausado:
            self.restante_ms = max(0, self.restante_ms - (agora - self._ultimo))
            self._ultimo = agora
        return self.restante_ms


Tamanho = namedtuple("Tamanho", "largura altura")
Pos = namedtuple("Pos", "x y")


def _limitar(v, lo, hi):
    return max(lo, min(v, hi))


# Copia da ajustarPosicao de Posicao.kt: mantem a janela dentro da tela.
# centrada_x=False: x e a distancia da borda esquerda; True: desvio do centro.
# y vai de 0 a (tela - janela).
def ajustar_posicao(pos, tela, janela, centrada_x):
    sobra_x = max(0, tela.largura - janela.largura)
    if centrada_x:
        x = _limitar(pos.x, -(sobra_x // 2), sobra_x // 2)
    else:
        x = _limitar(pos.x, 0, sobra_x)
    y = _limitar(pos.y, 0, max(0, tela.altura - janela.altura))
    return Pos(x, y)
