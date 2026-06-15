from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .android import AndroidDevice
from .vision import find_template, find_text


@dataclass(frozen=True)
class Flow:
    name: str
    description: str
    steps: list[dict[str, object]]


class StopFlow(RuntimeError):
    pass


def load_flow(path: Path) -> Flow:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return Flow(
        name=str(data.get("name", path.stem)),
        description=str(data.get("description", "")),
        steps=list(data.get("steps", [])),
    )


class FlowRunner:
    def __init__(self, device: AndroidDevice, base_dir: Path, variables: dict[str, object] | None = None) -> None:
        self.device = device
        self.base_dir = base_dir
        self.variables = variables or {}
        self.counters: dict[str, int] = {}

    def run(self, flow: Flow) -> None:
        try:
            self._run_steps(flow.steps, total=len(flow.steps))
        except StopFlow as exc:
            print(str(exc))
        if self.counters:
            summary = ", ".join(f"{name}={value}" for name, value in sorted(self.counters.items()))
            print(f"Counters: {summary}")

    def _run_steps(self, steps: list[dict[str, object]], *, total: int | None = None) -> None:
        count = total or len(steps)
        for index, step in enumerate(steps, start=1):
            action = str(step.get("action", "")).strip()
            label = str(step.get("label", f"step {index}"))
            print(f"[{index}/{count}] {label}")
            self._run_step(action, self._resolve(step), label)

    def _run_step(self, action: str, step: dict[str, Any], label: str) -> None:
        if action == "log":
            print(str(step.get("message", label)))
        elif action == "stop":
            raise StopFlow(str(step.get("message", "Flow stopped.")))
        elif action == "wait":
            time.sleep(float(step.get("seconds", 1)))
        elif action == "repeat":
            repeat = int(step.get("times", 1))
            delay = float(step.get("delay_seconds", 0))
            nested_steps = list(step.get("steps", []))
            for _ in range(repeat):
                self._run_steps(nested_steps)
                if delay:
                    time.sleep(delay)
        elif action == "wait_image":
            found = self._wait_image_step(step)
            if not found and not bool(step.get("optional", False)):
                raise RuntimeError(f"Could not find image for {label}: {step.get('template')}")
        elif action == "wait_ocr":
            found = self._wait_ocr_step(step)
            if not found and not bool(step.get("optional", False)):
                raise RuntimeError(f"Could not find OCR text for {label}: {self._ocr_query(step)}")
        elif action == "tap":
            self.device.tap(int(step["x"]), int(step["y"]))
            self._after_success(step)
        elif action == "tap_selector":
            self._tap_selector_step(step, label)
        elif action == "tap_image":
            found = self._tap_image_step(step)
            if not found and not bool(step.get("optional", False)):
                raise RuntimeError(f"Could not find image for {label}: {step.get('template')}")
        elif action == "tap_ocr":
            found = self._tap_ocr_step(step)
            if not found and not bool(step.get("optional", False)):
                raise RuntimeError(f"Could not find OCR text for {label}: {self._ocr_query(step)}")
        elif action == "tap_ocr_scroll":
            found = self._tap_ocr_scroll_step(step)
            if not found and not bool(step.get("optional", False)):
                raise RuntimeError(f"Could not find OCR text after scrolling for {label}: {self._ocr_query(step)}")
        elif action == "handle_stamina_popup":
            self._handle_stamina_popup_step(step)
        elif action == "if_image":
            wait_for_match = "timeout_seconds" in step
            branch = "then" if self._wait_image_step(step, tap=False, once=not wait_for_match) else "else"
            self._run_steps(list(step.get(branch, [])))
        elif action == "if_ocr":
            wait_for_match = "timeout_seconds" in step
            branch = "then" if self._wait_ocr_step(step, tap=False, once=not wait_for_match) else "else"
            self._run_steps(list(step.get(branch, [])))
        elif action == "if_var":
            branch = "then" if bool(self.variables.get(str(step["name"]), False)) else "else"
            self._run_steps(list(step.get(branch, [])))
        elif action == "stop_if_image":
            if self._wait_image_step(step, tap=False, once=True):
                raise StopFlow(str(step.get("message", "Stopping flow because stop image was found.")))
        elif action == "stop_if_ocr":
            if self._wait_ocr_step(step, tap=False, once=True):
                raise StopFlow(str(step.get("message", "Stopping flow because stop OCR text was found.")))
        elif action == "press":
            self.device.press(str(step["key"]))
            self._after_success(step)
        elif action == "swipe":
            self.device.swipe(
                int(step["start_x"]),
                int(step["start_y"]),
                int(step["end_x"]),
                int(step["end_y"]),
                int(step.get("duration_ms", 350)),
            )
            self._after_success(step)
        else:
            raise RuntimeError(f"Unknown flow action: {action}")

    def _tap_selector_step(self, step: dict[str, Any], label: str) -> None:
        selector = dict(step.get("selector", {}))
        timeout_seconds = float(step.get("timeout_seconds", selector.get("timeout_seconds", 8)))
        optional = bool(step.get("optional", selector.get("optional", False)))
        found = self.device.tap_selector(selector, timeout_seconds=timeout_seconds)
        if not found and not optional:
            raise RuntimeError(f"Could not find selector for {label}: {selector}")
        if found:
            self._after_success(step)

    def _tap_image_step(self, step: dict[str, Any]) -> bool:
        found = self._wait_image_step(step, tap=True)
        if found:
            self._after_success(step)
        return found

    def _wait_image_step(self, step: dict[str, Any], *, tap: bool = False, once: bool = False) -> bool:
        template = self._template_path(str(step["template"]))
        threshold = float(step.get("threshold", 0.82))
        timeout_seconds = 0.1 if once else float(step.get("timeout_seconds", 8))
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() <= deadline:
            match = find_template(self.device.screenshot_png(), template, threshold)
            if match is not None:
                x, y, score = match
                print(f"  matched {template.name} at {score:.3f}")
                if tap:
                    self.device.tap(x, y)
                return True
            if once:
                return False
            time.sleep(float(step.get("poll_seconds", 0.5)))
        return False

    def _tap_ocr_step(self, step: dict[str, Any]) -> bool:
        result = self._wait_ocr_step(step, tap=True)
        if result:
            self._after_success(step)
        return result

    def _tap_ocr_scroll_step(self, step: dict[str, Any]) -> bool:
        attempts = int(step.get("attempts", 8))
        settle_seconds = float(step.get("settle_seconds", 0.8))
        scan_timeout = float(step.get("scan_timeout_seconds", 1.2))
        swipe = dict(step.get("swipe", {}))

        for attempt in range(1, attempts + 1):
            print(f"  OCR scan attempt {attempt}/{attempts}")
            scan_step = dict(step)
            scan_step["timeout_seconds"] = scan_timeout
            if self._wait_ocr_step(scan_step, tap=True):
                self._after_success(step)
                return True
            if attempt == attempts:
                break
            self.device.swipe(
                int(swipe.get("start_x", 540)),
                int(swipe.get("start_y", 1450)),
                int(swipe.get("end_x", 540)),
                int(swipe.get("end_y", 650)),
                int(swipe.get("duration_ms", 450)),
            )
            time.sleep(settle_seconds)
        return False

    def _wait_ocr_step(self, step: dict[str, Any], *, tap: bool = False, once: bool = False) -> bool:
        timeout_seconds = 0.1 if once else float(step.get("timeout_seconds", 8))
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() <= deadline:
            match = find_text(
                self.device.screenshot_png(),
                text=self._maybe_string(step.get("text")),
                contains=self._maybe_string(step.get("contains")),
                regex=self._maybe_string(step.get("regex")),
                lang=str(step.get("lang", self.variables.get("ocr_language", "eng"))),
                confidence=int(step.get("confidence", 40)),
                tesseract_cmd=self._maybe_string(self.variables.get("tesseract_cmd")),
            )
            if match is not None:
                x, y, value, confidence = match
                print(f"  OCR matched {value!r} at confidence {confidence}")
                if tap:
                    self.device.tap(x, y)
                return True
            if once:
                return False
            time.sleep(float(step.get("poll_seconds", 0.7)))
        return False

    def _handle_stamina_popup_step(self, step: dict[str, Any]) -> None:
        self.variables["hard_mode_skip_ready"] = True
        popup = str(step.get("popup_template", "assets/templates/daily_missions/stamina_not_enough_popup.png"))
        threshold = float(step.get("threshold", 0.82))
        popup_wait = float(step.get("popup_timeout_seconds", 1.5))

        if not self._image_present(popup, threshold, popup_wait):
            print("  stamina popup not found; continuing to skip-count popup")
            return

        use_small = bool(self.variables.get("use_small_stamina_items", False))
        use_big = bool(self.variables.get("use_big_stamina_items", False))
        use_items = bool(self.variables.get("use_stamina_items", False) or use_small or use_big)
        if use_items and not use_small and not use_big:
            use_small = True
            use_big = True

        if not use_items or (not use_small and not use_big):
            self._cancel_stamina_popup(step, threshold)
            self.variables["hard_mode_skip_ready"] = False
            print("  stamina restore disabled; skipping hard-mode skip task")
            return

        restored = 0
        target = int(self.variables.get("max_stamina_restore", step.get("max_restore", 60)))
        small_template = str(step.get("small_template", "assets/templates/daily_missions/stamina_item_10.png"))
        big_template = str(step.get("big_template", "assets/templates/daily_missions/stamina_item_60.png"))
        confirm_template = str(step.get("confirm_template", "assets/templates/common/confirm_button.png"))

        if use_small:
            while restored < target:
                if not self._use_stamina_item(small_template, confirm_template, 10, threshold):
                    break
                restored += 10

        if restored < target and use_big:
            if self._use_stamina_item(big_template, confirm_template, 60, threshold):
                restored += 60

        self._cancel_stamina_popup(step, threshold)

        if restored <= 0:
            self.variables["hard_mode_skip_ready"] = False
            print("  no configured stamina item was available; skipping hard-mode skip task")
            return

        self.counters["stamina_restored"] = self.counters.get("stamina_restored", 0) + restored
        print(f"  restored stamina estimate: {restored}")
        self._retry_skip_after_stamina(step, popup, threshold)

    def _use_stamina_item(self, item_template: str, confirm_template: str, amount: int, threshold: float) -> bool:
        if not self._tap_image_template(item_template, threshold=threshold, timeout_seconds=1.5):
            return False
        print(f"  selected +{amount} stamina item")
        if not self._tap_image_template(confirm_template, threshold=threshold, timeout_seconds=4, optional=True):
            print("  confirm button not found after selecting stamina item")
        time.sleep(0.8)
        return True

    def _cancel_stamina_popup(self, step: dict[str, Any], threshold: float) -> None:
        cancel_template = str(step.get("cancel_template", "assets/templates/common/cancel_button.png"))
        self._tap_image_template(cancel_template, threshold=threshold, timeout_seconds=4, optional=True)

    def _retry_skip_after_stamina(self, step: dict[str, Any], popup_template: str, threshold: float) -> None:
        skip_template = str(step.get("skip_template", "assets/templates/daily_missions/skip_ticket_button.png"))
        if not self._tap_image_template(skip_template, threshold=threshold, timeout_seconds=8, optional=True):
            self.variables["hard_mode_skip_ready"] = False
            print("  skip button not found after stamina restore; skipping hard-mode skip task")
            return
        time.sleep(1)
        if self._image_present(popup_template, threshold, timeout_seconds=1.5):
            self._cancel_stamina_popup(step, threshold)
            self.variables["hard_mode_skip_ready"] = False
            print("  stamina still not enough after restore; skipping hard-mode skip task")
        else:
            self.variables["hard_mode_skip_ready"] = True

    def _tap_image_template(
        self,
        template: str,
        *,
        threshold: float,
        timeout_seconds: float,
        optional: bool = False,
    ) -> bool:
        found = self._wait_image_step(
            {
                "template": template,
                "threshold": threshold,
                "timeout_seconds": timeout_seconds,
                "optional": optional,
            },
            tap=True,
        )
        return found

    def _image_present(self, template: str, threshold: float, timeout_seconds: float) -> bool:
        return self._wait_image_step(
            {
                "template": template,
                "threshold": threshold,
                "timeout_seconds": timeout_seconds,
            },
            tap=False,
        )

    def _after_success(self, step: dict[str, Any]) -> None:
        counter = self._maybe_string(step.get("counter"))
        if counter:
            self.counters[counter] = self.counters.get(counter, 0) + int(step.get("increment", 1))
        time.sleep(float(step.get("after_seconds", 0.8)))

    def _template_path(self, path: str) -> Path:
        template = Path(path)
        if template.is_absolute():
            return template
        return self.base_dir / template

    def _resolve(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._resolve(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._resolve(item) for item in value]
        if isinstance(value, str):
            return self._format_value(value)
        return value

    def _format_value(self, value: str) -> str:
        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            return str(self.variables.get(key, match.group(0)))

        return re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", replace, value)

    @staticmethod
    def _maybe_string(value: object) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _ocr_query(step: dict[str, Any]) -> str:
        return str(step.get("text") or step.get("contains") or step.get("regex") or "")
