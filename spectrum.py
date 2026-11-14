#!/usr/bin/env python3
"""Аудио-спектроанализатор. Space — пауза, Q — выход."""

import os, sys, time, math, random


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


def hsv(h, v):
    """HSV (s=1) -> RGB: цвет полосы по высоте (зелёный -> жёлтый -> красный)."""
    i = int(h * 6.0) % 6
    f = h * 6.0 - int(h * 6.0)
    q, t = v * (1.0 - f), v * f
    r, g, b = ((v, t, 0), (q, v, 0), (0, v, t),
               (0, q, v), (t, 0, v), (v, 0, q))[i]
    return int(r * 255), int(g * 255), int(b * 255)


TRACKS = [
    "NEON CIRCUIT — Synthwave Dreams",
    "КОММУТАТОР — Шум магистрали 24/7",
    "Lofi Compiler — beats to compile to",
    "ГИПЕРБОРЕЯ — Полярная станция",
    "ACID Process — Buffer Overflow",
]


class Spectrum:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.hb = max(3, h - 2)                 # высота области столбиков
        self.n = max(8, min(50, (w - 2) // 2))  # число полос
        self.level = [0.0] * self.n             # сглаженные высоты
        self.peak = [0.0] * self.n              # peak-hold шапки
        self.kick = 0.0                         # «басовый» пульс
        self.last_kick = 0.0
        self.t = random.random() * 100.0
        self.played = 0.0                       # «время воспроизведения»
        self.track = random.choice(TRACKS)
        self.rowcol = self._row_colors()
        self.paused = False

    def _row_colors(self):
        # цвет строки: низ зелёный -> середина жёлтая -> верх красный
        out = []
        for r in range(self.hb):
            p = (self.hb - 1 - r) / max(1, self.hb - 1)
            r_, g_, b_ = hsv(0.33 * (1.0 - p), 0.95)
            out.append("\033[38;2;%d;%d;%dm" % (r_, g_, b_))
        return out

    def resize(self, w, h):
        # число полос и высота меняются — значения сохраняем, насколько можно
        n = max(8, min(50, (w - 2) // 2))
        hb = max(3, h - 2)
        lvl, pk = self.level[:n], self.peak[:n]
        lvl += [0.0] * (n - len(lvl))
        pk += [0.0] * (n - len(pk))
        self.w, self.h, self.n = w, h, n
        self.level, self.peak = lvl, pk
        if hb != self.hb:
            self.hb = hb
            self.rowcol = self._row_colors()

    def step(self, dt):
        self.t += dt
        self.played += dt
        # «кик»: раз в ~0.5 с даёт всплеск низких (левых) полос
        if self.t - self.last_kick >= 0.5:
            self.last_kick = self.t
            self.kick = 1.0
        self.kick *= math.exp(-dt * 5.0)
        for i in range(self.n):
            x = i / max(1, self.n - 1)
            # высота из суммы синусов разных частот
            v = 0.45 + 0.40 * math.sin(self.t * 1.3 + i * 0.55) \
                        * math.sin(self.t * 0.37 + i * 0.13)
            v += 0.25 * math.sin(self.t * 4.1 + i * 1.7)
            v += 0.30 * (1.0 - x) * self.kick            # кик качает бас
            v += 0.12 * (x + 0.2) * math.sin(self.t * 9.0 + i * 2.3)
            v = max(0.02, min(1.15, v))
            # быстрый подъём, медленное падение (затухание)
            if v > self.level[i]:
                self.level[i] = v
            else:
                self.level[i] += (v - self.level[i]) * min(1.0, dt * 3.0)
            # шапка держится и медленно опускается
            self.peak[i] = max(self.level[i], self.peak[i] - dt * 0.28)

    def draw(self):
        w, h, n, hb = self.w, self.h, self.n, self.hb
        grid = [[' '] * w for _ in range(h)]
        colr = [[None] * w for _ in range(h)]

        # бегущая строка с «названием трека»
        dim = "\033[38;2;150;150;175m"
        text = "  ♪ %s  ♫ 84 BPM  " % self.track
        off = int(self.played * 6.0) % len(text)
        marq = (text * 3)[off:off + w]
        for i, ch in enumerate(marq[:w]):
            grid[0][i] = ch
            colr[0][i] = dim

        # столбики: полоса i занимает колонку x = 1 + i*2
        white = "\033[38;2;255;255;255m"
        for i in range(n):
            x = 1 + i * 2
            if x >= w:
                break
            bh = min(hb, int(self.level[i] * hb + 0.5))
            for k in range(bh):
                y = hb - k                       # k=0 — низ столбика
                grid[y][x] = '█'
                colr[y][x] = self.rowcol[y - 1]
            # peak-hold шапка (белая)
            pr = hb - min(hb, int(self.peak[i] * hb + 0.5))
            if 1 <= pr <= hb:
                grid[pr][x] = '▔'
                colr[pr][x] = white

        # статус: фиктивное время трека и пауза
        mm, ss = divmod(int(self.played), 60)
        dim2 = "\033[38;2;120;120;135m"
        hot = "\033[1;38;2;255;220;90m"
        stat = [(ch, dim2) for ch in "♪ %02d:%02d / 04:45" % (mm, ss)]
        if self.paused:
            stat += [(ch, hot) for ch in "   ‖ пауза"]
        for i, (ch, c) in enumerate(stat):
            if i < w:
                grid[h - 1][i] = ch
                colr[h - 1][i] = c

        # кадр ровно по высоте терминала, без \n на последней строке
        out = ["\033[H"]
        for y in range(h):
            row = []
            for x in range(w):
                c = colr[y][x]
                row.append(' ' if c is None else c + grid[y][x])
            row.append("\033[0m\033[K")
            out.append("".join(row))
            if y < h - 1:
                out.append("\n")
        return "".join(out)


def main():
    fd = sys.stdin.fileno()
    old = None
    if os.name != 'nt':
        import termios, tty
        try:
            old = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except termios.error:
            old = None
    sys.stdout.write("\033[?25l\033[2J")
    sp = None
    last_size = None
    last = time.monotonic()
    try:
        while True:
            now = time.monotonic()
            dt = min(0.1, now - last)
            last = now
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines
            except OSError:
                w, h = 80, 24
            if sp is None or (w, h) != last_size:
                if sp is None:
                    sp = Spectrum(w, h)
                else:
                    sp.resize(w, h)
                last_size = (w, h)
                sys.stdout.write("\033[2J")
            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                sp.paused = not sp.paused
            if not sp.paused:
                sp.step(dt)
            sys.stdout.write(sp.draw())
            sys.stdout.flush()
            time.sleep(0.035)
    except KeyboardInterrupt:
        pass
    finally:
        if old is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
