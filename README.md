# translate-selected

Select text in any app (PDF reader, browser, etc.) and see the pt-BR translation in a fixed popup at the bottom of the screen, without copy and paste.

Made for reading English books and only checking the translation when you get stuck on a sentence.

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

Tests: `make test` (PC + Android). To have `git push` run the tests before sending, enable the hook once per clone with `make hooks`. Without Java or the Android SDK the push is blocked; `git push --no-verify` skips the check.

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

## Android (tablet)

App in `android/` with two ways to translate; both open the same popup at the bottom of the screen, over the app:

- **Floating bubble** (works in any reader, including the Files by Google PDF viewer): copy the text and tap the bubble **文**.
- **"Traduzir pt-BR" item** in the selection menu, in apps that show items from other apps in that menu.

Tested on a Lenovo TB336FU with Android 16, reading a PDF in Files by Google.

**Requirements**

- Android 6+
- USB debugging on (only for `make android`)
- Android SDK at `~/Android/Sdk` (or `ANDROID_HOME`) and Java 17+

```bash
make android      # builds the debug APK and installs it on the tablet via USB
make android-apk  # only builds the APK
```

The APK is at `android/app/build/outputs/apk/debug/app-debug.apk`. To install it by hand, copy the file to the tablet, open it in the file manager and allow installing from unknown sources.

**Bubble**

- Turn on: tap the **Tradutor** icon in the app list. The first time, it opens the "Sobrepor a outros apps" screen: enable it for Tradutor and tap the icon again
- On Android 13+, when you turn the bubble on the app asks for notification permission (to show "Toque para desligar"); denying it does not prevent the bubble from working
- Turn off: hold your finger still on the bubble until it vibrates, or tap the "Bolha do Tradutor ligada" notification
- Short tap translates; drag the bubble to move it (past the system touch slop, it neither translates nor turns off)
- The bubble remembers where it was left: when turned on again it returns to the last place, adjusted to the screen (also after rotating or switching devices)
- After the tablet restarts, the bubble does not come back on its own: tap the icon again
- Android shows "Tradutor colou da área de transferência" on every translation; this is expected

**Usage**

- Copy the text and tap the bubble (or select and tap "Traduzir pt-BR" in the menu) -> "Traduzindo…" appears, then the translation
- Hides by itself in 15 s; the bar at the bottom shows the remaining time
- Holding a finger on the popup pauses the time
- Hold still until it vibrates, then drag to move the popup; the next ones open there (dragging without holding scrolls the text)
- Tap outside -> the popup closes
- Request failure -> red popup with the reason
- Text over 3000 characters -> "Texto grande demais (N caracteres)" warning

**PDF readers:** the Files by Google PDF viewer has its own selection menu (only "Copiar" and "Selecionar tudo"), so "Traduzir pt-BR" does not appear there: use the bubble. In the browser the item also did not appear in the first test; not investigated yet.

**Configuration**

Constants in `android/app/src/main/java/com/conan/translator/Config.kt` (`HIDE_AFTER_S`, `POPUP_CHARS`) and, for the translation rules, in the core at `android/core/src/main/kotlin/com/conan/translator/Limits.kt` (`MAX_CHARS`, `MAX_URL`):

| Constant | Default | What it does |
|---|---|---|
| `HIDE_AFTER_S` | 15 | the popup hides by itself after this time |
| `MAX_CHARS` | 3000 | selections larger than this (counted by code point: an emoji counts as 1) show the "Texto grande demais" warning |
| `MAX_URL` | 8000 | cap on the already-encoded URL (accents and emoji inflate it); above it, shows the same warning. Conservative value, not yet measured on the device |
| `POPUP_CHARS` | 80 | maximum popup width, in characters |

Warnings in the red popup when tapping the bubble: "Nada copiado" (clipboard empty, holding an image/file, or reading blocked) and "Nada para traduzir" (text with no letters, such as "42"; no request is made). From the "Traduzir pt-BR" menu, these cases close without showing anything.

After changing these, run `make android`.

**Privacy:** text is only sent to Google Translate when you tap the bubble or "Traduzir pt-BR", not on every selection or copy.

## Development

The translation rules exist in two versions, one per platform, organized like this:

- **Core**: pure rules, no UI and no network, one copy per language: `pc/core.py` (Python) and `android/core/` (Kotlin, a Gradle module without Android).
- **Adapters**: what is specific to each platform. On PC: `pc/selection.py` (X11 selection), `pc/popup.py` (GTK window), `pc/network.py` (HTTP) and `pc/translator.py` (wires everything together). On Android: `android/app/` (bubble, popup, Quick Settings tile, selection menu and HTTP).
- **`cases/`**: JSON files with input -> expected output. The PC and Android tests read the same files, so they are the single source of truth for behavior: if one side changes without the other, the test breaks.

**Rule: when behavior changes, change the case first.** Write or adjust the case in `cases/` and only then the code in both languages. The stopwatch and position clamping do not use `cases/`: they have direct tests in each language.

| Command | What it does |
|---|---|
| `make test` | PC and Android tests |
| `make test-pc` | PC tests only |
| `make test-android` | Android tests only (core and app, via Gradle) |
| `make hooks` | enables the pre-push hook versioned in `hooks/`, which runs `make test` before each `git push`. Run once per clone; repeating it is safe |

Without Java or the Android SDK the push is blocked with a clear message; `git push --no-verify` skips the check.

**Why two languages:** unifying (Kotlin on both sides, or another language) was evaluated and postponed. The core is small (~100 lines) and switching would require Java + JNA on the PC. Reevaluate if the core grows (multiple translation services, language choice, history).
