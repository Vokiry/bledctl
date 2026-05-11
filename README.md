# bledctl

CLI utility for controlling ELK-BLEDOM Bluetooth Low Energy LED strip controllers.

Works with devices named `ELK-BLEDOM`, `BLEDOM`, `BLEDDM`, `LEDBLE`, `Lotus Lantern`, and compatible clones sold under various brands.

## Requirements

- Python 3.10+
- Linux with BlueZ (or macOS with CoreBluetooth / Windows with BLE support)
- BLE adapter
- `bleak>=0.21.0`

## Installation

### Linux / macOS

```bash
git clone https://github.com/youruser/bledctl ~/Projects/bledctl
cd ~/Projects/bledctl

# System-wide (requires sudo)
./install.sh

# Or for current user only
./install.sh --user
```

### Windows

1. Download or clone the repository
2. Run `install.bat` from the project folder
3. Make sure Python is installed and in PATH

### pip (any platform)

```bash
pip install .
# or for development
pip install -e .
```

### Requirements

Make sure `bleak` is installed:

```bash
# Linux (Arch)
sudo pacman -S python-bleak

# pip (all platforms)
pip install bleak
```

## Quick Start

```bash
# Auto-discover and connect all available devices (saves them)
bledctl autoconnect --add

# Or scan first, then add devices manually
bledctl scan

# Add devices
bledctl devices add AA:BB:CC:DD:EE:FF
bledctl devices add 11:22:33:44:55:66

# List saved devices
bledctl devices list

# Control all LEDs at once
bledctl on --all
bledctl color --hex=#FF8800 --all
bledctl effect jump_rgb --all --delay=300

# Control a specific LED
bledctl color --hex=#00FF88 --address=AA:BB:CC:DD:EE:FF

# Set a default device
bledctl devices default AA:BB:CC:DD:EE:FF
bledctl on  # uses default
```

## Commands

| Command | Description |
|---------|-------------|
| `bledctl scan [timeout]` | Scan for nearby BLE LED devices |
| `bledctl autoconnect [timeout]` | Scan and connect to all available devices |
| `bledctl devices list` | List all saved devices |
| `bledctl devices add <addr>` | Add a device |
| `bledctl devices remove <addr>` | Remove a device |
| `bledctl devices default <addr>` | Set default device |
| `bledctl on [--all]` | Power on (single or all devices) |
| `bledctl off [--all]` | Power off (single or all devices) |
| `bledctl color [--all]` | Set solid RGB color |
| `bledctl brightness [--all] <0-100>` | Set brightness |
| `bledctl effects` | List available effects |
| `bledctl effect [--all] <name>` | Run an effect on all devices |
| `bledctl guard [--all] [--hex=<color>]` | Keep connection alive, block others |

### Color Options

```bash
bledctl color --hex=#FF8800       # 6-digit hex
bledctl color --hex=#F80          # 3-digit hex
bledctl color -n red              # Named color
bledctl color -r 255 -g 136 -b 0  # RGB values
```

Named colors: red, green, blue, yellow, cyan, magenta, white, orange, pink, purple

### Effect Options

```bash
bledctl effect <name> --delay=500   # Animation speed (ms, lower=faster)
bledctl effect solid --color=#FF0000 # Color for solid mode
```

**Note:** For args with `=` sign, use `--name=value` syntax. Space-separated `--name value` is not supported.

### Global Options

| Option | Description |
|--------|-------------|
| `--timeout <seconds>` | BLE connection timeout (default: 10s) |
| `--address <addr>` | Target device address |
| `--all` | Apply command to all saved devices |
| `--add` (autoconnect only) | Add newly discovered devices to saved list |

## Effects

| Effect | Description |
|--------|-------------|
| `solid` | Static color (use `--color` to set) |
| `jump_rgb` | Jumps between red, green, blue |
| `jump_all` | Jumps through 7 rainbow colors |
| `fade_rgb` | Smooth crossfade red → green → blue |
| `fade_all` | Smooth crossfade through rainbow |
| `crossfade_red` | Pulsing red on/off |
| `crossfade_blue` | Pulsing blue on/off |
| `crossfade_white` | Pulsing white on/off |
| `crossfade_green_blue` | Alternating green/blue |
| `flash_rgb` | Flashes red/green/blue with black gaps |
| `flash_all` | Flashes rainbow colors with gaps |
| `strobe_white` | Rapid strobe at white |

Press Ctrl+C to stop an effect.

Effects can be applied to multiple devices with `--all`:

```bash
bledctl effect jump_rgb --all --delay=300
bledctl effect fade_all --all --delay=200
bledctl effect solid --all --color=#FF8800
```

## Guard Mode (Anti-Interference)

Keep connection alive to prevent other devices from controlling your LEDs:

```bash
# Guard with red color, reconnect every 5 seconds
bledctl guard --hex=#FF0000

# Guard all devices with specific color
bledctl guard --all --hex=#00FF00 --interval=3

# Guard with RGB values
bledctl guard --hex=#FF8800 --interval=10
```

The guard continuously reconnects at the specified interval, holding the connection and keeping the last color active. Other apps or users won't be able to control the device while guard is running.

Press Ctrl+C to stop and restore the LEDs to black.

## Multi-Device Control

The `autoconnect` command auto-discovers and connects to all available devices:

```bash
# Auto-discover and connect all devices (saves them for future use)
bledctl autoconnect --add

# Reconnect all saved devices without scanning
bledctl autoconnect
```

The `--all` flag controls all saved devices simultaneously:

```bash
bledctl devices add AA:BB:CC:DD:EE:FF --name="Desk"
bledctl devices add 11:22:33:44:55:66 --name="Shelf"

# Control all at once
bledctl on --all
bledctl color --hex=#00FF00 --all
bledctl effect jump_rgb --all --delay=300
bledctl off --all

# Individual control
bledctl color --hex=#FF0000 --address=AA:BB:CC:DD:EE:FF
bledctl color --hex=#0000FF --address=11:22:33:44:55:66
```

## Protocol

The ELK-BLEDOM protocol uses 9-byte frames sent over BLE GATT:

```
[0x7E] [length] [command] [data...] [checksum] [0xEF]
```

- **Service UUID**: `0000fff0-...` (fallback: `0000ffe5-...`)
- **Characteristic UUID**: `0000fff3-...` (fallback: `0000ffe9-...`)
- **Write type**: `WRITE_NO_RESPONSE`

## Config

Device addresses stored in `~/.config/bledctl.json` (or `~/.bledctl.json`):

```json
{
  "device": "AA:BB:CC:DD:EE:FF",
  "devices": {
    "AA:BB:CC:DD:EE:FF": {"name": "Desk", "address": "AA:BB:CC:DD:EE:FF"},
    "11:22:33:44:55:66": {"name": "Shelf", "address": "11:22:33:44:55:66"}
  }
}
```

## Troubleshooting

**"Device not found"**
- The MAC address may have changed since last connect — re-run `bledctl scan` and use `--address=<addr>` to override

**"Service Discovery has not been performed yet"**
- BLE connection dropped during effect. Run `bledctl on` to reconnect before effects.

**Effects not working**
- Some controllers use the alternate UUID pair. Try `bledctl devices add <addr>` again.

**BLE permission denied (Linux)**
```bash
sudo hciconfig hci0 up
sudo btmgmt power on
```

**Color shows as RGB(0,0,0)**
- Use `--hex=#VALUE` with `=` syntax, not `--hex #VALUE` with space

**LED strip not responding**
- These cheap controllers sometimes change MAC addresses. Re-scan and reconnect if commands stop working.

## File Structure

```
bledctl/
├── bledctl/           # Python package
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── bledcom.py
│   ├── effects.py
│   └── protocol.py
├── install.sh        # Linux/macOS installer
├── install.bat       # Windows installer
├── pyproject.toml    # Package metadata
├── requirements.txt
└── README.md
```

## License

MIT
