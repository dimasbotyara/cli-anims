#!/usr/bin/env python3
"""Бесконечный неоновый туннель с текстурой. Ctrl+C — выход."""

import math
import os
import sys
import time

RAMP = '.:-=+*#%@'


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
    for i in range(64):
        hue = i / 64.0
        row = []
        for level in range(8):
            v = 0.16 + 0.84 * (level / 7) ** 1.15
            r, g, b = hsv_to_rgb(hue, 0.88, v)
            row.append(f"\033[38;2;{r};{g};{b}m")
        pal.append(row)
    return pal


PAL = build_palette()
WHITE = '\033[1;38;2;235;245;255m'


def render(w, h, t):
    chars = [' '] * (w * h)
    cols = [None] * (w * h)
    cx, cy = w / 2.0, h / 2.0
    scale = h * 0.5

    for py in range(h):
        dy = (py + 0.5 - cy) / scale
        for px in range(w):
            dx = (px + 0.5 - cx) / scale
            r = math.hypot(dx, dy)
            i = py * w + px

            if r < 0.02:
                if math.sin(t * 3.0) > -0.3:
                    chars[i] = '*'
                    cols[i] = WHITE
                continue

            a = math.atan2(dy, dx) + 0.12 * math.sin(t * 0.5)
            depth = 1.0 / (r + 0.05)
            ring = 0.5 + 0.5 * math.sin(depth * 1.5 - t * 3.2)
            spoke = 0.5 + 0.5 * math.sin(a * 7.0 + depth * 0.35 + t * 0.6)
            val = (0.62 * ring + 0.38 * spoke)
            val *= min(1.0, (r * 1.55) ** 0.8)
            if val < 0.07:
                continue
            val = val ** 1.4

            hue = 0.55 + 0.10 * math.sin(a * 2.0 - t * 0.4) + 0.07 * ring
            hi = int((hue % 1.0) * 63)
            idx = min(8, int(val * 9))
            level = min(7, int(val * 8))
            chars[i] = RAMP[idx]
            cols[i] = PAL[hi][level]

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
    t = 0.0
    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            w = max(30, w)
            h = max(10, h)

            sys.stdout.write(render(w, h, t))
            sys.stdout.flush()
            t += 0.05
            time.sleep(0.035)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')


if __name__ == '__main__':
    main()
