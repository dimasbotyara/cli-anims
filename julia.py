#!/usr/bin/env python3
"""Множество Жюлиа. Ctrl+C — выход."""

import os, sys, time, math

# параметры анимации
C_RADIUS = 0.7885    # радиус окружности, по которой гуляет параметр c
THETA_STEP = 0.004   # прирост угла за кадр
Y_SPAN = 2.4         # вертикальный охват комплексной плоскости
MAX_ITER = 50        # предел итераций побега
ESCAPE_R2 = 16.0     # квадрат радиуса побега (|z| > 4): после побега log|z| > 1,
                     # поэтому сглаженная формула n + 1 - log2(log|z|) всегда корректна

INTERIOR = "\033[38;2;10;12;28m█"   # почти чёрный цвет точек внутри множества


def smooth_color(mu):
    # синусоидальная RGB-палитра: три фазы, сдвинутые на 120 градусов,
    # дают плавные переливы без ступенек между соседними итерациями
    t = mu * 0.16
    r = int(115 + 110 * math.sin(t))
    g = int(115 + 110 * math.sin(t + 2.0944))
    b = int(115 + 110 * math.sin(t + 4.1888))
    return f"\033[38;2;{r};{g};{b}m█"


class Julia:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.theta = 0.0   # текущий угол параметра c на окружности

    def update(self):
        # c(t) = 0.7885 * e^(i*theta) медленно обходит окружность вокруг кардиоиды
        self.theta = (self.theta + THETA_STEP) % math.tau

    def draw(self):
        w, h = self.w, self.h
        theta = self.theta
        cr = C_RADIUS * math.cos(theta)
        ci = C_RADIUS * math.sin(theta)
        max_iter = MAX_ITER
        r2 = ESCAPE_R2
        sqrt = math.sqrt
        log = math.log
        log2 = math.log2
        # поправка на аспект: символ ~2 раза выше своей ширины,
        # поэтому шаг по вертикали вдвое больше шага по горизонтали
        ystep = Y_SPAN / h
        xstep = ystep / 2.0
        x0 = -0.5 * xstep * w
        y0 = -0.5 * Y_SPAN
        xs = [x0 + i * xstep for i in range(w)]   # x-координаты колонок
        out = ["\033[H"]
        for row in range(h):
            zi = y0 + row * ystep
            line = []
            append = line.append
            for zr in xs:
                zx, zy = zr, zi
                n = 0
                # побег: |z|^2 > 4
                while zx * zx + zy * zy < r2 and n < max_iter:
                    # z = z^2 + c (обе координаты считаются из старых значений)
                    zy, zx = 2.0 * zx * zy + ci, zx * zx - zy * zy + cr
                    n += 1
                if n >= max_iter:
                    append(INTERIOR)
                    continue
                az = sqrt(zx * zx + zy * zy)
                # сглаженная итерация: n + 1 - log2(log|z|)
                mu = n + 1.0 - log2(log(az)) if az > 1.0 else float(n)
                append(smooth_color(mu))
            line.append('\033[0m\n')
            out.append(''.join(line))
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
                scene = Julia(w, h)   # смена размера — пересоздаём сцену
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
