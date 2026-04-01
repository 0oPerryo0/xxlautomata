# XXLAutomata — Setup Checklist

## 1. Installation

- [ ] Install Python 3.11+
- [ ] Run `pip install -r requirements.txt`
- [ ] Install [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki) (needed for stage/level detection in Hard Mode)
- [ ] Install [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools) and add `adb.exe` to PATH
  - Download the zip, extract it (e.g. `C:\platform-tools\`)
  - Open **Start → Search "Environment Variables" → Edit the system environment variables**
  - Under **System variables**, select `Path` → **Edit** → **New** → paste `C:\platform-tools\`
  - Click OK on all dialogs, then restart your terminal
  - Verify with: `adb version`
- [ ] Start your emulator (BlueStacks / LDPlayer) or connect a real Android device with USB debugging enabled

---

## 2. Template Images

All images go in `assets/templates/`. Each one is a **cropped PNG screenshot** of exactly that UI element taken from your game at your emulator's resolution. The bot uses pixel-perfect matching, so crop tightly with no extra padding.

### Common (used by multiple features)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `common/homescreen_summon_button.png` | The summon/gacha button on the **homescreen** — used as the "we are home" indicator by the back-navigation loop |
| [ ] | `common/back_button.png` | The back/return arrow button that appears on most screens |
| [ ] | `common/close_button.png` | The X / close button on popups and menus |
| [ ] | `common/ok_button.png` | The generic OK / confirm button on reward popups |
| [ ] | `common/confirm_button.png` | A secondary confirm button (different style from OK) |

---

### Daily Missions — Step 1 (Already Done Check)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `daily_missions/homescreen_mission_button.png` | The Quest / Mission button on the homescreen |
| [ ] | `daily_missions/mission_daily_tab.png` | The "Daily" tab inside the quest screen |
| [ ] | `daily_missions/max_activity_indicator.png` | *(Optional — OCR covers this)* The "Claimable at 100 Daily Activity" UI element when dailies are maxed out |

---

### Daily Missions — Step 2 (Sausage Bro)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `daily_missions/homescreen_shop_button.png` | The Shop button on the homescreen |
| [ ] | `daily_missions/sausage_bro_entry.png` | The Sausage Bro banner/entry inside the shop |
| [ ] | `daily_missions/sausage_bro_done.png` | The indicator shown when Sausage Bro is already completed today |
| [ ] | `daily_missions/roll_dice_button.png` | The "Roll the Dice" button in the Sausage Bro screen |
| [ ] | `daily_missions/dice_reward_ok.png` | The OK/confirm button on the dice reward popup |

---

### Daily Missions — Step 3 (Hard Mode Stage)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `daily_missions/homescreen_go_button.png` | The "Go" button on the homescreen |
| [ ] | `daily_missions/story_button.png` | The "Story" option in the battle/go menu |
| [ ] | `daily_missions/fast_run_button.png` | The "Fast Run" button on the level detail screen |
| [ ] | `daily_missions/energy_refill_popup.png` | The energy/stamina refill popup that appears when stamina is too low |
| [ ] | `daily_missions/energy_cancel_button.png` | The Cancel button inside the energy refill popup |
| [ ] | `daily_missions/fast_run_confirm_button.png` | The Confirm button on the Fast Run screen |
| [ ] | `daily_missions/fast_run_complete_button.png` | The Complete button after a Fast Run finishes |

> **Note:** Difficulty (Normal/Hard), chapter numbers (01–08), level numbers (1-1 to 8-4), "max", "confirm", and "complete" text are all detected by **OCR** — no image needed for those.

---

### Daily Missions — Step 4 (Bond Add-Up)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `daily_missions/homescreen_hookup_button.png` | The Hook Up / Bond button on the homescreen |
| [ ] | `daily_missions/bond_addup_button.png` | The "Bond Add-Up" button inside the Hook Up screen |
| [ ] | `daily_missions/bond_addup_confirm.png` | The confirm button for Bond Add-Up (if different from common confirm) |
| [ ] | `daily_missions/bond_addup_ok.png` | The OK button on the Bond Add-Up reward popup (if different from common OK) |

---

### Daily Missions — Step 5 (Guild Visit)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `daily_missions/homescreen_guild_button.png` | The Guild button on the homescreen |
| [ ] | `daily_missions/guild_inside_element.png` | Any tappable element inside the guild screen to register the visit |

---

### Daily Missions — Step 6 (Free Market Item)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `daily_missions/homescreen_market_button.png` | The Market button on the homescreen |
| [ ] | `daily_missions/market_free_item.png` | The free item listing in the market |
| [ ] | `daily_missions/market_buy_free_button.png` | The "Buy (Free)" / "0 cost" button next to the free item |

---

### Daily Missions — Step 7 (Part-Time Jobs)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `daily_missions/homescreen_parttime_button.png` | The Part-Time button on the homescreen |
| [ ] | `daily_missions/parttime_quick_send_button.png` | The "Quick Send" button in the Part-Time screen |
| [ ] | `daily_missions/parttime_quick_send_confirm.png` | The confirm button for Quick Send |
| [ ] | `daily_missions/parttime_quick_send_ok.png` | The OK button after Quick Send succeeds |

---

### Daily Missions — Step 8 (Claim Dailies)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `daily_missions/mission_claim_all_button.png` | The "Claim All" button on the Daily missions tab |
| [ ] | `daily_missions/mission_reward_screen.png` | The reward collection popup/screen shown after claiming |

---

### Daily Missions — Step 9 (Weekly Quests)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `daily_missions/mission_weekly_tab.png` | The "Weekly" tab inside the quest screen |
| [ ] | `daily_missions/mission_weekly_claim_all.png` | The "Claim All" button on the Weekly tab (only visible when enough progress) |

---

### Shop (optional feature)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `shop/shop_button.png` | The Shop button that opens the main shop |
| [ ] | `shop/silver_tab.png` | The Silver Bells tab inside the shop |
| [ ] | `shop/golden_tab.png` | The Golden Bells tab inside the shop |
| [ ] | `shop/buy_button.png` | The Buy button next to a shop item |
| [ ] | `shop/confirm_button.png` | The confirm button on the purchase dialog |

---

### Summons (optional feature)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `summons/summon_button.png` | The Summon / Gacha button |
| [ ] | `summons/free_pull_button.png` | The free daily pull button (shows 0 cost) |
| [ ] | `summons/pull_1_button.png` | The standard Pull x1 button (fallback if no free pull) |
| [ ] | `summons/skip_button.png` | The skip button during the pull animation |
| [ ] | `summons/result_close.png` | The close button on the pull result screen |

---

### Workshop / Gym (optional feature)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `workshop/workshop_button.png` | The Workshop or Gym entry button |
| [ ] | `workshop/start_button.png` | The Start button to begin a workshop run |
| [ ] | `workshop/auto_button.png` | The Auto / Auto-battle toggle button |
| [ ] | `workshop/skip_button.png` | The Skip button during battle animation |
| [ ] | `workshop/collect_button.png` | The Collect rewards button after a run |
| [ ] | `workshop/no_runs_left.png` | The indicator shown when all 3 daily runs are used up |

---

### Card Game (optional feature)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `card_game/card_game_button.png` | The card matching game entry button |
| [ ] | `card_game/play_button.png` | The Play button to start a round |
| [ ] | `card_game/card_face_down.png` | A single face-down card (the bot taps these to flip) |
| [ ] | `card_game/round_complete.png` | The screen shown when a round ends |
| [ ] | `card_game/collect_button.png` | The Collect button after a round |
| [ ] | `card_game/no_rounds_left.png` | The indicator when all 3 daily rounds are used |

---

### Guild Gifts (optional feature)

| Status | File | What to screenshot |
|--------|------|--------------------|
| [ ] | `guild/guild_button.png` | The Guild entry button |
| [ ] | `guild/send_all_button.png` | The "Send All Gifts" button (preferred) |
| [ ] | `guild/send_gifts_button.png` | The individual Send Gifts button (fallback) |
| [ ] | `guild/collect_all_button.png` | The "Collect All" received gifts button |
| [ ] | `guild/collect_gifts_button.png` | The individual collect button (fallback) |
| [ ] | `guild/confirm_button.png` | The confirm button for guild actions |

---

## 3. Tips for Taking Screenshots

1. Run your emulator at a **fixed resolution** — always the same one. Changing resolution breaks all templates.
2. Use a screenshot tool that lets you drag-select a region (e.g. Windows Snipping Tool, ShareX).
3. Crop the button/element **tightly** — just the button, no surrounding background.
4. Save as **PNG** (not JPEG — compression changes pixel values and breaks matching).
5. If a button appears in multiple colours/states, screenshot the state the bot needs to detect.
6. The **OCR** (pytesseract) handles all text reading — you do **not** need images for: difficulty labels, chapter numbers, level numbers, "max", "confirm", "complete".

---

## 4. Configuration

Edit `config.json` before running:

- `device.serial` — set to your emulator ADB address (e.g. `localhost:5555` for BlueStacks, `localhost:5554` for LDPlayer)
- `daily_missions.hard_mode_stage` — stage in `chapter-level` format, e.g. `"1-1"`. Leave blank to skip Hard Mode.
- `features.*` — toggle each automation feature on/off
- `template_threshold` — matching sensitivity (0.0–1.0). Lower = more lenient. Start at `0.8`.

---

## 5. Running

```bash
python main.py
```

1. The app auto-starts the ADB server on launch.
2. Click **Refresh Devices** to see your emulator, select it, click **Connect**.
3. Tick the features you want, fill in Hard Mode stage if needed.
4. Click **▶ Start Bot**.
