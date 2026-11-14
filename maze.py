#!/usr/bin/env python3
"""Maze — вырезание, решение BFS, новый лабиринт. Space — пауза, Q — выход."""

import os, sys, random, time
from collections import deque

FRAME = 0.04                       # длительность кадра
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
WALL_C = (45, 55, 100)             # стены
HEAD_C = (255, 185, 60)            # голова резака
STACK_C = (150, 105, 40)           # текущая ветка резака
PATH_C = (255, 235, 80)            # найденный путь
PALETTE = ((35, 95, 230), (0, 165, 255), (0, 215, 190), (70, 235, 115),
           (185, 235, 60), (255, 195, 45), (255, 125, 60), (255, 75, 95))
PHASES = {'carve': 'вырезание лабиринта', 'hold': 'пауза',
          'solve': 'поиск BFS', 'trace': 'прокладка пути', 'flash': 'вспышка!'}


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


class MazeShow:
    def __init__(self, w, h):
        self.w, self.h = w, h
        # предел размера: тайл = 2 символа, плюс статус-строка
        self.cap_w = max(3, min(31, (w - 2) // 4))
        self.cap_h = max(3, min(15, (h - 2) // 2))
        self.gen = 0
        self.frame = 0
        self.new_maze()

    def new_maze(self):
        """Новый лабиринт; размер медленно растёт до предела терминала."""
        self.gen += 1
        self.cw = min(self.cap_w, 6 + self.gen)
        self.ch = min(self.cap_h, 4 + self.gen)
        self.tw, self.th = 2 * self.cw + 1, 2 * self.ch + 1
        self.walls = [[True] * self.tw for _ in range(self.th)]
        self.seen = [[False] * self.cw for _ in range(self.ch)]
        sx, sy = random.randrange(self.cw), random.randrange(self.ch)
        self.stack = [(sx, sy)]          # стек резака (recursive backtracker)
        self.seen[sy][sx] = True
        self.walls[2 * sy + 1][2 * sx + 1] = False
        self.start = (1, 1)
        self.goal = (self.tw - 2, self.th - 2)
        self.dist = {self.start: 0}      # BFS-волна: тайл -> расстояние
        self.wave = [self.start]         # фронт волны — пока только старт
        self.prev = {self.start: None}   # для восстановления пути
        self.path = []
        self.pi = 0                      # сколько тайлов пути уже показано
        self.phase, self.timer = 'carve', 0

    # --- фаза 1: вырезание лабиринта по шагам ---
    def carve_steps(self):
        k = max(1, (self.cw * self.ch) // 25)      # шагов за кадр
        for _ in range(k):
            if not self.stack:
                self.phase, self.timer = 'hold', 20    # короткая пауза
                return
            cx, cy = self.stack[-1]
            nbs = [(cx + dx, cy + dy) for dx, dy in DIRS
                   if 0 <= cx + dx < self.cw and 0 <= cy + dy < self.ch
                   and not self.seen[cy + dy][cx + dx]]
            if nbs:
                nx, ny = random.choice(nbs)
                self.walls[cy + ny + 1][cx + nx + 1] = False  # стенка
                self.walls[2 * ny + 1][2 * nx + 1] = False    # клетка
                self.seen[ny][nx] = True
                self.stack.append((nx, ny))
            else:
                self.stack.pop()                   # откат backtracker'а

    # --- фаза 2: BFS-волна от старта к выходу ---
    def solve_steps(self):
        k = max(2, (self.cw * self.ch) // 20)      # тайлов волны за кадр
        found = False
        for _ in range(k):
            if not self.wave:
                break
            cur = self.wave.pop(0)
            for dx, dy in DIRS:
                nxt = (cur[0] + dx, cur[1] + dy)
                if nxt in self.dist or self.walls[nxt[1]][nxt[0]]:
                    continue
                self.dist[nxt] = self.dist[cur] + 1
                self.prev[nxt] = cur
                if nxt == self.goal:
                    found = True
                self.wave.append(nxt)
        if found or not self.wave:
            self.build_path()
            self.phase = 'trace'

    def build_path(self):
        """Восстановление пути от выхода к старту."""
        self.path = []
        node = self.goal if self.goal in self.prev else self.start
        while node is not None:
            self.path.append(node)
            node = self.prev.get(node)
        self.path.reverse()
        self.pi = 0

    def update(self):
        self.frame += 1
        if self.phase == 'carve':
            self.carve_steps()
        elif self.phase == 'hold':
            self.timer -= 1
            if not self.timer:
                self.phase = 'solve'
        elif self.phase == 'solve':
            self.solve_steps()
        elif self.phase == 'trace':
            self.pi = min(len(self.path), self.pi + max(2, len(self.path) // 30))
            if self.pi >= len(self.path):
                self.phase, self.timer = 'flash', 14   # вспышка пути
        elif self.phase == 'flash':
            self.timer -= 1
            if not self.timer:
                self.new_maze()    # очистка и генерация следующего

    # --- отрисовка ---
    def draw(self):
        cells = [[('  ', None)] * self.tw for _ in range(self.th)]
        wall = rgb(WALL_C)
        for y in range(self.th):
            for x in range(self.tw):
                if self.walls[y][x]:
                    cells[y][x] = ('██', wall)
        if self.phase == 'carve':
            # текущая ветка резака — тёплый след, голова — яркая
            for i, (cx, cy) in enumerate(self.stack):
                x, y = 2 * cx + 1, 2 * cy + 1
                col = rgb(HEAD_C, True) if i == len(self.stack) - 1 \
                    else rgb(STACK_C)
                cells[y][x] = ('▓▓', col)
        if self.phase in ('solve', 'trace', 'flash'):
            for (x, y), d in self.dist.items():    # радужная волна BFS
                cells[y][x] = ('██', rgb(PALETTE[d % len(PALETTE)]))
            for x, y in self.wave:                 # фронт волны — белый
                cells[y][x] = ('██', rgb((255, 255, 255), True))
        if self.phase in ('trace', 'flash'):
            on = self.phase == 'trace' or (self.frame // 3) % 2 == 0
            col = rgb(PATH_C, True) if on else rgb((255, 255, 255), True)
            for x, y in self.path[:self.pi]:       # подсветка найденного пути
                cells[y][x] = ('██', col)
        cells[1][1] = ('S ', rgb((90, 235, 120), True))          # старт
        gx, gy = self.goal
        cells[gy][gx] = ('E ', rgb((255, 90, 90), True))         # выход
        out = ['\033[H']
        for row in cells:
            out.append(''.join(c + t if c else t for t, c in row) + '\033[0m\n')
        # статусная строка: поколение, размер, фаза
        line = f" Поколение {self.gen} · лабиринт {self.cw}×{self.ch} · " \
               f"{PHASES[self.phase]}"
        hint = ' · Space — пауза, Q — выход'
        if len(line) + 25 <= self.w:
            line += '\033[2m' + hint + '\033[0m'
        out.append(line[:self.w] + '\033[0m\n')
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
    scene = None
    last_size = None
    paused = False
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            if (w, h) != last_size or scene is None:
                scene = MazeShow(w, h)   # пересоздаём сцену при resize
                last_size = (w, h)
            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused
            if not paused:
                scene.update()
            sys.stdout.write(scene.draw())
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
