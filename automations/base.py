"""Base class for all automation modules."""

import threading
import time
from typing import Callable

from core.adb import ADBDevice
from utils.image import is_on_screen, find_template_by_name
from utils.logger import get_logger

# ── Shared navigation templates ───────────────────────────────────────────────
# The summon button is always visible on the homescreen and acts as the
# reliable "we are home" indicator.
T_HOMESCREEN = "common/homescreen_summon_button.png"
T_BACK_BTN = "common/back_button.png"


class BaseAutomation:
    """
    All automation modules inherit from this class.

    Subclasses must implement:
        run(stop_event: threading.Event) -> None

    The stop_event is checked between steps. When set, the module should
    exit cleanly as soon as possible.
    """

    def __init__(
        self,
        device: ADBDevice,
        config: dict,
        log_callback: Callable[[str], None],
    ):
        self._device = device
        self._config = config
        self._log_cb = log_callback
        self._threshold = config.get("template_threshold", 0.8)
        self._timing = config.get("timing", {})
        self._action_delay = self._timing.get("action_delay", 1.0)
        self._long_delay = self._timing.get("long_delay", 3.0)
        self.log = get_logger(self.__class__.__name__)

    # ------------------------------------------------------------------
    # Must override
    # ------------------------------------------------------------------

    def run(self, stop_event: threading.Event):
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _log(self, msg: str):
        self.log.info(msg)
        self._log_cb(msg)

    def _stopped(self, stop_event: threading.Event) -> bool:
        return stop_event.is_set()

    def _sleep(self, seconds: float, stop_event: threading.Event) -> bool:
        """Sleep in small increments so stop_event can interrupt. Returns True if stopped."""
        end = time.time() + seconds
        while time.time() < end:
            if stop_event.is_set():
                return True
            time.sleep(0.2)
        return False

    def _screenshot(self):
        return self._device.screenshot()

    def _tap_template(self, screen, template_name: str, delay: float = None) -> bool:
        """Find template on screen and tap it. Returns False immediately if screen is None."""
        if screen is None:
            return False
        d = delay if delay is not None else self._action_delay
        return self._device.tap_if_found(screen, template_name, self._threshold, d)

    def _tap_any(self, screen, *template_names: str, delay: float = None) -> bool:
        """Try each template in order; tap the first one found. Returns True if any matched."""
        if screen is None:
            return False
        for name in template_names:
            if self._tap_template(screen, name, delay=delay):
                return True
        return False

    def _wait_template(self, template_name: str, timeout: float = 20.0):
        """Wait until a template appears on screen."""
        return self._device.wait_for_template(template_name, timeout=timeout, threshold=self._threshold)

    def _return_home(self, stop_event: threading.Event, max_attempts: int = 20) -> bool:
        """
        Navigate back to the game homescreen.

        Each iteration:
          1. Take a screenshot.
          2. If the summon button (homescreen indicator) is visible → done.
          3. If a back button is visible → tap it and wait.
          4. Otherwise → send the Android back key as a fallback and wait.

        Returns True if the homescreen was confirmed, False if max_attempts
        was reached without finding it.
        """
        for attempt in range(max_attempts):
            if self._stopped(stop_event):
                return False

            screen = self._screenshot()
            if screen is None:
                self._sleep(1.0, stop_event)
                continue

            # ── Confirmed home ────────────────────────────────────────
            if is_on_screen(screen, T_HOMESCREEN, self._threshold):
                return True

            # ── Back button visible → tap it ──────────────────────────
            pos = find_template_by_name(screen, T_BACK_BTN, self._threshold)
            if pos:
                self._device.tap(pos[0], pos[1], delay=0.3)
            else:
                # Fallback: Android system back key
                self._device.press_back()

            self._sleep(self._action_delay, stop_event)

        self._log("  WARNING: could not confirm homescreen after max attempts")
        return False
