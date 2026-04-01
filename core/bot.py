"""Bot orchestrator — runs enabled automation modules in sequence."""

import threading
import time
from typing import Callable, Optional

from core.adb import ADBDevice
from utils.logger import get_logger

log = get_logger("bot")


class Bot:
    def __init__(self, device: ADBDevice, config: dict, log_callback: Optional[Callable[[str], None]] = None):
        self._device = device
        self._config = config
        self._log_callback = log_callback
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        if self._running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True

    def stop(self):
        self._stop_event.set()
        self._running = False
        self._log("Bot stopped.")

    @property
    def running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _log(self, msg: str):
        log.info(msg)
        if self._log_callback:
            self._log_callback(msg)

    def _build_modules(self) -> list:
        """Instantiate enabled automation modules based on config."""
        features = self._config.get("features", {})
        modules = []

        if features.get("daily_missions"):
            from automations.daily_missions import DailyMissionsAutomation
            modules.append(DailyMissionsAutomation(self._device, self._config, self._log))

        if features.get("part_time_jobs"):
            from automations.part_time_jobs import PartTimeJobsAutomation
            modules.append(PartTimeJobsAutomation(self._device, self._config, self._log))

        if features.get("workshop"):
            from automations.workshop import WorkshopAutomation
            modules.append(WorkshopAutomation(self._device, self._config, self._log))

        if features.get("card_game"):
            from automations.card_game import CardGameAutomation
            modules.append(CardGameAutomation(self._device, self._config, self._log))

        if features.get("guild"):
            from automations.guild import GuildAutomation
            modules.append(GuildAutomation(self._device, self._config, self._log))

        if features.get("summons"):
            from automations.summons import SummonsAutomation
            modules.append(SummonsAutomation(self._device, self._config, self._log))

        if features.get("shop"):
            from automations.shop import ShopAutomation
            modules.append(ShopAutomation(self._device, self._config, self._log))

        return modules

    def _run(self):
        self._log("Bot started.")

        if not self._device.connected:
            self._log("ERROR: Device not connected. Stopping.")
            self._running = False
            return

        if not self._device.is_game_running():
            self._log("Game not running — launching...")
            self._device.launch_game()

        modules = self._build_modules()
        if not modules:
            self._log("No features enabled. Nothing to do.")
            self._running = False
            return

        for module in modules:
            if self._stop_event.is_set():
                break
            name = module.__class__.__name__
            self._log(f"--- Running: {name} ---")
            try:
                module.run(self._stop_event)
            except Exception as e:
                self._log(f"ERROR in {name}: {e}")
                log.exception(f"Unhandled error in {name}")

        self._log("All tasks complete.")
        self._running = False
