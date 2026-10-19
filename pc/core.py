"""Core: pure rules, no GTK and no network."""
import json
import re
import urllib.parse
from collections import namedtuple

MAX_CHARS = 3000
# cap on the already-encoded URL; equal to MAX_URL in Limits.kt (conservative value, not measured)
MAX_URL = 8000
TARGET_LANGUAGE = "pt"


# Copy of joinLines in android/core/src/main/kotlin/com/conan/translator/Translator.kt: keep both equal,
# checked by the shared cases in cases/join_lines.json.
# Text copied from a PDF has \n at every line end (and a hyphen in split words);
# joins the lines, a blank line still separates paragraphs.
def join_lines(text):
    def hyphen(m):  # dis-|tributed drops the hyphen; Monolith-|To keeps it
        return "" if m.group(1).islower() else "-"

    paragraphs = re.split(r"\n[ \t]*\n\s*", text.replace("\r\n", "\n"))
    out = []
    for par in paragraphs:
        par = re.sub(r"-[ \t]*\n[ \t]*(?=(.?))", hyphen, par)
        par = re.sub(r"[ \t]*\n[ \t]*", " ", par)
        par = re.sub(r"[ \t]{2,}", " ", par)
        out.append(par.strip())
    return "\n\n".join(out)


# Copy of Stopwatch.kt: time left on the popup. No clock: the "now" (ms)
# comes in on each call. States: idle (loading), running, paused (mouse over).
class Stopwatch:
    def __init__(self, total_ms):
        self.total_ms = total_ms
        self.remaining_ms = total_ms
        self.started = False
        self._paused = False
        self._last = 0

    @property
    def finished(self):
        return self.started and self.remaining_ms <= 0

    @property
    def fraction(self):
        return min(1.0, max(0.0, self.remaining_ms / self.total_ms))

    def start(self, now):
        # full time; if paused, it only runs on resume
        self.remaining_ms = self.total_ms
        self.started = True
        self._last = now

    def stop(self):
        # back to "loading"; the pause still applies
        self.remaining_ms = self.total_ms
        self.started = False

    def pause(self, now):
        self.elapse(now)
        self._paused = True

    def resume(self, now):
        if not self._paused:
            return
        self._paused = False
        self._last = now

    def elapse(self, now):
        if self.started and not self._paused:
            self.remaining_ms = max(0, self.remaining_ms - (now - self._last))
            self._last = now
        return self.remaining_ms


Size = namedtuple("Size", "width height")
Position = namedtuple("Position", "x y")


def _limit(v, lo, hi):
    return max(lo, min(v, hi))


# Copy of clampPosition in Position.kt: keeps the window inside the screen.
# centered_x=False: x is the distance from the left edge; True: offset from the center.
# y goes from 0 to (screen - window).
def clamp_position(pos, screen, window, centered_x):
    slack_x = max(0, screen.width - window.width)
    if centered_x:
        x = _limit(pos.x, -(slack_x // 2), slack_x // 2)
    else:
        x = _limit(pos.x, 0, slack_x)
    y = _limit(pos.y, 0, max(0, screen.height - window.height))
    return Position(x, y)


# --- translate: validation + URL + response, with the HTTP fetch coming from outside ---
# Copy of Translator.kt (translate/translationUrl), checked by cases/validation.json.
class _Marker:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


Empty = _Marker("Empty")
NoLetters = _Marker("NoLetters")
Translation = namedtuple("Translation", "text")
Failure = namedtuple("Failure", "reason")


class TooLarge(namedtuple("TooLarge", "n")):
    @property
    def message(self):
        return f"Texto grande demais ({self.n} caracteres)"


# Contract between the network adapter and the core (equal to NetworkError in Translator.kt):
# fetch raises NetworkError; the adapter converts platform exceptions (see network.py).
# kind: "timeout", "no_connection", "http" (+ code) or "other" (+ detail).
class NetworkError(Exception):
    def __init__(self, kind, code=None, detail=None):
        super().__init__(kind)
        self.kind = kind
        self.code = code
        self.detail = detail

    @classmethod
    def timeout(cls):
        return cls("timeout")

    @classmethod
    def no_connection(cls):
        return cls("no_connection")

    @classmethod
    def http(cls, code):
        return cls("http", code=code)

    @classmethod
    def other(cls, detail):
        return cls("other", detail=detail)

    @property
    def message(self):  # the only place for network error messages (user-facing, pt-BR)
        if self.kind == "timeout":
            return "Tempo esgotado"
        if self.kind == "no_connection":
            return "Sem conexão com a internet"
        if self.kind == "http":
            return f"Erro do servidor (HTTP {self.code})"
        return self.detail


def translation_url(text):
    # Single encoding rule for q (makes Python and Java agree): RFC 3986. Only
    # A-Z a-z 0-9 - . _ ~ stay raw; space becomes +; everything else becomes %XX in UTF-8.
    # They diverged on ~ (Java: %7E) and * (Java: raw, Python: %2A); Kotlin is the one that adjusts.
    q = urllib.parse.quote_plus(text, safe="", encoding="utf-8")
    return ("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto"
            f"&tl={TARGET_LANGUAGE}&dt=t&q={q}")


def validate(text):
    """Empty, NoLetters, TooLarge(n) or None if the text (lines already joined) is fine."""
    if not text.strip():
        return Empty
    if not any(c.isalpha() for c in text):
        return NoLetters
    if len(text) > MAX_CHARS:  # str counts code points: an emoji is 1
        return TooLarge(len(text))
    return None


def _reason(e):
    if isinstance(e, NetworkError):
        return e.message
    return str(e) or type(e).__name__  # exception outside the contract: treated as "other"


def _extract(body):
    data = json.loads(body)
    # lists only: str and dict also index in Python, but Kotlin (and the API) only accept lists
    if not isinstance(data, list) or not isinstance(data[0], list):
        raise ValueError("unexpected format")
    out = []
    for part in data[0]:
        if not isinstance(part, list):
            raise ValueError("invalid part")
        p = part[0]
        if p is not None and not isinstance(p, str):
            raise ValueError("invalid part")
        out.append(p or "")
    return "".join(out)


def translate(raw, fetch):
    """fetch(url) -> body (str); raises an exception on network failure (NetworkError)."""
    text = join_lines(raw)
    invalid = validate(text)
    if invalid is not None:
        return invalid
    url = translation_url(text)
    if len(url) > MAX_URL:
        return TooLarge(len(text))  # n is <= MAX_CHARS: counts characters, not the URL
    try:
        body = fetch(url)
    except Exception as e:
        return Failure(_reason(e))
    try:
        return Translation(_extract(body))
    except Exception:
        return Failure("Resposta inesperada do Google Tradutor")
