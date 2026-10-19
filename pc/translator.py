#!/usr/bin/env python3
"""Selection translator: select text in any app -> popup with the pt-BR translation.

Usage: python3 pc/translator.py   (Ctrl+C in the terminal to stop)
"""
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from core import TooLarge, Translation, join_lines, translate, validate  # noqa: E402
from popup import Popup  # noqa: E402
from network import fetch  # noqa: E402
from selection import Selection  # noqa: E402


class App:
    def __init__(self):
        self.popup = Popup()
        self.last = ""
        self.selection = Selection(self.popup.button_pressed, self.on_text)

    def on_text(self, text):
        text = join_lines(text)  # joins PDF line breaks; the size limit applies afterwards
        if text == self.last:
            return
        invalid = validate(text)
        if isinstance(invalid, TooLarge):  # red warning, no network
            self.last = text
            self.popup.show_text(text, "⚠ " + invalid.message, state="error")
            return
        if invalid is not None:  # empty or no letters: no popup
            return
        self.last = text
        self.popup.show_text(text, "", state="loading")
        threading.Thread(target=self.worker, args=(text,), daemon=True).start()

    def worker(self, text):
        r = translate(text, fetch)
        if isinstance(r, Translation):
            result, error = r.text, False
        elif isinstance(r, TooLarge):  # URL too large once encoded
            result, error = "⚠ " + r.message, True
        else:  # Failure (Empty/NoLetters already filtered out in on_text)
            result, error = "⚠ " + r.reason, True
        GLib.idle_add(self.done, text, result, error)

    def done(self, text, result, error):
        # user clicked (closed) while loading, or already selected something else
        if not self.popup.get_visible() or text != self.last:
            if error and text == self.last:
                self.last = ""
            return
        if error:
            self.last = ""  # allows retrying with the same selection
            self.popup.show_text(text, result, state="error")
        else:
            self.popup.show_text(text, result)


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    App()
    print("Tradutor ativo. Selecione texto. Ctrl+C para sair.")
    Gtk.main()
