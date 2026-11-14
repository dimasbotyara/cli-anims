#!/usr/bin/env python3
"""Доска Гальтона. Space — пауза, Q — выход."""

import os, sys, random, time, math


def read_key():
    """Неблокирующее чтение клавиши; None — ничего не нажато."""
    if os.name == 'nt':
        import msvcrt
        if not msvcrt.kbhit():
            return None
        return msvcrt.getwch().lower()
    import select
    try:
        fd = sys.stdin.fileno()
    except (ValueError, OSError):
        return None
    if not select.select([fd], [], [], 0)[0]:
        return None
    data = os.read(fd, 32)
    return chr(data[0]).lower() if data else None


# --- ANSI ---
RST    = "\033[0m"
C_PEG  = "\033[38;2;118;118;130m"    # колышки — тускло-серые
C_BALL = "\033[1;38;2;255;232;130m"  # шарики — ярко-жёлтые
C_DIM  = "\033[38;2;112;120;132m"    # подписи в статусе
C_TXT  = "\033[38;2;205;212;222m"    # числа в статусе

# градиент столбиков снизу вверх: тёмно-синий -> голубой -> зелёный -> жёлтый
GRAD_STOPS = [(0.00, (30, 36, 100)), (0.35, (52, 112, 224)),
              (0.65, (62, 204, 162)), (0.85, (172, 232, 84)),
              (1.00, (255, 242, 130))]
GRAD_N = 64


def build_gradient():
    """Таблица цветов столбиков: индекс — доля высоты от 0 до 1."""
    grad = []
    for i in range(GRAD_N):
        t = i / (GRAD_N - 1)
        for k in range(len(GRAD_STOPS) - 1):
            (t0, c0), (t1, c1) = GRAD_STOPS[k], GRAD_STOPS[k + 1]
            if t <= t1 or k == len(GRAD_STOPS) - 2:
                f = 0.0 if t1 <= t0 else min(1.0, (t - t0) / (t1 - t0))
                grad.append("\033[38;2;%d;%d;%dm" % tuple(
                    int(a + (b - a) * f) for a, b in zip(c0, c1)))
                break
    return grad


GRAD = build_gradient()


class Ball:
    """Шарик: отскоки решены заранее, t — позиция в «полурядах»."""
    __slots__ = ('steps', 't')

    def __init__(self, rows):
        self.steps = [random.choice((-1, 1)) for _ in range(rows)]
        self.t = 0.0


class Galton:
    """Доска: треугольник колышков, летящие шарики и столбики-накопители."""

    def __init__(self, w, h, counts=None, total=0):
        self.w, self.h = w, h
        self.c0 = w // 2
        # ряды колышков: ограничены шириной, высотой и здравым смыслом
        self.rows = max(2, min((w - 5) // 2, h - 6, 13))
        self.bins = self.rows + 1
        self.bar_h = max(0, h - self.rows - 3)   # высота области столбиков
        if counts is not None and len(counts) == self.bins:
            self.counts, self.total = list(counts), total  # resize сохранил статистику
        else:                                    # число карманов изменилось
            self.counts, self.total = [0] * self.bins, 0
        self.balls = []
        self.paused = False
        self.spawn_in = 2

    def update(self):
        """Кадр физики: спавн, полшага каждому шарику, приземления."""
        if self.paused:
            return
        self.spawn_in -= 1
        if self.spawn_in <= 0 and len(self.balls) < 8:
            self.balls.append(Ball(self.rows))
            self.spawn_in = random.randint(3, 7)
        alive = []
        for b in self.balls:
            b.t += 0.5                           # полкадра — полшага вниз
            if b.t >= self.rows + 1:             # пролетел доску — в карман
                self.counts[(sum(b.steps) + self.rows) // 2] += 1
                self.total += 1
            else:
                alive.append(b)
        self.balls = alive

    def ball_xy(self, b):
        """Клетка шарика: (строка кадра, колонка)."""
        r = min(int(b.t), self.rows)
        # пройденные отскоки плюс горизонтальный полушаг на текущем ряду
        off = sum(b.steps[:r]) + (b.steps[r] * (b.t - r) if r < self.rows else 0.0)
        return r + 1, self.c0 + int(math.floor(off + 0.5))

    def draw(self):
        w, h, R = self.w, self.h, self.rows
        c0 = self.c0
        grid = [[' '] * w for _ in range(h)]
        colr = [[None] * w for _ in range(h)]

        # воронка сверху
        for dx in (-2, -1, 1, 2):
            grid[0][c0 + dx] = '─'
            colr[0][c0 + dx] = C_PEG
        grid[0][c0] = '▼'
        colr[0][c0] = C_BALL

        # треугольник колышков
        for r in range(R):
            for o in range(-r, r + 1, 2):
                grid[r + 1][c0 + o] = '·'
                colr[r + 1][c0 + o] = C_PEG

        # шарики в полёте (поверх колышков)
        for b in self.balls:
            y, x = self.ball_xy(b)
            if 0 <= y < h and 0 <= x < w:
                grid[y][x] = '●'
                colr[y][x] = C_BALL

        # столбики-накопители: при переполнении масштабируются по самому высокому
        bottom = h - 2
        cap = self.bar_h
        maxc = max(self.counts) if self.counts else 0
        if cap > 0 and maxc > cap:
            shown = [max(1, int(c * cap / maxc + 0.5)) for c in self.counts]
        else:
            shown = [min(c, cap) for c in self.counts]   # cap <= 0 -> нули
        peak = max(shown) if shown else 0
        for i, s in enumerate(shown):
            col = c0 + 2 * i - R
            for k in range(s):
                f = (k + 1) / peak               # градиент по высоте столбика
                row = bottom - k
                if row > R + 1:                  # не залезаем на доску
                    grid[row][col] = '█'
                    colr[row][col] = GRAD[min(GRAD_N - 1, int(f * GRAD_N))]

        out = ["\033[H"]
        for y in range(h - 1):                   # последняя строка — статус
            row = []
            for x in range(w):
                cell = grid[y][x]
                row.append(' ' if cell == ' ' else colr[y][x] + cell)
            out.append("".join(row) + RST + "\033[K\n")
        out.append(self._status(w) + "\033[K\n")
        return "".join(out)

    def _status(self, w):
        """Статус: число шаров, среднее и сигма распределения."""
        n = self.total
        if n > 0:
            mean = sum(i * c for i, c in enumerate(self.counts)) / n
            sigma = math.sqrt(sum(c * (i - mean) ** 2
                                  for i, c in enumerate(self.counts)) / n)
            plain = "шары: %d   среднее: %.2f   сигма: %.2f" % (n, mean, sigma)
            colored = "".join(c + t + RST for c, t in (
                (C_DIM, "шары: "), (C_TXT, str(n)), (C_DIM, "   среднее: "),
                (C_TXT, "%.2f" % mean), (C_DIM, "   сигма: "),
                (C_TXT, "%.2f" % sigma)))
        else:
            plain = "шары: 0   среднее: —   сигма: —"
            colored = C_DIM + plain + RST
        if self.paused:
            plain += "   ‖ пауза"
            colored += C_DIM + "   ‖ пауза" + RST
        return " " * max(0, (w - len(plain)) // 2) + colored


def main():
    fd = sys.stdin.fileno()
    old = None
    if os.name != 'nt':
        try:
            import termios, tty
            old = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:                        # stdin не tty — работаем без клавиш
            old = None
    sys.stdout.write("\033[?25l\033[2J")         # курсор спрятать, экран чистый
    g = None
    last_size = None
    paused = False
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = max(8, sz.columns), max(6, sz.lines - 1)
            except OSError:
                w, h = 80, 24
            if g is None or (w, h) != last_size:
                # доска пересоздаётся, статистика выживает, если влезает
                counts = g.counts if g is not None else None
                total = g.total if g is not None else 0
                g = Galton(w, h, counts, total)
                last_size = (w, h)
                sys.stdout.write("\033[2J")
            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused
            g.paused = paused
            g.update()
            sys.stdout.write(g.draw())
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
