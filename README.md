# translate-selected

Select text in any app (PDF reader, browser, etc.) and see the pt-BR translation in a fixed popup at the bottom of the screen, without copy and paste.

Made for reading English books and only checking the translation when you get stuck on a sentence.

**Android (tablet, Kotlin):** https://github.com/C0nanT/translate-selected-android

## Requirements

- Linux with an **X11** session (does not work on Wayland)
- Python 3 + GTK 3 (`python3-gi`), already included in Ubuntu/GNOME
- Internet access (uses the free Google Translate endpoint)

## Usage

```bash
make start    # runs attached to the terminal
```

Ctrl+C or closing the terminal stops it.

Or directly: `python3 pc/translator.py`.

Tests: `make test`. To have `git push` run the tests before sending, enable the hook once per clone with `make hooks`; `git push --no-verify` skips the check.

- Select the text -> "Traduzindo…" appears, then the translation
- Click anywhere -> the popup closes
- Hold and drag the popup to move it; the next ones open there (saved in `~/.config/translate-selected.json`; delete the file to go back to the default)
- If the request fails, the popup turns red with the reason

While it is running, **any** selected text is sent to Google Translate.

## Configuration

Constants at the top of `pc/popup.py` (`HIDE_AFTER_S`, `POPUP_CHARS`, `CLICK_HIDE_MS`, `MARGIN`), `pc/core.py` (`MAX_CHARS`) and `pc/selection.py` (`POLL_MS`):

| Constant | Default | What it does |
|---|---|---|
| `POLL_MS` | 30 | while the mouse button is down, checks every so often whether it has been released (only then translates) |
| `HIDE_AFTER_S` | 15 | the popup hides by itself after this time |
| `MAX_CHARS` | 3000 | ignores selections larger than this |
| `POPUP_CHARS` | 80 | maximum popup width, in characters |
| `CLICK_HIDE_MS` | 0 | delay before closing after a click |
| `MARGIN` | 8 | distance from the popup to the screen edge |

## Development

- **Core**: pure rules, no UI and no network: `pc/core.py`.
- **Adapters**: what is specific to the platform: `pc/selection.py` (X11 selection), `pc/popup.py` (GTK window), `pc/network.py` (HTTP) and `pc/translator.py` (wires everything together).
- **`cases/`**: JSON files with input -> expected output, read by the tests. They are the single source of truth for behavior.

**Rule: when behavior changes, change the case first.** Write or adjust the case in `cases/` and only then the code. The stopwatch and position clamping do not use `cases/`: they have direct tests.

**`cases/` is duplicated in the [Android repo](https://github.com/C0nanT/translate-selected-android)**, whose Kotlin core follows the same rules. When a case changes here, copy the change there too (and vice versa), or the two versions drift apart.

| Command | What it does |
|---|---|
| `make test` | unit tests (no GTK/network) |
| `make hooks` | enables the pre-push hook versioned in `hooks/`, which runs `make test` before each `git push`. Run once per clone; repeating it is safe |

**Why two languages:** unifying (Kotlin on both sides, or another language) was evaluated and postponed. The core is small (~100 lines) and switching would require Java + JNA on the PC. Reevaluate if the core grows (multiple translation services, language choice, history).
