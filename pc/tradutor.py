#!/usr/bin/env python3
"""Tradutor de selecao: selecione texto em qualquer app -> popup com traducao pt-BR.

Uso: python3 pc/tradutor.py   (Ctrl+C no terminal para parar)
"""
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from nucleo import TooLarge, Translation, join_lines, translate, validate  # noqa: E402
from popup import Popup  # noqa: E402
from rede import fetch  # noqa: E402
from selecao import Selecao  # noqa: E402


class App:
    def __init__(self):
        self.popup = Popup()
        self.last = ""
        self.selecao = Selecao(self.popup.botao_apertado, self.on_text)

    def on_text(self, text):
        text = join_lines(text)  # junta quebras de linha do PDF; limite vale depois
        if text == self.last:
            return
        invalid = validate(text)
        if isinstance(invalid, TooLarge):  # aviso vermelho, sem rede
            self.last = text
            self.popup.show_text(text, "⚠ " + invalid.message, state="error")
            return
        if invalid is not None:  # vazio ou sem letras: nao abre popup
            return
        self.last = text
        self.popup.show_text(text, "", state="loading")
        threading.Thread(target=self.worker, args=(text,), daemon=True).start()

    def worker(self, text):
        r = translate(text, fetch)
        if isinstance(r, Translation):
            result, error = r.text, False
        elif isinstance(r, TooLarge):  # URL grande demais depois de codificada
            result, error = "⚠ " + r.message, True
        else:  # Failure (Empty/NoLetters ja filtrados em on_text)
            result, error = "⚠ " + r.reason, True
        GLib.idle_add(self.done, text, result, error)

    def done(self, text, result, error):
        # usuario clicou (fechou) durante carregamento, ou ja selecionou outra coisa
        if not self.popup.get_visible() or text != self.last:
            if error and text == self.last:
                self.last = ""
            return
        if error:
            self.last = ""  # permite tentar de novo com a mesma selecao
            self.popup.show_text(text, result, state="error")
        else:
            self.popup.show_text(text, result)


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    App()
    print("Tradutor ativo. Selecione texto. Ctrl+C para sair.")
    Gtk.main()
