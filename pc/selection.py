"""Selection: X11 primary selection; waits for the mouse release, then just passes the text on."""
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk

POLL_MS = 30           # while dragging the mouse: check every POLL_MS whether the button was released


class Selection:
    """Calls on_selected(text) when the selection changes and the mouse was released.

    button_pressed: zero-argument function (comes from the popup, which can read the pointer).
    Ignoring repeated text is done in App.on_text, not here.
    """

    def __init__(self, button_pressed, on_selected):
        self._button_pressed = button_pressed
        self._on_selected = on_selected
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
        # still dragging the mouse -> wait for release (avoids translating fragments)
        if self._button_pressed():
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
            self._on_selected(text)
