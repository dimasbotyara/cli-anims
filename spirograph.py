#!/usr/bin/env python3
"""Спирограф: гипотрохоида рисуется светящейся линией. Ctrl+C — выход."""

import math
import os
import random
import sys
import time


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
        for level in (0.18, 0.36, 0.58, 0.80, 1.0):
            r, g, b = hsv_to_rgb(hue, 0.82, level)
            row.append(f"\033[1;38;2;{r};{g};{b}m")
        pal.append(row)
    return pal


PAL = build_palette()
WHITE = '\033[1;38;2;255;255;255m'


def make_curve(rnd):
    while True:
        R = rnd.randint(6, 13)
        r = rnd.randint(2, max(2, int(R * 0.55)))
        d = rnd.uniform(r * 1.2, r * 2.2)
        g = math.gcd(R - r, r)
        turns = r / g
        if turns <= 8:
            break

    total = math.tau * turns
    n = 7000
    raw = []
    maxr = 1e-9
    for i in range(n):
        t = total * i / n
        x = (R - r) * math.cos(t) + d * math.cos((R - r) / r * t)
        y = (R - r) * math.sin(t) - d * math.sin((R - r) / r * t)
        r2 = math.hypot(x, y)
        if r2 > maxr:
            maxr = r2
        raw.append((x, y))

    pts = []
    for x, y in raw:
        nx, ny = x / maxr, y / maxr
        hue = (math.atan2(ny, nx) / math.tau + 0.5) % 1.0
        pts.append((nx, ny, int(hue * 63)))
    return pts


class Spiro:
    def __init__(self):
        self.rnd = random.Random()
        self.new()

    def new(self):
        self.points = make_curve(self.rnd)
        self.n = len(self.points)
        self.progress = 0.0
        self.finished = False
        self.hold = 0.0

    def update(self, dt):
        if not self.finished:
            self.progress = min(1.0, self.progress + dt * 0.13)
            if self.progress >= 1.0:
                self.finished = True
        else:
            self.hold += dt
            if self.hold > 2.9:
                self.new()


def render(sp, w, h):
    chars = [' '] * (w * h)
    cols = [None] * (w * h)

    cx, cy = w / 2.0, h / 2.0
    scale = min(h * 0.42, w * 0.21)

    if sp.finished:
        if sp.hold > 2.25:
            level = max(1, 3 - int((sp.hold - 2.25) / 0.65 * 3))
        else:
            level = 3
    else:
        level = 3

    drawn = int(sp.progress * sp.n)
    head = drawn - 1

    for i in range(drawn):
        nx, ny, hi = sp.points[i]
        x = int(round(cx + nx * scale * 2.0))
        y = int(round(cy + ny * scale))
        if 0 <= x < w and 0 <= y < h:
            j = y * w + x
            chars[j] = '·'
            if not sp.finished and i > head - 24:
                cols[j] = PAL[hi][4]
            else:
                cols[j] = PAL[hi][level]

    if not sp.finished and head >= 0:
        nx, ny, hi = sp.points[head]
        x = int(round(cx + nx * scale * 2.0))
        y = int(round(cy + ny * scale))
        if 0 <= x < w and 0 <= y < h:
            j = y * w + x
            chars[j] = '@'
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
    sp = None
    size = None
    last = time.monotonic()
    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            w = max(30, w)
            h = max(12, h)

            if (w, h) != size:
                sp = Spiro()
                size = (w, h)
                sys.stdout.write('\033[2J')

            now = time.monotonic()
            dt = min(0.1, now - last)
            last = now
            sp.update(dt)

            sys.stdout.write(render(sp, w, h))
            sys.stdout.flush()
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')


if __name__ == '__main__':
    main()
