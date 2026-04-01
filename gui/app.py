"""Main tkinter GUI for XXLAutomata."""

import json
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from core.adb import ADBDevice
from core.bot import Bot

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

FEATURES = [
    ("daily_missions", "Daily Missions"),
    ("part_time_jobs", "Part-Time Jobs"),
    ("workshop", "Workshop / Gym (3x)"),
    ("card_game", "Card Matching Game (3x)"),
    ("guild", "Guild Gifts"),
    ("summons", "Daily Free Summons"),
    ("shop", "Auto Shop Purchases"),
]

DARK_BG = "#1e1e2e"
PANEL_BG = "#2a2a3e"
ACCENT = "#7c3aed"
ACCENT_HOVER = "#6d28d9"
FG = "#e0e0f0"
GREEN = "#22c55e"
RED = "#ef4444"
YELLOW = "#facc15"
MONO = ("Consolas", 9)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("XXLAutomata — XXL WOOFIA Bot")
        self.resizable(False, False)
        self.configure(bg=DARK_BG)

        self._config = self._load_config()
        self._device = ADBDevice(
            serial=self._config["device"].get("serial", ""),
            adb_path=self._config["device"].get("adb_path", "adb"),
        )
        self._bot: Bot | None = None
        self._feature_vars: dict[str, tk.BooleanVar] = {}

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Config I/O
    # ------------------------------------------------------------------

    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_config(self):
        # Update feature flags from checkboxes
        for key, var in self._feature_vars.items():
            self._config["features"][key] = var.get()
        # Update device serial
        self._config["device"]["serial"] = self._device_var.get().strip()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=4)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        # ── Title bar ──────────────────────────────────────────────────
        title_frame = tk.Frame(self, bg=ACCENT)
        title_frame.pack(fill="x")
        tk.Label(
            title_frame, text="XXLAutomata", bg=ACCENT, fg="white",
            font=("Segoe UI", 16, "bold"), pady=8,
        ).pack(side="left", padx=16)
        tk.Label(
            title_frame, text="XXL WOOFIA automation tool", bg=ACCENT, fg="#d8b4fe",
            font=("Segoe UI", 9),
        ).pack(side="left")

        # ── Main layout ───────────────────────────────────────────────
        main = tk.Frame(self, bg=DARK_BG)
        main.pack(fill="both", expand=True, padx=16, pady=12)

        left = tk.Frame(main, bg=DARK_BG)
        left.pack(side="left", fill="y", padx=(0, 12))

        right = tk.Frame(main, bg=DARK_BG)
        right.pack(side="left", fill="both", expand=True)

        # ── Device panel ──────────────────────────────────────────────
        self._build_device_panel(left)

        # ── Features panel ───────────────────────────────────────────
        self._build_features_panel(left)

        # ── Daily missions settings ───────────────────────────────────
        self._build_daily_panel(left)

        # ── Shop options ─────────────────────────────────────────────
        self._build_shop_panel(left)

        # ── Control buttons ──────────────────────────────────────────
        self._build_controls(left)

        # ── Log panel ────────────────────────────────────────────────
        self._build_log_panel(right)

    def _section_label(self, parent, text: str):
        f = tk.Frame(parent, bg=PANEL_BG, bd=0)
        f.pack(fill="x", pady=(8, 2))
        tk.Label(f, text=text, bg=PANEL_BG, fg=ACCENT, font=("Segoe UI", 10, "bold"), pady=4, padx=8).pack(anchor="w")
        return f

    def _build_device_panel(self, parent):
        self._section_label(parent, "Device")
        frame = tk.Frame(parent, bg=PANEL_BG)
        frame.pack(fill="x", pady=(0, 4))

        tk.Label(frame, text="Serial / Address:", bg=PANEL_BG, fg=FG, font=("Segoe UI", 9), padx=8).pack(anchor="w")

        row = tk.Frame(frame, bg=PANEL_BG)
        row.pack(fill="x", padx=8, pady=4)

        self._device_var = tk.StringVar(value=self._config["device"].get("serial", ""))
        entry = tk.Entry(row, textvariable=self._device_var, bg="#3a3a52", fg=FG,
                         insertbackground=FG, relief="flat", font=MONO, width=24)
        entry.pack(side="left", ipady=4)

        self._connect_btn = self._make_button(row, "Connect", self._on_connect, width=10)
        self._connect_btn.pack(side="left", padx=(6, 0))

        self._status_dot = tk.Label(frame, text="● Not connected", bg=PANEL_BG, fg=RED,
                                    font=("Segoe UI", 9), padx=8, pady=4)
        self._status_dot.pack(anchor="w")

        # Device list dropdown
        tk.Label(frame, text="Detected devices:", bg=PANEL_BG, fg=FG, font=("Segoe UI", 9), padx=8).pack(anchor="w")
        self._device_list_var = tk.StringVar()
        self._device_combo = ttk.Combobox(frame, textvariable=self._device_list_var, width=30,
                                           state="readonly", font=MONO)
        self._device_combo.pack(padx=8, pady=(2, 6), anchor="w")
        self._device_combo.bind("<<ComboboxSelected>>", self._on_device_selected)

        self._make_button(frame, "Refresh Devices", self._on_refresh_devices, width=18).pack(padx=8, pady=(0, 6), anchor="w")

    def _build_features_panel(self, parent):
        self._section_label(parent, "Features")
        frame = tk.Frame(parent, bg=PANEL_BG)
        frame.pack(fill="x", pady=(0, 4))

        features_cfg = self._config.get("features", {})
        for key, label in FEATURES:
            var = tk.BooleanVar(value=features_cfg.get(key, False))
            self._feature_vars[key] = var
            cb = tk.Checkbutton(
                frame, text=label, variable=var,
                bg=PANEL_BG, fg=FG, selectcolor="#3a3a52",
                activebackground=PANEL_BG, activeforeground=FG,
                font=("Segoe UI", 9), padx=8, pady=2, anchor="w",
            )
            cb.pack(fill="x")

        btn_row = tk.Frame(frame, bg=PANEL_BG)
        btn_row.pack(fill="x", padx=8, pady=4)
        self._make_button(btn_row, "All", lambda: self._toggle_all(True), width=6).pack(side="left")
        self._make_button(btn_row, "None", lambda: self._toggle_all(False), width=6).pack(side="left", padx=4)

    def _build_daily_panel(self, parent):
        self._section_label(parent, "Daily Missions Settings")
        frame = tk.Frame(parent, bg=PANEL_BG)
        frame.pack(fill="x", pady=(0, 4))

        tk.Label(
            frame,
            text="Hard Mode Stage  (exact name shown in-game, e.g. '3-5 Hard')",
            bg=PANEL_BG, fg=FG, font=("Segoe UI", 9), padx=8, wraplength=260, justify="left",
        ).pack(anchor="w", pady=(4, 0))

        self._hard_stage_var = tk.StringVar(
            value=self._config.get("daily_missions", {}).get("hard_mode_stage", "")
        )
        tk.Entry(
            frame, textvariable=self._hard_stage_var,
            bg="#3a3a52", fg=FG, insertbackground=FG,
            relief="flat", font=MONO, width=22,
        ).pack(padx=8, pady=(2, 6), anchor="w")

        tk.Label(
            frame,
            text="Leave blank to skip the Hard Mode step.",
            bg=PANEL_BG, fg="#888899", font=("Segoe UI", 8), padx=8,
        ).pack(anchor="w", pady=(0, 4))

    def _build_shop_panel(self, parent):
        self._section_label(parent, "Shop Options")
        frame = tk.Frame(parent, bg=PANEL_BG)
        frame.pack(fill="x", pady=(0, 4))

        shop_cfg = self._config.get("shop", {})

        self._buy_silver_var = tk.BooleanVar(value=shop_cfg.get("buy_with_silver_bells", False))
        self._buy_golden_var = tk.BooleanVar(value=shop_cfg.get("buy_with_golden_bells", False))

        for var, label in [
            (self._buy_silver_var, "Buy with Silver Bells"),
            (self._buy_golden_var, "Buy with Golden Bells"),
        ]:
            tk.Checkbutton(
                frame, text=label, variable=var,
                bg=PANEL_BG, fg=FG, selectcolor="#3a3a52",
                activebackground=PANEL_BG, activeforeground=FG,
                font=("Segoe UI", 9), padx=8, pady=2, anchor="w",
            ).pack(fill="x")

        tk.Label(frame, text="Max Golden Bells to spend (0=unlimited):", bg=PANEL_BG, fg=FG,
                 font=("Segoe UI", 9), padx=8).pack(anchor="w")
        self._max_bells_var = tk.StringVar(value=str(shop_cfg.get("max_golden_bells_spend", 0)))
        tk.Entry(frame, textvariable=self._max_bells_var, bg="#3a3a52", fg=FG, insertbackground=FG,
                 relief="flat", font=MONO, width=8).pack(padx=8, pady=(0, 6), anchor="w")

    def _build_controls(self, parent):
        frame = tk.Frame(parent, bg=DARK_BG)
        frame.pack(fill="x", pady=8)

        self._start_btn = self._make_button(frame, "▶  Start Bot", self._on_start, bg=GREEN, fg="white", width=16)
        self._start_btn.pack(side="left")

        self._stop_btn = self._make_button(frame, "■  Stop", self._on_stop, bg=RED, fg="white", width=10)
        self._stop_btn.pack(side="left", padx=6)
        self._stop_btn.config(state="disabled")

        self._make_button(frame, "Save Config", self._on_save_config, width=12).pack(side="left")

    def _build_log_panel(self, parent):
        tk.Label(parent, text="Activity Log", bg=DARK_BG, fg=ACCENT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")

        self._log_box = scrolledtext.ScrolledText(
            parent, state="disabled", bg="#12121e", fg="#a0a0c0",
            font=MONO, relief="flat", width=60, height=30,
            insertbackground=FG,
        )
        self._log_box.pack(fill="both", expand=True, pady=(4, 0))

        clear_btn = self._make_button(parent, "Clear Log", self._clear_log, width=10)
        clear_btn.pack(anchor="e", pady=4)

    # ------------------------------------------------------------------
    # Button factory
    # ------------------------------------------------------------------

    def _make_button(self, parent, text: str, command, bg=None, fg=FG, width=None, **kw) -> tk.Button:
        bg = bg or PANEL_BG
        btn = tk.Button(
            parent, text=text, command=command, bg=bg, fg=fg,
            activebackground=ACCENT_HOVER, activeforeground="white",
            relief="flat", font=("Segoe UI", 9, "bold"),
            cursor="hand2", padx=8, pady=4,
            **({"width": width} if width else {}),
            **kw,
        )
        return btn

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_connect(self):
        serial = self._device_var.get().strip()
        self._device = ADBDevice(
            serial=serial,
            adb_path=self._config["device"].get("adb_path", "adb"),
        )
        self._log_ui("Connecting to device...")
        ok = self._device.connect()
        if ok:
            self._status_dot.config(text=f"● Connected: {self._device._device.serial}", fg=GREEN)
            self._log_ui(f"Connected to {self._device._device.serial}")
        else:
            self._status_dot.config(text="● Connection failed", fg=RED)
            self._log_ui("Connection failed. Check ADB and device.")

    def _on_refresh_devices(self):
        devices = self._device.list_devices()
        self._device_combo["values"] = devices if devices else ["(none found)"]
        if devices:
            self._device_combo.current(0)
        self._log_ui(f"Found {len(devices)} device(s): {', '.join(devices) or 'none'}")

    def _on_device_selected(self, _event=None):
        val = self._device_list_var.get()
        if val and val != "(none found)":
            self._device_var.set(val)

    def _on_start(self):
        if not self._device.connected:
            messagebox.showwarning("Not Connected", "Please connect to a device first.")
            return

        self._apply_shop_config()
        self._save_config()

        self._bot = Bot(self._device, self._config, self._log_ui)
        self._bot.start()

        self._start_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self._log_ui("Bot started.")

        # Poll for completion
        self._poll_bot()

    def _poll_bot(self):
        if self._bot and not self._bot.running:
            self._start_btn.config(state="normal")
            self._stop_btn.config(state="disabled")
            self._log_ui("Bot finished.")
        else:
            self.after(1000, self._poll_bot)

    def _on_stop(self):
        if self._bot:
            self._bot.stop()
        self._start_btn.config(state="normal")
        self._stop_btn.config(state="disabled")

    def _on_save_config(self):
        self._apply_shop_config()
        self._save_config()
        self._log_ui("Config saved.")

    def _apply_shop_config(self):
        self._config["shop"]["buy_with_silver_bells"] = self._buy_silver_var.get()
        self._config["shop"]["buy_with_golden_bells"] = self._buy_golden_var.get()
        try:
            self._config["shop"]["max_golden_bells_spend"] = int(self._max_bells_var.get())
        except ValueError:
            self._config["shop"]["max_golden_bells_spend"] = 0
        for key, var in self._feature_vars.items():
            self._config["features"][key] = var.get()
        if "daily_missions" not in self._config:
            self._config["daily_missions"] = {}
        self._config["daily_missions"]["hard_mode_stage"] = self._hard_stage_var.get().strip()

    def _toggle_all(self, value: bool):
        for var in self._feature_vars.values():
            var.set(value)

    def _on_close(self):
        if self._bot:
            self._bot.stop()
        self.destroy()

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_ui(self, msg: str):
        """Thread-safe log to the scrolled text widget."""
        def _append():
            self._log_box.config(state="normal")
            self._log_box.insert("end", msg + "\n")
            self._log_box.see("end")
            self._log_box.config(state="disabled")
        self.after(0, _append)

    def _clear_log(self):
        self._log_box.config(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.config(state="disabled")
