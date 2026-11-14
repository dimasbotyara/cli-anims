#!/usr/bin/env python3
"""Tetris — сам играет. Space — пауза, Q — выход."""

import os, sys, random, time

FRAME, ACTION_EVERY, FLASH_TICKS, OVER_TICKS = 0.05, 2, 5, 60
LINE_SCORE = (0, 100, 300, 500, 800)
SHAPES = {   # базовые матрицы фигур
    'I': ((0, 0, 0, 0), (1, 1, 1, 1), (0, 0, 0, 0), (0, 0, 0, 0)),
    'O': ((1, 1), (1, 1)),
    'T': ((0, 1, 0), (1, 1, 1), (0, 0, 0)),
    'S': ((0, 1, 1), (1, 1, 0), (0, 0, 0)),
    'Z': ((1, 1, 0), (0, 1, 1), (0, 0, 0)),
    'J': ((1, 0, 0), (1, 1, 1), (0, 0, 0)),
    'L': ((0, 0, 1), (1, 1, 1), (0, 0, 0)),
}
COLORS = {'I': (70, 225, 225), 'O': (240, 210, 70), 'T': (205, 95, 235),
          'S': (95, 230, 95), 'Z': (240, 95, 75), 'J': (75, 125, 240),
          'L': (240, 155, 65)}


def rgb(c, bold=False):
    return f"\033[{'1;' if bold else ''}38;2;{c[0]};{c[1]};{c[2]}m"


def read_key():
    """Неблокирующее чтение клавиши; None, если нажатий нет."""
    try:
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
    except Exception:
        return None          # stdin не tty или закрыт — играем без клавиш

def build_pieces():
    # предвычисляем повороты всех фигур (нормировка к углу 0,0)
    pieces = {}
    for name, m in SHAPES.items():
        states, cur = [], m
        for _ in range(4):
            cells = tuple(sorted((x, y) for y, row in enumerate(cur)
                                 for x, v in enumerate(row) if v))
            mx = min(x for x, _ in cells); my = min(y for _, y in cells)
            cells = tuple(sorted((x - mx, y - my) for x, y in cells))
            if cells not in states:
                states.append(cells)
            cur = tuple(zip(*cur[::-1]))       # поворот на 90°
        pieces[name] = states
    return pieces


PIECES = build_pieces()


def metrics(grid):
    """Агрегированная высота колонок, дырки и неровность рельефа."""
    h, w = len(grid), len(grid[0])
    heights, holes = [], 0
    for x in range(w):
        top = next((y for y in range(h) if grid[y][x]), h)
        heights.append(h - top)
        holes += sum(1 for y in range(top + 1, h) if not grid[y][x])
    bump = sum(abs(a - b) for a, b in zip(heights, heights[1:]))
    return sum(heights), holes, bump


class Tetris:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.bw = max(5, min(10, (w - 16) // 2))   # ширина стакана в клетках
        self.bh = max(6, min(20, h - 3))           # высота стакана
        self.reset()

    def reset(self):
        self.board = [[None] * self.bw for _ in range(self.bh)]
        self.score = 0; self.lines = 0; self.level = 1
        self.piece = random.choice(list(PIECES))
        self.next_piece = random.choice(list(PIECES))
        self.rot = 0; self.px = 0; self.py = -1
        self.target = None; self.flash_rows = []; self.flash_timer = 0
        self.over_timer = 0; self.frame = 0
        self.spawn()

    def fits(self, cells, px, py):
        """Помещаются ли клетки cells в позицию (px, py)."""
        return all(0 <= px + x < self.bw and py + y < self.bh
                   and (py + y < 0 or self.board[py + y][px + x] is None)
                   for x, y in cells)

    def spawn(self):
        self.piece, self.next_piece = self.next_piece, random.choice(list(PIECES))
        self.rot, self.target, self.py = 0, None, -1
        cells = PIECES[self.piece][0]
        self.px = max(0, (self.bw - (max(x for x, _ in cells) + 1)) // 2)
        if not self.fits(cells, self.px, self.py):
            self.over_timer = OVER_TICKS    # стакан полон — скоро рестарт

    def plan(self):
        # ИИ: перебор поворотов и колонок; вес — высота+, дырки++, неровность+
        best, best_val = (0, self.px), None
        for r, cells in enumerate(PIECES[self.piece]):
            width = max(x for x, _ in cells) + 1
            for tx in range(self.bw - width + 1):
                py = -1
                if not self.fits(cells, tx, py):
                    continue
                while self.fits(cells, tx, py + 1):    # роняем до упора
                    py += 1
                if py < 0:                             # в стакан не попадает
                    continue
                grid = [row[:] for row in self.board]
                for x, y in cells:
                    grid[py + y][tx + x] = True
                full = [y for y in range(self.bh) if all(grid[y])]
                for _ in full:                          # убираем линии
                    grid.pop(next(y for y in range(self.bh) if all(grid[y])))
                    grid.insert(0, [None] * self.bw)
                agg, holes, bump = metrics(grid)
                val = 0.76 * len(full) - 0.51 * agg - 0.76 * holes - 0.18 * bump
                if best_val is None or val > best_val:
                    best_val, best = val, (r, tx)
        return best

    def update(self):
        self.frame += 1
        if self.over_timer:                # пауза на табло, затем авто-рестарт
            self.over_timer -= 1
            if not self.over_timer:
                self.reset()
            return
        if self.flash_timer:               # вспышка очищаемых линий
            self.flash_timer -= 1
            if not self.flash_timer:
                self.finish_clear()
            return
        if self.frame % max(1, ACTION_EVERY - (self.level - 1) // 5):
            return                         # скорость растёт с уровнем
        if self.target is None:            # план строим один раз на фигуру
            self.target = self.plan()
        cells = PIECES[self.piece][self.rot]
        tr, tx = self.target
        moved = False
        if self.rot != tr:                 # шаг 1: поворот (со сдвигом, если тесно)
            nrot = (self.rot + 1) % len(PIECES[self.piece])
            ncells = PIECES[self.piece][nrot]
            for dx in (0, -1, 1):
                if self.fits(ncells, self.px + dx, self.py):
                    self.rot, self.px = nrot, self.px + dx
                    moved = True
                    break
        if not moved and self.px != tx:    # шаг 2: сдвиг к целевой колонке
            step = 1 if tx > self.px else -1
            if self.fits(cells, self.px + step, self.py):
                self.px += step
                moved = True
        if not moved:                      # шаг 3: вниз или фиксация
            if self.fits(cells, self.px, self.py + 1):
                self.py += 1
            else:
                self.lock()

    def lock(self):
        top_out = any(self.py + y < 0 for x, y in PIECES[self.piece][self.rot])
        for x, y in PIECES[self.piece][self.rot]:
            if self.py + y >= 0:
                self.board[self.py + y][self.px + x] = COLORS[self.piece]
        self.target = None
        if top_out:                        # фигура не влезла целиком
            self.over_timer = OVER_TICKS
            return
        full = [y for y in range(self.bh) if all(self.board[y])]
        if full:
            self.flash_rows = full; self.flash_timer = FLASH_TICKS
        else:
            self.spawn()

    def finish_clear(self):
        n = len(self.flash_rows)
        skip = set(self.flash_rows)
        self.board = [[None] * self.bw for _ in range(n)] + \
            [row for i, row in enumerate(self.board) if i not in skip]
        self.flash_rows = []
        self.lines += n
        self.score += LINE_SCORE[min(n, 4)] * self.level
        self.level = self.lines // 10 + 1
        self.spawn()

    def _panel(self):
        """Панель справа: счёт, линии, скорость и следующая фигура."""
        pw = max(6, self.w - (2 * self.bw + 2) - 2)   # доступная ширина
        mini = [['  '] * 4 for _ in range(2)]
        for x, yy in PIECES[self.next_piece][0]:
            mini[yy][x] = '██'
        pre = rgb(COLORS[self.next_piece])
        panel = [(' Счёт: %d' % self.score)[:pw],
                 (' Линии: %d' % self.lines)[:pw],
                 ' Скорость: %dx' % ((self.level - 1) // 5 + 1),
                 '', ' Далее:',
                 pre + ''.join(mini[0]) + '\033[0m',
                 pre + ''.join(mini[1]) + '\033[0m']
        if self.over_timer:
            panel.append(rgb((255, 70, 70), True) + ' рестарт...')
        return panel

    def draw(self):
        grid = [row[:] for row in self.board]
        for x, y in PIECES[self.piece][self.rot]:      # падающая фигура
            if 0 <= self.py + y < self.bh:
                grid[self.py + y][self.px + x] = COLORS[self.piece]
        fcol = rgb((255, 255, 255) if (self.frame // 2) % 2 == 0
                   else (110, 110, 110), True)         # цвет вспышки линий
        panel = self._panel()
        out = ['\033[H', '┌' + '──' * self.bw + '┐\033[0m\033[K\n']
        for y in range(self.bh):
            if self.over_timer and y == self.bh // 2:
                body = rgb((255, 70, 70), True) + 'GAME OVER'.center(2 * self.bw)
            else:
                body = ''.join(
                    '  ' if v is None else
                    (fcol + '██' if self.flash_timer and y in self.flash_rows
                     else rgb(v) + '██')
                    for v in grid[y])
            p = panel[y] if y < len(panel) else None
            out.append('│' + body + '\033[0m│' +
                       ('  ' + p if p else '') + '\033[0m\033[K\n')
        out.append('└' + '──' * self.bw + '┘\033[0m\033[K\n')
        return ''.join(out)

def main():
    fd = sys.stdin.fileno()
    old = None
    if os.name != 'nt':
        try:                             # stdin не tty — работаем без клавиш
            import termios, tty
            old = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            old = None
    sys.stdout.write("\033[?25l\033[2J")
    game = None
    last_size = None
    paused = False
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            if (w, h) != last_size or game is None:
                game = Tetris(w, h)      # пересоздаём сцену при resize
                last_size = (w, h)
            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused
            if not paused:
                game.update()
            sys.stdout.write(game.draw())
            sys.stdout.flush()
            time.sleep(FRAME)
    except KeyboardInterrupt:
        pass
    finally:
        if old is not None:
            try:
                import termios
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            except Exception:
                pass
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == '__main__':
    main()
