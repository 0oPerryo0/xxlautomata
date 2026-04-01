"""Automates collecting part-time job rewards (passive gold/rewards)."""

import threading

from automations.base import BaseAutomation


class PartTimeJobsAutomation(BaseAutomation):
    """
    Flow:
        1. Open part-time job screen
        2. Collect all completed jobs
        3. Re-dispatch available jobs
        4. Close screen
    """

    T_JOBS_BTN = "part_time_jobs/jobs_button.png"
    T_COLLECT_BTN = "part_time_jobs/collect_button.png"
    T_COLLECT_ALL_BTN = "part_time_jobs/collect_all_button.png"
    T_DISPATCH_BTN = "part_time_jobs/dispatch_button.png"
    T_CONFIRM_BTN = "part_time_jobs/confirm_button.png"
    T_CLOSE_BTN = "common/close_button.png"
    T_OK_BTN = "common/ok_button.png"

    def run(self, stop_event: threading.Event):
        self._log("Part-Time Jobs: opening")

        screen = self._screenshot()
        if screen is None:
            return

        if not self._tap_template(screen, self.T_JOBS_BTN):
            self._log("Part-Time Jobs: could not find Jobs button — skipping")
            return

        self._sleep(self._long_delay, stop_event)
        if self._stopped(stop_event):
            return

        # Try collect all first
        screen = self._screenshot()
        if screen is not None:
            if self._tap_template(screen, self.T_COLLECT_ALL_BTN):
                self._log("Part-Time Jobs: collected all rewards")
                self._sleep(self._action_delay, stop_event)
                screen = self._screenshot()
                if screen is not None:
                    self._tap_template(screen, self.T_OK_BTN)
            else:
                # Collect individually
                collected = 0
                for _ in range(10):
                    if self._stopped(stop_event):
                        break
                    screen = self._screenshot()
                    if screen is None:
                        break
                    if self._tap_template(screen, self.T_COLLECT_BTN):
                        collected += 1
                        self._sleep(self._action_delay, stop_event)
                        screen = self._screenshot()
                        if screen is not None:
                            self._tap_template(screen, self.T_OK_BTN)
                            self._sleep(0.5, stop_event)
                    else:
                        break
                self._log(f"Part-Time Jobs: collected {collected} reward(s)")

        self._sleep(self._action_delay, stop_event)

        # Re-dispatch available job slots
        dispatched = 0
        for _ in range(5):
            if self._stopped(stop_event):
                break
            screen = self._screenshot()
            if screen is None:
                break
            if self._tap_template(screen, self.T_DISPATCH_BTN):
                self._sleep(self._action_delay, stop_event)
                screen = self._screenshot()
                if screen is not None:
                    if self._tap_template(screen, self.T_CONFIRM_BTN):
                        dispatched += 1
                        self._sleep(self._action_delay, stop_event)
            else:
                break

        self._log(f"Part-Time Jobs: dispatched {dispatched} job(s)")

        screen = self._screenshot()
        if screen is not None:
            self._tap_template(screen, self.T_CLOSE_BTN)

        self._log("Part-Time Jobs: done")
