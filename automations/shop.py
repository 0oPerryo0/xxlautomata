"""Automates purchasing items from the in-game shop."""

import threading

from automations.base import BaseAutomation


class ShopAutomation(BaseAutomation):
    """
    Flow:
        1. Open the Shop
        2. Buy configured items (Silver Bells / Golden Bells sections)
        3. Confirm purchase dialogs
        4. Close shop

    Configure via config.json -> shop:
        buy_with_silver_bells: true/false
        buy_with_golden_bells: true/false
        max_golden_bells_spend: max allowed spend (0 = unlimited)
    """

    T_SHOP_BTN = "shop/shop_button.png"
    T_SILVER_TAB = "shop/silver_tab.png"
    T_GOLDEN_TAB = "shop/golden_tab.png"
    T_BUY_BTN = "shop/buy_button.png"
    T_CONFIRM_BTN = "shop/confirm_button.png"
    T_CLOSE_BTN = "common/close_button.png"
    T_OK_BTN = "common/ok_button.png"

    def run(self, stop_event: threading.Event):
        shop_cfg = self._config.get("shop", {})
        buy_silver = shop_cfg.get("buy_with_silver_bells", False)
        buy_golden = shop_cfg.get("buy_with_golden_bells", False)

        if not buy_silver and not buy_golden:
            self._log("Shop: nothing configured to buy, skipping")
            return

        self._log("Shop: opening shop")
        screen = self._screenshot()
        if screen is None:
            return

        if not self._tap_template(screen, self.T_SHOP_BTN):
            self._log("Shop: could not find Shop button — skipping")
            return

        self._sleep(self._long_delay, stop_event)

        if buy_silver and not self._stopped(stop_event):
            self._buy_section(stop_event, self.T_SILVER_TAB, "Silver Bells")

        if buy_golden and not self._stopped(stop_event):
            self._buy_section(stop_event, self.T_GOLDEN_TAB, "Golden Bells")

        screen = self._screenshot()
        if screen is not None:
            self._tap_template(screen, self.T_CLOSE_BTN)

        self._log("Shop: done")

    def _buy_section(self, stop_event: threading.Event, tab_template: str, label: str):
        screen = self._screenshot()
        if screen is None:
            return
        if not self._tap_template(screen, tab_template):
            self._log(f"Shop: could not find {label} tab")
            return
        self._sleep(self._action_delay, stop_event)

        # Buy available items (up to 10)
        bought = 0
        for _ in range(10):
            if self._stopped(stop_event):
                break
            screen = self._screenshot()
            if screen is None:
                break
            if not self._tap_template(screen, self.T_BUY_BTN):
                break  # No more buy buttons visible
            self._sleep(0.8, stop_event)
            # Confirm
            screen = self._screenshot()
            if screen is not None:
                if self._tap_template(screen, self.T_CONFIRM_BTN):
                    bought += 1
                    self._sleep(self._action_delay, stop_event)
                    # Dismiss reward
                    screen = self._screenshot()
                    if screen is not None:
                        self._tap_template(screen, self.T_OK_BTN)
                        self._sleep(0.5, stop_event)

        self._log(f"Shop: bought {bought} item(s) with {label}")
