# XXL Woofia Automata

Work-in-progress ADB automation for the Android game **xxlwoofia**.

This project is an experiment in making the daily routine less repetitive. It launches the game through ADB, waits for the start screen, clears common popups, and runs a configurable daily flow using screenshots, image matching, OCR, and simple tap/swipe commands.

Only the Traditional Chinese version of the game is supported right now. The templates and OCR targets are built around that UI text.

It is not polished yet. Expect to tweak templates, thresholds, coordinates, and flow steps for your emulator resolution and game state.

## Current Status

The daily flow is still being built and tuned. Right now it is focused on:

- Opening the game from an emulator or Android device.
- Detecting `tap to start` with OCR.
- Closing startup popups.
- Detecting the home screen.
- Running daily tasks such as free gacha, sausage bro, bond collect, shop free item, hard-mode skip ticket, part-time jobs, daily chests, and weekly rewards.
- Handling stamina popups with optional +10 and +60 stamina item usage.

The game is Unity-rendered, so normal Android UI inspection does not expose useful buttons. Most automation depends on image templates under `assets/templates/`.

## Before You Use It

Use this only on your own device or emulator. Also check the game's rules before running automation on a live account.

The bot is sensitive to screen resolution, UI scale, popups, animation state, and template quality. If something fails, the fix is usually to capture a new screenshot and re-crop the template from the exact emulator setup you are using.

## Requirements

- Windows PowerShell
- Python 3.11+
- Android Platform Tools, with `adb` available
- An Android emulator or a USB-debugging-enabled Android device
- Optional: Tesseract OCR for OCR-based steps

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-xxlwoofia-bot.txt
```

If PowerShell blocks activation, run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Create your local config:

```powershell
Copy-Item config.example.json config.json
```

Then edit `config.json` for your setup.

## Config

Example:

```json
{
  "package": "",
  "device_serial": "",
  "launch_wait_seconds": 0,
  "package_keywords": ["xxlwoofia", "woofia", "xxl"],
  "daily_mission": {
    "hard_mode_stage": "1-1",
    "use_small_stamina_items": false,
    "use_big_stamina_items": false,
    "max_stamina_restore": 60,
    "ocr_language": "eng+chi_tra+chi_sim",
    "tesseract_cmd": ""
  }
}
```

Notes:

- Leave `package` blank if auto-detection works.
- Set `device_serial` if `adb devices` shows more than one emulator/device.
- Set `hard_mode_stage` to the hard-mode stage you want to skip, for example `8-4`.
- Turn on `use_small_stamina_items` or `use_big_stamina_items` only if you want the bot to spend stamina items.

## Tesseract OCR

The Python package `pytesseract` is only a wrapper. You still need the actual Tesseract program installed separately if you use OCR.

Typical Windows path:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

If Tesseract is not on PATH, set this in `config.json`:

```json
"tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

For this project, install English, Traditional Chinese, and Simplified Chinese language data if possible.

The flow itself is currently tuned for Traditional Chinese game text. Other language versions will need new templates and OCR strings.

## Running

Check ADB and package detection:

```powershell
.\run.ps1 doctor
```

Launch the game:

```powershell
.\run.ps1 launch
```

Capture a screenshot for cropping templates:

```powershell
.\run.ps1 screenshot
```

Run the daily flow:

```powershell
.\run.ps1 daily
```

You can also call the module directly:

```powershell
python -m xxlwoofia_bot run daily --config config.json
```

## Templates

Templates live in:

```text
assets/templates/
```

The flow references these PNGs directly from `flows/daily_mission.json`. If the bot says it cannot find an image, check that the file exists and that it was cropped from the same emulator resolution and UI state.

The matcher currently uses a hybrid approach:

- Feature matching first, which can help when resolution changes.
- Multi-scale pixel matching as a fallback, which works better for small flat UI buttons.

For best results, avoid tiny icon-only crops. A slightly larger crop with stable nearby detail usually matches better.

## Daily Flow

The main flow is:

```text
flows/daily_mission.json
```

Useful actions include:

- `tap_image`
- `wait_image`
- `tap_ocr`
- `tap_ocr_scroll`
- `tap`
- `press`
- `repeat`
- `if_image`
- `if_ocr`
- `if_var`
- `handle_stamina_popup`

The flow is intentionally JSON-based so new tasks can be added without rewriting the core Python code.

## Troubleshooting

If image recognition fails, the most common reasons are:

- The emulator resolution changed.
- The template was cropped from a different screen state.
- The crop is too small or too plain.
- A popup is covering or dimming the screen.
- The image threshold is still too high.
- The wrong device is selected in ADB.

If ADB shows multiple devices, set `device_serial` in `config.json`.

If OCR fails, install Tesseract and set `tesseract_cmd`.

## Project Layout

```text
xxlwoofia_bot/          Core Python code
flows/                  JSON automation flows
assets/templates/       Cropped UI templates
docs/                   Extra notes
run.ps1                 PowerShell helper
config.example.json     Example config
```

## Roadmap

Things still worth improving:

- Better template debugging output.
- A small template test command.
- Region-limited OCR for speed.
- More stable handling for popups and animation delays.
- A simple UI for choosing which daily tasks to run.
