<h1 align="center">
  XXL Woofia Automata
</h1>

<h3 align="center">
  Work-in-progress ADB automation for the Traditional Chinese version of xxlwoofia.
</h3>

<p align="center">
  Launch the game, clear daily chores, and automate repetitive taps using ADB, image matching, and OCR.
</p>

## Status

This is still in progress. The daily flow works as a configurable automation script, but it still needs template tuning for each emulator setup. Screen resolution, UI scale, popups, and template crops can all affect recognition.

Only the **Traditional Chinese** version of the game is supported right now.

## Features

- [x] Detects connected ADB device or emulator

- [x] Launches xxlwoofia from the Android home screen

- [x] Handles the `tap to start` screen and startup popups

- [x] Uses hybrid image recognition: feature matching first, multi-scale template fallback

- [x] Runs the current daily mission route: free gacha, sausage bro, bond, shop, hard-mode story skip, part-time, daily chest, weekly rewards

- [x] Supports optional +10 and +60 stamina item usage for hard-mode skipping

- [ ] Add a template debugging command

- [ ] Add a small UI for choosing which tasks to run

- [ ] Make OCR faster with screen-region detection

## Requirements

- Python 3.11+

- Android Platform Tools / `adb`

- Windows PowerShell

- Android emulator or USB-debugging-enabled Android device

- Optional: Tesseract OCR for OCR-based text detection

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-xxlwoofia-bot.txt
Copy-Item config.example.json config.json
```

If PowerShell blocks venv activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Configuration

Edit `config.json` after copying it from `config.example.json`.

Common settings:

- `device_serial`: Set this if `adb devices` shows more than one emulator or device

- `hard_mode_stage`: Hard-mode stage to run, for example `8-4`

- `use_small_stamina_items`: Allows the bot to use +10 stamina items

- `use_big_stamina_items`: Allows the bot to use +60 stamina items

- `tesseract_cmd`: Full path to `tesseract.exe` if Tesseract is not on PATH

Example Tesseract path:

```json
"tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

## Usage

Check ADB:

```powershell
.\run.ps1 doctor
```

Capture a screenshot for template cropping:

```powershell
.\run.ps1 screenshot
```

Run the daily automation:

```powershell
.\run.ps1 daily
```

## Templates

Most game UI is Unity-rendered, so normal Android UI inspection does not expose useful buttons. The bot uses cropped PNG templates from:

```text
assets/templates/
```

If recognition fails, crop a new template from the exact emulator resolution and game state you are using. Slightly larger crops with stable nearby detail usually work better than tiny icon-only crops.

## Project Structure

```text
xxlwoofia_bot/          Core Python automation code
flows/                  JSON automation flows
assets/templates/       Cropped UI templates
docs/                   Extra notes
run.ps1                 PowerShell helper
config.example.json     Example config
```

## Contributing

This is a personal WIP project, but issues, fixes, and better template/flow ideas are welcome.

## License

No license has been selected yet.
