"""Automates daily free summons (gacha pulls)."""

import threading

from automations.base import BaseAutomation


class SummonsAutomation(BaseAutomation):
    """
    Flow:
        1. Open the Summon / Gacha screen
        2. Perform the free daily pull(s)
        3. Dismiss result screen
        4. Return to main screen

    Config: features.summons + summons.daily_free_only
    """

    T_SUMMON_BTN = "summons/summon_button.png"
    T_FREE_PULL_BTN = "summons/free_pull_button.png"
    T_PULL_1_BTN = "summons/pull_1_button.png"
    T_SKIP_BTN = "summons/skip_button.png"
    T_RESULT_CLOSE = "summons/result_close.png"
    T_CLOSE_BTN = "common/close_button.png"
    T_OK_BTN = "common/ok_button.png"

    def run(self, stop_event: threading.Event):
        self._log("Summons: opening gacha screen")

        screen = self._screenshot()
        if screen is None:
            return

        if not self._tap_template(screen, self.T_SUMMON_BTN):
            self._log("Summons: could not find Summon button — skipping")
            return

        self._sleep(self._long_delay, stop_event)
        if self._stopped(stop_event):
            return

        # Look for the free pull button
        screen = self._screenshot()
        if screen is None:
            return

        if self._tap_template(screen, self.T_FREE_PULL_BTN):
            self._log("Summons: tapped Free Pull button")
        elif self._tap_template(screen, self.T_PULL_1_BTN):
            self._log("Summons: tapped Pull x1 button")
        else:
            self._log("Summons: no free pull available today")
            self._close(stop_event)
            return

        # Wait for animation / result screen
        self._sleep(5.0, stop_event)
        if self._stopped(stop_event):
            return

        # Skip animation if possible
        screen = self._screenshot()
        if screen is not None:
            self._tap_template(screen, self.T_SKIP_BTN)
            self._sleep(1.5, stop_event)

        # Close result screen
        screen = self._screenshot()
        if screen is not None:
            if not self._tap_template(screen, self.T_RESULT_CLOSE):
                self._tap_template(screen, self.T_OK_BTN)

        self._close(stop_event)
        self._log("Summons: done")

    def _close(self, stop_event: threading.Event):
        self._sleep(self._action_delay, stop_event)
        screen = self._screenshot()
        if screen is not None:
            self._tap_template(screen, self.T_CLOSE_BTN)
