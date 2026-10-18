#!/usr/bin/env python3
"""Tradutor de selecao: selecione texto em qualquer app -> popup com traducao pt-BR.

Uso: python3 tradutor.py   (Ctrl+C no terminal para parar)
"""
import json
import threading
import urllib.parse
import urllib.request

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk, Pango

POLL_MS = 30           # arrastando mouse -> checa a cada POLL_MS se soltou o botao
HIDE_AFTER_S = 15      # popup some sozinho (pausa com mouse em cima)
TICK_MS = 50           # passo da barra de tempo
MAX_CHARS = 3000
POPUP_CHARS = 80       # largura maxima do popup, em caracteres
CLICK_HIDE_MS = 0      # apos clicar na tela, popup some nesse tempo
BUTTONS = (Gdk.ModifierType.BUTTON1_MASK | Gdk.ModifierType.BUTTON2_MASK
           | Gdk.ModifierType.BUTTON3_MASK)


def translate(text, target="pt"):
    url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(
        {"client": "gtx", "sl": "auto", "tl": target, "dt": "t", "q": text}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8"))
    return "".join(part[0] for part in data[0] if part[0])


class Popup(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.POPUP)
        self.set_accept_focus(False)
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.TOOLTIP)
        # fundo transparente -> cantos arredondados sem quina preta
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)

        frame = Gtk.EventBox()
        frame.connect("button-press-event", lambda *_: self.hide())
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            .tp { background: #1e1e2e; border: 1px solid #89b4fa; border-radius: 6px; }
            .tp label { color: #cdd6f4; font-size: 13pt; }
            .tp .orig { color: #7f849c; font-size: 10pt; }
            .tp.error { border-color: #f38ba8; }
            .tp.error label { color: #f38ba8; }
            .tp.error .orig { color: #7f849c; }
            .tp.loading { border-radius: 9px; }
            .tp spinner { color: #89b4fa; min-width: 12px; min-height: 12px; }
            .tp progressbar trough { min-height: 3px; background: #313244; border: none; border-radius: 2px; }
            .tp progressbar progress { min-height: 3px; background: #89b4fa; border: none; border-radius: 2px; }
            .tp.error progressbar progress { background: #f38ba8; }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        frame.get_style_context().add_class("tp")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(10); box.set_margin_bottom(10)
        box.set_margin_start(12); box.set_margin_end(12)
        self.orig = Gtk.Label(xalign=0)
        self.orig.get_style_context().add_class("orig")
        self.trad = Gtk.Label(xalign=0)
        for lbl in (self.orig, self.trad):
            lbl.set_line_wrap(True)
            lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            box.pack_start(lbl, False, False, 0)
        self.orig.set_ellipsize(Pango.EllipsizeMode.END)
        self.orig.set_lines(2)
        self.spinner = Gtk.Spinner()
        box.pack_start(self.spinner, False, False, 0)
        # tempo restante: barra ancorada a direita -> encolhe da esquerda p/ direita
        self.bar = Gtk.ProgressBar(inverted=True)
        box.pack_start(self.bar, False, False, 0)
        self.box = box
        frame.add(box)
        self.add(frame)
        self._hide_id = None

    def show_text(self, original, translated, state=None):
        """state: None (traducao), "loading" ou "error" -> classe CSS."""
        loading = state == "loading"
        self.orig.set_text(original)
        self.trad.set_text(translated)
        ctx = self.get_child().get_style_context()
        for cls in ("loading", "error"):
            (ctx.add_class if cls == state else ctx.remove_class)(cls)
        # label com wrap pede largura minima -> popup fino e alto; forca largura
        width = max(20, min(len(translated), POPUP_CHARS))
        for lbl in (self.orig, self.trad):
            lbl.set_width_chars(width)
            lbl.set_max_width_chars(width)
        self.get_child().show_all()  # filhos visiveis -> medida de tamanho correta
        # carregando -> so o icone girando; senao so os textos
        for lbl in (self.orig, self.trad):
            lbl.set_visible(not loading)
        self.bar.set_visible(not loading)
        self.bar.set_fraction(1.0)
        self.spinner.set_visible(loading)
        (self.spinner.start if loading else self.spinner.stop)()
        m = 3 if loading else 10
        self.box.set_margin_top(m); self.box.set_margin_bottom(m)
        m = 3 if loading else 12
        self.box.set_margin_start(m); self.box.set_margin_end(m)
        self.resize(1, 1)

        # posiciona perto do mouse (fim da selecao), sem sair da tela
        _, x, y, _ = self._pointer()
        mon = Gdk.Display.get_default().get_monitor_at_point(x, y).get_geometry()
        _, nat = self.get_preferred_size()
        w, h = nat.width, nat.height
        right = mon.x + mon.width
        gap = 8 if loading else 15
        # nao cabe a direita -> abre para a esquerda do mouse
        x = x + gap if x + gap + w <= right - 5 else x - w - gap
        x = min(max(x, mon.x + 5), right - w - 5)
        if loading:  # icone na mesma linha do cursor
            y = min(max(y - h // 2, mon.y), mon.y + mon.height - h)
        else:
            y = y + 20 if y + 20 + h < mon.y + mon.height else max(mon.y, y - h - 20)
        self.move(x, y)
        self.show()

        self._cancel_timers()
        self._left_ms = HIDE_AFTER_S * 1000
        self._hide_id = GLib.timeout_add(TICK_MS, self._tick)
        self._was_pressed = self._pointer()[3] & BUTTONS
        self._poll_id = GLib.timeout_add(100, self._watch_click)

    def _pointer(self):
        dev = Gdk.Display.get_default().get_default_seat().get_pointer()
        return Gdk.get_default_root_window().get_device_position(dev)

    def _hovered(self):
        win = self.get_window()
        if not win:
            return False
        _, px, py, _ = self._pointer()
        _, wx, wy = win.get_origin()
        return wx <= px < wx + win.get_width() and wy <= py < wy + win.get_height()

    def _tick(self):
        # mouse em cima -> tempo congela
        if self._hovered():
            return True
        self._left_ms -= TICK_MS
        if self._left_ms <= 0:
            return self._auto_hide()
        self.bar.set_fraction(self._left_ms / (HIDE_AFTER_S * 1000))
        return True

    def _watch_click(self):
        # clique em qualquer lugar da tela -> some apos CLICK_HIDE_MS
        pressed = self._pointer()[3] & BUTTONS
        if pressed and not self._was_pressed:
            self._cancel_timers()
            self._hide_id = GLib.timeout_add(CLICK_HIDE_MS, self._auto_hide)
            return False
        self._was_pressed = pressed
        return True

    def _cancel_timers(self):
        for attr in ("_hide_id", "_poll_id"):
            src = getattr(self, attr, None)
            if src:
                GLib.source_remove(src)
            setattr(self, attr, None)

    def _auto_hide(self):
        self._hide_id = None
        self._cancel_timers()
        self.hide()
        return False


class App:
    def __init__(self):
        self.popup = Popup()
        self.last = ""
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
        if self.popup._pointer()[3] & BUTTONS:
            if self.pending and not self._polling:
                self._polling = True
                self.pending = GLib.timeout_add(POLL_MS, self.read_selection)
                return False
            return True
        self.pending = None
        self._polling = False
        self.cb.request_text(self.on_text)
        return False

    def on_text(self, _cb, text):
        if not text:
            return
        text = " ".join(text.split())  # junta quebras de linha do PDF
        if text == self.last or len(text) > MAX_CHARS or not any(c.isalpha() for c in text):
            return
        self.last = text
        self.popup.show_text(text, "", state="loading")
        threading.Thread(target=self.worker, args=(text,), daemon=True).start()

    def worker(self, text):
        try:
            result, error = translate(text), False
        except Exception as e:
            result, error = f"Falha na requisição de tradução: {e}", True
        GLib.idle_add(self.done, text, result, error)

    def done(self, text, result, error):
        # usuario clicou (fechou) durante carregamento, ou ja selecionou outra coisa
        if not self.popup.get_visible() or text != self.last:
            if error and text == self.last:
                self.last = ""
            return
        if error:
            self.last = ""  # permite tentar de novo com a mesma selecao
            self.popup.show_text(text, "⚠ " + result, state="error")
        else:
            self.popup.show_text(text, result)


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    App()
    print("Tradutor ativo. Selecione texto. Ctrl+C para sair.")
    Gtk.main()
