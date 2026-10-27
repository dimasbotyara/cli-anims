#!/usr/bin/env python3
"""Аквариум: рыбки, пузырьки, водоросли и песок. Space — пауза, Q — выход."""

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


FISH_COLORS = [
    (255, 90, 90), (255, 170, 60), (255, 230, 80),
    (90, 230, 130), (80, 200, 255), (170, 120, 255), (255, 120, 210),
]

# (вправо, влево)
FISH_SHAPES = [
    ('><>', '<><'),
    ('><))>', '<((><'),
    ('><)))>', '<(((><'),
]

WEED_COLORS = [
    (30, 150, 90), (40, 180, 110), (25, 120, 80), (70, 200, 120),
]


class Fish:
    __slots__ = ('shape', 'd', 'x', 'base_y', 'speed', 'phase', 'amp', 'color')

    def __init__(self, w, h):
        self.shape = random.choice(FISH_SHAPES)
        self.d = random.choice((-1, 1))
        self.x = random.uniform(0, w)
        self.base_y = random.uniform(1.5, max(2.0, h - 3.5))
        self.speed = random.uniform(0.12, 0.45)
        self.phase = random.uniform(0, math.tau)
        self.amp = random.uniform(0.3, 1.6)
        self.color = random.choice(FISH_COLORS)

    def update(self, t, w, h):
        self.x += self.speed * self.d
        size = len(self.shape[0])
        if self.d > 0 and self.x > w:
            self.x = -size
            self.base_y = random.uniform(1.5, max(2.0, h - 3.5))
        elif self.d < 0 and self.x < -size:
            self.x = w
            self.base_y = random.uniform(1.5, max(2.0, h - 3.5))

    def y(self, t):
        return self.base_y + math.sin(t * 1.4 + self.phase) * self.amp


class Aquarium:
    def __init__(self, w, h):
        self.w, self.h = w, h
        n_fish = max(5, w * h // 110)
        self.fish = [Fish(w, h) for _ in range(n_fish)]
        self.bubbles = []
        for _ in range(max(10, w * h // 60)):
            self.bubbles.append([
                random.uniform(0, w), random.uniform(0, h),
                random.uniform(0.08, 0.35), random.uniform(0, math.tau),
                random.choice(('·', 'o', 'O', '.')),
            ])
        self.weeds = []
        for _ in range(max(3, w // 14)):
            self.weeds.append([
                random.uniform(0, w),
                random.uniform(2.0, max(3.0, h * 0.45)),
                random.uniform(0, math.tau),
                random.uniform(0.7, 1.5),
                random.choice(WEED_COLORS),
            ])
        self.shells = []
        for _ in range(max(1, w // 30)):
            self.shells.append((random.randint(1, max(1, w - 2)), random.choice(('*', '@', 'o'))))

    def update(self, t):
        for f in self.fish:
            f.update(t, self.w, self.h)
        for b in self.bubbles:
            b[1] -= b[2]
            b[0] += math.sin(t * 2.0 + b[3]) * 0.08
            if b[1] < 1.0 or b[0] < 0 or b[0] >= self.w:
                b[1] = self.h - 2
                b[0] = random.uniform(0, self.w)
                b[2] = random.uniform(0.08, 0.35)

    def draw(self, t):
        w, h = self.w, self.h
        chars = [' '] * (w * h)
        cols = [None] * (w * h)

        def put(x, y, ch, color):
            if 0 <= x < w and 0 <= y < h:
                i = y * w + x
                chars[i] = ch
                cols[i] = color

        # поверхность воды
        for x in range(w):
            wave = math.sin(x * 0.22 + t * 0.9) + 0.4 * math.sin(x * 0.07 - t * 1.6)
            if wave > -0.2:
                put(x, 0, '~', '\033[38;2;70;150;200m')

        # песок и ракушки
        for x in range(w):
            if x % 5 == 0:
                put(x, h - 1, '.', '\033[38;2;120;95;55m')
            else:
                put(x, h - 1, '~', '\033[38;2;180;150;90m')
        for x, ch in self.shells:
            put(x, h - 1, ch, '\033[38;2;230;150;160m')

        # водоросли
        for x0, height, phase, speed, color in self.weeds:
            cs = f"\033[38;2;{color[0]};{color[1]};{color[2]}m"
            for i in range(int(height)):
                y = h - 2 - i
                if y < 1:
                    break
                sway = math.sin(t * speed + phase + i * 0.35) * i * 0.22
                slope = math.cos(t * speed + phase + i * 0.35)
                ch = '(' if slope > 0.25 else (')' if slope < -0.25 else '|')
                put(int(round(x0 + sway)), y, ch, cs)

        # пузырьки
        for x, y, _, phase, ch in self.bubbles:
            b = 150 + int(80 * (0.5 + 0.5 * math.sin(t * 3 + phase)))
            put(int(x), int(y), ch, f"\033[38;2;{b // 2};{b};255m")

        # рыбки
        for f in self.fish:
            shape = f.shape[0] if f.d > 0 else f.shape[1]
            ix = int(round(f.x))
            iy = int(round(f.y(t)))
            c = f"\033[1;38;2;{f.color[0]};{f.color[1]};{f.color[2]}m"
            for k, ch in enumerate(shape):
                put(ix + k, iy, ch, c)

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
    t = 0.0
    paused = False
    aq = None
    size = None
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            w = max(20, w)
            h = max(8, h)

            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused

            if (w, h) != size:
                aq = Aquarium(w, h)
                size = (w, h)
                sys.stdout.write('\033[2J')

            if not paused:
                t += 0.06
                aq.update(t)

            sys.stdout.write(aq.draw(t))
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
