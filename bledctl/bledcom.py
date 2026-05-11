import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

try:
    import bleak
    from bleak import BleakClient, BleakScanner
except ImportError:
    sys.stderr.write("Error: bleak not installed. Run: pip install bleak\n")
    sys.exit(1)

from .protocol import make_frame, HEADER, FOOTER

SERVICE_UUIDS = [
    "0000fff0-0000-1000-8000-00805f9b34fb",
    "0000ffe5-0000-1000-8000-00805f9b34fb",
]
CHAR_UUIDS = [
    "0000fff3-0000-1000-8000-00805f9b34fb",
    "0000ffe9-0000-1000-8000-00805f9b34fb",
]

NAME_PREFIXES = ["ELK-BLEDOM", "BLEDOM", "BLEDDM", "LEDBLE", "Lotus Lantern", "lotus"]


def get_config_path() -> Path:
    base = Path.home()
    if (base / ".config").exists():
        return base / ".config" / "bledctl.json"
    return base / ".bledctl.json"


def load_config() -> dict:
    path = get_config_path()
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {}


def save_config(data: dict) -> None:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def load_devices() -> dict:
    cfg = load_config()
    devices = cfg.get("devices", {})
    return devices


def save_devices(devices: dict) -> None:
    cfg = load_config()
    cfg["devices"] = devices
    save_config(cfg)


def add_device(address: str, name: Optional[str] = None) -> None:
    devices = load_devices()
    devices[address] = {"name": name or address, "address": address}
    save_devices(devices)


def remove_device(address: str) -> bool:
    devices = load_devices()
    if address in devices:
        del devices[address]
        save_devices(devices)
        return True
    return False


def get_all_devices() -> dict:
    return load_devices()


class BledcomClient:
    def __init__(self, address: Optional[str] = None, timeout: float = 10.0):
        self.address = address
        self.timeout = timeout
        self._client: Optional[BleakClient] = None
        self._char_uuid: Optional[str] = None
        self._connected = False
        self._last_color = (0, 0, 0)

    async def scan(self, timeout: float = 5.0) -> list[dict]:
        try:
            devices = await BleakScanner.discover(timeout)
        except asyncio.CancelledError:
            return []
        found = []
        for d in devices:
            name = (d.name or "").upper()
            for prefix in NAME_PREFIXES:
                if prefix.upper() in name:
                    rssi = getattr(d, "rssi", None) or -100
                    found.append({"name": d.name, "address": d.address, "rssi": rssi})
                    break
        return sorted(found, key=lambda x: x["rssi"] or -100, reverse=True)

    async def connect(self, address: Optional[str] = None) -> bool:
        if address:
            self.address = address
        if not self.address:
            return False

        try:
            if self._client and self._connected:
                try:
                    if self._client.is_connected:
                        return True
                except Exception:
                    pass
                try:
                    await self._client.disconnect()
                except Exception:
                    pass

            self._client = None
            self._char_uuid = None
            self._connected = False

            self._client = BleakClient(self.address, timeout=self.timeout)
            await self._client.connect()

            for svc in self._client.services:
                if svc.uuid.upper() in [u.upper() for u in SERVICE_UUIDS]:
                    for char in svc.characteristics:
                        if char.uuid.upper() in [u.upper() for u in CHAR_UUIDS]:
                            self._char_uuid = char.uuid
                            self._connected = True
                            devices = load_devices()
                            devices[self.address] = {"name": self.address, "address": self.address}
                            save_devices(devices)
                            return True

            if self._client.services:
                for svc in self._client.services:
                    for char in svc.characteristics:
                        if "fff3" in char.uuid.lower() or "ffe9" in char.uuid.lower():
                            self._char_uuid = char.uuid
                            self._connected = True
                            devices = load_devices()
                            devices[self.address] = {"name": self.address, "address": self.address}
                            save_devices(devices)
                            return True

            try:
                await self._client.disconnect()
            except Exception:
                pass
            return False
        except asyncio.CancelledError:
            if self._client:
                try:
                    await self._client.disconnect()
                except Exception:
                    pass
            raise
        except Exception as e:
            print(f"Connection failed: {e}", file=sys.stderr)
            return False

    async def send(self, frame: bytearray) -> bool:
        if not self._client or not self._char_uuid:
            return False
        try:
            await self._client.write_gatt_char(self._char_uuid, frame, response=False)
            return True
        except Exception as e:
            print(f"Send failed: {e}", file=sys.stderr)
            return False

    async def power_on(self) -> bool:
        from .protocol import make_power_frame
        return await self.send(make_power_frame(True))

    async def power_off(self) -> bool:
        from .protocol import make_power_frame
        return await self.send(make_power_frame(False))

    async def set_color(self, r: int, g: int, b: int) -> bool:
        from .protocol import make_color_frame
        self._last_color = (r, g, b)
        return await self.send(make_color_frame(r, g, b))

    async def set_brightness(self, brightness: int) -> bool:
        from .protocol import make_brightness_frame
        return await self.send(make_brightness_frame(brightness))

    async def keepalive(self) -> bool:
        if not self._connected or not self._client:
            if self.address:
                connected = await self.connect(self.address)
                if not connected:
                    return False
        r, g, b = self._last_color
        return await self.set_color(r, g, b)

    async def disconnect(self) -> None:
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            finally:
                self._client = None
                self._connected = False


async def run_on_all(addresses: list[str], action: str, timeout: float = 10.0) -> dict:
    results = {}
    for addr in addresses:
        client = BledcomClient(addr, timeout=timeout)
        if await client.connect(addr):
            if action == "on":
                ok = await client.power_on()
            elif action == "off":
                ok = await client.power_off()
            elif action == "off":
                ok = await client.power_off()
            else:
                ok = False
            try:
                await client.disconnect()
            except Exception:
                pass
            results[addr] = ok
        else:
            results[addr] = False
    return results


async def set_color_all(addresses: list[str], r: int, g: int, b: int, timeout: float = 10.0) -> dict:
    results = {}
    for addr in addresses:
        client = BledcomClient(addr, timeout=timeout)
        if await client.connect(addr):
            ok = await client.set_color(r, g, b)
            try:
                await client.disconnect()
            except Exception:
                pass
            results[addr] = ok
        else:
            results[addr] = False
    return results


async def set_brightness_all(addresses: list[str], level: int, timeout: float = 10.0) -> dict:
    results = {}
    for addr in addresses:
        client = BledcomClient(addr, timeout=timeout)
        if await client.connect(addr):
            ok = await client.set_brightness(level)
            try:
                await client.disconnect()
            except Exception:
                pass
            results[addr] = ok
        else:
            results[addr] = False
    return results
