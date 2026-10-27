#!/usr/bin/env python3
"""Дождливая ночь: капли, круги на воде и вспышки молний. Ctrl+C — выход."""

import math
import os
import random
import sys
import time

RAIN_COLORS = (
    '\033[38;2;55;80;120m',
    '\033[38;2;75;105;150m',
    '\033[38;2;100;135;185m',
    '\033[38;2;130;170;220m',
    '\033[1;38;2;175;210;255m',
)
GROUND = '\033[38;2;35;55;85m'
PUDDLE = '\033[38;2;55;85;130m'
RIPPLE = (
    '\033[38;2;70;110;150m',
    '\033[38;2;95;140;185m',
    '\033[38;2;130;180;225m',
)
BOLT = '\033[1;38;2;225;240;255m'


class Rain:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.t = 0.0
        self.drops = []
        for _ in range(max(60, w * h // 6)):
            self.drops.append(self._spawn(initial=True))
        self.ripples = []
        self.bolt = None
        self.bolt_life = 0
        self.flash = 0.0
        self.cooldown = random.uniform(1.5, 4.0)
        self.tufts = [(random.uniform(0, w), random.choice((',', "'", '`')))
                      for _ in range(max(6, w // 10))]

    def _spawn(self, initial=False):
        speed = random.uniform(0.35, 1.55)
        if speed < 0.7:
            ch = '.'
        elif speed < 1.2:
            ch = '|'
        else:
            ch = '/'
        y = random.uniform(0, self.h - 2) if initial else random.uniform(-2, 0)
        return [random.uniform(0, self.w), y, speed, ch]

    def _make_bolt(self):
        x = random.uniform(self.w * 0.15, self.w * 0.85)
        y = 0.0
        pts = []
        while y < self.h - 1:
            pts.append((int(round(x)), int(round(y))))
            y += random.uniform(0.8, 1.8)
            x += random.choice((-1.2, -0.6, 0.0, 0.0, 0.6, 1.2))
            x = max(1.0, min(self.w - 2.0, x))
        bolt = []
        for i, (x, y) in enumerate(pts):
            nx, ny = pts[min(i + 1, len(pts) - 1)]
            px, py = pts[max(i - 1, 0)]
            dx, dy = nx - px, ny - py
            if abs(dx) <= abs(dy) * 0.8:
                ch = '|'
            elif dx > 0:
                ch = '\\'
            else:
                ch = '/'
            bolt.append((x, y, ch))
        self.bolt = bolt
        self.bolt_life = random.randint(5, 9)
        self.flash = 1.0

    def update(self, dt):
        self.t += dt
        w, h = self.w, self.h

        for d in self.drops:
            d[1] += d[2]
            d[0] -= 0.10 + d[2] * 0.08
            if d[1] >= h - 1:
                if random.random() < 0.28 and len(self.ripples) < 50:
                    self.ripples.append([d[0], 0])
                d[0] = random.uniform(0, w)
                d[1] = random.uniform(-3, 0)
                d[2] = random.uniform(0.35, 1.55)
                if d[2] < 0.7:
                    d[3] = '.'
                elif d[2] < 1.2:
                    d[3] = '|'
                else:
                    d[3] = '/'
            if d[0] < 0:
                d[0] += w
            elif d[0] >= w:
                d[0] -= w

        alive = []
        for r in self.ripples:
            r[1] += 1
            if r[1] <= 8:
                alive.append(r)
        self.ripples = alive

        if self.bolt_life > 0:
            self.bolt_life -= 1
            if self.bolt_life == 0:
                self.bolt = None
        self.flash *= 0.82

        self.cooldown -= dt
        if self.cooldown <= 0 and self.bolt is None:
            self._make_bolt()
            self.cooldown = random.uniform(3.5, 8.0)

    def draw(self):
        w, h = self.w, self.h
        chars = [' '] * (w * h)
        if self.flash > 0.06:
            a = min(1.0, self.flash)
            bg = f"\033[48;2;{int(16 + 45 * a)};{int(22 + 55 * a)};{int(40 + 80 * a)}m"
            cols = [bg] * (w * h)
        else:
            cols = [None] * (w * h)

        def put(x, y, ch, color):
            if 0 <= x < w and 0 <= y < h:
                i = y * w + x
                chars[i] = ch
                cols[i] = color

        # земля
        for x in range(w):
            put(x, h - 1, '_' if x % 3 else '-', GROUND)
        for x, ch in self.tufts:
            put(int(x), h - 2, ch, GROUND)

        # круги на воде
        for rx, age in self.ripples:
            rad = age // 2
            color = RIPPLE[min(2, age // 3)]
            x = int(round(rx))
            if rad == 0:
                put(x, h - 1, 'o', color)
            else:
                put(x - rad, h - 1, '(', color)
                put(x + rad, h - 1, ')', color)
            put(x, h - 2, '·', PUDDLE)

        # капли
        for x, y, speed, ch in self.drops:
            ci = min(4, int(speed * 3))
            if self.flash > 0.4:
                ci = min(4, ci + 2)
            put(int(x), int(y), ch, RAIN_COLORS[ci])

        # молния
        if self.bolt:
            for x, y, ch in self.bolt:
                put(x, y, ch, BOLT)
                if self.bolt_life % 2 == 0:
                    put(x + 1, y, ch, RAIN_COLORS[4])

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
    rain = None
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
            h = max(10, h)

            if (w, h) != size:
                rain = Rain(w, h)
                size = (w, h)
                sys.stdout.write('\033[2J')

            now = time.monotonic()
            dt = min(0.1, now - last)
            last = now
            rain.update(dt)

            sys.stdout.write(rain.draw())
            sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')


if __name__ == '__main__':
    main()
