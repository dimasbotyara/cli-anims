#!/usr/bin/env python3
"""Горящий корабль — фрактал с медленным зумом. Ctrl+C — выход."""

import os, sys, time, math, random

RST   = "\033[0m"
C_DIM = "\033[38;2;112;120;132m"    # подпись под кадром
LOG2  = math.log(2.0)

# огненная палитра: чёрный -> тёмно-красный -> оранжевый -> жёлтый -> белый
STOPS = [
    (0.00, (0, 0, 0)),
    (0.18, (66, 10, 8)),
    (0.42, (186, 34, 8)),
    (0.62, (255, 105, 10)),
    (0.82, (255, 200, 60)),
    (1.00, (255, 250, 224)),
]
PAL_N = 240                          # размер таблицы цветов


def build_palette():
    """Таблица готовых ANSI-строк: цвет + символ нужной «жаркости»."""
    ramp = " .·:+*x#%@"              # чем горячее точка, тем плотнее символ
    pal = []
    for i in range(PAL_N):
        t = i / (PAL_N - 1)
        for k in range(len(STOPS) - 1):
            t0, c0 = STOPS[k]
            t1, c1 = STOPS[k + 1]
            if t <= t1 or k == len(STOPS) - 2:
                f = 0.0 if t1 <= t0 else min(1.0, (t - t0) / (t1 - t0))
                r = int(c0[0] + (c1[0] - c0[0]) * f)
                g = int(c0[1] + (c1[1] - c0[1]) * f)
                b = int(c0[2] + (c1[2] - c0[2]) * f)
                break
        ch = ramp[min(len(ramp) - 1, int(t * len(ramp)))]
        pal.append("\033[38;2;%d;%d;%dm%s" % (r, g, b, ch))
    return pal


class Ship:
    """Сцена: медленный зум в область корабля около c = (-1.75, -0.03)."""

    HS0 = 0.34                       # стартовая полуширина окна
    HS_MIN = 0.012                   # предел зума, потом цикл начинается заново

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.maxit = 56              # максимальная итерация
        self.pal = build_palette()
        self.reset()

    def reset(self):
        # центр слегка «плавает», чтобы каждый цикл чуть отличался
        self.cx = -1.75 + random.uniform(-0.003, 0.003)
        self.cy = -0.03 + random.uniform(-0.003, 0.003)
        self.hs = self.HS0

    def update(self):
        self.hs *= 0.988             # скорость зума за кадр (в лог-масштабе равномерно)
        if self.hs < self.HS_MIN:
            self.reset()

    def draw(self):
        w, h = self.w, self.h
        fh = h - 1                   # последняя строка кадра — подпись
        hs = self.hs
        # символы вытянуты по вертикали (~1:2), поэтому окно сжато по оси y
        vs = hs * 2.0 * fh / w
        step = 2.0 * hs / w
        crs = [self.cx + (col - w / 2 + 0.5) * step for col in range(w)]
        maxit, pal, log2, _abs = self.maxit, self.pal, LOG2, abs
        out = ["\033[H"]
        for row in range(fh):
            ci = self.cy + (fh / 2 - row - 0.5) * (2.0 * vs / fh)
            line = []
            append = line.append
            for cr in crs:
                zx = zy = 0.0
                i = 0
                # z = (|Re z| + i·|Im z|)^2 + c
                while zx * zx + zy * zy <= 4.0 and i < maxit:
                    zx, zy = zx * zx - zy * zy + cr, 2.0 * _abs(zx * zy) + ci
                    i += 1
                if i >= maxit:
                    append(" ")      # внутренность корабля — чёрная
                else:
                    # сглаженное число итераций -> индекс в палитре
                    mag = zx * zx + zy * zy
                    t = (i + 1.0 - math.log(0.5 * math.log(mag)) / log2) / maxit
                    if t < 0.0:
                        t = 0.0
                    elif t > 1.0:
                        t = 1.0
                    append(pal[int(t * (PAL_N - 1))])
            out.append("".join(line) + "\033[0m\n")
        # подпись — тоже часть кадра
        out.append("%sгорящий корабль   зум ×%.0f   c ≈ (%.4f; %+.4f)i   "
                   "%d итераций%s\033[K\n"
                   % (C_DIM, self.HS0 / hs, self.cx, self.cy, maxit, RST))
        return "".join(out)


def main():
    sys.stdout.write("\033[?25l\033[2J")   # курсор спрятать, экран чистый
    ship = None
    last_size = None
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = max(2, sz.columns), max(2, sz.lines - 1)
            except OSError:
                w, h = 80, 24
            if ship is None or (w, h) != last_size:
                ship = Ship(w, h)          # resize — сцена пересоздаётся
                last_size = (w, h)
                sys.stdout.write("\033[2J")
            ship.update()
            sys.stdout.write(ship.draw())
            sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
