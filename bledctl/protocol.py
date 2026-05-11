HEADER = 0x7E
FOOTER = 0xEF

CMD_POWER_ON = 0x04
CMD_POWER_OFF = 0x00
CMD_SET_COLOR = 0x05
CMD_SET_BRIGHTNESS = 0x01

EFFECTS = [
    "solid",
    "jump_rgb",
    "jump_all",
    "fade_rgb",
    "fade_all",
    "crossfade_red",
    "crossfade_green_blue",
    "crossfade_blue",
    "crossfade_white",
    "flash_rgb",
    "flash_all",
    "strobe_white",
]

COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "white": (255, 255, 255),
    "orange": (255, 165, 0),
    "pink": (255, 105, 180),
    "purple": (128, 0, 128),
}

RAINBOW_7 = [
    (255, 0, 0),
    (255, 128, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 128, 255),
    (0, 0, 255),
    (128, 0, 255),
]


def make_frame(command: int, data: bytes = b"") -> bytearray:
    length = len(data) + 2
    frame = bytearray([HEADER, length, command]) + bytearray(data)
    frame.append(FOOTER)
    return frame


def make_power_frame(on: bool) -> bytearray:
    if on:
        return bytearray([HEADER, 0x04, CMD_POWER_ON, 0xF0, 0x00, 0x01, 0xFF, 0x00, FOOTER])
    return bytearray([HEADER, 0x04, CMD_POWER_OFF, 0x00, 0x00, 0x00, 0xFF, 0x00, FOOTER])


def make_color_frame(r: int, g: int, b: int) -> bytearray:
    return bytearray([HEADER, 0x07, CMD_SET_COLOR, 0x03, r, g, b, 0x10, FOOTER])


def make_brightness_frame(brightness: int) -> bytearray:
    brightness = max(0, min(100, brightness))
    b_val = int(brightness * 2.55)
    return bytearray([HEADER, 0x04, CMD_SET_BRIGHTNESS, b_val, 0x00, 0x00, 0x00, 0x00, FOOTER])
