"""ADB device wrapper — screenshot, tap, swipe, key events."""

import io
import subprocess
import time
from typing import Optional, Tuple

import numpy as np
from PIL import Image

from utils.image import find_template_by_name

try:
    import adbutils
except ImportError:
    adbutils = None  # type: ignore

from utils.logger import get_logger

log = get_logger("adb")

PACKAGE_NAME = "com.megagames.xxlwoofia"


def start_adb_server(adb_path: str = "adb") -> bool:
    """
    Run `adb start-server` so the daemon is running before any connection attempt.
    Returns True if the command succeeded (exit code 0), False otherwise.
    Called once at program startup.
    """
    try:
        result = subprocess.run(
            [adb_path, "start-server"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            log.info("ADB server started")
            return True
        log.warning(f"adb start-server exited {result.returncode}: {result.stderr.strip()}")
        return False
    except FileNotFoundError:
        log.error(f"'{adb_path}' not found — install Android Platform Tools and add to PATH")
        return False
    except subprocess.TimeoutExpired:
        log.error("adb start-server timed out")
        return False


class ADBDevice:
    def __init__(self, serial: str = "", adb_path: str = "adb"):
        self._serial = serial
        self._adb_path = adb_path
        self._device = None
        self._connected = False

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Connect to device/emulator. Returns True on success."""
        if adbutils is None:
            log.error("adbutils not installed. Run: pip install adbutils")
            return False
        try:
            client = adbutils.AdbClient(host="127.0.0.1", port=5037)
            if self._serial:
                self._device = client.device(self._serial)
            else:
                devices = client.device_list()
                if not devices:
                    log.error("No ADB devices found. Start your emulator or connect a device.")
                    return False
                self._device = client.device(devices[0].serial)
                log.info(f"Auto-selected device: {devices[0].serial}")
            self._connected = True
            log.info(f"Connected to {self._device.serial}")
            return True
        except Exception as e:
            log.error(f"ADB connection failed: {e}")
            return False

    def disconnect(self):
        self._connected = False
        self._device = None

    @property
    def connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------
    # Device info
    # ------------------------------------------------------------------

    def list_devices(self) -> list[str]:
        """Return list of connected device serials."""
        if adbutils is None:
            return []
        try:
            client = adbutils.AdbClient(host="127.0.0.1", port=5037)
            return [d.serial for d in client.device_list()]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Screen capture
    # ------------------------------------------------------------------

    def screenshot(self) -> Optional[np.ndarray]:
        """Capture the screen and return as an OpenCV BGR numpy array."""
        if not self._connected or self._device is None:
            return None
        try:
            raw = self._device.screenshot()  # returns PIL Image
            if isinstance(raw, Image.Image):
                pil = raw
            else:
                pil = Image.open(io.BytesIO(raw))
            import cv2
            arr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
            return arr
        except Exception as e:
            log.error(f"Screenshot failed: {e}")
            return None

    def screenshot_pil(self) -> Optional[Image.Image]:
        """Capture screen as a PIL Image."""
        if not self._connected or self._device is None:
            return None
        try:
            raw = self._device.screenshot()
            if isinstance(raw, Image.Image):
                return raw
            return Image.open(io.BytesIO(raw))
        except Exception as e:
            log.error(f"Screenshot (PIL) failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Input events
    # ------------------------------------------------------------------

    def tap(self, x: int, y: int, delay: float = 0.5):
        """Send a tap at (x, y)."""
        if not self._connected or self._device is None:
            return
        try:
            self._device.shell(f"input tap {x} {y}")
            log.debug(f"Tap ({x}, {y})")
            time.sleep(delay)
        except Exception as e:
            log.error(f"Tap failed: {e}")

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300, delay: float = 0.5):
        """Send a swipe gesture."""
        if not self._connected or self._device is None:
            return
        try:
            self._device.shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")
            log.debug(f"Swipe ({x1},{y1}) -> ({x2},{y2})")
            time.sleep(delay)
        except Exception as e:
            log.error(f"Swipe failed: {e}")

    def key_event(self, keycode: int, delay: float = 0.3):
        """Send a key event (Android keycode)."""
        if not self._connected or self._device is None:
            return
        try:
            self._device.shell(f"input keyevent {keycode}")
            time.sleep(delay)
        except Exception as e:
            log.error(f"Key event {keycode} failed: {e}")

    def press_back(self):
        self.key_event(4)  # KEYCODE_BACK

    def press_home(self):
        self.key_event(3)  # KEYCODE_HOME

    # ------------------------------------------------------------------
    # App management
    # ------------------------------------------------------------------

    def launch_game(self):
        """Launch the game if not already running."""
        if not self._connected or self._device is None:
            return
        try:
            self._device.shell(
                f"monkey -p {PACKAGE_NAME} -c android.intent.category.LAUNCHER 1"
            )
            log.info("Game launched")
            time.sleep(5)
        except Exception as e:
            log.error(f"Launch failed: {e}")

    def is_game_running(self) -> bool:
        """Check if the game is the foreground app."""
        if not self._connected or self._device is None:
            return False
        try:
            out = self._device.shell(
                "dumpsys activity activities | grep mResumedActivity"
            )
            return PACKAGE_NAME in out
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def tap_if_found(
        self,
        screenshot: np.ndarray,
        template_name: str,
        threshold: float = 0.8,
        delay: float = 1.0,
    ) -> bool:
        """Find a template in screenshot and tap it. Returns True if tapped."""
        if screenshot is None:
            return False
        pos = find_template_by_name(screenshot, template_name, threshold)
        if pos:
            self.tap(pos[0], pos[1], delay=delay)
            return True
        return False

    def wait_for_template(
        self,
        template_name: str,
        timeout: float = 30.0,
        interval: float = 1.5,
        threshold: float = 0.8,
    ) -> Optional[Tuple[int, int]]:
        """Poll screenshots until template appears or timeout. Returns (x, y) or None."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            screen = self.screenshot()
            if screen is not None:
                pos = find_template_by_name(screen, template_name, threshold)
                if pos:
                    return pos
            time.sleep(interval)
        return None
