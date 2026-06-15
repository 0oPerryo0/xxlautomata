from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


class AdbError(RuntimeError):
    pass


@dataclass(frozen=True)
class Device:
    serial: str
    state: str


class Adb:
    def __init__(self, serial: str | None = None, adb_path: str = "adb") -> None:
        self.serial = serial or None
        self.adb_path = adb_path

    @staticmethod
    def exists(adb_path: str = "adb") -> bool:
        return shutil.which(adb_path) is not None

    def command(self, args: list[str]) -> list[str]:
        cmd = [self.adb_path]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)
        return cmd

    def run(
        self,
        args: list[str],
        *,
        check: bool = True,
        timeout: int = 30,
    ) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            self.command(args),
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
        if check and proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip()
            raise AdbError(detail or f"adb exited with code {proc.returncode}")
        return proc

    def run_bytes(
        self,
        args: list[str],
        *,
        check: bool = True,
        timeout: int = 30,
    ) -> subprocess.CompletedProcess[bytes]:
        proc = subprocess.run(
            self.command(args),
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        if check and proc.returncode != 0:
            detail = proc.stderr.decode(errors="replace").strip()
            raise AdbError(detail or f"adb exited with code {proc.returncode}")
        return proc

    def shell(self, args: list[str], *, timeout: int = 30) -> str:
        return self.run(["shell", *args], timeout=timeout).stdout.strip()


def parse_devices(output: str) -> list[Device]:
    devices: list[Device] = []
    for line in output.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2:
            devices.append(Device(serial=parts[0], state=parts[1]))
    return devices


def detect_device(adb_path: str = "adb", requested_serial: str | None = None) -> Device:
    if not Adb.exists(adb_path):
        raise AdbError("adb was not found. Install Android Platform Tools and add adb to PATH.")

    base = Adb(adb_path=adb_path)
    base.run(["start-server"], timeout=20)
    devices = parse_devices(base.run(["devices"], timeout=20).stdout)

    if requested_serial:
        for device in devices:
            if device.serial == requested_serial:
                if device.state != "device":
                    raise AdbError(f"Device {requested_serial} is connected but state is {device.state}.")
                return device
        raise AdbError(f"Device {requested_serial} was not found by adb.")

    ready = [device for device in devices if device.state == "device"]
    if not ready:
        if devices:
            states = ", ".join(f"{d.serial}={d.state}" for d in devices)
            raise AdbError(f"No ready ADB device. Current states: {states}.")
        raise AdbError("No ADB devices found. Connect a device or start an emulator.")

    if len(ready) > 1:
        serials = ", ".join(device.serial for device in ready)
        raise AdbError(f"Multiple devices connected ({serials}). Set device_serial in config.json.")

    return ready[0]
