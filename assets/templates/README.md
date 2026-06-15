# Template Images

Put cropped PNG screenshots here when a game element is not visible through Android UIAutomator.

Recommended structure:

```text
assets/templates/common/cancel_button.png
assets/templates/common/close_button.png
assets/templates/common/confirm_button.png
assets/templates/common/home_screen_marker.png
assets/templates/common/ok_button.png
assets/templates/common/sidebar_retracted.png
assets/templates/daily_missions/bond_collect_button.png
assets/templates/daily_missions/bond_new_cg_cancel_button.png
assets/templates/daily_missions/daily_done_indicator.png
assets/templates/daily_missions/difficulty_indicator.png
assets/templates/daily_missions/finish_button.png
assets/templates/daily_missions/homescreen_mission_button.png
assets/templates/daily_missions/homescreen_bond_button.png
assets/templates/daily_missions/homescreen_parttime_button.png
assets/templates/daily_missions/homescreen_play_button.png
assets/templates/daily_missions/homescreen_shop_button.png
assets/templates/daily_missions/homescreen_summon_button.png
assets/templates/daily_missions/mission_daily_tab.png
assets/templates/daily_missions/mission_claim_all_button.png
assets/templates/daily_missions/mission_collect_daily_button.png
assets/templates/daily_missions/mission_daily_chest_button.png
assets/templates/daily_missions/mission_weekly_collect_all_lit.png
assets/templates/daily_missions/mission_weekly_chest_button.png
assets/templates/daily_missions/mission_weekly_tab.png
assets/templates/daily_missions/normal_mode_indicator.png
assets/templates/daily_missions/parttime_collect_button.png
assets/templates/daily_missions/parttime_one_click_assign_button.png
assets/templates/daily_missions/sausage_gamble_button.png
assets/templates/daily_missions/sausage_guy_entry.png
assets/templates/daily_missions/sausage_result_popup.png
assets/templates/daily_missions/shop_free_item_button.png
assets/templates/daily_missions/skip_max_button.png
assets/templates/daily_missions/skip_ticket_button.png
assets/templates/daily_missions/summon_close_button.png
assets/templates/daily_missions/summon_free_pull_button.png
assets/templates/daily_missions/summon_silverbell_banner.png
assets/templates/daily_missions/summon_skip_button.png
assets/templates/daily_missions/stamina_item_10.png
assets/templates/daily_missions/stamina_item_60.png
assets/templates/daily_missions/stamina_not_enough_popup.png
assets/templates/daily_missions/story_mode_button.png
```

Crop tightly around the button or visual element. Keep your emulator/device resolution fixed; changing resolution can break image matching.

Use this command to capture a full screenshot, then crop the needed button or marker into the matching path above:

```powershell
.\run.ps1 screenshot
```

Install image matching dependencies with:

```powershell
pip install -r requirements-xxlwoofia-bot.txt
```
