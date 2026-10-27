#!/usr/bin/env python3
"""Чёрная дыра: аккреционный диск, фотонное кольцо и линзирование. Ctrl+C — выход."""

import math
import os
import random
import sys
import time

RAMP = ' .:-=+*#%@'


def make_stars(w, h):
    stars = []
    for _ in range(max(50, w * h // 16)):
        stars.append([
            random.uniform(0, w), random.uniform(0, h),
            random.uniform(0.25, 1.0), random.uniform(0, math.tau),
        ])
    return stars


def star_color(v):
    r = int(v * 255)
    g = int(v * 245)
    b = int(v * 255)
    return f"\033[38;2;{r};{g};{b}m"


def render(w, h, t, stars):
    chars = [' '] * (w * h)
    cols = [None] * (w * h)

    def put(x, y, ch, color):
        if 0 <= x < w and 0 <= y < h:
            i = y * w + x
            chars[i] = ch
            cols[i] = color

    for sx, sy, sb, sp in stars:
        x, y = int(sx), int(sy)
        if not (0 <= x < w and 0 <= y < h):
            continue
        q = sb * (0.5 + 0.5 * math.sin(t * 2.1 + sp))
        if q < 0.12:
            continue
        if q < 0.4:
            ch = '.'
        elif q < 0.7:
            ch = '+'
        else:
            ch = '*'
        put(x, y, ch, star_color(0.3 + 0.7 * q))

    cx = w * 0.5 + math.sin(t * 0.23) * 1.4
    cy = h * 0.5 + math.cos(t * 0.19) * 0.5
    R = min(w * 0.33, h * 0.92)
    rh = R * 0.30
    inner = rh * 1.28
    outer = R * 1.50

    for y in range(h):
        dy = y - cy
        dyv = dy * 2.1
        yd = dy * 5.0
        for x in range(w):
            dx = x - cx
            r = math.hypot(dx, dyv)

            # тень чёрной дыры — стираем звёзды
            if r < rh:
                put(x, y, ' ', None)
                continue

            ang = math.atan2(dyv, dx)

            # аккреционный диск (сильно наклонённый)
            er = math.hypot(dx, yd)
            if inner <= er <= outer:
                u = (er - inner) / (outer - inner)
                swirl = 0.5 + 0.5 * math.sin(ang * 5.0 - er * 0.45 - t * 4.0)
                fine = 0.5 + 0.5 * math.sin(ang * 15.0 + er * 0.9 + t * 2.0)
                beam = 0.65 + 0.50 * max(0.0, -math.cos(ang))
                base = (1.0 - u) ** 1.5
                bright = base * (0.45 + 0.55 * swirl) * (0.55 + 0.45 * fine) * beam
                if bright > 0.04:
                    idx = min(len(RAMP) - 1, max(1, int(bright * len(RAMP))))
                    inten = 0.32 + 0.68 * min(1.0, bright * 1.25)
                    tg = 0.42 + 0.48 * (1.0 - u) ** 1.5
                    tb = 0.10 + 0.68 * (1.0 - u) ** 3.5
                    rcol = int(255 * inten)
                    gcol = int(255 * inten * tg)
                    bcol = int(255 * inten * tb)
                    put(x, y, RAMP[idx], f"\033[38;2;{rcol};{gcol};{bcol}m")

            # линзированные дуги над и под дырой
            qs = r / rh
            if 1.10 < qs < 1.34 and abs(dyv) > 0.45 * r:
                arc = 1.0 - abs(qs - 1.21) / 0.13
                if arc > 0.05:
                    inten = 0.30 + 0.70 * arc
                    rcol = int(255 * inten)
                    gcol = int(190 * inten)
                    bcol = int(115 * inten)
                    put(x, y, '#', f"\033[1;38;2;{rcol};{gcol};{bcol}m")

            # фотонное кольцо
            if abs(r - rh * 1.045) < 0.55:
                pulse = 0.75 + 0.25 * math.sin(ang * 3.0 - t * 2.0)
                rcol = int(235 * pulse)
                gcol = int(225 * pulse)
                bcol = int(255 * pulse)
                put(x, y, '@', f"\033[1;38;2;{rcol};{gcol};{bcol}m")

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
    stars = None
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
            w = max(40, w)
            h = max(14, h)

            if (w, h) != size:
                stars = make_stars(w, h)
                size = (w, h)
                sys.stdout.write('\033[2J')

            sys.stdout.write(render(w, h, t, stars))
            sys.stdout.flush()
            t += 0.045
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')


if __name__ == '__main__':
    main()
