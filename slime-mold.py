#!/usr/bin/env python3
"""Физарум: колония слизевика. Ctrl+C — выход."""

import os, sys, time, math, random

N_AGENTS = 350     # число агентов
SENSOR_DIST = 2.0  # дальность сенсоров
SENSOR_ANG = 0.46  # угол между центральным и боковыми сенсорами, рад
TURN = 0.45        # скорость поворота к следу
DEPOSIT = 5.0      # сколько следа агент откладывает за шаг
CHARS = " .·:+*#@"


class Slime:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.frame = 0
        self.trail = [[0.0] * w for _ in range(h)]
        # агенты стартуют кольцом в центре со случайными углами
        cx, cy = w / 2.0, h / 2.0
        self.agents = []
        for _ in range(min(N_AGENTS, max(10, (w - 2) * (h - 2) // 2))):
            ang = random.random() * math.tau
            r = random.random() * 2.5
            self.agents.append([cx + math.cos(ang) * r,
                                cy + math.sin(ang) * r * 0.5, ang])
        self.pal = self._palette()

    def _palette(self):
        # холодная палитра (глубокий синий -> голубой) -> яркая тёплая у максимумов
        pal = []
        for j in range(64):
            t = j / 63.0
            if t < 0.55:
                u = t / 0.55
                r, g, b = 15 + 45 * u, 55 + 165 * u, 130 + 125 * u
            else:
                u = (t - 0.55) / 0.45
                r, g, b = 60 + 195 * u, 220 - 40 * u, 255 - 215 * u
            pal.append("\033[38;2;%d;%d;%dm" % (int(r), int(g), int(b)))
        return pal

    def sense(self, x, y, ang):
        # проба следа перед агентом; по вертикали шаг половинный (аспект 1:2)
        sx = x + math.cos(ang) * SENSOR_DIST
        sy = y + math.sin(ang) * SENSOR_DIST * 0.5
        return self.trail[int(sy) % self.h][int(sx) % self.w]

    def step(self):
        w, h = self.w, self.h
        cos, sin = math.cos, math.sin
        # сенсоры: вперёд, влево+угол, вправо-угол -> поворот к сильнейшему
        for a in self.agents:
            x, y, ang = a
            f = self.sense(x, y, ang)
            l = self.sense(x, y, ang + SENSOR_ANG)
            r = self.sense(x, y, ang - SENSOR_ANG)
            if l > f and l > r:
                ang += TURN
            elif r > f and r > l:
                ang -= TURN
            else:
                ang += random.uniform(-0.1, 0.1)   # лёгкий шум рысканья
            x += cos(ang)
            y += sin(ang) * 0.5
            # отложение следа в текущую клетку (с потолком насыщения)
            ix, iy = int(x) % w, int(y) % h
            v = self.trail[iy][ix] + DEPOSIT
            self.trail[iy][ix] = v if v < 50.0 else 50.0
            a[0], a[1], a[2] = x % w, y % h, ang
        # след затухает
        self.trail = [[v * 0.94 for v in row] for row in self.trail]
        # раз в 2 кадра — дешёвое диффузное усреднение по строкам
        self.frame += 1
        if self.frame % 2 == 0:
            wd = self.w
            for row in self.trail:
                left = row[-1]
                for i in range(wd):
                    cur = row[i]
                    right = row[i + 1] if i + 1 < wd else row[0]
                    row[i] = (left + 2.0 * cur + right) * 0.25
                    left = cur

    def draw(self):
        w, h = self.w, self.h
        # нормировка на текущий максимум следа
        vmax = 4.0
        for row in self.trail:
            m = max(row)
            if m > vmax:
                vmax = m
        inv = 1.0 / vmax
        pal, chars = self.pal, CHARS
        grid = [[' '] * w for _ in range(h)]
        colr = [[None] * w for _ in range(h)]
        for y in range(h):
            src, gout, cout = self.trail[y], grid[y], colr[y]
            for x in range(w):
                v = src[x]
                if v >= 0.05:
                    t = v * inv
                    gout[x] = chars[min(7, int(t * 8.0))]
                    cout[x] = pal[min(63, int(t * 64.0))]
        # подпись в левом нижнем углу
        dim = "\033[38;2;105;105;115m"
        for i, ch in enumerate("физарум · %d агентов" % len(self.agents)):
            if i < w:
                grid[h - 1][i] = ch
                colr[h - 1][i] = dim
        # кадр ровно по высоте терминала, без \n на последней строке
        out = ["\033[H"]
        for y in range(h):
            row = []
            gout, cout = grid[y], colr[y]
            for x in range(w):
                c = cout[x]
                row.append(' ' if c is None else c + gout[x])
            row.append("\033[0m\033[K")
            out.append("".join(row))
            if y < h - 1:
                out.append("\n")
        return "".join(out)


def main():
    last = time.monotonic()
    size = None
    sl = None
    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            now = time.monotonic()
            dt = min(0.1, now - last)
            last = now
            try:
                sz = os.get_terminal_size()
                w, h = max(4, sz.columns), max(3, sz.lines)
            except OSError:
                w, h = 80, 24
            if (w, h) != size or sl is None:
                # пересоздаём колонию под новый размер
                sl = Slime(w, h)
                size = (w, h)
                sys.stdout.write("\033[2J")
            sl.step()
            sys.stdout.write(sl.draw())
            sys.stdout.flush()
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
