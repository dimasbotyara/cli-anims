#!/usr/bin/env python3
"""Ночной город. Ctrl+C — выход."""

import math
import os
import random
import sys
import time


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
        self.t = 0
        self.gy = h - 1   # ряд «земли»/шоссе

        # --- процедурный силуэт: 10-15 зданий, пока влезают по ширине ---
        self.buildings = []   # [x, ширина, верх, цвет, антенна|None]
        self.windows = []     # [x, y, горит?, яркость, сдвиг тепла, тусклый цвет]
        x = random.randint(0, 1)
        while x < w - 3 and len(self.buildings) < 15:
            bw = random.randint(4, max(5, min(9, w // 8)))
            bw = min(bw, w - 1 - x)
            if bw < 3:
                break
            bh = random.randint(max(2, h // 5), max(3, int(h * 0.55)))
            top = max(1, self.gy - bh)
            # корпус: тёмно-синий или тёмно-серый
            if random.random() < 0.6:
                col = (random.randint(22, 34), random.randint(28, 40), random.randint(46, 64))
            else:
                g = random.randint(40, 55)
                col = (g, g, g + 3)
            bld = [x, bw, top, col, None]
            # сетка окон с шагом 2, часть сразу горит тёплым жёлтым
            dim = f"\033[38;2;{int(col[0] * 1.6)};{int(col[1] * 1.6)};{int(col[2] * 1.6)}m"
            for wy in range(top + 1, self.gy - 1, 2):
                for wx in range(x + 1, x + bw - 1, 2):
                    if random.random() < 0.85:
                        self.windows.append([wx, wy, random.random() < 0.45,
                                             random.uniform(0.5, 1.0),
                                             random.uniform(-14, 14), dim])
            # антенна на части высоких крыш
            if self.gy - top >= h // 3 and random.random() < 0.65:
                bld[4] = (x + bw // 2, top - random.randint(1, 2), random.random() * 2.0)
            self.buildings.append(bld)
            x += bw + random.choice((0, 0, 1))

        # --- луна: положение и радиус под размер терминала ---
        self.moon_x = w - max(5, w // 7)
        self.moon_y = max(1, min(3, h // 4))
        self.moon_r = 2 if h >= 12 else 1

        # --- звёзды в верхней части неба ---
        self.stars = []
        sky = max(1, int(h * 0.6))
        for _ in range(max(6, w * h // 70)):
            self.stars.append((random.randrange(w), random.randrange(sky),
                               random.random() * math.tau,
                               random.uniform(0.06, 0.22),
                               random.uniform(0.25, 0.85)))

        self.meteor = None   # падающая звезда
        self.plane = None    # самолёт

    def update(self):
        self.t += 1
        # окна медленно и случайно включаются/выключаются
        for win in self.windows:
            if random.random() < 0.0009:
                win[2] = not win[2]
        # падающая звезда — изредка
        if self.meteor is None:
            if random.random() < 0.006:
                self.meteor = [random.uniform(4, self.w - 4),
                               random.uniform(0, max(1.0, self.h / 3)),
                               random.choice((-1, 1)) * random.uniform(0.7, 1.4),
                               random.uniform(0.3, 0.55),
                               random.randint(12, 20)]
        else:
            m = self.meteor
            m[0] += m[2]
            m[1] += m[3]
            m[4] -= 1
            if m[4] <= 0 or m[1] >= self.gy or not -2 <= m[0] <= self.w + 2:
                self.meteor = None
        # самолёт — ещё реже
        if self.plane is None:
            if random.random() < 0.004:
                d = random.choice((-1, 1))
                self.plane = [-8.0 if d > 0 else self.w + 8.0,
                              random.uniform(1, max(2.0, self.h / 3)),
                              d * 0.22]
        else:
            self.plane[0] += self.plane[2]
            if not -10 <= self.plane[0] <= self.w + 10:
                self.plane = None

    def draw(self):
        w, h, t = self.w, self.h, self.t
        gy = self.gy
        chars = [' '] * (w * h)
        cols = [None] * (w * h)

        def put(x, y, ch, col):
            if 0 <= x < w and 0 <= y < h:
                i = y * w + x
                chars[i] = ch
                cols[i] = col

        # 1) мерцающие звёзды (дальше рисуются поверх)
        for x, y, ph, spd, base in self.stars:
            v = base * (0.55 + 0.45 * math.sin(t * spd + ph))
            b = int(v * 255)
            if b > 14:
                put(x, y, '·', f"\033[38;2;{b};{int(b * 0.97)};{min(255, int(b * 1.1))}m")

        # 2) луна с фазой — фаза медленно ползёт по кругу
        R = self.moon_r
        ph = (t * 0.0006) % 1.0
        k = math.cos(math.tau * ph)
        waxing = ph < 0.5
        mx, my = self.moon_x, self.moon_y
        for dy in range(-R - 1, R + 2):
            for dx in range(-R - 1, R + 2):
                d2 = dx * dx + dy * dy
                if R * R + 1 < d2 <= R * R + 4:      # мягкий ореол
                    put(mx + dx, my + dy, '·', "\033[38;2;96;98;118m")
                elif d2 <= R * R + 1:
                    lit = (dx > k) if waxing else (dx < -k)
                    if lit:
                        put(mx + dx, my + dy, '█', "\033[38;2;236;236;216m")
                    else:
                        put(mx + dx, my + dy, '░', "\033[38;2;70;72;86m")

        # 3) падающая звезда с гаснущим следом
        if self.meteor:
            m = self.meteor
            put(int(round(m[0])), int(round(m[1])), '+', "\033[1;38;2;255;255;240m")
            for kk in range(1, 5):
                v = int(190 * (1 - kk / 5))
                put(int(round(m[0] - m[2] * kk * 1.7)),
                    int(round(m[1] - m[3] * kk * 1.7)), '·',
                    f"\033[38;2;{v};{v};{min(255, v + 40)}m")

        # 4) самолёт с проблесковым огоньком
        if self.plane:
            p = self.plane
            px, py = int(round(p[0])), int(round(p[1]))
            put(px, py, '>' if p[2] > 0 else '<', "\033[38;2;128;133;148m")
            lx = px - (1 if p[2] > 0 else -1)
            if (t // 5) % 2 == 0:
                put(lx, py, '·', "\033[1;38;2;255;255;255m")
            else:
                put(lx, py, '·', "\033[1;38;2;255;72;60m")

        # 5) шоссе внизу
        road = "\033[38;2;64;64;70m"
        for x in range(w):
            put(x, gy, '-' if x % 5 == 2 else '·', road)

        # 6) корпуса зданий с крышами
        for bx, bw, top, col, ant in self.buildings:
            body = f"\033[38;2;{col[0]};{col[1]};{col[2]}m"
            roofc = (f"\033[38;2;{min(255, int(col[0] * 1.7))};"
                     f"{min(255, int(col[1] * 1.7))};{min(255, int(col[2] * 1.7))}m")
            for y in range(top, gy):
                if y == top:
                    ch, cc = '▓', roofc
                else:
                    ch, cc = '▒', body
                base = y * w
                for x in range(bx, bx + bw):
                    chars[base + x] = ch
                    cols[base + x] = cc

        # 7) окна поверх корпусов
        for wx, wy, on, br, shift, dim in self.windows:
            if on:
                r = min(255, int(255 * br))
                g = min(255, int((205 + shift) * br))
                b = min(255, int((120 + shift) * br))
                put(wx, wy, '█', f"\033[38;2;{r};{g};{b}m")
            else:
                put(wx, wy, '·', dim)

        # 8) антенны с мигающими красными огоньками
        for bx, bw, top, col, ant in self.buildings:
            if ant is None:
                continue
            ax, ay, phase = ant
            mast = "\033[38;2;108;112;122m"
            for y in range(max(0, ay), top):
                put(ax, y, '│', mast)
            if (t // 9 + int(phase)) % 2 == 0:
                put(ax, max(0, ay), '·', "\033[1;38;2;255;64;52m")
            else:
                put(ax, max(0, ay), '·', "\033[38;2;118;30;24m")

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
