from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .adb import Adb, AdbError, detect_device
from .android import AndroidDevice
from .config import Config, load_config
from .flows import FlowRunner, load_flow


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default="config.json", help="Path to config JSON.")
    common.add_argument("--adb", default="adb", help="Path to adb executable.")

    parser = argparse.ArgumentParser(description="ADB automation for xxlwoofia.")
    parser.add_argument("--config", default="config.json", help="Path to config JSON.")
    parser.add_argument("--adb", default="adb", help="Path to adb executable.")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", parents=[common], help="Check adb and connected device.")
    subparsers.add_parser("launch", parents=[common], help="Open the game from the Android home screen.")
    subparsers.add_parser("dump-ui", parents=[common], help="Save the current Android UI hierarchy XML.")
    subparsers.add_parser("screenshot", parents=[common], help="Save a PNG screenshot from the device.")

    run_parser = subparsers.add_parser("run", parents=[common], help="Run an automation flow.")
    run_parser.add_argument("name", help="Flow name, for example: daily")
    run_parser.add_argument("--flow", help="Path to a flow JSON file.")
    run_parser.add_argument("--no-launch", action="store_true", help="Do not launch the game before running.")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(Path(args.config))

    try:
        device = connect(config, args.adb)
        android = AndroidDevice(Adb(serial=device.serial, adb_path=args.adb))

        if args.command == "doctor":
            print(f"ADB connected: {device.serial}")
            package = android.resolve_package(config.package, list(config.package_keywords))
            print(f"Game package: {package}")
            return 0

        if args.command == "launch":
            package = android.resolve_package(config.package, list(config.package_keywords))
            android.open_from_home(package, config.launch_wait_seconds)
            print(f"Launched {package}")
            return 0

        if args.command == "dump-ui":
            path = android.save_ui_dump(PROJECT_ROOT / "ui-dumps")
            print(f"Saved UI dump: {path}")
            return 0

        if args.command == "screenshot":
            path = android.save_screenshot(PROJECT_ROOT / "screenshots")
            print(f"Saved screenshot: {path}")
            return 0

        if args.command == "run":
            flow_path = Path(args.flow) if args.flow else default_flow_path(args.name)
            flow = load_flow(flow_path)
            package = android.resolve_package(config.package, list(config.package_keywords))
            if not args.no_launch:
                android.open_from_home(package, config.launch_wait_seconds)
            FlowRunner(android, PROJECT_ROOT, config.flow_vars()).run(flow)
            print(f"Completed flow: {flow.name}")
            return 0

        return 2
    except (AdbError, RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def connect(config: Config, adb_path: str) -> object:
    serial = config.device_serial or None
    return detect_device(adb_path=adb_path, requested_serial=serial)


def default_flow_path(name: str) -> Path:
    candidates = [
        PROJECT_ROOT / "flows" / f"{name}.json",
        PROJECT_ROOT / "flows" / f"{name}_mission.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Flow not found. Tried: " + ", ".join(str(path) for path in candidates)
    )
