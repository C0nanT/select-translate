"""Rede: HTTP com urllib (adaptador)."""
import errno
import socket
import urllib.error
import urllib.request

from nucleo import ErroRede

# sem rota / rede fora do ar (OSError puro, nao ConnectionError)
_SEM_ROTA = {errno.ENETUNREACH, errno.EHOSTUNREACH, errno.ENETDOWN, errno.EHOSTDOWN}


def converter_excecao(e):
    """Converte excecao do urllib/socket para o tipo comum ErroRede."""
    if isinstance(e, ErroRede):
        return e
    if isinstance(e, urllib.error.HTTPError):  # antes de URLError, que e a mae
        return ErroRede.http(e.code)
    if isinstance(e, urllib.error.URLError) and isinstance(e.reason, Exception):
        return converter_excecao(e.reason)
    if isinstance(e, TimeoutError):  # inclui socket.timeout
        return ErroRede.tempo_esgotado()
    if isinstance(e, (socket.gaierror, ConnectionError)) or \
            (isinstance(e, OSError) and e.errno in _SEM_ROTA):
        return ErroRede.sem_conexao()
    return ErroRede.outro(str(e) or type(e).__name__)


def busca(url):
    """GET da URL e devolve o corpo; qualquer falha vira ErroRede."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status != 200:
                raise ErroRede.http(r.status)
            return r.read().decode("utf-8")
    except Exception as e:
        raise converter_excecao(e) from e
