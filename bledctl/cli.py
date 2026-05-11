import argparse
import asyncio
import json
import sys
from pathlib import Path

try:
    from bleak import BleakScanner
except ImportError:
    sys.stderr.write("Error: bleak not installed. Run: pip install bleak\n")
    sys.exit(1)

from . import (
    BledcomClient,
    COLORS,
    EFFECTS,
    EFFECT_FUNCTIONS,
    MULTI_EFFECT_FUNCTIONS,
    get_all_devices,
    add_device,
    remove_device,
    set_color_all,
    set_brightness_all,
)


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


def get_active_addresses(args, extra_addrs: list = None) -> list[str]:
    devices = get_all_devices()
    addresses = []

    if extra_addrs:
        addresses.extend(extra_addrs)

    if args.all:
        addresses.extend(list(devices.keys()))
    elif args.address:
        addresses.append(args.address)
    else:
        default = load_config().get("device")
        if default:
            addresses.append(default)
        elif devices:
            addresses.append(next(iter(devices.keys())))
        else:
            print("No device configured. Run: bledctl devices add <addr>", file=sys.stderr)
            sys.exit(1)

    return list(dict.fromkeys(addresses))


def parse_color(color_arg: str) -> tuple[int, int, int]:
    name_lower = color_arg.lower()
    if name_lower in COLORS:
        return COLORS[name_lower]
    try:
        hex_val = color_arg.lstrip("#")
        if len(hex_val) == 6:
            return int(hex_val[0:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16)
        elif len(hex_val) == 3:
            return int(hex_val[0] * 2, 16), int(hex_val[1] * 2, 16), int(hex_val[2] * 2, 16)
        raise ValueError("Invalid hex")
    except ValueError:
        print(f"Invalid color: {color_arg}", file=sys.stderr)
        sys.exit(1)


async def cmd_scan(args):
    client = BledcomClient(timeout=args.timeout)
    devices = await client.scan(args.timeout)
    if not devices:
        print("No devices found.")
        return
    print(f"Found {len(devices)} device(s):")
    for d in devices:
        print(f"  {d['name']}  {d['address']}  (RSSI: {d['rssi']} dBm)")


async def cmd_devices(args):
    devices = get_all_devices()

    if args.sub == "list":
        if not devices:
            print("No devices configured. Add one with: bledctl devices add <addr>")
            return
        print(f"Configured device(s):")
        for addr, info in devices.items():
            name = info.get("name", addr)
            print(f"  {name}  {addr}")
        default = load_config().get("device")
        if default:
            print(f"\nDefault: {default}")

    elif args.sub == "add":
        if not args.address:
            print("Usage: bledctl devices add <addr> [--name <name>] [--force]", file=sys.stderr)
            sys.exit(1)
        add_device(args.address, args.name)
        print(f"Added device: {args.address}" + (f" ({args.name})" if args.name else ""))

    elif args.sub == "remove":
        if not args.address:
            print("Usage: bledctl devices remove <addr>", file=sys.stderr)
            sys.exit(1)
        if remove_device(args.address):
            print(f"Removed device: {args.address}")
        else:
            print(f"Device not found: {args.address}", file=sys.stderr)
            sys.exit(1)

    elif args.sub == "default":
        if not args.address:
            print("Current default:", load_config().get("device") or "(none)")
        else:
            cfg = load_config()
            cfg["device"] = args.address
            save_config(cfg)
            print(f"Default set to: {args.address}")


async def cmd_autoconnect(args):
    try:
        found = await BledcomClient(timeout=args.timeout).scan(args.timeout)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nScan cancelled.")
        return
    if not found:
        print("No devices found.")
        return

    saved = get_all_devices()
    new_count = 0
    connected_addrs = []

    for d in found:
        addr = d["address"]
        is_new = addr not in saved
        if is_new:
            if args.add:
                add_device(addr, d["name"])
                new_count += 1
            else:
                continue
        else:
            add_device(addr, d["name"])

        try:
            client = BledcomClient(addr, timeout=args.timeout)
            if await client.connect(addr):
                await client.power_on()
                connected_addrs.append(addr)
                try:
                    await client.disconnect()
                except Exception:
                    pass
            else:
                print(f"Could not connect: {addr}")
        except (KeyboardInterrupt, asyncio.CancelledError):
            print(f"\nStopped at {addr}.")
            break

    if connected_addrs:
        print(f"Connected to {len(connected_addrs)} device(s):")
        for addr in connected_addrs:
            name = saved.get(addr, {}).get("name") or addr
            print(f"  {name}  {addr}")
        if new_count > 0:
            print(f"\nAdded {new_count} new device(s).")
    else:
        print("No devices could be connected.")
        sys.exit(1)


async def cmd_on(args):
    addresses = get_active_addresses(args)
    results = {}
    for addr in addresses:
        client = BledcomClient(addr, timeout=args.timeout)
        if await client.connect(addr):
            await client.power_on()
            results[addr] = True
            try:
                await client.disconnect()
            except Exception:
                pass
        else:
            results[addr] = False

    if len(addresses) > 1 or args.all:
        for addr, ok in results.items():
            status = "OK" if ok else "FAILED"
            print(f"  {addr}: {status}")
    else:
        addr = addresses[0]
        if results.get(addr):
            print("Powered on.")
        else:
            print("Power on failed.", file=sys.stderr)
            sys.exit(1)


async def cmd_off(args):
    addresses = get_active_addresses(args)
    results = {}
    for addr in addresses:
        client = BledcomClient(addr, timeout=args.timeout)
        if await client.connect(addr):
            await client.power_off()
            results[addr] = True
            try:
                await client.disconnect()
            except Exception:
                pass
        else:
            results[addr] = False

    if len(addresses) > 1 or args.all:
        for addr, ok in results.items():
            status = "OK" if ok else "FAILED"
            print(f"  {addr}: {status}")
    else:
        addr = addresses[0]
        if results.get(addr):
            print("Powered off.")
        else:
            print("Power off failed.", file=sys.stderr)
            sys.exit(1)


async def cmd_set_color(args):
    r, g, b = 0, 0, 0
    if args.name:
        r, g, b = parse_color(args.name)
    elif args.hex:
        r, g, b = parse_color(args.hex)
    else:
        r = max(0, min(255, args.r or 0))
        g = max(0, min(255, args.g or 0))
        b = max(0, min(255, args.b or 0))

    addresses = get_active_addresses(args)
    results = await set_color_all(addresses, r, g, b, args.timeout)

    if len(addresses) > 1 or args.all:
        for addr, ok in results.items():
            status = "OK" if ok else "FAILED"
            print(f"  {addr}: {status}")
        print(f"Color set to RGB({r}, {g}, {b})")
    else:
        addr = addresses[0]
        if results.get(addr):
            print(f"Color set to RGB({r}, {g}, {b})")
        else:
            print("Color set failed.", file=sys.stderr)
            sys.exit(1)


async def cmd_brightness(args):
    addresses = get_active_addresses(args)
    results = await set_brightness_all(addresses, args.level, args.timeout)

    if len(addresses) > 1 or args.all:
        for addr, ok in results.items():
            status = "OK" if ok else "FAILED"
            print(f"  {addr}: {status}")
        print(f"Brightness set to {args.level}%")
    else:
        addr = addresses[0]
        if results.get(addr):
            print(f"Brightness set to {args.level}%")
        else:
            print("Brightness set failed.", file=sys.stderr)
            sys.exit(1)


async def cmd_effects_list(args):
    print("Available effects:")
    for name in EFFECTS:
        print(f"  {name}")


async def cmd_guard(args):
    addresses = get_active_addresses(args)
    interval = args.interval or 5

    if args.name:
        r, g, b = parse_color(args.name)
    elif args.hex:
        r, g, b = parse_color(args.hex)
    else:
        r = max(0, min(255, args.r or 0))
        g = max(0, min(255, args.g or 0))
        b = max(0, min(255, args.b or 0))

    print(f"Guarding {len(addresses)} device(s) — color RGB({r}, {g}, {b}), reconnect every {interval}s", flush=True)
    print("Press Ctrl+C to stop.", flush=True)

    clients = []
    for addr in addresses:
        client = BledcomClient(addr, timeout=args.timeout)
        if await client.connect(addr):
            await client.set_color(r, g, b)
            clients.append(client)
            print(f"  {addr}: connected", flush=True)
        else:
            print(f"  {addr}: could not connect", flush=True)

    if not clients:
        print("No devices connected.", file=sys.stderr)
        sys.exit(1)

    async def guard_loop():
        while True:
            await asyncio.sleep(interval)
            for i, client in enumerate(clients):
                try:
                    await client.keepalive()
                except Exception as e:
                    print(f"  {client.address}: {e}", flush=True)

    guard_task = asyncio.create_task(guard_loop())
    try:
        await guard_task
    except (KeyboardInterrupt, asyncio.CancelledError):
        guard_task.cancel()
        try:
            await guard_task
        except asyncio.CancelledError:
            pass
        for client in clients:
            try:
                await client.set_color(0, 0, 0)
                await client.disconnect()
            except Exception:
                pass
        print("\nGuard stopped.")


async def cmd_effect(args):
    effect_name = args.effect.lower()
    if effect_name not in EFFECT_FUNCTIONS:
        print(f"Unknown effect: {effect_name}. Run: bledctl effects", file=sys.stderr)
        sys.exit(1)

    addresses = get_active_addresses(args)
    delay = args.delay or 500
    r, g, b = 255, 255, 255
    if args.color:
        r, g, b = parse_color(args.color)

    if len(addresses) > 1:
        clients = []
        for addr in addresses:
            client = BledcomClient(addr, timeout=args.timeout)
            if await client.connect(addr):
                clients.append(client)
            else:
                print(f"Could not connect: {addr}")

        if not clients:
            print("No devices connected.", file=sys.stderr)
            sys.exit(1)

        stop_event = asyncio.Event()

        async def run_effect():
            func = MULTI_EFFECT_FUNCTIONS[effect_name]
            if effect_name == "solid":
                await func(stop_event, clients, r, g, b)
            else:
                await func(stop_event, clients, delay)

        print(f"Running effect: {effect_name} on {len(clients)} device(s) (delay={delay}ms). Press Ctrl+C to stop.")
        task = asyncio.create_task(run_effect())
        try:
            await task
        except (KeyboardInterrupt, asyncio.CancelledError):
            stop_event.set()
            try:
                await asyncio.gather(*[c.set_color(0, 0, 0) for c in clients])
            except Exception:
                pass
            print("\nStopped.")
        finally:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            for c in clients:
                try:
                    await c.disconnect()
                except Exception:
                    pass
    else:
        address = addresses[0]
        client = BledcomClient(address, timeout=args.timeout)
        if not await client.connect(address):
            print("Connection failed.", file=sys.stderr)
            sys.exit(1)

        stop_event = asyncio.Event()

        async def run_effect():
            func = EFFECT_FUNCTIONS[effect_name]
            if effect_name == "solid":
                await func(stop_event, client, r, g, b)
            else:
                await func(stop_event, client, delay)

        print(f"Running effect: {effect_name} (delay={delay}ms). Press Ctrl+C to stop.")
        task = asyncio.create_task(run_effect())
        try:
            await task
        except (KeyboardInterrupt, asyncio.CancelledError):
            stop_event.set()
            try:
                await client.set_color(0, 0, 0)
            except Exception:
                pass
            print("\nStopped.")
        finally:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bledctl", description="ELK-BLEDOM Bluetooth LED controller CLI")
    parser.add_argument("--timeout", type=float, default=10.0, help="BLE timeout (default: 10s)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scan", help="Scan for nearby BLE LED devices")
    p.add_argument("timeout", nargs="?", type=float, default=5.0, help="Scan duration (default: 5s)")

    p = sub.add_parser("autoconnect", help="Scan and connect to all available devices")
    p.add_argument("timeout", nargs="?", type=float, default=5.0, help="Scan duration (default: 5s)")
    p.add_argument("--add", action="store_true", help="Add new devices to saved list")

    p = sub.add_parser("devices", help="Manage saved devices")
    p.add_argument("sub", choices=["list", "add", "remove", "default"])
    p.add_argument("address", nargs="?", help="Device MAC address")
    p.add_argument("--name", help="Friendly name for the device")
    p.add_argument("--force", action="store_true", help="Add without testing connection")
    p.add_argument("--timeout", type=float, default=10.0)

    p = sub.add_parser("on", help="Power on")
    p.add_argument("--address")
    p.add_argument("--all", action="store_true", help="Apply to all saved devices")

    p = sub.add_parser("off", help="Power off")
    p.add_argument("--address")
    p.add_argument("--all", action="store_true", help="Apply to all saved devices")

    p = sub.add_parser("color", help="Set solid color")
    p.add_argument("--address")
    p.add_argument("--all", action="store_true", help="Apply to all saved devices")
    p.add_argument("-n", "--name", help="Color name (red, green, blue, ...)")
    p.add_argument("--hex", nargs="?", help="Hex color (e.g. #FF0000)")
    p.add_argument("-r", type=int, help="Red (0-255)")
    p.add_argument("-g", type=int, help="Green (0-255)")
    p.add_argument("-b", type=int, help="Blue (0-255)")

    p = sub.add_parser("brightness", help="Set brightness (0-100)")
    p.add_argument("--address")
    p.add_argument("--all", action="store_true", help="Apply to all saved devices")
    p.add_argument("level", type=int, help="Brightness level (0-100)")

    p = sub.add_parser("effects", help="List available effects")

    p = sub.add_parser("effect", help="Run an effect")
    p.add_argument("effect", help="Effect name")
    p.add_argument("--address")
    p.add_argument("--all", action="store_true", help="Apply to all saved devices")
    p.add_argument("--delay", nargs="?", type=int, help="Delay in ms (default: 500)")
    p.add_argument("--color", nargs="?", help="Color for solid effect (name or #hex)")

    p = sub.add_parser("guard", help="Keep connection alive, blocking other devices")
    p.add_argument("--address")
    p.add_argument("--all", action="store_true", help="Apply to all saved devices")
    p.add_argument("--hex", nargs="?", help="Hex color (e.g. #FF0000)")
    p.add_argument("-n", "--name", help="Color name (red, green, blue, ...)")
    p.add_argument("-r", type=int, help="Red (0-255)")
    p.add_argument("-g", type=int, help="Green (0-255)")
    p.add_argument("-b", type=int, help="Blue (0-255)")
    p.add_argument("--interval", type=int, default=5, help="Reconnection interval in seconds (default: 5)")
    p.add_argument("--timeout", type=float, default=10.0)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.cmd:
        parser.print_help()
        return

    mapping = {
        "scan": cmd_scan,
        "autoconnect": cmd_autoconnect,
        "devices": cmd_devices,
        "on": cmd_on,
        "off": cmd_off,
        "color": cmd_set_color,
        "brightness": cmd_brightness,
        "effects": cmd_effects_list,
        "effect": cmd_effect,
        "guard": cmd_guard,
    }

    asyncio.run(mapping[args.cmd](args))


if __name__ == "__main__":
    main()
