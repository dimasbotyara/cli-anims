#!/usr/bin/env python3
"""Двойной маятник. Ctrl+C — выход."""

import os, sys, time, math
from collections import deque

# параметры всех маятников (одинаковые; отличаются только начальные углы)
L1 = L2 = 1.0
M1 = M2 = 1.0
G = 9.81
DT = 0.004        # шаг интегрирования
SUBSTEPS = 7      # подшагов РК4 на кадр
TRAIL_LEN = 90    # длина следа нижнего шарика


class Pendulum:
    __slots__ = ('th1', 'w1', 'th2', 'w2', 'color', 'trail')

    def __init__(self, th1, th2, color):
        self.th1 = th1
        self.w1 = 0.0
        self.th2 = th2
        self.w2 = 0.0
        self.color = color
        self.trail = deque(maxlen=TRAIL_LEN)   # экранные координаты следа

    @staticmethod
    def _deriv(th1, w1, th2, w2):
        # стандартные уравнения движения двойного маятника
        d = th1 - th2
        den = 2.0 * M1 + M2 - M2 * math.cos(2.0 * d)
        a1 = (-G * (2.0 * M1 + M2) * math.sin(th1)
              - M2 * G * math.sin(th1 - 2.0 * th2)
              - 2.0 * math.sin(d) * M2 * (w2 * w2 * L2 + w1 * w1 * L1 * math.cos(d))
              ) / (L1 * den)
        a2 = (2.0 * math.sin(d) * (w1 * w1 * L1 * (M1 + M2)
              + G * (M1 + M2) * math.cos(th1)
              + w2 * w2 * L2 * M2 * math.cos(d))
              ) / (L2 * den)
        return (w1, a1, w2, a2)

    def step(self, dt):
        # один классический шаг РК4 по состоянию (th1, w1, th2, w2)
        f = self._deriv
        y = (self.th1, self.w1, self.th2, self.w2)
        k1 = f(*y)
        s = tuple(y[i] + 0.5 * dt * k1[i] for i in range(4))
        k2 = f(*s)
        s = tuple(y[i] + 0.5 * dt * k2[i] for i in range(4))
        k3 = f(*s)
        s = tuple(y[i] + dt * k3[i] for i in range(4))
        k4 = f(*s)
        self.th1 += dt * (k1[0] + 2.0 * (k2[0] + k3[0]) + k4[0]) / 6.0
        self.w1 += dt * (k1[1] + 2.0 * (k2[1] + k3[1]) + k4[1]) / 6.0
        self.th2 += dt * (k1[2] + 2.0 * (k2[2] + k3[2]) + k4[2]) / 6.0
        self.w2 += dt * (k1[3] + 2.0 * (k2[3] + k3[3]) + k4[3]) / 6.0


class Scene:
    """Три почти одинаковых маятника: расхождение траекторий — демонстрация хаоса."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        eps = 0.03   # крошечная разница начальных углов
        self.pends = [
            Pendulum(2.10, 2.10, (255, 90, 90)),               # красный
            Pendulum(2.10 + eps, 2.10, (90, 255, 130)),        # зелёный
            Pendulum(2.10 + 2.0 * eps, 2.10, (90, 200, 255)),  # голубой
        ]
        # точка подвеса и масштаб под текущий размер терминала
        self.px = w // 2
        self.py = max(1, h * 2 // 5)
        # полная длина (L1+L2)=2 обязана влезать и вниз, и вбок
        down = float(self.h - self.py - 1)
        side = (self.w - 2) / 4.0    # вертикаль ужата вдвое из-за аспекта символов
        self.scale = max(1.0, min(down, side))

    def _coords(self, p):
        # экранные координаты шариков; вертикаль умножаем на 0.5 (аспект)
        x1 = self.px + math.sin(p.th1) * L1 * self.scale
        y1 = self.py + math.cos(p.th1) * L1 * self.scale * 0.5
        x2 = x1 + math.sin(p.th2) * L2 * self.scale
        y2 = y1 + math.cos(p.th2) * L2 * self.scale * 0.5
        return x1, y1, x2, y2

    def update(self):
        for p in self.pends:
            for _ in range(SUBSTEPS):
                p.step(DT)
            # след нижнего шарика — одна точка за кадр
            p.trail.append(self._coords(p)[2:])

    @staticmethod
    def _rod(x0, y0, x1, y1, color, put):
        # стержень: сэмплы вдоль отрезка; по вертикали сэмплы гуще
        steps = max(2, int(abs(x1 - x0) + abs(y1 - y0) * 2.0) + 1)
        for i in range(steps + 1):
            t = i / steps
            put(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, '·', color, False)

    def draw(self):
        w, h = self.w, self.h
        grid = [[' '] * w for _ in range(h)]
        cols = [[None] * w for _ in range(h)]
        bold = [[False] * w for _ in range(h)]

        def put(x, y, ch, color, hot):
            xi, yi = int(x), int(y)
            if 0 <= xi < w and 0 <= yi < h:
                grid[yi][xi] = ch
                cols[yi][xi] = color
                bold[yi][xi] = hot

        # крепление подвеса
        for dx in (-1, 0, 1):
            put(self.px + dx, self.py, '─', (150, 150, 160), False)

        # сначала следы — они лежат под всем остальным
        for p in self.pends:
            n = len(p.trail) or 1
            for i, (tx, ty) in enumerate(p.trail):
                b = 0.10 + 0.50 * (i + 1) / n     # свежие точки ярче старых
                put(tx, ty, '.', tuple(int(c * b) for c in p.color), False)

        # затем стержни и шарики
        for p in self.pends:
            x1, y1, x2, y2 = self._coords(p)
            dim = tuple(int(c * 0.5) for c in p.color)
            self._rod(self.px, self.py, x1, y1, dim, put)
            self._rod(x1, y1, x2, y2, dim, put)
            put(x1, y1, 'o', p.color, False)      # средний шарик
            put(x2, y2, '@', p.color, True)       # нижний — ярче всех

        # сборка кадра
        out = ["\033[H"]
        for y in range(h):
            row = []
            for x in range(w):
                if grid[y][x] == ' ':
                    row.append(' ')
                else:
                    c = cols[y][x]
                    if bold[y][x]:
                        row.append(f"\033[1;38;2;{c[0]};{c[1]};{c[2]}m{grid[y][x]}")
                    else:
                        row.append(f"\033[38;2;{c[0]};{c[1]};{c[2]}m{grid[y][x]}")
            row.append('\033[0m\n')
            out.append(''.join(row))
        return ''.join(out)


def main():
    # cbreak-режим; если stdin — не терминал, просто работаем без него
    fd = None
    old = None
    if os.name != 'nt':
        try:
            import termios, tty
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            old = None
            fd = None
    sys.stdout.write("\033[?25l\033[2J")
    scene = None
    last_size = None
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w = max(2, sz.columns)
                h = max(2, sz.lines - 1)
            except OSError:
                w, h = 80, 24
            if (w, h) != last_size or scene is None:
                scene = Scene(w, h)   # смена размера — пересоздаём сцену
                last_size = (w, h)
            scene.update()
            sys.stdout.write(scene.draw())
            sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        if old is not None and fd is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
