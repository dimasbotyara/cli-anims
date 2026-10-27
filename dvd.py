#!/usr/bin/env python3
"""Классический прыгающий DVD-логотип с радужным следом. Space — пауза, Q — выход."""

import math
import os
import random
import sys
import time


def read_key():
    if os.name == 'nt':
        import msvcrt
        if not msvcrt.kbhit():
            return None
        return msvcrt.getwch().lower()
    import select
    fd = sys.stdin.fileno()
    if not select.select([fd], [], [], 0)[0]:
        return None
    data = os.read(fd, 32)
    return chr(data[0]).lower() if data else None


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
    for i in range(72):
        hue = i / 72.0
        row = []
        for level in (0.16, 0.30, 0.48, 0.72, 1.0):
            r, g, b = hsv_to_rgb(hue, 0.85, level)
            row.append(f"\033[38;2;{r};{g};{b}m")
        pal.append(row)
    return pal


PAL = build_palette()

ART_D = ('████ ', '██ ██', '██ ██', '██ ██', '████ ')
ART_V = ('██  ██', '██  ██', '██  ██', ' ████ ', '  ██  ')
ART = tuple(d + ' ' + v + ' ' + d for d, v in zip(ART_D, ART_V))
FALLBACK = ('DVD',)

SPARK_COLORS = (
    '\033[1;38;2;255;255;220m',
    '\033[1;38;2;255;220;120m',
    '\033[38;2;255;180;80m',
)


class Dvd:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.logo = ART if w >= 22 and h >= 9 else FALLBACK
        self.lw = len(self.logo[0])
        self.lh = len(self.logo)
        self.x = random.uniform(0, max(1, w - self.lw))
        self.y = random.uniform(0, max(1, h - self.lh))
        self.vx = random.choice((-1.0, 1.0)) * random.uniform(0.55, 0.85)
        self.vy = random.choice((-1.0, 1.0)) * random.uniform(0.35, 0.60)
        self.hue = random.random()
        self.trail = []
        self.sparks = []
        self.frame = 0
        self.bounces = 0

    def burst(self, x, y):
        for _ in range(12):
            a = random.uniform(0, math.tau)
            sp = random.uniform(0.25, 0.95)
            self.sparks.append([
                x, y, math.cos(a) * sp, math.sin(a) * sp * 0.5,
                random.randint(8, 16), random.choice('*+·'),
            ])

    def update(self):
        self.frame += 1
        self.hue = (self.hue + 0.0025) % 1.0

        self.x += self.vx
        self.y += self.vy

        hit = False
        if self.x <= 0:
            self.x = 0.0
            self.vx = abs(self.vx)
            hit = True
        elif self.x + self.lw >= self.w:
            self.x = float(self.w - self.lw)
            self.vx = -abs(self.vx)
            hit = True
        if self.y <= 0:
            self.y = 0.0
            self.vy = abs(self.vy)
            hit = True
        elif self.y + self.lh >= self.h:
            self.y = float(self.h - self.lh)
            self.vy = -abs(self.vy)
            hit = True

        if hit:
            self.bounces += 1
            self.hue = (self.hue + 0.13) % 1.0
            self.burst(self.x + self.lw / 2, self.y + self.lh / 2)

        if self.frame % 5 == 0:
            self.trail.append((self.x, self.y, self.hue))
            if len(self.trail) > 4:
                self.trail.pop(0)

        alive = []
        for s in self.sparks:
            s[0] += s[2]
            s[1] += s[3]
            s[3] += 0.025
            s[2] *= 0.97
            s[4] -= 1
            if s[4] > 0 and 0 <= s[0] < self.w and 0 <= s[1] < self.h:
                alive.append(s)
        self.sparks = alive

    def draw(self):
        w, h = self.w, self.h
        chars = [' '] * (w * h)
        cols = [None] * (w * h)

        def stamp(x0, y0, hue, level):
            hi = int(hue * 71) % 72
            for ry, line in enumerate(self.logo):
                for rx, ch in enumerate(line):
                    if ch == ' ':
                        continue
                    x = int(x0) + rx
                    y = int(y0) + ry
                    if 0 <= x < w and 0 <= y < h:
                        i = y * w + x
                        chars[i] = ch
                        cols[i] = PAL[hi][level]

        for n, (tx, ty, th) in enumerate(self.trail):
            stamp(tx, ty, th, 1 if n == len(self.trail) - 1 else 0)
        stamp(self.x, self.y, self.hue, 4)

        for s in self.sparks:
            x, y = int(s[0]), int(s[1])
            if 0 <= x < w and 0 <= y < h:
                i = y * w + x
                chars[i] = s[5]
                if s[4] > 10:
                    cols[i] = SPARK_COLORS[0]
                elif s[4] > 5:
                    cols[i] = SPARK_COLORS[1]
                else:
                    cols[i] = SPARK_COLORS[2]

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
    fd = sys.stdin.fileno()
    old = None
    if os.name != 'nt' and os.isatty(fd):
        import termios
        import tty
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)

    sys.stdout.write("\033[?25l\033[2J")
    dvd = None
    size = None
    paused = False
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            w = max(20, w)
            h = max(6, h)

            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused

            if (w, h) != size:
                dvd = Dvd(w, h)
                size = (w, h)
                sys.stdout.write('\033[2J')

            if not paused:
                dvd.update()

            sys.stdout.write(dvd.draw())
            sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        if old is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write('\033[0m\033[?25h\n')


if __name__ == '__main__':
    main()
