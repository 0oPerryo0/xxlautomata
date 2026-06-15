# xxlwoofia ADB Automation

Small ADB automation scaffold for launching `xxlwoofia` and running configurable UI flows.

This project uses Python plus the Android `adb` executable. It is meant for automation on your own device or emulator. Check the game's rules before using automation on a live account.

## Setup

1. Install Android Platform Tools so `adb` is available in your terminal.
2. Enable USB debugging on the Android device or start an emulator.
3. Copy the example config:

   ```powershell
   Copy-Item config.example.json config.json
   ```

4. Edit `config.json` if package auto-detection fails.

## Commands

Check ADB and connected devices:

```powershell
python -m xxlwoofia_bot doctor
```

Open the game from the Android home screen:

```powershell
python -m xxlwoofia_bot launch --config config.json
```

Dump the current screen to help build selectors:

```powershell
python -m xxlwoofia_bot dump-ui --config config.json
```

Save a screenshot for cropping image templates:

```powershell
python -m xxlwoofia_bot screenshot --config config.json
```

Run the daily mission flow:

```powershell
python -m xxlwoofia_bot run daily --config config.json
```

You can also use the PowerShell helper:

```powershell
.\run.ps1 doctor
.\run.ps1 launch
.\run.ps1 daily
.\run.ps1 dump-ui
.\run.ps1 screenshot
```

## Config

`config.example.json` contains:

- `package`: Android package name. Leave blank to auto-detect packages containing `xxlwoofia`, `woofia`, or `xxl`.
- `device_serial`: Optional ADB serial. Leave blank if only one device is connected.
- `launch_wait_seconds`: Extra wait after launching the game. The daily flow already waits 10 seconds before looking for `tap to start`.
- `daily_mission.hard_mode_stage`: The hard story stage to run, such as `1-1`.
- `daily_mission.use_small_stamina_items`: Whether the bot may spend +10 stamina items when stamina is not enough.
- `daily_mission.use_big_stamina_items`: Whether the bot may spend one +60 stamina item when stamina is not enough.
- `daily_mission.max_stamina_restore`: Maximum stamina to restore for the hard-mode skip task. Default is `60`.
- `daily_mission.ocr_language`: Tesseract language string used for chapter and hard-level OCR.
- `daily_mission.tesseract_cmd`: Optional full path to `tesseract.exe` if it is not on PATH.

The connected test device auto-detected the package as:

```text
com.nightfun.xxlwoofia
```

If auto-detection cannot find the package, list packages with:

```powershell
adb shell cmd package list packages
```

Then put the package name in `config.json`.

## Adding New Flows

Create another JSON file under `flows/`, then run it with:

```powershell
python -m xxlwoofia_bot run my_flow --flow flows/my_flow.json --config config.json
```

Supported actions:

- `wait`: pause for `seconds`
- `wait_image`: wait until an image template is visible
- `wait_ocr`: wait until OCR sees matching text
- `tap`: tap fixed `x` and `y`
- `tap_selector`: tap a UI element found by text, content description, resource id, or class
- `tap_image`: tap a cropped screenshot template from `assets/templates`
- `tap_ocr`: tap text found by OCR, including regex matches
- `tap_ocr_scroll`: scan for OCR text, swipe, and retry until found
- `handle_stamina_popup`: use configured small/big stamina items, retry skip, or skip the hard-mode task if restore cannot proceed
- `repeat`: run nested steps multiple times, useful for stacked startup popups
- `if_image`, `if_ocr`, `if_var`: run nested `then` or `else` steps
- `stop`, `stop_if_image`, `stop_if_ocr`: stop the current flow early
- `press`: send an Android key event such as `BACK`, `HOME`, or `ENTER`
- `swipe`: perform a swipe gesture

Selectors can use `text`, `text_contains`, `content_desc`, `content_desc_contains`, `resource_id`, `resource_id_contains`, `class_name`, `index`, `optional`, and `timeout_seconds`.

For image matching support, install the optional dependencies:

```powershell
pip install -r requirements-xxlwoofia-bot.txt
```

The current UI dump shows `xxlwoofia` is Unity-rendered, so Android exposes only one game surface instead of individual mission buttons. For this game, `tap_image` templates or fixed coordinate taps will be more useful than `tap_selector`.

## Daily Mission Flow

`flows/daily_mission.json` follows this order:

- Start only if ADB sees a running emulator/device.
- Launch the game and wait until the home screen template is visible.
- Open missions and stop early if the daily-done indicator is found.
- Expand the sidebar if it is retracted.
- Run sausage guy, bond collect, free shop item, hard story skip-ticket stage, and part-time assignment.
- Return to missions, collect daily rewards, check weekly, and collect weekly if the lit collect button is visible.

The flow uses OCR for chapter labels such as `01`, `02`, `03`, and hard level text matching `困難 x-y`. The selected stage comes from `daily_mission.hard_mode_stage` in `config.json`.
