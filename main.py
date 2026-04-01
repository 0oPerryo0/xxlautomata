"""Entry point for XXLAutomata."""

import sys
import os

# Ensure project root is on the path so all imports resolve correctly
sys.path.insert(0, os.path.dirname(__file__))

import json
from core.adb import start_adb_server
from gui.app import App

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def main():
    # Start the ADB daemon before the GUI appears so device discovery works immediately
    adb_path = "adb"
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            adb_path = json.load(f).get("device", {}).get("adb_path", "adb")
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    start_adb_server(adb_path)

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
