<p align="center">
  <img src="assets/banner.png" alt="OpenTuya Sync" width="100%">
</p>

<p align="center">
  <b>English</b> | <a href="README.es.md">Español</a>
</p>

# Bring Ambilight to any Tuya Smart Light

OpenTuya Sync turns your Tuya / Ledvance smart bulbs into a real-time
ambient lighting system for Windows.

**100% Local. No Cloud. Open Source.**

Plugin architecture: several color **sources** (screen, audio, flash,
Spotify, webcam) and several **outputs** (Tuya and its white-label clones,
WLED, Hue), freely combinable. Qt GUI with a device list and manual color
control, minimizes to the system tray instead of closing.

## Demo

<p align="center">
  <img src="assets/demo.gif" alt="OpenTuya Sync demo — the bulb reacting to the screen in real time" width="100%">
</p>

<!--
  TODO: record ~10-15s of a game/movie playing with the real bulb reacting
  next to the monitor, convert to GIF, drop it at assets/demo.gif. GitHub
  renders animated GIFs inline on the repo page — this is the single
  highest-impact thing you can add: show the result in the first 5
  seconds instead of making people read for it.
-->

## OpenTuya Sync vs. the official app

| | Official app (Smart Life / Tuya) | OpenTuya Sync |
|---|---|---|
| Manual color selection | ✅ | ✅ |
| Ambilight (screen sync) | ❌ | ✅ |
| Music sync | ❌ | ✅ |
| Webcam ambient | ❌ | ✅ |
| Works with no cloud account | ❌ | ✅ |
| Requires Tuya cloud account | ✅ | ❌ |
| Open source | ❌ | ✅ |

## Features

- **Ambilight** — follows your screen color in real time (`dxcam`, works
  with exclusive-fullscreen games, falls back to `mss`).
- **Music mode** — reacts to whatever's playing through your speakers
  (WASAPI loopback), with auto-gain and bass-beat detection.
- **Flash mode** — configurable strobe/flash effect.
- **Spotify** — follows the color of the album art of what's currently
  playing. One-time setup, done entirely inside the app (no terminal
  needed).
- **Webcam** — ambient light based on what your camera sees.
- **Manual control** — full HSV color wheel + brightness slider, for direct
  control like any bulb app.
- **Local-only Tuya control** — talks to the bulb directly on your LAN using
  its Local Key, no Tuya cloud dependency for day-to-day use.
- **Network scan** — auto-fills Device ID / IP / protocol version for Tuya
  devices found on your LAN (the Local Key itself can't be recovered this
  way — see [Adding a device](#adding-a-device)).
- **Per-source brightness limits** — set a floor and ceiling on how dim or
  bright each automatic mode can go, editable live while it's running (so
  you can knock down a screen-brightness spike — a flashbang in a game,
  say — without stopping ambilight).
- **Bluetooth output** — supports ELK-BLEDOB/LotusLamp X-protocol light
  bars/strips (NBBUFF, Ledagic, similar clones) alongside the WiFi outputs.
- System tray, dark cyberpunk UI, standalone `.exe` build.

## Install & run from source

```bash
python -m pip install -r requirements.txt
python main.py
```

## Build the `.exe`

```bash
build.bat
```

This produces `dist\OpenTuyaSync\OpenTuyaSync.exe` using PyInstaller
(`--onedir` mode). A few things worth knowing about the build:

- **No Python needed on the target PC.** The Python interpreter and every
  dependency (PySide6, dxcam, OpenCV, numpy, tinytuya, soundcard, the VC++
  runtime DLLs...) are bundled inside `_internal/`.
- **Copy the whole `dist\OpenTuyaSync\` folder**, not just the `.exe`. It's
  `--onedir`, not `--onefile` — the exe depends on files inside
  `_internal/` next to it.
- The `.exe` isn't code-signed, so Windows SmartScreen will likely show an
  "unrecognized publisher" warning the first time it runs on another PC
  (`More info` → `Run anyway`). This isn't a bug, just the cost of not
  having a paid publisher certificate.
- Built and tested on 64-bit Windows.

## Compatible brands

| Output | Brands | Status |
|---|---|---|
| **Tuya** | Tuya, **Ledvance SMART+ WiFi**, LSC Smart Connect (Action), Nedis SmartLife, Mirabella Genio, Treatlife | Tested extensively against a real bulb — the bulb used for all testing throughout this project is a **Ledvance WiFi bulb** |
| **WLED** | Any ESP8266/ESP32 running WLED firmware | **Untested** — no hardware available. Implemented against the official JSON API |
| **Philips Hue** | Bridge + Hue lights | **Untested** — no hardware available. Implemented against the official API |
| **ELK-BLEDOB (Bluetooth)** | Generic "LotusLamp X"-app light bars/strips sold under names like NBBUFF, Ledagic, and similar Amazon/AliExpress clones | **Untested** — no hardware available. Unlike the others, there's no official API for this one: it's built from a protocol reverse-engineered by a third party ([8none1/elk-bledob](https://github.com/8none1/elk-bledob)), not vendor documentation. Bluetooth LE, not WiFi — connects by MAC address, has a scan button in "Add device" |

Ledvance, Nedis, Mirabella, LSC and Treatlife are white-label clones of the
same Tuya protocol — add them as a "Tuya" device with their own Device ID
and Local Key.

Careful with the Ledvance name: Ledvance sells two unrelated product
lines. Their **SMART+ WiFi** bulbs (what this project targets) run the
Tuya protocol directly over WiFi — no separate hub needed. Their
**SMART+ Zigbee** line is a different family entirely, needs its own
Zigbee bridge, and is **not** supported here.

## The five sources

| Source | What it does | Status |
|---|---|---|
| **Ambilight** | Follows the screen color. Uses `dxcam` (works in exclusive-fullscreen games) with `mss` as fallback | Tested with real screen content, pure black/white |
| **Music** | Follows the audio coming out of your speakers (loopback). Auto-gain + bass-beat detection | Tested with real audio playing on the PC |
| **Flash** | Strobes at a configurable rate. Doesn't touch the real relay, alternates brightness within color mode | Logic tested, no physical device flashing during the test |
| **Spotify** | Follows the color of the currently-playing album art | **Needs one-time setup** — see below. Image download+averaging is tested with real images; OAuth itself is not (no dev account was available during testing) |
| **Webcam** | Follows the color seen by a camera (room ambient light) | Tested with a real connected camera |

### Setting up Spotify (one time)

All done from inside the app now:

1. Pick **Spotify** as the source and hit **Iniciar** — if it's not
   configured yet, a setup dialog opens automatically.
2. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard),
   create a free app.
3. In that app's "Redirect URIs", add exactly: `http://127.0.0.1:8888/callback`
4. Paste the Client ID and Client Secret into the dialog and click
   **Autorizar con Spotify** — it opens your browser, you authorize, and the
   app saves everything to `config.json` on its own.

(`spotify_auth_setup.py` still exists as a standalone terminal alternative,
but you shouldn't need it.)

## Adding a device

"+ Agregar" button in the main window.

- **Tuya**: click **🔍 Escanear red** to auto-fill Device ID, IP and
  protocol version from devices found on your LAN. The **Local Key**
  still has to be entered by hand — Tuya generates it cloud-side during
  pairing and it's never broadcast in a way a passive network scan can
  read. Get it from the Smart Life app (device settings → device info).
  Same fields for the white-label brands listed above.
- **WLED**: just the IP.
- **Hue**: Bridge IP, press the physical button on the Bridge, then hit
  **Emparejar** within 30 seconds, then pick the light ID.
- **ELK-BLEDOB (Bluetooth)**: click **🔍 Buscar por Bluetooth** to list
  nearby BLE devices that broadcast a name, or type the MAC address by
  hand if you already know it (e.g. from the nRF Connect app). The scan
  shows every nearby named BLE device, not just this brand — clones vary
  in what name they advertise.

Checked devices in the list are the ones that receive color when a source
is running. You can have several devices, from different brands, active at
the same time.

## Plugin architecture

```
core/
  plugin_base.py   CaptureSource / OutputTarget interfaces
  color.py         shared color math (RGB, auto-gain, beat detection)
  engine.py        connects one active source to the enabled devices
  config.py        config.json, supports multiple devices

capture/
  dxcam_capture.py     screen
  music_capture.py     audio (loopback)
  flash_capture.py     strobe
  spotify_capture.py   album art
  webcam_capture.py    webcam

outputs/
  tuya_output.py        Tuya + white-label clones
  wled_output.py        WLED
  hue_output.py         Philips Hue
  elk_bledob_output.py  ELK-BLEDOB / LotusLamp X (Bluetooth)
```

Adding a new source or output is one new file plus one line in the
matching `registry.py` — the rest of the app doesn't need to know it
exists.

## What's actually verified, and what isn't

Honest, not marketing:

- **Tuya**: tested in depth — on/off, color, brightness, temperature,
  scene mode, reconnection, end-to-end through the packaged `.exe`
  against a real bulb.
- **Ambilight**: contrast tested with real pure black/white screen content
  (reaches pure RGB 0,0,0 and 255,255,255). `dxcam` tested against the
  desktop (not a specific game).
- **Music**: tested with real audio playing on the PC (not just
  synthetic), reacting with auto-gain and beat detection.
- **Webcam**: tested with a real connected camera — capture, color
  averaging, clean shutdown.
- **Spotify**: image download+averaging is tested with real images.
  OAuth/token refresh/"now playing" is **not tested** — no developer
  account was available. You'll need to configure and verify it yourself.
- **WLED and Hue**: **untested**, no hardware available. Implemented
  against each vendor's official, stable public docs, which isn't the same
  as confirming it works. Let us know if something's off.
- **ELK-BLEDOB (Bluetooth)**: **untested**, no hardware available — and
  higher uncertainty than WLED/Hue, since there's no official docs to
  implement against at all, just a third party's reverse-engineered
  protocol. `bleak` itself (the BLE library) was confirmed working on
  Windows — scanning correctly reports "Bluetooth radio is not powered
  on" when Bluetooth is off — but no actual device has confirmed the byte
  protocol works. Your specific clone may use a different characteristic
  UUID or byte layout. Report back either way.
- **Per-source brightness limits**: the min/max sliders, per-source
  persistence, live updates while a source is running, and the HSV
  clamping math are all covered by direct tests. Not yet verified against
  a real bulb reacting to an actual in-game flash.
- **GUI and `.exe`**: the window renders, loads devices from
  `config.json`, and the full flow (pick source → Iniciar → the bulb
  changes → Detener → reverts on its own) was verified end to end, and
  separately confirmed the compiled `.exe` loads the exact same interface.
  The system tray (minimize, icon next to the clock) created without
  errors, but wasn't clicked for real during testing.

## Notes

- Don't run two sources against the same device at the same time (e.g.
  this app and some other controller) — whichever writes last wins.
- `assets/icon.ico` is a code-generated placeholder, not a real design.
  Swap it for whatever you want and rebuild.

## License

[MIT](LICENSE)

---

<p align="center">Developed by Chemikl Project</p>
