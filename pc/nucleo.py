"""Nucleo: regras puras, sem GTK e sem rede."""
import json
import re
import urllib.parse
from collections import namedtuple

MAX_CHARS = 3000
# teto da URL ja codificada; igual a MAX_URL de Limites.kt (valor conservador, nao medido)
MAX_URL = 8000
IDIOMA_DESTINO = "pt"


# Copia da juntarLinhas de android/nucleo/src/main/kotlin/com/conan/tradutor/Tradutor.kt: manter as duas iguais,
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


# --- traduzir: validacao + URL + resposta, com a busca HTTP vinda de fora ---
# Copia de Tradutor.kt (traduzir/urlTraducao), conferida por casos/validacao.json.
class _Marca:
    def __init__(self, nome):
        self.nome = nome

    def __repr__(self):
        return self.nome


Vazio = _Marca("Vazio")
SemLetras = _Marca("SemLetras")
Traducao = namedtuple("Traducao", "texto")
Erro = namedtuple("Erro", "motivo")


class GrandeDemais(namedtuple("GrandeDemais", "n")):
    @property
    def mensagem(self):
        return f"Texto grande demais ({self.n} caracteres)"


# Contrato entre o adaptador de rede e o nucleo (igual a ErroRede em Tradutor.kt):
# a busca lanca ErroRede; o adaptador converte as excecoes da plataforma (ver rede.py).
# tipo: "tempo_esgotado", "sem_conexao", "http" (+ codigo) ou "outro" (+ detalhe).
class ErroRede(Exception):
    def __init__(self, tipo, codigo=None, detalhe=None):
        super().__init__(tipo)
        self.tipo = tipo
        self.codigo = codigo
        self.detalhe = detalhe

    @classmethod
    def tempo_esgotado(cls):
        return cls("tempo_esgotado")

    @classmethod
    def sem_conexao(cls):
        return cls("sem_conexao")

    @classmethod
    def http(cls, codigo):
        return cls("http", codigo=codigo)

    @classmethod
    def outro(cls, detalhe):
        return cls("outro", detalhe=detalhe)

    @property
    def mensagem(self):  # unico lugar das mensagens de erro de rede
        if self.tipo == "tempo_esgotado":
            return "Tempo esgotado"
        if self.tipo == "sem_conexao":
            return "Sem conexão com a internet"
        if self.tipo == "http":
            return f"Erro do servidor (HTTP {self.codigo})"
        return self.detalhe


def url_traducao(texto):
    # Regra unica de codificacao do q (iguala Python e Java): RFC 3986. Ficam crus
    # so A-Z a-z 0-9 - . _ ~ ; espaco vira +; todo o resto vira %XX em UTF-8.
    # Divergiam em ~ (Java: %7E) e * (Java: cru, Python: %2A); o Kotlin e que se ajusta.
    q = urllib.parse.quote_plus(texto, safe="", encoding="utf-8")
    return ("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto"
            f"&tl={IDIOMA_DESTINO}&dt=t&q={q}")


def validar(texto):
    """Vazio, SemLetras, GrandeDemais(n) ou None se o texto (ja com linhas juntadas) serve."""
    if not texto.strip():
        return Vazio
    if not any(c.isalpha() for c in texto):
        return SemLetras
    if len(texto) > MAX_CHARS:  # str conta code points: emoji vale 1
        return GrandeDemais(len(texto))
    return None


def _motivo(e):
    if isinstance(e, ErroRede):
        return e.mensagem
    return str(e) or type(e).__name__  # excecao fora do contrato: trata como "outro"


def _extrair(corpo):
    dados = json.loads(corpo)
    # so listas: str e dict tambem se indexam em Python, mas o Kotlin (e a API) so aceitam lista
    if not isinstance(dados, list) or not isinstance(dados[0], list):
        raise ValueError("formato inesperado")
    out = []
    for parte in dados[0]:
        if not isinstance(parte, list):
            raise ValueError("parte invalida")
        p = parte[0]
        if p is not None and not isinstance(p, str):
            raise ValueError("parte invalida")
        out.append(p or "")
    return "".join(out)


def traduzir(bruto, busca):
    """busca(url) -> corpo (str); lanca excecao em falha de rede (ErroRede)."""
    texto = juntar_linhas(bruto)
    invalido = validar(texto)
    if invalido is not None:
        return invalido
    url = url_traducao(texto)
    if len(url) > MAX_URL:
        return GrandeDemais(len(texto))  # n e <= MAX_CHARS: conta caracteres, nao a URL
    try:
        corpo = busca(url)
    except Exception as e:
        return Erro(_motivo(e))
    try:
        return Traducao(_extrair(corpo))
    except Exception:
        return Erro("Resposta inesperada do Google Tradutor")
