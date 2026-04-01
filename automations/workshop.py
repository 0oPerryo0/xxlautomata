"""Automates Workshop / Gym runs (3x daily — XP, skill cards, upgrade items)."""

import threading

from automations.base import BaseAutomation


class WorkshopAutomation(BaseAutomation):
    """
    Flow:
        1. Open the Workshop / Gym screen
        2. Run all available sessions (up to 3 per day)
        3. Collect rewards
        4. Close screen
    """

    MAX_RUNS = 3  # game allows 3 per day

    T_WORKSHOP_BTN = "workshop/workshop_button.png"
    T_START_BTN = "workshop/start_button.png"
    T_AUTO_BTN = "workshop/auto_button.png"
    T_SKIP_BTN = "workshop/skip_button.png"
    T_COLLECT_BTN = "workshop/collect_button.png"
    T_CLOSE_BTN = "common/close_button.png"
    T_OK_BTN = "common/ok_button.png"
    T_NO_RUNS_LEFT = "workshop/no_runs_left.png"

    def run(self, stop_event: threading.Event):
        self._log("Workshop: opening")

        screen = self._screenshot()
        if screen is None:
            return

        if not self._tap_template(screen, self.T_WORKSHOP_BTN):
            self._log("Workshop: could not find Workshop button — skipping")
            return

        self._sleep(self._long_delay, stop_event)

        runs_done = 0
        for i in range(self.MAX_RUNS):
            if self._stopped(stop_event):
                break

            screen = self._screenshot()
            if screen is None:
                break

            # Check if runs are exhausted
            from utils.image import is_on_screen
            if is_on_screen(screen, self.T_NO_RUNS_LEFT, self._threshold):
                self._log("Workshop: no runs remaining today")
                break

            # Start a run
            if not self._tap_template(screen, self.T_START_BTN):
                self._log("Workshop: Start button not found — stopping")
                break

            self._sleep(self._action_delay, stop_event)

            # Enable auto-battle if available
            screen = self._screenshot()
            if screen is not None:
                self._tap_template(screen, self.T_AUTO_BTN)

            # Wait for battle to finish (up to 60s), skip if possible
            for _ in range(20):
                if self._stopped(stop_event):
                    break
                self._sleep(2.0, stop_event)
                screen = self._screenshot()
                if screen is None:
                    continue
                # Try to skip
                if self._tap_template(screen, self.T_SKIP_BTN, delay=0.5):
                    break
                # Check if collect/reward appeared
                from utils.image import is_on_screen
                if is_on_screen(screen, self.T_COLLECT_BTN, self._threshold):
                    break

            # Collect rewards
            screen = self._screenshot()
            if screen is not None:
                self._tap_template(screen, self.T_COLLECT_BTN)
                self._sleep(self._action_delay, stop_event)
                screen = self._screenshot()
                if screen is not None:
                    self._tap_template(screen, self.T_OK_BTN)
                    self._sleep(self._action_delay, stop_event)

            runs_done += 1
            self._log(f"Workshop: completed run {runs_done}/{self.MAX_RUNS}")

        self._log(f"Workshop: finished {runs_done} run(s)")
        screen = self._screenshot()
        if screen is not None:
            self._tap_template(screen, self.T_CLOSE_BTN)

        self._log("Workshop: done")
