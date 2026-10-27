#!/usr/bin/env python3
"""Метаболы — плавающие светящиеся капли. Ctrl+C — выход."""

import math
import os
import random
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


def build_palette(hues):
    pal = []
    for hue in hues:
        row = []
        for level in range(10):
            v = 0.22 + 0.78 * (level / 9) ** 0.8
            r, g, b = hsv_to_rgb(hue + 0.05 * level / 9, 0.88, v)
            row.append(f"\033[38;2;{r};{g};{b}m")
        pal.append(row)
    return pal


class Ball:
    __slots__ = ('ax', 'ay', 'fx', 'fy', 'ph', 'r', 'hue', 'pal')

    def __init__(self, i, total, w, h):
        self.ax = random.uniform(0.16, 0.34) * w
        self.ay = random.uniform(0.14, 0.32) * h
        self.fx = random.uniform(0.20, 0.65)
        self.fy = random.uniform(0.20, 0.65)
        self.ph = random.uniform(0, math.tau)
        self.r = random.uniform(0.20, 0.38) * h
        self.hue = (0.52 + i / max(1, total) * 0.7) % 1.0
        self.pal = None


def render(balls, w, h, t):
    chars = [' '] * (w * h)
    cols = [None] * (w * h)
    cx, cy = w / 2.0, h / 2.0

    positions = []
    for b in balls:
        x = cx + math.sin(t * b.fx + b.ph) * b.ax
        y = cy + math.cos(t * b.fy + b.ph * 1.3) * b.ay
        r = b.r * (1.0 + 0.08 * math.sin(t * 0.9 + b.ph))
        positions.append((x, y, r * r, b.pal))

    for py in range(h):
        for px in range(w):
            best = 0.0
            best_pal = None
            field = 0.0
            for (bx, by, r2, pal) in positions:
                dx = px - bx
                dy = (py - by) * 2.0
                d2 = dx * dx + dy * dy
                c = r2 / (d2 + 0.5)
                field += c
                if c > best:
                    best = c
                    best_pal = pal
            if field <= 1.0:
                continue
            v = 1.0 - 1.0 / field
            shade = max(0.0, min(1.0, v)) ** 0.55
            idx = min(8, int(shade * 9))
            i = py * w + px
            chars[i] = RAMP[idx]
            cols[i] = best_pal[idx]

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


def make_balls(w, h):
    n = 6
    balls = [Ball(i, n, w, h) for i in range(n)]
    hues = [b.hue for b in balls]
    pals = build_palette(hues)
    for b, p in zip(balls, pals):
        b.pal = p
    return balls


def main():
    balls = None
    size = None
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

            if (w, h) != size:
                balls = make_balls(w, h)
                size = (w, h)
                sys.stdout.write('\033[2J')

            sys.stdout.write(render(balls, w, h, t))
            sys.stdout.flush()
            t += 0.04
            time.sleep(0.035)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')


if __name__ == '__main__':
    main()
