#!/usr/bin/env python3
"""Стая птиц (boids): separation, alignment, cohesion. Space — пауза, Q — выход."""

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


def hsv_to_rgb(h, s, v):
    h = (h % 1.0) * 6.0
    i = int(h)
    f = h - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return int(r * 255), int(g * 255), int(b * 255)


TRAIL_RAMP = ' .·:-=+*#%@'
TRAIL_COLORS = [
    f"\033[38;2;{int(18 + 0 * k)};{int(38 + 20 * k)};{int(75 + 18 * k)}m"
    for k in range(11)
]
HEAD_COLORS = []
for _i in range(64):
    _h = 0.46 + 0.42 * _i / 63
    _r, _g, _b = hsv_to_rgb(_h, 0.85, 1.0)
    HEAD_COLORS.append(f"\033[1;38;2;{_r};{_g};{_b}m")


class Boid:
    __slots__ = ('x', 'y', 'vx', 'vy')

    def __init__(self, w, h):
        self.x = w / 2 + random.uniform(-6, 6)
        self.y = h / 2 + random.uniform(-4, 4)
        a = random.uniform(0, math.tau)
        s = random.uniform(0.35, 0.8)
        self.vx = math.cos(a) * s
        self.vy = math.sin(a) * s


class Flock:
    def __init__(self, w, h):
        self.w, self.h = w, h
        n = max(25, min(160, w * h // 26))
        self.boids = [Boid(w, h) for _ in range(n)]
        self.alpha = [0.0] * (w * h)

    def update(self):
        w, h = self.w, self.h
        near2 = 11.0 * 11.0
        sep_r = 3.4
        boids = self.boids

        for b in boids:
            sep_x = sep_y = 0.0
            ali_x = ali_y = 0.0
            coh_x = coh_y = 0.0
            cnt = 0
            for o in boids:
                if o is b:
                    continue
                dx = o.x - b.x
                dy = (o.y - b.y) * 2.0
                d2 = dx * dx + dy * dy
                if d2 < 1e-5 or d2 > near2:
                    continue
                d = math.sqrt(d2)
                ali_x += o.vx
                ali_y += o.vy
                coh_x += o.x
                coh_y += o.y
                cnt += 1
                if d < sep_r:
                    k = (sep_r - d) / sep_r
                    sep_x -= dx / d * k
                    sep_y -= dy / d * k

            ax = sep_x * 0.050
            ay = sep_y * 0.025
            ax += (w * 0.5 - b.x) * 0.0012
            ay += (h * 0.5 - b.y) * 0.0012
            dxc = b.x - w * 0.5
            dyc = (b.y - h * 0.5) * 2.0
            dc = math.hypot(dxc, dyc) + 1e-6
            ax += -dyc / dc * 0.004
            ay += dxc / dc * 0.002
            if cnt:
                ax += (ali_x / cnt - b.vx) * 0.045
                ay += (ali_y / cnt - b.vy) * 0.045
                dx = coh_x / cnt - b.x
                dy = (coh_y / cnt - b.y) * 2.0
                d = math.hypot(dx, dy)
                if d > 1e-3:
                    ax += dx / d * 0.014
                    ay += dy / d * 0.007

            m = 5.0
            if b.x < m:
                ax += (m - b.x) * 0.020
            elif b.x > w - m:
                ax -= (b.x - (w - m)) * 0.020
            if b.y < m * 0.6:
                ay += (m * 0.6 - b.y) * 0.015
            elif b.y > h - m * 0.6:
                ay -= (b.y - (h - m * 0.6)) * 0.015

            b.vx += ax
            b.vy += ay

            sp = math.hypot(b.vx, b.vy)
            if sp > 0.95:
                b.vx = b.vx / sp * 0.95
                b.vy = b.vy / sp * 0.95
            elif sp < 0.32 and sp > 1e-6:
                b.vx = b.vx / sp * 0.32
                b.vy = b.vy / sp * 0.32

            b.x += b.vx
            b.y += b.vy

            if b.x < 0.5:
                b.x = 0.5
                b.vx = abs(b.vx)
            elif b.x > w - 1.5:
                b.x = w - 1.5
                b.vx = -abs(b.vx)
            if b.y < 0.5:
                b.y = 0.5
                b.vy = abs(b.vy)
            elif b.y > h - 1.5:
                b.y = h - 1.5
                b.vy = -abs(b.vy)

        for i in range(len(self.alpha)):
            self.alpha[i] *= 0.86
        for b in boids:
            ix, iy = int(b.x), int(b.y)
            if 0 <= ix < w and 0 <= iy < h:
                self.alpha[iy * w + ix] = 1.0

    def draw(self):
        w, h = self.w, self.h
        chars = [' '] * (w * h)
        cols = [None] * (w * h)

        for i, a in enumerate(self.alpha):
            if a < 0.035:
                continue
            idx = int((a ** 0.7) * 10)
            idx = max(1, min(10, idx))
            chars[i] = TRAIL_RAMP[idx]
            cols[i] = TRAIL_COLORS[idx]

        for b in self.boids:
            ix, iy = int(b.x), int(b.y)
            if not (0 <= ix < w and 0 <= iy < h):
                continue
            vx, vy = b.vx, b.vy
            if abs(vx) > abs(vy) * 1.3:
                ch = '>' if vx > 0 else '<'
            elif abs(vy) > abs(vx) * 1.3:
                ch = 'v' if vy > 0 else '^'
            else:
                ch = '\\' if vx * vy > 0 else '/'
            hue = (math.atan2(vy, vx) / math.tau) % 1.0
            ci = int(hue * 63)
            i = iy * w + ix
            chars[i] = ch
            cols[i] = HEAD_COLORS[ci]

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
    flock = None
    size = None
    paused = False
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            w = max(30, w)
            h = max(10, h)

            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused

            if (w, h) != size:
                flock = Flock(w, h)
                size = (w, h)
                sys.stdout.write('\033[2J')

            if not paused:
                flock.update()

            sys.stdout.write(flock.draw())
            sys.stdout.flush()
            time.sleep(0.035)
    except KeyboardInterrupt:
        pass
    finally:
        if old is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write('\033[0m\033[?25h\n')


if __name__ == '__main__':
    main()
