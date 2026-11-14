#!/usr/bin/env python3
"""Интерференция волн. Ctrl+C — выход."""

import os, sys, time, math

# шкала яркости: от штиля до гребня волны
CHARS = " .·:+*#@"


class Waves:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.t = 0.0
        # источники: базовая позиция (в долях поля), фазы дрейфа, волновое число
        self.sources = []
        n = 4
        for i in range(n):
            self.sources.append({
                'fx': 0.2 + 0.6 * i / (n - 1),   # равномерно по ширине
                'fy': 0.4 if i % 2 == 0 else 0.6,
                'phx': i * 1.9,                  # фазы медленного дрейфа
                'phy': i * 2.7,
                'phw': i * 1.3,                  # начальная фаза волны
                'k': 0.75 + 0.15 * (i % 3),      # своё волновое число
            })

    def update(self):
        self.t += 0.20

    def draw(self):
        w, h = self.w, self.h
        t = self.t
        sqrt = math.sqrt
        sin = math.sin
        # текущие позиции источников: базовая точка + медленный дрейф
        pos = []
        for s in self.sources:
            x = (s['fx'] + 0.07 * sin(t * 0.21 + s['phx'])) * w
            y = (s['fy'] + 0.12 * sin(t * 0.17 + s['phy'])) * h
            pos.append((x, y, s['k'], s['phw'] + t * 1.6))
        nsrc = len(pos)
        grid = [[' '] * w for _ in range(h)]
        cols = [[None] * w for _ in range(h)]
        for row in range(h):
            grow = grid[row]
            crow = cols[row]
            # вертикальную дистанцию считаем один раз на строку;
            # умножаем на 2 — символы выше, чем шире (поправка на аспект)
            dy2 = [((row - sy) * 2.0) ** 2 for (_, sy, _, _) in pos]
            for col in range(w):
                v = 0.0
                for i in range(nsrc):
                    sx, _, k, ph = pos[i]
                    dx = col - sx
                    r = sqrt(dx * dx + dy2[i])
                    # волна с затуханием по расстоянию от источника
                    v += sin(r * k - ph) / (1.0 + 0.085 * r)
                # высота поверхности 0..1 (с запасом на наложение волн)
                b = (v / nsrc + 1.0) * 0.5
                if b < 0.0:
                    b = 0.0
                elif b > 1.0:
                    b = 1.0
                idx = int(b * 7.0 + 0.5)
                grow[col] = CHARS[idx]
                # сине-циановая палитра: тёмная синева -> яркий циан
                crow[col] = (int(10 + 90 * b), int(30 + 210 * b), int(80 + 175 * b))
        # метки источников поверх воды
        for (sx, sy, _, _) in pos:
            xi, yi = int(sx), int(sy)
            if 0 <= xi < w and 0 <= yi < h:
                grid[yi][xi] = 'O'
                cols[yi][xi] = (225, 250, 255)
        # сборка кадра
        out = ["\033[H"]
        for y in range(h):
            grow = grid[y]
            crow = cols[y]
            row = []
            for x in range(w):
                if grow[x] == ' ':
                    row.append(' ')
                else:
                    c = crow[x]
                    row.append(f"\033[38;2;{c[0]};{c[1]};{c[2]}m{grow[x]}")
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
                scene = Waves(w, h)   # смена размера — пересоздаём сцену
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
