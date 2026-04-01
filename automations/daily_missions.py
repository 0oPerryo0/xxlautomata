"""
Daily Missions automation — executes the full daily routine in order:

 1. Check if dailies are already completed (skip if so)
 2. Sausage Bro event  (Shop → Sausage Bro → Roll the Dice if not done)
 3. Hard Mode stage    (navigate to user-selected stage, run it)
 4. Bond Add-Up        (homescreen → Hook Up → Bond Add-Up)
 5. Guild visit        (homescreen → Guild → tap inside → back)
 6. Free market item   (homescreen → Market → buy the free item)
 7. Part-Time jobs     (homescreen → Part-Time → Quick Send → Confirm)
 8. Claim dailies      (homescreen → Mission → Claim All → tap reward)
 9. Weekly quests      (Mission → Weekly tab → Claim All if active)
"""

import threading

from automations.base import BaseAutomation
from utils.image import is_on_screen, find_template_by_name
from utils.ocr import find_text_position


class DailyMissionsAutomation(BaseAutomation):

    # ── Common ────────────────────────────────────────────────────────
    T_CLOSE = "common/close_button.png"
    T_OK = "common/ok_button.png"
    T_CONFIRM = "common/confirm_button.png"

    # ── Step 1 — already done check ───────────────────────────────────
    # The "Claimable at 100 Daily Activity" UI element that appears when
    # the player has already maxed out their daily activity points.
    # Used as a template fallback — OCR is the primary detection method.
    T_MAX_ACTIVITY_INDICATOR = "daily_missions/max_activity_indicator.png"

    # ── Step 2 — Sausage Bro ──────────────────────────────────────────
    T_SHOP_BTN = "daily_missions/homescreen_shop_button.png"
    T_SAUSAGE_BRO_ENTRY = "daily_missions/sausage_bro_entry.png"
    T_SAUSAGE_DONE = "daily_missions/sausage_bro_done.png"
    T_ROLL_DICE_BTN = "daily_missions/roll_dice_button.png"
    T_DICE_REWARD_OK = "daily_missions/dice_reward_ok.png"

    # ── Step 3 — Hard Mode ────────────────────────────────────────────
    # Buttons/screens that are reliably detected by template matching.
    # Text labels (difficulty, chapter numbers, level numbers, max, complete)
    # are detected by OCR at runtime.
    T_GO_BTN            = "daily_missions/homescreen_go_button.png"
    T_STORY_BTN         = "daily_missions/story_button.png"
    T_FAST_RUN_BTN      = "daily_missions/fast_run_button.png"
    T_ENERGY_REFILL     = "daily_missions/energy_refill_popup.png"
    T_ENERGY_CANCEL     = "daily_missions/energy_cancel_button.png"
    T_FAST_RUN_CONFIRM  = "daily_missions/fast_run_confirm_button.png"
    T_FAST_RUN_COMPLETE = "daily_missions/fast_run_complete_button.png"

    # OCR confidence thresholds
    # Lower = more permissive (catches blurry/small text); higher = fewer false positives
    OCR_GENERAL  = 50   # generic words: claimable, normal, hard, max, confirm, complete
    OCR_CHAPTER  = 60   # zero-padded chapter labels: '01'…'08'
    OCR_LEVEL    = 65   # precise level labels: '1-1'…'8-4'

    # ── Step 4 — Bond Add-Up ─────────────────────────────────────────
    T_HOOKUP_BTN = "daily_missions/homescreen_hookup_button.png"
    T_BOND_ADDUP_BTN = "daily_missions/bond_addup_button.png"
    T_BOND_ADDUP_CONFIRM = "daily_missions/bond_addup_confirm.png"
    T_BOND_ADDUP_OK = "daily_missions/bond_addup_ok.png"

    # ── Step 5 — Guild ────────────────────────────────────────────────
    T_GUILD_BTN = "daily_missions/homescreen_guild_button.png"
    T_GUILD_INSIDE = "daily_missions/guild_inside_element.png"

    # ── Step 6 — Free Market Item ─────────────────────────────────────
    T_MARKET_BTN = "daily_missions/homescreen_market_button.png"
    T_FREE_ITEM = "daily_missions/market_free_item.png"
    T_BUY_FREE_BTN = "daily_missions/market_buy_free_button.png"

    # ── Step 7 — Part-Time ────────────────────────────────────────────
    T_PARTTIME_BTN = "daily_missions/homescreen_parttime_button.png"
    T_QUICK_SEND_BTN = "daily_missions/parttime_quick_send_button.png"
    T_QUICK_SEND_CONFIRM = "daily_missions/parttime_quick_send_confirm.png"
    T_QUICK_SEND_OK = "daily_missions/parttime_quick_send_ok.png"

    # ── Step 8 — Claim Dailies ────────────────────────────────────────
    T_MISSION_BTN = "daily_missions/homescreen_mission_button.png"
    T_DAILY_TAB = "daily_missions/mission_daily_tab.png"
    T_CLAIM_ALL_DAILY = "daily_missions/mission_claim_all_button.png"
    T_REWARD_SCREEN = "daily_missions/mission_reward_screen.png"

    # ── Step 9 — Weekly Quests ────────────────────────────────────────
    T_WEEKLY_TAB = "daily_missions/mission_weekly_tab.png"
    T_CLAIM_ALL_WEEKLY = "daily_missions/mission_weekly_claim_all.png"

    # -----------------------------------------------------------------

    def run(self, stop_event: threading.Event):
        self._log("=== Daily Missions: starting full routine ===")

        # Step 1 ── already done?
        if self._is_already_done(stop_event):
            self._log("Daily Missions: already completed today — skipping routine")
            return

        # Step 2 ── Sausage Bro
        if not self._stopped(stop_event):
            self._do_sausage_bro(stop_event)

        # Step 3 ── Hard Mode stage
        if not self._stopped(stop_event):
            self._do_hard_mode(stop_event)

        # Step 4 ── Bond Add-Up
        if not self._stopped(stop_event):
            self._do_bond_addup(stop_event)

        # Step 5 ── Guild visit
        if not self._stopped(stop_event):
            self._do_guild_visit(stop_event)

        # Step 6 ── Free market item
        if not self._stopped(stop_event):
            self._buy_free_market_item(stop_event)

        # Step 7 ── Part-Time quick send
        if not self._stopped(stop_event):
            self._do_part_time(stop_event)

        # Step 8 ── Claim dailies
        if not self._stopped(stop_event):
            self._claim_dailies(stop_event)

        # Step 9 ── Weekly tab
        if not self._stopped(stop_event):
            self._check_weekly(stop_event)

        self._log("=== Daily Missions: routine complete ===")

    # =================================================================
    # Step 1 — Check if already done
    # =================================================================

    def _is_already_done(self, stop_event: threading.Event) -> bool:
        """
        Open the Quest/Mission tab from the homescreen and check whether the
        daily activity bar already reads 'Claimable at 100' (i.e. maxed out).

        Detection uses two methods in order:
          1. Template match  — looks for T_MAX_ACTIVITY_INDICATOR
          2. OCR fallback    — scans for the phrase '100' near 'claimable'

        Closes the quest screen before returning so the rest of the flow
        can start cleanly from the homescreen.
        """
        self._log("[1/9] Checking if dailies already done...")

        screen = self._screenshot()
        if screen is None:
            return False

        if not self._tap_template(screen, self.T_MISSION_BTN):
            self._log("  Mission button not found — assuming not done")
            return False

        self._sleep(self._long_delay, stop_event)

        # Make sure we're on the Daily tab
        screen = self._screenshot()
        if screen is not None:
            self._tap_template(screen, self.T_DAILY_TAB, delay=self._action_delay)

        screen = self._screenshot()
        if screen is None:
            self._return_home(stop_event)
            return False

        done = False

        # ── Method 1: template match ──────────────────────────────────

        if is_on_screen(screen, self.T_MAX_ACTIVITY_INDICATOR, self._threshold):
            self._log("  Max activity indicator found — dailies complete")
            done = True

        # ── Method 2: OCR fallback ───────────────────────────────────
        if not done:
    
            # The UI shows text like "Claimable at 100 Daily Activity"
            # We search for "claimable" as the key word
            if find_text_position(screen, "claimable", confidence=self.OCR_GENERAL):
                self._log("  OCR found 'claimable' text — dailies complete")
                done = True

        if not done:
            self._log("  Dailies not yet complete — proceeding")

        # Close the quest screen and return to homescreen
        self._return_home(stop_event)
        return done

    # =================================================================
    # Step 2 — Sausage Bro event
    # =================================================================

    def _do_sausage_bro(self, stop_event: threading.Event):
        self._log("[2/9] Sausage Bro event")

        screen = self._screenshot()
        if not self._tap_template(screen, self.T_SHOP_BTN):
            self._log("  Shop button not found — skipping Sausage Bro")
            return
        self._sleep(self._long_delay, stop_event)

        screen = self._screenshot()
        if not self._tap_template(screen, self.T_SAUSAGE_BRO_ENTRY):
            self._log("  Sausage Bro entry not found — skipping")
            self._return_home(stop_event)
            return
        self._sleep(self._long_delay, stop_event)

        # Check if already done for today
        screen = self._screenshot()

        if is_on_screen(screen, self.T_SAUSAGE_DONE, self._threshold):
            self._log("  Sausage Bro: already done today")
        else:
            # Roll the dice
            if self._tap_template(screen, self.T_ROLL_DICE_BTN):
                self._log("  Rolled the dice!")
                self._sleep(self._long_delay, stop_event)
                screen = self._screenshot()
                if screen is not None:
                    self._tap_any(screen, self.T_DICE_REWARD_OK, self.T_OK)
                    self._sleep(self._action_delay, stop_event)
            else:
                self._log("  Roll Dice button not found")

        self._return_home(stop_event)
        self._log("  Sausage Bro: done")

    # =================================================================
    # Step 3 — Hard Mode stage
    # =================================================================

    def _do_hard_mode(self, stop_event: threading.Event):
        """
        Full hard-mode flow:
          1. Tap Go on homescreen
          2. Tap Story
          3. Ensure difficulty is set to Hard (OCR checks Normal/Hard label)
          4. Scroll to correct chapter (chapters descend 08→01, so 01 is at bottom)
          5. Tap chapter → level selection screen → tap correct level via OCR
          6. Tap Fast Run button
          7. If energy refill popup appears → cancel → return home → stop bot
          8. Tap Max → Confirm → wait 5 s → tap Complete
        """
        stage_str = self._config.get("daily_missions", {}).get("hard_mode_stage", "")
        if not stage_str:
            self._log("[3/9] Hard Mode: no stage configured — skipping")
            return

        # Parse "chapter-level", e.g. "1-1" → chapter=1, level=1
        try:
            ch_str, lv_str = stage_str.strip().split("-")
            chapter = int(ch_str)   # 1–8
            level   = int(lv_str)   # 1–4
        except (ValueError, IndexError):
            self._log(f"[3/9] Hard Mode: invalid stage '{stage_str}' — use format like '1-1'")
            return

        self._log(f"[3/9] Hard Mode: targeting {chapter}-{level}")

        # ── 1. Tap Go ─────────────────────────────────────────────────
        screen = self._screenshot()
        if not self._tap_template(screen, self.T_GO_BTN):
            self._log("  Go button not found — skipping")
            return
        self._sleep(self._long_delay, stop_event)
        if self._stopped(stop_event):
            return

        # ── 2. Tap Story ──────────────────────────────────────────────
        screen = self._screenshot()
        if not self._tap_template(screen, self.T_STORY_BTN):
            self._log("  Story button not found — skipping")
            self._return_home(stop_event)
            return
        self._sleep(self._long_delay, stop_event)
        if self._stopped(stop_event):
            return

        # ── 3. Ensure Hard difficulty ─────────────────────────────────
        self._ensure_hard_mode(stop_event)
        if self._stopped(stop_event):
            return

        # ── 4. Navigate to the correct chapter ───────────────────────
        if not self._navigate_to_chapter(chapter, stop_event):
            self._log(f"  Chapter {chapter:02d} not found — skipping")
            self._return_home(stop_event)
            return
        self._sleep(self._long_delay, stop_event)
        if self._stopped(stop_event):
            return

        # ── 5. Select the level via OCR ───────────────────────────────
        if not self._select_level(chapter, level, stop_event):
            self._log(f"  Level {chapter}-{level} not found — skipping")
            self._return_home(stop_event)
            return
        self._sleep(self._action_delay, stop_event)
        if self._stopped(stop_event):
            return

        # ── 6. Tap Fast Run ───────────────────────────────────────────
        screen = self._screenshot()
        if not self._tap_template(screen, self.T_FAST_RUN_BTN):
            self._log("  Fast Run button not found — skipping")
            self._return_home(stop_event)
            return
        self._sleep(self._long_delay, stop_event)

        # ── 7. Energy refill check ────────────────────────────────────
        screen = self._screenshot()

        if is_on_screen(screen, self.T_ENERGY_REFILL, self._threshold):
            self._log("  Not enough stamina — cancelling and stopping automation")
            self._tap_template(screen, self.T_ENERGY_CANCEL)
            self._sleep(self._action_delay, stop_event)
            self._return_home(stop_event)
            stop_event.set()   # halt the entire bot run
            return

        # ── 8. Fast Run screen: Max → Confirm → wait → Complete ───────
        self._do_fast_run(stop_event)

        self._return_home(stop_event)
        self._log("  Hard Mode: done")

    # -----------------------------------------------------------------

    def _ensure_hard_mode(self, stop_event: threading.Event):
        """
        Read the difficulty indicator via OCR.
        If it shows 'normal', tap it once to toggle to Hard and verify.
        """

        screen = self._screenshot()
        if screen is None:
            return

        # Check current state — store result to avoid running OCR twice
        pos = find_text_position(screen, "normal", confidence=self.OCR_GENERAL)
        if pos:
            self._log("  Difficulty is Normal — tapping to switch to Hard")
            self._device.tap(pos[0], pos[1], delay=self._action_delay)
            self._sleep(self._action_delay, stop_event)
            screen = self._screenshot()
            if screen is not None and find_text_position(screen, "hard", confidence=self.OCR_GENERAL):
                self._log("  Difficulty confirmed: Hard")
            else:
                self._log("  Warning: difficulty switch unconfirmed — continuing")
        elif find_text_position(screen, "hard", confidence=self.OCR_GENERAL):
            self._log("  Difficulty already set to Hard")
        else:
            self._log("  Could not read difficulty — continuing")

    def _navigate_to_chapter(self, chapter: int, stop_event: threading.Event) -> bool:
        """
        Chapters are listed in descending order (08 at top, 01 at bottom).
        Strategy:
          1. Swipe to the bottom so chapter 01 is visible.
          2. Scan with OCR for the zero-padded label (e.g. '01').
          3. Scroll upwards until found, tapping when located.
        Returns True if the chapter was found and tapped.
        """

        label = f"{chapter:02d}"   # '01', '02', …, '08'

        screen = self._screenshot()
        if screen is None:
            return False
        h, w = screen.shape[:2]

        # Scroll to bottom (8 swipes is enough for 8 chapters)
        self._log(f"  Scrolling to bottom to find chapter {label}")
        for _ in range(8):
            if self._stopped(stop_event):
                return False
            self._device.swipe(w // 2, int(h * 0.75), w // 2, int(h * 0.25),
                               duration_ms=400)
            self._sleep(0.4, stop_event)

        # Now scan upward until we find the chapter label
        for _ in range(10):
            if self._stopped(stop_event):
                return False
            screen = self._screenshot()
            if screen is None:
                return False
            pos = find_text_position(screen, label, confidence=self.OCR_CHAPTER)
            if pos:
                self._device.tap(pos[0], pos[1], delay=self._action_delay)
                self._log(f"  Tapped chapter {label}")
                return True
            # Scroll up to reveal higher chapter numbers
            self._device.swipe(w // 2, int(h * 0.25), w // 2, int(h * 0.75),
                               duration_ms=400)
            self._sleep(0.6, stop_event)

        return False

    def _select_level(self, chapter: int, level: int, stop_event: threading.Event) -> bool:
        """
        In the level selection screen, levels are labelled 'chapter-level'
        (e.g. '1-1', '1-2', '1-3', '1-4').
        Use OCR to find and tap the correct label.
        Scrolls up to 4 times if not immediately visible.
        """

        label = f"{chapter}-{level}"   # e.g. '1-1'

        screen = self._screenshot()
        if screen is None:
            return False
        h, w = screen.shape[:2]

        for attempt in range(5):
            if self._stopped(stop_event):
                return False
            screen = self._screenshot()
            if screen is None:
                return False
            pos = find_text_position(screen, label, confidence=self.OCR_LEVEL)
            if pos:
                self._device.tap(pos[0], pos[1], delay=self._action_delay)
                self._log(f"  Tapped level {label}")
                return True
            if attempt < 4:
                # Scroll down a little in case not all levels are visible
                self._device.swipe(w // 2, int(h * 0.7), w // 2, int(h * 0.3),
                                   duration_ms=300)
                self._sleep(0.5, stop_event)

        return False

    def _do_fast_run(self, stop_event: threading.Event):
        """
        Fast Run confirmation screen:
          1. Find 'max' via OCR and tap it (sets run count to maximum).
          2. Tap the Confirm button (template).
          3. Wait ~5 seconds for the run to process.
          4. Find 'complete' via OCR and tap it; fall back to template.
        """


        # Tap Max
        screen = self._screenshot()
        if screen is not None:
            pos = find_text_position(screen, "max", confidence=self.OCR_GENERAL)
            if pos:
                self._device.tap(pos[0], pos[1], delay=self._action_delay)
                self._log("  Tapped Max runs")
            else:
                self._log("  'Max' not found via OCR — attempting confirm anyway")

        # Tap Confirm
        screen = self._screenshot()
        if screen is not None:
            if not self._tap_template(screen, self.T_FAST_RUN_CONFIRM):
                # Try OCR fallback
                pos = find_text_position(screen, "confirm", confidence=self.OCR_GENERAL)
                if pos:
                    self._device.tap(pos[0], pos[1], delay=self._action_delay)
                    self._log("  Confirm tapped via OCR")
                else:
                    self._log("  Confirm button not found — aborting fast run")
                    return

        self._log("  Fast run in progress — waiting 5 s...")
        self._sleep(5.0, stop_event)
        if self._stopped(stop_event):
            return

        # Tap Complete
        screen = self._screenshot()
        if screen is not None:
            pos = find_text_position(screen, "complete", confidence=self.OCR_GENERAL)
            if pos:
                self._device.tap(pos[0], pos[1], delay=self._action_delay)
                self._log("  Complete tapped via OCR")
            elif not self._tap_template(screen, self.T_FAST_RUN_COMPLETE):
                # Last resort: tap centre of screen to dismiss
                h, w = screen.shape[:2]
                self._device.tap(w // 2, h // 2, delay=self._action_delay)
                self._log("  Complete not found — tapped screen centre to dismiss")

    # =================================================================
    # Step 4 — Bond Add-Up
    # =================================================================

    def _do_bond_addup(self, stop_event: threading.Event):
        self._log("[4/9] Bond Add-Up")

        screen = self._screenshot()
        if not self._tap_template(screen, self.T_HOOKUP_BTN):
            self._log("  Hook Up button not found — skipping")
            return
        self._sleep(self._long_delay, stop_event)

        screen = self._screenshot()
        if not self._tap_template(screen, self.T_BOND_ADDUP_BTN):
            self._log("  Bond Add-Up button not found — skipping")
            self._return_home(stop_event)
            return
        self._sleep(self._action_delay, stop_event)

        screen = self._screenshot()
        if screen is not None:
            self._tap_any(screen, self.T_BOND_ADDUP_CONFIRM, self.T_CONFIRM)
            self._sleep(self._action_delay, stop_event)
            screen = self._screenshot()
            if screen is not None:
                self._tap_any(screen, self.T_BOND_ADDUP_OK, self.T_OK)
                self._sleep(self._action_delay, stop_event)

        self._return_home(stop_event)
        self._log("  Bond Add-Up: done")

    # =================================================================
    # Step 5 — Guild visit
    # =================================================================

    def _do_guild_visit(self, stop_event: threading.Event):
        self._log("[5/9] Guild visit")

        screen = self._screenshot()
        if not self._tap_template(screen, self.T_GUILD_BTN):
            self._log("  Guild button not found — skipping")
            return
        self._sleep(self._long_delay, stop_event)

        # Tap anywhere inside the guild screen to register the visit
        screen = self._screenshot()
        if screen is not None:
            # Tap the central element or any interactive guild item
            self._tap_template(screen, self.T_GUILD_INSIDE, delay=self._action_delay)

        self._sleep(self._action_delay, stop_event)
        self._return_home(stop_event)
        self._log("  Guild visit: done")

    # =================================================================
    # Step 6 — Buy free market item
    # =================================================================

    def _buy_free_market_item(self, stop_event: threading.Event):
        self._log("[6/9] Free market item")

        screen = self._screenshot()
        if not self._tap_template(screen, self.T_MARKET_BTN):
            self._log("  Market button not found — skipping")
            return
        self._sleep(self._long_delay, stop_event)

        screen = self._screenshot()
        if screen is None:
            return

        # Scroll through market to find the free item
        found = False
        for _ in range(4):
            screen = self._screenshot()
            if screen is None:
                break
            if self._tap_template(screen, self.T_FREE_ITEM, delay=0.5):
                found = True
                break
            if self._tap_template(screen, self.T_BUY_FREE_BTN):
                found = True
                break
            h, w = screen.shape[:2]
            self._device.swipe(w // 2, int(h * 0.7), w // 2, int(h * 0.3), duration_ms=400)
            self._sleep(0.8, stop_event)

        if found:
            # Confirm purchase
            self._sleep(self._action_delay, stop_event)
            screen = self._screenshot()
            if screen is not None:
                self._tap_any(screen, self.T_CONFIRM, self.T_OK)
                self._sleep(self._action_delay, stop_event)
            self._log("  Free item purchased")
        else:
            self._log("  Free item not found (may have been claimed already)")

        self._return_home(stop_event)

    # =================================================================
    # Step 7 — Part-Time quick send
    # =================================================================

    def _do_part_time(self, stop_event: threading.Event):
        self._log("[7/9] Part-Time jobs")

        screen = self._screenshot()
        if not self._tap_template(screen, self.T_PARTTIME_BTN):
            self._log("  Part-Time button not found — skipping")
            return
        self._sleep(self._long_delay, stop_event)

        screen = self._screenshot()
        if not self._tap_template(screen, self.T_QUICK_SEND_BTN):
            self._log("  Quick Send button not found — skipping")
            self._return_home(stop_event)
            return
        self._sleep(self._action_delay, stop_event)

        screen = self._screenshot()
        if screen is not None:
            if self._tap_template(screen, self.T_QUICK_SEND_CONFIRM):
                self._sleep(self._action_delay, stop_event)
                screen = self._screenshot()
                if screen is not None:
                    self._tap_any(screen, self.T_QUICK_SEND_OK, self.T_OK)
                    self._sleep(self._action_delay, stop_event)
                self._log("  Quick Send confirmed")
            else:
                self._log("  Quick Send confirm not found")

        self._return_home(stop_event)

    # =================================================================
    # Step 8 — Claim daily missions
    # =================================================================

    def _claim_dailies(self, stop_event: threading.Event):
        self._log("[8/9] Claiming daily missions")

        screen = self._screenshot()
        if not self._tap_template(screen, self.T_MISSION_BTN):
            self._log("  Mission button not found — skipping")
            return
        self._sleep(self._long_delay, stop_event)

        # Make sure we're on the Daily tab
        screen = self._screenshot()
        if screen is not None:
            self._tap_template(screen, self.T_DAILY_TAB, delay=self._action_delay)

        # Click Claim All
        screen = self._screenshot()
        if not self._tap_template(screen, self.T_CLAIM_ALL_DAILY):
            self._log("  Claim All not available — nothing to claim yet")
        else:
            self._log("  Claimed all daily missions")
            self._sleep(self._action_delay, stop_event)
            # Tap through reward popup
            for _ in range(5):
                if self._stopped(stop_event):
                    break
                screen = self._screenshot()
                if screen is None:
                    break
        
                if is_on_screen(screen, self.T_REWARD_SCREEN, self._threshold):
                    self._device.tap(screen.shape[1] // 2, screen.shape[0] // 2,
                                     delay=self._action_delay)
                    break
                else:
                    self._tap_any(screen, self.T_OK, self.T_CLOSE)
                    break

        # Continue to step 9 (we're already in the mission screen)
        self._log("  Daily claim: done")

    # =================================================================
    # Step 9 — Weekly quests
    # =================================================================

    def _check_weekly(self, stop_event: threading.Event):
        self._log("[9/9] Checking weekly quests")

        # We may still be in the mission screen from step 8; if not, reopen it
        screen = self._screenshot()

        if not is_on_screen(screen, self.T_WEEKLY_TAB, self._threshold):
            # Reopen missions
            if not self._tap_template(screen, self.T_MISSION_BTN):
                self._log("  Mission screen not accessible — skipping weekly")
                return
            self._sleep(self._long_delay, stop_event)

        # Switch to Weekly tab
        screen = self._screenshot()
        if not self._tap_template(screen, self.T_WEEKLY_TAB):
            self._log("  Weekly tab not found — skipping")
            self._return_home(stop_event)
            return
        self._sleep(self._action_delay, stop_event)

        # Claim all if the button is active (enabled)
        screen = self._screenshot()
        if self._tap_template(screen, self.T_CLAIM_ALL_WEEKLY):
            self._log("  Weekly: Claim All tapped")
            self._sleep(self._action_delay, stop_event)
            screen = self._screenshot()
            if screen is not None:
                self._tap_any(screen, self.T_OK, self.T_CLOSE)
        else:
            self._log("  Weekly: Claim All not active (not enough progress yet)")

        self._return_home(stop_event)

