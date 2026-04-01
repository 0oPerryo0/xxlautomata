"""Automates the daily card matching game (3 rounds per day)."""

import threading
import random

from automations.base import BaseAutomation


class CardGameAutomation(BaseAutomation):
    """
    The card matching game involves selecting cards from a grid.
    Since card positions are random, the strategy is:
        - Tap cards sequentially to find matches
        - Track revealed cards to make matches when possible

    For simplicity this implementation taps through the grid systematically.
    When template matching identifies a matched pair, it taps them.

    Flow:
        1. Open card game screen
        2. Play up to 3 rounds
        3. Collect rewards
        4. Close
    """

    MAX_ROUNDS = 3

    T_CARD_GAME_BTN = "card_game/card_game_button.png"
    T_PLAY_BTN = "card_game/play_button.png"
    T_CARD = "card_game/card_face_down.png"
    T_MATCH_RESULT = "card_game/match_result.png"
    T_ROUND_COMPLETE = "card_game/round_complete.png"
    T_COLLECT_BTN = "card_game/collect_button.png"
    T_CLOSE_BTN = "common/close_button.png"
    T_OK_BTN = "common/ok_button.png"
    T_NO_ROUNDS_LEFT = "card_game/no_rounds_left.png"

    def run(self, stop_event: threading.Event):
        self._log("Card Game: opening")

        screen = self._screenshot()
        if screen is None:
            return

        if not self._tap_template(screen, self.T_CARD_GAME_BTN):
            self._log("Card Game: could not find button — skipping")
            return

        self._sleep(self._long_delay, stop_event)

        rounds_done = 0
        for _ in range(self.MAX_ROUNDS):
            if self._stopped(stop_event):
                break

            screen = self._screenshot()
            if screen is None:
                break

            from utils.image import is_on_screen
            if is_on_screen(screen, self.T_NO_ROUNDS_LEFT, self._threshold):
                self._log("Card Game: no rounds remaining today")
                break

            if not self._tap_template(screen, self.T_PLAY_BTN):
                self._log("Card Game: Play button not found")
                break

            self._sleep(self._long_delay, stop_event)

            # Play the round — tap cards until round ends (max 60 taps)
            for _ in range(60):
                if self._stopped(stop_event):
                    break
                screen = self._screenshot()
                if screen is None:
                    break

                # Check if round finished
                if is_on_screen(screen, self.T_ROUND_COMPLETE, self._threshold):
                    break

                # Find a face-down card and tap it
                from utils.image import find_template_by_name
                pos = find_template_by_name(screen, self.T_CARD, self._threshold)
                if pos:
                    self._device.tap(pos[0], pos[1], delay=0.6)
                else:
                    self._sleep(1.0, stop_event)

            # Collect round reward
            self._sleep(self._action_delay, stop_event)
            screen = self._screenshot()
            if screen is not None:
                if not self._tap_template(screen, self.T_COLLECT_BTN):
                    self._tap_template(screen, self.T_OK_BTN)
                self._sleep(self._action_delay, stop_event)

            rounds_done += 1
            self._log(f"Card Game: completed round {rounds_done}/{self.MAX_ROUNDS}")

        self._log(f"Card Game: finished {rounds_done} round(s)")
        screen = self._screenshot()
        if screen is not None:
            self._tap_template(screen, self.T_CLOSE_BTN)

        self._log("Card Game: done")
