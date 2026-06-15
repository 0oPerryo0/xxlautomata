from __future__ import annotations

import re
import time
from pathlib import Path
from xml.etree import ElementTree

from .adb import Adb, AdbError


BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def parse_bounds(bounds: str) -> tuple[int, int, int, int]:
    match = BOUNDS_RE.fullmatch(bounds or "")
    if not match:
        raise ValueError(f"Invalid Android bounds: {bounds!r}")
    return tuple(int(value) for value in match.groups())  # type: ignore[return-value]


def bounds_center(bounds: str) -> tuple[int, int]:
    left, top, right, bottom = parse_bounds(bounds)
    return (left + right) // 2, (top + bottom) // 2


class AndroidDevice:
    def __init__(self, adb: Adb) -> None:
        self.adb = adb

    def installed_packages(self) -> list[str]:
        output = self.adb.shell(["cmd", "package", "list", "packages"], timeout=30)
        packages: list[str] = []
        for line in output.splitlines():
            if line.startswith("package:"):
                packages.append(line.removeprefix("package:").strip())
        return packages

    def resolve_package(self, configured_package: str, keywords: list[str]) -> str:
        if configured_package:
            return configured_package

        packages = self.installed_packages()
        lowered_keywords = [keyword.lower() for keyword in keywords if keyword]
        matches = [
            package
            for package in packages
            if any(keyword in package.lower() for keyword in lowered_keywords)
        ]

        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise AdbError(
                "Multiple possible game packages found: "
                + ", ".join(matches)
                + ". Set package in config.json."
            )
        raise AdbError("Could not auto-detect the game package. Set package in config.json.")

    def open_from_home(self, package: str, launch_wait_seconds: float) -> None:
        self.adb.shell(["input", "keyevent", "KEYCODE_HOME"], timeout=10)
        time.sleep(1)
        self.adb.run(
            ["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"],
            timeout=20,
        )
        time.sleep(launch_wait_seconds)

    def tap(self, x: int, y: int) -> None:
        self.adb.shell(["input", "tap", str(x), str(y)], timeout=10)

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 350) -> None:
        self.adb.shell(
            [
                "input",
                "swipe",
                str(start_x),
                str(start_y),
                str(end_x),
                str(end_y),
                str(duration_ms),
            ],
            timeout=10,
        )

    def press(self, key: str) -> None:
        key = key if key.startswith("KEYCODE_") else f"KEYCODE_{key}"
        self.adb.shell(["input", "keyevent", key], timeout=10)

    def dump_ui_xml(self) -> str:
        remote_path = "/sdcard/xxlwoofia-window.xml"
        self.adb.shell(["uiautomator", "dump", remote_path], timeout=20)
        return self.adb.shell(["cat", remote_path], timeout=20)

    def screenshot_png(self) -> bytes:
        return self.adb.run_bytes(["exec-out", "screencap", "-p"], timeout=20).stdout

    def save_screenshot(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"screenshot-{int(time.time())}.png"
        path.write_bytes(self.screenshot_png())
        return path

    def save_ui_dump(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"ui-{int(time.time())}.xml"
        path.write_text(self.dump_ui_xml(), encoding="utf-8")
        return path

    def find_node(self, selector: dict[str, object]) -> ElementTree.Element | None:
        xml = self.dump_ui_xml()
        root = ElementTree.fromstring(xml)
        nodes = list(root.iter("node"))
        matches = [node for node in nodes if node_matches(node, selector)]
        index = int(selector.get("index", 0))
        if index < len(matches):
            return matches[index]
        return None

    def tap_selector(self, selector: dict[str, object], timeout_seconds: float = 8.0) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() <= deadline:
            node = self.find_node(selector)
            if node is not None:
                bounds = node.attrib.get("bounds", "")
                x, y = bounds_center(bounds)
                self.tap(x, y)
                return True
            time.sleep(0.5)
        return False


def node_matches(node: ElementTree.Element, selector: dict[str, object]) -> bool:
    checks = {
        "text": "text",
        "content_desc": "content-desc",
        "resource_id": "resource-id",
        "class_name": "class",
    }
    contains_checks = {
        "text_contains": "text",
        "content_desc_contains": "content-desc",
        "resource_id_contains": "resource-id",
    }

    for selector_key, attr_name in checks.items():
        expected = selector.get(selector_key)
        if expected is not None and node.attrib.get(attr_name, "") != str(expected):
            return False

    for selector_key, attr_name in contains_checks.items():
        expected = selector.get(selector_key)
        if expected is None:
            continue
        actual = node.attrib.get(attr_name, "")
        if str(expected).lower() not in actual.lower():
            return False

    return True
