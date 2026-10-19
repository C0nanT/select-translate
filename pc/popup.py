"""Popup: janela GTK (adaptador de tela)."""
import json
import os

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk, Pango

HIDE_AFTER_S = 15      # popup some sozinho (pausa com mouse em cima)
TICK_MS = 50           # passo da barra de tempo
POPUP_CHARS = 80       # largura maxima do popup, em caracteres
CLICK_HIDE_MS = 0      # apos clicar na tela, popup some nesse tempo
MARGIN = 8             # distancia da borda da tela
DRAG_PX = 4            # mexer menos que isso = clique (fecha), nao arrasto
POS_FILE = os.path.expanduser("~/.config/select-translate.json")  # posicao arrastada
BUTTONS = (Gdk.ModifierType.BUTTON1_MASK | Gdk.ModifierType.BUTTON2_MASK
           | Gdk.ModifierType.BUTTON3_MASK)


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

        # clique fecha; segurar e arrastar move (POPUP nao tem WM -> move na mao)
        frame = Gtk.EventBox()
        frame.add_events(Gdk.EventMask.BUTTON_MOTION_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        frame.connect("button-press-event", self._press)
        frame.connect("motion-notify-event", self._motion)
        frame.connect("button-release-event", self._release)
        self._drag = None
        # ancora = ponto de baixo, no centro (x, y da tela): popup cresce p/ cima
        self._anchor = self._load_anchor()
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

        # posicao fixa: embaixo no centro, ou onde foi arrastado por ultimo
        _, nat = self.get_preferred_size()
        w, h = nat.width, nat.height
        if self._anchor:
            cx, bottom = self._anchor
            area = self._workarea(cx, bottom - 1)
        else:
            _, px, py, _ = self._pointer()
            area = self._workarea(px, py)
            cx, bottom = area.x + area.width // 2, area.y + area.height - MARGIN
        # sem sair da tela (monitor mudou, popup mais alto...)
        x = min(max(cx - w // 2, area.x + MARGIN), area.x + area.width - w - MARGIN)
        y = min(max(bottom - h, area.y + MARGIN), area.y + area.height - h - MARGIN)
        self.move(x, y)
        self.show()

        self._cancel_timers()
        self._left_ms = HIDE_AFTER_S * 1000
        self._hide_id = GLib.timeout_add(TICK_MS, self._tick)
        self._was_pressed = self._pointer()[3] & BUTTONS
        self._poll_id = GLib.timeout_add(100, self._watch_click)

    def _workarea(self, x, y):
        # area util do monitor no ponto (sem painel/dock)
        return Gdk.Display.get_default().get_monitor_at_point(x, y).get_workarea()

    def _press(self, _w, ev):
        if ev.button == 1:
            self._drag = (ev.x_root, ev.y_root, *self.get_position(), False)
        return True

    def _motion(self, _w, ev):
        if not self._drag:
            return False
        rx, ry, wx, wy, moved = self._drag
        dx, dy = ev.x_root - rx, ev.y_root - ry
        if not moved and max(abs(dx), abs(dy)) < DRAG_PX:
            return True
        self._drag = (rx, ry, wx, wy, True)
        self.move(int(wx + dx), int(wy + dy))
        return True

    def _release(self, _w, ev):
        drag, self._drag = self._drag, None
        if not drag or not drag[4]:
            self._auto_hide()  # clique sem arrastar -> fecha
            return True
        x, y = self.get_position()
        w, h = self.get_size()
        self._anchor = (x + w // 2, y + h)
        self._save_anchor()
        return True

    def _load_anchor(self):
        try:
            with open(POS_FILE) as f:
                pos = json.load(f)
            return int(pos["x"]), int(pos["y"])
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _save_anchor(self):
        try:
            os.makedirs(os.path.dirname(POS_FILE), exist_ok=True)
            with open(POS_FILE, "w") as f:
                json.dump({"x": self._anchor[0], "y": self._anchor[1]}, f)
        except OSError:
            pass  # sem disco -> vale so ate fechar o programa

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
        # (no proprio popup quem decide e o _release: clique fecha, arrasto move)
        pressed = self._pointer()[3] & BUTTONS
        if pressed and not self._was_pressed and not self._hovered():
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

    def botao_apertado(self):
        return bool(self._pointer()[3] & BUTTONS)
