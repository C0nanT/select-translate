"""Selecao: selecao primaria do X11, espera soltar o mouse, so repassa o texto."""
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk

POLL_MS = 30           # arrastando mouse -> checa a cada POLL_MS se soltou o botao


class Selecao:
    """Chama ao_selecionar(texto) quando a selecao muda e o mouse foi solto.

    botao_apertado: funcao sem argumentos (vem do popup, que sabe ler o ponteiro).
    Ignorar texto repetido e feito em App.on_text, nao aqui.
    """

    def __init__(self, botao_apertado, ao_selecionar):
        self._botao_apertado = botao_apertado
        self._ao_selecionar = ao_selecionar
        self.pending = None
        self._polling = False
        self.cb = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        self.cb.connect("owner-change", self.on_change)

    def on_change(self, *_):
        if self.pending:
            GLib.source_remove(self.pending)
        self._polling = False
        self.pending = GLib.idle_add(self.read_selection)

    def read_selection(self):
        # ainda arrastando o mouse -> espera soltar (evita traduzir pedacos)
        if self._botao_apertado():
            if self.pending and not self._polling:
                self._polling = True
                self.pending = GLib.timeout_add(POLL_MS, self.read_selection)
                return False
            return True
        self.pending = None
        self._polling = False
        self.cb.request_text(self._on_text)
        return False

    def _on_text(self, _cb, text):
        if text:
            self._ao_selecionar(text)
