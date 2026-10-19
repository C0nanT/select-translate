"""Rede: HTTP com urllib (adaptador)."""
import urllib.error
import urllib.request

from nucleo import ErroHttp


def busca(url):
    """GET da URL e devolve o corpo; falhas viram ErroHttp/TimeoutError/ConnectionError."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise ErroHttp(e.code) from e
    except urllib.error.URLError as e:
        if isinstance(e.reason, TimeoutError):
            raise TimeoutError() from e
        raise ConnectionError(str(e.reason)) from e
