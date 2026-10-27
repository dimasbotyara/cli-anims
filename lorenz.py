#!/usr/bin/env python3
"""Аттрактор Лоренца — светящаяся бабочка из точек. Ctrl+C — выход."""

import math
import os
import random
import sys
import time
from collections import deque

SIGMA, RHO, BETA = 10.0, 28.0, 8.0 / 3.0
DT = 0.004
TRAIL = 4200


def hsv_to_rgb(h, s, v):
    h = (h % 1.0) * 6.0
    i = int(h)
    f = h - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return int(r * 255), int(g * 255), int(b * 255)


def build_palette():
    pal = []
    for i in range(48):
        hue = 0.52 + 0.36 * i / 47
        row = []
        for j in range(10):
            v = 0.16 + 0.84 * (j / 9) ** 1.7
            r, g, b = hsv_to_rgb(hue, 0.82, v)
            row.append(f"\033[38;2;{r};{g};{b}m")
        pal.append(row)
    return pal


PALETTE = build_palette()
WHITE = '\033[1;38;2;255;255;255m'


def step(p):
    x, y, z = p
    dx = SIGMA * (y - x)
    dy = x * (RHO - z) - y
    dz = x * y - BETA * z
    return x + dx * DT, y + dy * DT, z + dz * DT


def render(points, w, h, yaw, t):
    chars = [' '] * (w * h)
    cols = [None] * (w * h)
    ca, sa = math.cos(yaw), math.sin(yaw)
    zoom = 1.0 + 0.05 * math.sin(t * 0.5)
    sx = w * 0.44 / 22.0 * zoom
    sy = h * 0.43 / 27.0 * zoom
    cx, cy = w / 2.0, h / 2.0
    n = len(points)

    for i, (x, y, z) in enumerate(points):
        xr = x * ca - y * sa
        yr = x * sa + y * ca
        px = int(cx + xr * sx)
        py = int(cy - (z - 26.0) * sy + yr * sy * 0.10)
        if 0 <= px < w and 0 <= py < h:
            j = py * w + px
            age = i / (n - 1) if n > 1 else 1.0
            hi = int(max(0.0, min(0.999, z / 50.0)) * 47)
            bi = int(max(0.0, min(0.999, 0.18 + 0.82 * age ** 1.45)) * 9)
            chars[j] = '·'
            cols[j] = PALETTE[hi][bi]

    # яркая «голова» траектории
    for x, y, z in list(points)[-6:]:
        xr = x * ca - y * sa
        yr = x * sa + y * ca
        px = int(cx + xr * sx)
        py = int(cy - (z - 26.0) * sy + yr * sy * 0.10)
        if 0 <= px < w and 0 <= py < h:
            j = py * w + px
            chars[j] = '*'
            cols[j] = WHITE

    out = []
    for y in range(h):
        cur = None
        row = []
        for x in range(w):
            i = y * w + x
            c = cols[i]
            if c != cur:
                row.append('\033[0m' if c is None else c)
                cur = c
            row.append(chars[i])
        row.append('\033[0m\n')
        out.append(''.join(row))
    return '\033[H' + ''.join(out)


def main():
    rnd = random.Random(42)
    p = (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(10, 30))
    for _ in range(3000):
        p = step(p)

    points = deque(maxlen=TRAIL)
    for _ in range(TRAIL):
        p = step(p)
        points.append(p)

    sys.stdout.write("\033[?25l\033[2J")
    yaw = 0.0
    t = 0.0
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            w = max(30, w)
            h = max(10, h)

            for _ in range(10):
                p = step(p)
                points.append(p)

            sys.stdout.write(render(points, w, h, yaw, t))
            sys.stdout.flush()

            yaw += 0.012
            t += 0.03
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')


if __name__ == '__main__':
    main()
