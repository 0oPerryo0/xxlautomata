"""Automates guild interactions — sending gifts to allies."""

import threading

from automations.base import BaseAutomation


class GuildAutomation(BaseAutomation):
    """
    Flow:
        1. Open Guild screen
        2. Send gifts to all allies
        3. Collect any received gifts
        4. Close screen
    """

    T_GUILD_BTN = "guild/guild_button.png"
    T_SEND_GIFTS_BTN = "guild/send_gifts_button.png"
    T_SEND_ALL_BTN = "guild/send_all_button.png"
    T_COLLECT_GIFTS_BTN = "guild/collect_gifts_button.png"
    T_COLLECT_ALL_BTN = "guild/collect_all_button.png"
    T_CONFIRM_BTN = "guild/confirm_button.png"
    T_CLOSE_BTN = "common/close_button.png"
    T_OK_BTN = "common/ok_button.png"

    def run(self, stop_event: threading.Event):
        self._log("Guild: opening")

        screen = self._screenshot()
        if screen is None:
            return

        if not self._tap_template(screen, self.T_GUILD_BTN):
            self._log("Guild: could not find Guild button — skipping")
            return

        self._sleep(self._long_delay, stop_event)
        if self._stopped(stop_event):
            return

        screen = self._screenshot()
        if screen is None:
            return

        # Send gifts
        if self._tap_template(screen, self.T_SEND_ALL_BTN):
            self._log("Guild: sent gifts to all allies")
            self._sleep(self._action_delay, stop_event)
            screen = self._screenshot()
            if screen is not None:
                self._tap_template(screen, self.T_OK_BTN)
        elif self._tap_template(screen, self.T_SEND_GIFTS_BTN):
            self._sleep(self._action_delay, stop_event)
            screen = self._screenshot()
            if screen is not None:
                self._tap_template(screen, self.T_CONFIRM_BTN)
                self._sleep(self._action_delay, stop_event)
                screen = self._screenshot()
                if screen is not None:
                    self._tap_template(screen, self.T_OK_BTN)
            self._log("Guild: gifts sent")
        else:
            self._log("Guild: no gift buttons found (already sent today?)")

        self._sleep(self._action_delay, stop_event)

        # Collect received gifts
        screen = self._screenshot()
        if screen is not None:
            if self._tap_template(screen, self.T_COLLECT_ALL_BTN):
                self._log("Guild: collected all received gifts")
                self._sleep(self._action_delay, stop_event)
                screen = self._screenshot()
                if screen is not None:
                    self._tap_template(screen, self.T_OK_BTN)
            elif self._tap_template(screen, self.T_COLLECT_GIFTS_BTN):
                self._log("Guild: collected gifts")
                self._sleep(self._action_delay, stop_event)
                screen = self._screenshot()
                if screen is not None:
                    self._tap_template(screen, self.T_OK_BTN)

        screen = self._screenshot()
        if screen is not None:
            self._tap_template(screen, self.T_CLOSE_BTN)

        self._log("Guild: done")
