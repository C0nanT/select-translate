"""Network: HTTP with urllib (adapter)."""
import errno
import socket
import urllib.error
import urllib.request

from core import NetworkError

# no route / network down (plain OSError, not ConnectionError)
_NO_ROUTE = {errno.ENETUNREACH, errno.EHOSTUNREACH, errno.ENETDOWN, errno.EHOSTDOWN}


def convert_exception(e):
    """Converts a urllib/socket exception to the common NetworkError type."""
    if isinstance(e, NetworkError):
        return e
    if isinstance(e, urllib.error.HTTPError):  # before URLError, which is its parent
        return NetworkError.http(e.code)
    if isinstance(e, urllib.error.URLError) and isinstance(e.reason, Exception):
        return convert_exception(e.reason)
    if isinstance(e, TimeoutError):  # includes socket.timeout
        return NetworkError.timeout()
    if isinstance(e, (socket.gaierror, ConnectionError)) or \
            (isinstance(e, OSError) and e.errno in _NO_ROUTE):
        return NetworkError.no_connection()
    return NetworkError.other(str(e) or type(e).__name__)


def fetch(url):
    """GET the URL and return the body; any failure becomes NetworkError."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status != 200:
                raise NetworkError.http(r.status)
            return r.read().decode("utf-8")
    except Exception as e:
        raise convert_exception(e) from e
