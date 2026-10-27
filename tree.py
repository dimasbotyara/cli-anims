#!/usr/bin/env python3
"""Растущее дерево: ветки, листья, звёзды и смена сезонов. Ctrl+C — выход."""

import math
import os
import random
import sys
import time

MAXD = 7

BLOOMS = (
    ((255, 95, 150), (255, 160, 195), (255, 230, 242)),   # сакура
    ((90, 230, 125), (165, 250, 175), (235, 255, 215)),   # зелёный
    ((255, 155, 55), (255, 205, 100), (255, 242, 190)),   # осень
)

LEAF_PAL = [
    [f"\033[1;38;2;{r};{g};{b}m" for (r, g, b) in bloom]
    for bloom in BLOOMS
]

TRUNK_PAL = {}
for _d in range(1, MAXD + 3):
    _k = (_d - 1) / (MAXD + 1)
    TRUNK_PAL[_d] = f"\033[38;2;{int(155 - 60 * _k)};{int(115 - 50 * _k)};{int(80 - 42 * _k)}m"

STAR_PAL = [
    '\033[38;2;70;80;105m',
    '\033[38;2;105;120;155m',
    '\033[38;2;150;170;210m',
    '\033[1;38;2;220;230;255m',
]
GRASS_PAL = (
    '\033[38;2;35;90;55m',
    '\033[38;2;55;125;70m',
    '\033[38;2;90;170;95m',
)
GROUND = '\033[38;2;38;58;38m'


class Tree:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.base_y = h - 2.0
        self.t = 0.0
        self.cycle_t0 = 0.0
        self.cycle_len = 15.5
        self.seed = random.randrange(1 << 30)
        self.bloom = random.randrange(3)
        self.particles = []
        self._make_scenery()
        self._new_tree()

    def _make_scenery(self):
        w, h = self.w, self.h
        self.stars = []
        for _ in range(max(20, w * h // 55)):
            self.stars.append([
                random.uniform(0, w), random.uniform(0, h * 0.72),
                random.uniform(0.25, 1.0), random.uniform(0, math.tau),
            ])
        self.grass = []
        for _ in range(max(8, w // 5)):
            x = random.uniform(0, w)
            y = random.choice((h - 1, h - 1, h - 2))
            self.grass.append([
                x, y, random.uniform(0, math.tau),
                random.choice((',', "'", '"', '`')),
                random.randrange(3),
            ])

    def _grow(self, rnd, x, y, ang, length, depth):
        x2 = x + math.cos(ang) * length * 1.8
        y2 = y + math.sin(ang) * length
        birth = 0.06 + (MAXD - depth) / MAXD * 0.72 + rnd.random() * 0.05
        self.branches.append((x, y, x2, y2, depth, birth))
        if depth <= 1:
            if rnd.random() < 0.85:
                self.tips.append((
                    x2, y2, rnd.uniform(0, math.tau),
                    rnd.choice(('*', '+', '·')),
                    0.84 + rnd.random() * 0.13,
                ))
            return
        spread = rnd.uniform(0.42, 0.72)
        for sign in (-1, 1):
            self._grow(
                rnd, x2, y2,
                ang + sign * spread + rnd.uniform(-0.10, 0.10),
                length * rnd.uniform(0.68, 0.79),
                depth - 1,
            )

    def _new_tree(self):
        rnd = random.Random(self.seed)
        self.branches = []
        self.tips = []

        cx = self.w / 2.0
        top_x = cx + rnd.uniform(-0.8, 0.8)
        top_y = self.base_y - self.h * 0.24
        self.branches.append((cx, self.base_y, top_x, top_y, MAXD + 1, 0.0))

        length = self.h * 0.17
        for off in (-0.52, 0.0, 0.52):
            self._grow(
                rnd, top_x, top_y,
                -math.pi / 2 + off + rnd.uniform(-0.08, 0.08),
                length * rnd.uniform(0.9, 1.1),
                MAXD,
            )

    def _wind(self, x, y, depth, t):
        height = max(0.0, self.base_y - y)
        gust = 1.0 + 0.45 * math.sin(t * 0.37)
        return (
            math.sin(t * 1.25 + depth * 0.55 + x * 0.10) * 0.030
            + math.sin(t * 0.72 + 0.6) * 0.012
        ) * height * gust

    def update(self, dt):
        self.t += dt

        if self.t - self.cycle_t0 > self.cycle_len:
            self.seed = random.randrange(1 << 30)
            self.bloom = (self.bloom + 1) % 3
            self.cycle_t0 = self.t
            self._new_tree()
            self.particles = []

        progress = min(1.0, (self.t - self.cycle_t0) / 7.0)
        if (progress > 0.92 and len(self.particles) < 26
                and self.tips and random.random() < 0.11):
            tx, ty, ph, ch, _ = random.choice(self.tips)
            wx = tx + self._wind(tx, ty, 1, self.t)
            self.particles.append([
                wx, ty, random.uniform(-0.15, 0.15),
                random.uniform(0.10, 0.28), ph, ch,
            ])

        alive = []
        for p in self.particles:
            p[0] += math.sin(self.t * 2.5 + p[4]) * 0.10 + p[2]
            p[1] += p[3]
            if 0 <= p[0] < self.w and p[1] < self.h - 1:
                alive.append(p)
        self.particles = alive

    def _line(self, put, x0, y0, x1, y1, ch, color, width):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        if width <= 1:
            offs = (0,)
        elif width == 2:
            offs = (0, 1)
        else:
            offs = (-1, 0, 1)
        for k in range(n + 1):
            f = k / n
            x = int(round(x0 + (x1 - x0) * f))
            y = int(round(y0 + (y1 - y0) * f))
            for off in offs:
                put(x + off, y, ch, color)

    def draw(self):
        w, h = self.w, self.h
        chars = [' '] * (w * h)
        cols = [None] * (w * h)

        def put(x, y, ch, color):
            if 0 <= x < w and 0 <= y < h:
                i = y * w + x
                chars[i] = ch
                cols[i] = color

        # звёзды
        for sx, sy, sb, sp in self.stars:
            q = sb * (0.55 + 0.45 * math.sin(self.t * 1.6 + sp))
            if q < 0.12:
                continue
            ch = '.' if q < 0.4 else ('+' if q < 0.75 else '*')
            put(int(sx), int(sy), ch, STAR_PAL[min(3, int(q * 4))])

        # земля и трава
        for x in range(w):
            put(x, h - 1, '_', GROUND)
        for gx, gy, ph, ch, ci in self.grass:
            sway = math.sin(self.t * 1.5 + ph) * 0.7
            put(int(round(gx + sway)), gy, ch, GRASS_PAL[ci])

        progress = min(1.0, (self.t - self.cycle_t0) / 7.0)

        # ветки
        for x0, y0, x1, y1, depth, birth in self.branches:
            if progress <= birth:
                continue
            local = min(1.0, (progress - birth) / 0.10)
            ex = x0 + (x1 - x0) * local
            ey = y0 + (y1 - y0) * local
            wx0 = self._wind(x0, y0, depth, self.t)
            wx1 = self._wind(ex, ey, depth, self.t)
            if depth > MAXD:
                width = 3
            elif depth > MAXD - 2:
                width = 2
            else:
                width = 1
            ch = '#' if depth >= MAXD - 1 else ('*' if depth >= MAXD - 3 else '·')
            self._line(
                put, x0 + wx0, y0, ex + wx1, ey,
                ch, TRUNK_PAL[min(depth, MAXD + 2)], width,
            )

        # листья
        if progress > 0.84:
            for tx, ty, ph, ch, birth in self.tips:
                if progress < birth:
                    continue
                wx = tx + self._wind(tx, ty, 1, self.t)
                tw = 0.5 + 0.5 * math.sin(self.t * 1.8 + ph)
                lvl = 0 if tw > 0.66 else (1 if tw > 0.33 else 2)
                put(int(round(wx)), int(round(ty)), ch, LEAF_PAL[self.bloom][lvl])

        # опавшие листья
        for p in self.particles:
            put(int(round(p[0])), int(round(p[1])), p[5], LEAF_PAL[self.bloom][1])

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
    tree = None
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
                tree = Tree(w, h)
                size = (w, h)
                sys.stdout.write('\033[2J')

            now = time.monotonic()
            dt = min(0.1, now - last)
            last = now
            tree.update(dt)

            sys.stdout.write(tree.draw())
            sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')


if __name__ == '__main__':
    main()
