#!/usr/bin/env python3
"""Солнечная система. Ctrl+C — выход."""

import math
import os
import random
import sys
import time


# Планеты от Меркурия к Нептуну: (цвет truecolor, символ)
PLANETS = [
    ((172, 162, 152), 'o'),   # Меркурий
    ((232, 192, 122), 'o'),   # Венера
    (( 96, 162, 255), 'o'),   # Земля (с Луной)
    ((255, 112,  82), 'o'),   # Марс
    ((232, 180, 132), 'O'),   # Юпитер
    ((222, 202, 142), 'O'),   # Сатурн (с кольцом)
    ((140, 232, 232), 'o'),   # Уран
    ((106, 132, 255), 'o'),   # Нептун
]


def render(chars, cols, w, h):
    # Сборка кадра: код цвета вставляется только при смене цвета
    out = ["\033[H"]
    for y in range(h):
        cur = None
        row = []
        base = y * w
        for x in range(w):
            i = base + x
            c = cols[i]
            if c != cur:
                row.append('\033[0m' if c is None else c)
                cur = c
            row.append(chars[i])
        row.append('\033[0m\n')
        out.append(''.join(row))
    return ''.join(out)


class Scene:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.t = random.random() * 500.0   # случайная фаза — запусы различаются
        self.cx, self.cy = (w - 1) / 2.0, (h - 1) / 2.0
        # радиус в «условных» единицах по X; по Y эллипс сжат вдвое (аспект 1:2)
        self.rmax = max(4.0, min(w / 2 - 2, h - 3))

        # мерцающие звёзды: (x, y, фаза, скорость, базовая яркость, символ)
        self.stars = []
        for _ in range(max(8, w * h // 55)):
            self.stars.append((
                random.randrange(w), random.randrange(h),
                random.random() * math.tau,
                random.uniform(0.05, 0.2),
                random.uniform(0.25, 0.85),
                random.choice('..·+*'),
            ))

        # орбиты: (радиус, фаза, угловая скорость ∝ r^-1.5 — законы Кеплера)
        self.orbits = []
        self.rings = []   # предрассчитанные точки тусклых орбитальных колец
        for i in range(len(PLANETS)):
            r = self.rmax * (0.22 + 0.72 * i / 7)
            self.orbits.append((r, random.random() * math.tau, 0.9 / r ** 1.5))
            pts = set()
            steps = max(24, int(r * 3.2))
            for s in range(steps):
                a = math.tau * s / steps
                x = int(round(self.cx + r * math.cos(a)))
                y = int(round(self.cy + r * 0.5 * math.sin(a)))
                if 0 <= x < w and 0 <= y < h:
                    pts.add((x, y))
            self.rings.append(pts)

        # комета: вытянутый эллипс с фокусом в Солнце, ρ = p / (1 + e·cosθ)
        self.ce = 0.62                      # эксцентриситет
        self.ca = self.rmax * 0.62          # большая полуось
        self.cp = self.ca * (1 - self.ce ** 2)
        self.cth = random.random() * math.tau
        self.cw = random.choice((1, -1))    # направление обхода

    def update(self):
        self.t += 1
        # 2-й закон Кеплера: у перигелия комета ускоряется (dθ/dt ∝ 1/ρ²)
        rho = self.cp / (1 + self.ce * math.cos(self.cth))
        k = 0.02 * (0.6 * self.rmax) ** 2
        self.cth += self.cw * k / max(1.0, rho * rho)

    def draw(self):
        w, h, t = self.w, self.h, self.t
        chars = [' '] * (w * h)
        cols = [None] * (w * h)

        def put(x, y, ch, col):
            if 0 <= x < w and 0 <= y < h:
                i = y * w + x
                chars[i] = ch
                cols[i] = col

        # 1) фон — мерцающие звёзды
        for x, y, ph, spd, base, ch in self.stars:
            v = base * (0.55 + 0.45 * math.sin(t * spd + ph))
            b = int(v * 255)
            if b > 14:
                put(x, y, ch, f"\033[38;2;{b};{int(b * 0.97)};{min(255, int(b * 1.12))}m")

        # 2) тусклые орбитальные кольца
        ring_col = "\033[38;2;56;60;76m"
        for pts in self.rings:
            for x, y in pts:
                i = y * w + x
                if chars[i] == ' ':
                    chars[i] = '·'
                    cols[i] = ring_col

        # 3) Солнце с пульсирующей короной
        sx, sy = int(round(self.cx)), int(round(self.cy))
        pulse = 0.7 + 0.3 * math.sin(t * 0.09)
        corona = f"\033[38;2;{int(215 * pulse)};{int(125 * pulse)};30m"
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            put(sx + dx, sy + dy, '·', corona)
        put(sx, sy, '☀', f"\033[1;38;2;255;{int(185 + 45 * pulse)};45m")

        # 4) планеты на орбитах
        ex = ey = None
        for i, (r, ph, om) in enumerate(self.orbits):
            a = ph + t * om
            x = int(round(self.cx + r * math.cos(a)))
            y = int(round(self.cy + r * 0.5 * math.sin(a)))
            color, ch = PLANETS[i]
            if i == 5:   # кольцо Сатурна по бокам
                rc = "\033[38;2;168;152;104m"
                put(x - 2, y, '─', rc)
                put(x + 2, y, '─', rc)
            put(x, y, ch, f"\033[1;38;2;{color[0]};{color[1]};{color[2]}m")
            if i == 2:
                ex, ey = x, y

        # Луна на быстрой орбите вокруг Земли
        if ex is not None:
            ma = t * 0.22
            put(int(round(ex + 2.3 * math.cos(ma))),
                int(round(ey + 1.15 * math.sin(ma))),
                '·', "\033[38;2;205;205;215m")

        # 5) комета: голова + хвост, вытянутый от Солнца наружу
        th = self.cth
        rho = self.cp / (1 + self.ce * math.cos(th))
        x = self.cx + rho * math.cos(th)
        y = self.cy + rho * math.sin(th) * 0.5
        ux, uy = math.cos(th), 0.5 * math.sin(th)   # направление «от Солнца»
        norm = math.hypot(ux, uy) or 1.0
        ux, uy = ux / norm, uy / norm
        # хвост длиннее вблизи перигелия
        tail = 2 + int(5.5 * max(0.0, 1.0 - rho / (self.ca * (1 + self.ce))))
        for k in range(tail, 0, -1):
            v = 0.15 + 0.7 * (1 - k / (tail + 1))
            put(int(round(x + ux * k)), int(round(y + uy * k)), '·',
                f"\033[38;2;{int(140 * v)};{int(220 * v)};{int(255 * v)}m")
        put(int(round(x)), int(round(y)), '*', "\033[1;38;2;225;245;255m")

        return render(chars, cols, w, h)


def main():
    fd = sys.stdin.fileno()
    old = None
    if os.name != 'nt':
        # cbreak: клавиши отдаются сразу; Ctrl+C (ISIG) продолжает работать
        try:
            import termios
            import tty
            old = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            old = None
    sys.stdout.write("\033[?25l\033[2J")
    scene = None
    size = None
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            w = max(6, w)
            h = max(2, h)
            if (w, h) != size or scene is None:
                scene = Scene(w, h)      # пересоздание при resize
                size = (w, h)
                sys.stdout.write("\033[2J")
            scene.update()
            sys.stdout.write(scene.draw())
            sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        if old is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
