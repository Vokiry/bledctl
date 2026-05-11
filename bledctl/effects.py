import asyncio

from .protocol import RAINBOW_7


async def solid(effect: asyncio.Event, client, r: int, g: int, b: int):
    while not effect.is_set():
        await client.set_color(r, g, b)
        await asyncio.sleep(0.1)


async def multi_solid(effect: asyncio.Event, clients: list, r: int, g: int, b: int):
    while not effect.is_set():
        await asyncio.gather(*[c.set_color(r, g, b) for c in clients])
        await asyncio.sleep(0.1)


async def jump_rgb(effect: asyncio.Event, client, delay: int = 500):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    idx = 0
    while not effect.is_set():
        r, g, b = colors[idx % 3]
        await client.set_color(r, g, b)
        idx += 1
        await asyncio.sleep(delay / 1000)


async def multi_jump_rgb(effect: asyncio.Event, clients: list, delay: int = 500):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    idx = 0
    while not effect.is_set():
        r, g, b = colors[idx % 3]
        await asyncio.gather(*[c.set_color(r, g, b) for c in clients])
        idx += 1
        await asyncio.sleep(delay / 1000)


async def jump_all(effect: asyncio.Event, client, delay: int = 500):
    idx = 0
    while not effect.is_set():
        r, g, b = RAINBOW_7[idx % 7]
        await client.set_color(r, g, b)
        idx += 1
        await asyncio.sleep(delay / 1000)


async def multi_jump_all(effect: asyncio.Event, clients: list, delay: int = 500):
    idx = 0
    while not effect.is_set():
        r, g, b = RAINBOW_7[idx % 7]
        await asyncio.gather(*[c.set_color(r, g, b) for c in clients])
        idx += 1
        await asyncio.sleep(delay / 1000)


async def fade_rgb(effect: asyncio.Event, client, delay: int = 500):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    target = [255, 0, 0]
    current = [0, 0, 0]
    idx = 0

    while not effect.is_set():
        if current[0] == target[0] and current[1] == target[1] and current[2] == target[2]:
            idx = (idx + 1) % 3
            target[0], target[1], target[2] = colors[idx]
        for i in range(3):
            if current[i] < target[i]:
                current[i] = min(target[i], current[i] + 5)
            elif current[i] > target[i]:
                current[i] = max(target[i], current[i] - 5)
        await client.set_color(int(current[0]), int(current[1]), int(current[2]))
        await asyncio.sleep(delay / 1000)


async def multi_fade_rgb(effect: asyncio.Event, clients: list, delay: int = 500):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    targets = [[255, 0, 0] for _ in clients]
    currents = [[0, 0, 0] for _ in clients]
    idx = 0

    while not effect.is_set():
        for i, t in enumerate(targets):
            if currents[i][0] == t[0] and currents[i][1] == t[1] and currents[i][2] == t[2]:
                t[0], t[1], t[2] = colors[idx % 3]
        idx += 1

        for i, c in enumerate(currents):
            for j in range(3):
                if c[j] < targets[i][j]:
                    c[j] = min(targets[i][j], c[j] + 5)
                elif c[j] > targets[i][j]:
                    c[j] = max(targets[i][j], c[j] - 5)

        await asyncio.gather(*[clients[i].set_color(int(currents[i][0]), int(currents[i][1]), int(currents[i][2])) for i in range(len(clients))])
        await asyncio.sleep(delay / 1000)


async def fade_all(effect: asyncio.Event, client, delay: int = 500):
    target = list(RAINBOW_7[0])
    current = [0, 0, 0]
    idx = 0

    while not effect.is_set():
        if current[0] == target[0] and current[1] == target[1] and current[2] == target[2]:
            idx = (idx + 1) % 7
            target[0], target[1], target[2] = RAINBOW_7[idx]
        for i in range(3):
            if current[i] < target[i]:
                current[i] = min(target[i], current[i] + 5)
            elif current[i] > target[i]:
                current[i] = max(target[i], current[i] - 5)
        await client.set_color(int(current[0]), int(current[1]), int(current[2]))
        await asyncio.sleep(delay / 1000)


async def multi_fade_all(effect: asyncio.Event, clients: list, delay: int = 500):
    targets = [list(RAINBOW_7[0]) for _ in clients]
    currents = [[0, 0, 0] for _ in clients]
    idx = 0

    while not effect.is_set():
        for i, t in enumerate(targets):
            if currents[i][0] == t[0] and currents[i][1] == t[1] and currents[i][2] == t[2]:
                idx = (idx + 1) % 7
                t[0], t[1], t[2] = RAINBOW_7[idx]
        for i, c in enumerate(currents):
            for j in range(3):
                if c[j] < targets[i][j]:
                    c[j] = min(targets[i][j], c[j] + 5)
                elif c[j] > targets[i][j]:
                    c[j] = max(targets[i][j], c[j] - 5)
        await asyncio.gather(*[clients[i].set_color(int(currents[i][0]), int(currents[i][1]), int(currents[i][2])) for i in range(len(clients))])
        await asyncio.sleep(delay / 1000)


async def crossfade_red(effect: asyncio.Event, client, delay: int = 500):
    on = True
    while not effect.is_set():
        if on:
            await client.set_color(255, 0, 0)
        else:
            await client.set_color(0, 0, 0)
        on = not on
        await asyncio.sleep(delay / 1000)


async def multi_crossfade_red(effect: asyncio.Event, clients: list, delay: int = 500):
    on = True
    while not effect.is_set():
        r, g, b = (255, 0, 0) if on else (0, 0, 0)
        await asyncio.gather(*[c.set_color(r, g, b) for c in clients])
        on = not on
        await asyncio.sleep(delay / 1000)


async def crossfade_green_blue(effect: asyncio.Event, client, delay: int = 500):
    colors = [(0, 255, 0), (0, 0, 255)]
    idx = 0
    while not effect.is_set():
        r, g, b = colors[idx % 2]
        await client.set_color(r, g, b)
        idx += 1
        await asyncio.sleep(delay / 1000)


async def multi_crossfade_green_blue(effect: asyncio.Event, clients: list, delay: int = 500):
    colors = [(0, 255, 0), (0, 0, 255)]
    idx = 0
    while not effect.is_set():
        r, g, b = colors[idx % 2]
        await asyncio.gather(*[c.set_color(r, g, b) for c in clients])
        idx += 1
        await asyncio.sleep(delay / 1000)


async def crossfade_blue(effect: asyncio.Event, client, delay: int = 500):
    on = True
    while not effect.is_set():
        if on:
            await client.set_color(0, 0, 255)
        else:
            await client.set_color(0, 0, 0)
        on = not on
        await asyncio.sleep(delay / 1000)


async def multi_crossfade_blue(effect: asyncio.Event, clients: list, delay: int = 500):
    on = True
    while not effect.is_set():
        r, g, b = (0, 0, 255) if on else (0, 0, 0)
        await asyncio.gather(*[c.set_color(r, g, b) for c in clients])
        on = not on
        await asyncio.sleep(delay / 1000)


async def crossfade_white(effect: asyncio.Event, client, delay: int = 500):
    on = True
    while not effect.is_set():
        if on:
            await client.set_color(255, 255, 255)
        else:
            await client.set_color(0, 0, 0)
        on = not on
        await asyncio.sleep(delay / 1000)


async def multi_crossfade_white(effect: asyncio.Event, clients: list, delay: int = 500):
    on = True
    while not effect.is_set():
        r, g, b = (255, 255, 255) if on else (0, 0, 0)
        await asyncio.gather(*[c.set_color(r, g, b) for c in clients])
        on = not on
        await asyncio.sleep(delay / 1000)


async def flash_rgb(effect: asyncio.Event, client, delay: int = 500):
    colors = [(255, 0, 0), (0, 0, 0), (0, 255, 0), (0, 0, 0), (0, 0, 255), (0, 0, 0)]
    idx = 0
    while not effect.is_set():
        r, g, b = colors[idx % 6]
        await client.set_color(r, g, b)
        idx += 1
        await asyncio.sleep(delay / 1000)


async def multi_flash_rgb(effect: asyncio.Event, clients: list, delay: int = 500):
    colors = [(255, 0, 0), (0, 0, 0), (0, 255, 0), (0, 0, 0), (0, 0, 255), (0, 0, 0)]
    idx = 0
    while not effect.is_set():
        r, g, b = colors[idx % 6]
        await asyncio.gather(*[c.set_color(r, g, b) for c in clients])
        idx += 1
        await asyncio.sleep(delay / 1000)


async def flash_all(effect: asyncio.Event, client, delay: int = 500):
    while not effect.is_set():
        for color in RAINBOW_7:
            if effect.is_set():
                break
            await client.set_color(*color)
            await asyncio.sleep(delay / 1000)
            await client.set_color(0, 0, 0)
            await asyncio.sleep(delay / 1000)


async def multi_flash_all(effect: asyncio.Event, clients: list, delay: int = 500):
    while not effect.is_set():
        for color in RAINBOW_7:
            if effect.is_set():
                break
            await asyncio.gather(*[c.set_color(*color) for c in clients])
            await asyncio.sleep(delay / 1000)
            await asyncio.gather(*[c.set_color(0, 0, 0) for c in clients])
            await asyncio.sleep(delay / 1000)


async def strobe_white(effect: asyncio.Event, client, delay: int = 50):
    while not effect.is_set():
        await client.set_color(255, 255, 255)
        await asyncio.sleep(delay / 1000)
        await client.set_color(0, 0, 0)
        await asyncio.sleep(delay / 1000)


async def multi_strobe_white(effect: asyncio.Event, clients: list, delay: int = 50):
    while not effect.is_set():
        await asyncio.gather(*[c.set_color(255, 255, 255) for c in clients])
        await asyncio.sleep(delay / 1000)
        await asyncio.gather(*[c.set_color(0, 0, 0) for c in clients])
        await asyncio.sleep(delay / 1000)


EFFECT_FUNCTIONS = {
    "solid": solid,
    "jump_rgb": jump_rgb,
    "jump_all": jump_all,
    "fade_rgb": fade_rgb,
    "fade_all": fade_all,
    "crossfade_red": crossfade_red,
    "crossfade_green_blue": crossfade_green_blue,
    "crossfade_blue": crossfade_blue,
    "crossfade_white": crossfade_white,
    "flash_rgb": flash_rgb,
    "flash_all": flash_all,
    "strobe_white": strobe_white,
}

MULTI_EFFECT_FUNCTIONS = {
    "solid": multi_solid,
    "jump_rgb": multi_jump_rgb,
    "jump_all": multi_jump_all,
    "fade_rgb": multi_fade_rgb,
    "fade_all": multi_fade_all,
    "crossfade_red": multi_crossfade_red,
    "crossfade_green_blue": multi_crossfade_green_blue,
    "crossfade_blue": multi_crossfade_blue,
    "crossfade_white": multi_crossfade_white,
    "flash_rgb": multi_flash_rgb,
    "flash_all": multi_flash_all,
    "strobe_white": multi_strobe_white,
}
