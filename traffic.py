#!/usr/bin/env python3
"""Перекрёсток со светофором. Space — пауза, Q — выход."""

import os, sys, time, random

CAR_COLORS = ((230, 85, 85), (90, 160, 250), (250, 205, 90),
              (120, 225, 130), (215, 125, 245), (245, 245, 245))
SIG_COLOR = {'G': (90, 255, 130), 'Y': (255, 220, 70), 'R': (255, 85, 85)}


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


def signals(t):
    """Фаза светофора по часам t: (север-юг, запад-восток)."""
    p = t % 11.0
    if p < 4.0:
        return 'G', 'R'
    if p < 5.0:
        return 'Y', 'R'
    if p < 5.5:
        return 'R', 'R'
    if p < 9.5:
        return 'R', 'G'
    if p < 10.5:
        return 'R', 'Y'
    return 'R', 'R'


class Car:
    __slots__ = ('d', 'f', 'v', 'vmax', 'color', 'brake')

    def __init__(self, d):
        self.d = d
        self.f = -1.0                        # передний край, по ходу движения
        self.vmax = random.uniform(9.0, 15.0)
        self.v = self.vmax * 0.6
        self.color = random.choice(CAR_COLORS)
        self.brake = False


class Traffic:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.ry2 = max(2, h // 2)            # нижняя полоса: З->В
        self.ry1 = self.ry2 - 1              # верхняя полоса: В->З
        self.vx2 = w // 2                    # правая колонка: С->Ю
        self.vx1 = self.vx2 - 1              # левая колонка: Ю->С
        self.cars = []
        self.passed = 0
        self.paused = False
        self.t = 0.0                         # часы светофора

    def line_f(self, d):
        """Стоп-линия: предел f перед перекрёстком на красный."""
        if d == 0:
            return self.vx1 - 1.0            # З->В: встать левее перекрёстка
        if d == 1:
            return self.w - 2.0 - self.vx2   # В->З
        if d == 2:
            return self.ry1 - 1.0            # С->Ю
        return self.h - 3.0 - self.ry2       # Ю->С

    def step(self, dt):
        self.t += dt
        ns, ew = signals(self.t)
        w, h = self.w, self.h
        # спавн по четырём направлениям, если у края свободно
        for d in range(4):
            if random.random() < dt * 0.5:
                if not any(c.d == d and c.f < 6.0 for c in self.cars):
                    self.cars.append(Car(d))
        # движение: соблюдаем дистанцию и стоп-линию на запрещающий сигнал
        for d in range(4):
            lane = sorted((c for c in self.cars if c.d == d),
                          key=lambda c: c.f)
            line = self.line_f(d)
            green = (ns if d >= 2 else ew) == 'G'
            for i, c in enumerate(lane):
                ahead = lane[i + 1] if i + 1 < len(lane) else None
                # дистанция до хвоста впереди идущей машины
                dc = (ahead.f - 2.0) - c.f if ahead else 1e9
                dline = line - c.f
                if not green and dline > 0.0:    # ещё не пересёк линию
                    dc = min(dc, dline)
                if dc < 1.6:
                    nv = 0.0                     # стоит
                elif dc < 3.2:
                    nv = min(c.vmax * 0.4, c.v)  # подтормаживает
                else:
                    nv = min(c.vmax, c.v + 22.0 * dt)
                c.brake = nv == 0.0 or nv < c.v - 0.01
                c.v = nv
                c.f += nv * dt
        # уехавшие за край — в счётчик проехавших
        keep = []
        for c in self.cars:
            lim = self.w + 2.0 if c.d < 2 else self.h + 1.0
            if c.f > lim:
                self.passed += 1
            else:
                keep.append(c)
        self.cars = keep

    def _light(self, grid, colr, y, x, sig):
        if 0 <= y < self.h - 1 and 0 <= x < self.w:
            r, g, b = SIG_COLOR[sig]
            grid[y][x] = '●'
            colr[y][x] = "\033[38;2;%d;%d;%dm" % (r, g, b)

    def draw(self):
        w, h = self.w, self.h
        grid = [[' '] * w for _ in range(h)]
        colr = [[None] * w for _ in range(h)]
        dark = "\033[38;2;62;62;72m"
        ry1, ry2, vx1, vx2 = self.ry1, self.ry2, self.vx1, self.vx2
        # две дороги крестом, по полосе в каждую сторону
        for x in range(w):
            ch = '┼' if vx1 <= x <= vx2 else '─'
            grid[ry1][x] = grid[ry2][x] = ch
            colr[ry1][x] = colr[ry2][x] = dark
        for y in range(h - 1):
            if y != ry1 and y != ry2:
                grid[y][vx1] = grid[y][vx2] = '│'
                colr[y][vx1] = colr[y][vx2] = dark
        # стоп-огни у перекрёстка (вне полос, чтобы не путались с машинами)
        ns, ew = signals(self.t)
        self._light(grid, colr, ry1 - 1, vx2 + 1, ns)   # поток С->Ю
        self._light(grid, colr, ry2 + 1, vx1 - 1, ns)   # поток Ю->С
        self._light(grid, colr, ry2 + 1, vx1 - 2, ew)   # поток З->В
        self._light(grid, colr, ry1 - 1, vx2 + 2, ew)   # поток В->З
        # машины: две клетки, при торможении — красный хвостовой символ
        red = "\033[1;38;2;255;60;50m"
        for c in self.cars:
            p = int(c.f)
            if c.d == 0:            # З->В: перед справа
                fx, fy, rx, ry_, fch, rch = p, ry2, p - 1, ry2, '▜', '▛'
            elif c.d == 1:          # В->З: перед слева
                fx, fy, rx, ry_, fch, rch = w - 1 - p, ry1, w - p, ry1, '▛', '▜'
            elif c.d == 2:          # С->Ю: перед снизу
                fx, fy, rx, ry_, fch, rch = vx2, p, vx2, p - 1, '▜', '▛'
            else:                   # Ю->С: перед сверху
                fx, fy, rx, ry_, fch, rch = vx1, h - 2 - p, vx1, h - 1 - p, '▜', '▛'
            col = "\033[38;2;%d;%d;%dm" % c.color
            if 0 <= fx < w and 0 <= fy < h - 1:
                grid[fy][fx] = fch
                colr[fy][fx] = col
            if 0 <= rx < w and 0 <= ry_ < h - 1:
                grid[ry_][rx] = '●' if c.brake else rch
                colr[ry_][rx] = red if c.brake else col

        # кадр: сцена + статусная строка последней строкой, без \n в конце
        out = ["\033[H"]
        for y in range(h - 1):
            row = []
            gout, cout = grid[y], colr[y]
            for x in range(w):
                c = cout[x]
                row.append(' ' if c is None else c + gout[x])
            row.append("\033[0m\033[K")
            out.append("".join(row))
            out.append("\n")
        out.append(self._status(w) + "\033[0m\033[K")
        return "".join(out)

    def _status(self, w):
        """Статус: счётчик проехавших, машины на дороге, фаза светофора."""
        ns, ew = signals(self.t)
        dim, white = "\033[38;2;120;120;135m", "\033[38;2;220;220;225m"
        txt = [(dim, "проехало: "), (white, str(self.passed)),
               (dim, "   машин: "), (white, str(len(self.cars))),
               (dim, "   С-Ю "), ("\033[1;38;2;%d;%d;%dm" % SIG_COLOR[ns], ns),
               (dim, "  З-В "), ("\033[1;38;2;%d;%d;%dm" % SIG_COLOR[ew], ew)]
        if self.paused:
            txt.append(("\033[1;38;2;255;220;90m", "   ‖ пауза"))
        out = []
        col = 0
        for c, s in txt:
            for ch in s:
                if col >= w:
                    break
                out.append(c + ch)
                col += 1
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
    tf = None
    last_size = None
    last = time.monotonic()
    paused = False
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
            if tf is None or (w, h) != last_size:
                tf = Traffic(w, h)
                last_size = (w, h)
                sys.stdout.write("\033[2J")
            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused
            tf.paused = paused
            if not paused:
                tf.step(dt)
            sys.stdout.write(tf.draw())
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
