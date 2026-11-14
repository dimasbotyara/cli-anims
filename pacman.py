#!/usr/bin/env python3
"""Pacman — сам играет. Space — пауза, Q — выход."""

import os, sys, random, time
from collections import deque

FRAME = 0.05        # длительность кадра
MOVE_EVERY = 2      # pacman делает ход каждые N кадров
DIE_TICKS = 18      # сколько кадров мигает pacman после поимки
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
PAC_CHAR = {(1, 0): '▶', (-1, 0): '◀', (0, 1): '▼', (0, -1): '▲'}


def rgb(c, bold=False):
    """Truecolor-код: rgb((r, g, b), яркий)."""
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

def bfs(walls, start, goal_test=None):
    """BFS: карта расстояний от start; заодно путь к ближайшей цели."""
    dist = {start: 0}
    prev = {start: None}
    q = deque([start])
    path = []
    while q:
        cur = q.popleft()
        if goal_test and cur != start and goal_test(cur):
            path = []                 # путь к ближайшей цели найден
            node = cur
            while node != start:
                path.append(node); node = prev[node]
            path.reverse()
            goal_test = None          # дальше достраиваем только карту
        for dx, dy in DIRS:
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt not in dist and not walls[nxt[1]][nxt[0]]:
                dist[nxt] = dist[cur] + 1
                prev[nxt] = cur
                q.append(nxt)
    return dist, path

def gen_maze(cw, ch):
    """Лабиринт recursive backtracker + петли, чтобы было где убегать."""
    tw, th = 2 * cw + 1, 2 * ch + 1
    walls = [[True] * tw for _ in range(th)]
    seen = [[False] * cw for _ in range(ch)]
    sx, sy = random.randrange(cw), random.randrange(ch)
    stack = [(sx, sy)]
    seen[sy][sx] = True
    walls[2 * sy + 1][2 * sx + 1] = False
    while stack:
        cx, cy = stack[-1]
        nbs = [(cx + dx, cy + dy) for dx, dy in DIRS
               if 0 <= cx + dx < cw and 0 <= cy + dy < ch
               and not seen[cy + dy][cx + dx]]
        if not nbs:
            stack.pop()
            continue
        nx, ny = random.choice(nbs)
        walls[cy + ny + 1][cx + nx + 1] = False   # стенка между клетками
        walls[2 * ny + 1][2 * nx + 1] = False     # сама клетка
        seen[ny][nx] = True
        stack.append((nx, ny))
    for y in range(1, th - 1):        # петли: убираем часть внутренних стен
        for x in range(1, tw - 1):
            if walls[y][x] and (x % 2 == 0) != (y % 2 == 0) \
                    and ((not walls[y][x - 1] and not walls[y][x + 1])
                         or (not walls[y - 1][x] and not walls[y + 1][x])) \
                    and random.random() < 0.12:
                walls[y][x] = False
    cx, cy = tw // 2, th // 2         # дом призраков — открытый крест в центре
    walls[cy][cx] = False
    for dx, dy in DIRS:
        if 0 < cx + dx < tw - 1 and 0 < cy + dy < th - 1:
            walls[cy + dy][cx + dx] = False
    return walls

class Ghost:
    __slots__ = ('pos', 'color', 'pull', 'dormant')

    def __init__(self, pos, color, pull):
        self.pos = pos; self.color = color
        self.pull = pull       # вероятность тяги к pacman (стиль поведения)
        self.dormant = 0       # кадров отдыха в доме после съедения

class Game:
    def __init__(self, w, h):
        self.w, self.h = w, h
        # клетка лабиринта = 2 тайла, тайл = 2 символа, плюс статус-строка
        self.cw = max(3, min(21, (w - 2) // 4))
        self.ch = max(3, min(11, (h - 3) // 2))
        self.tw, self.th = 2 * self.cw + 1, 2 * self.ch + 1
        self.walls = gen_maze(self.cw, self.ch)
        self.house = (self.tw // 2, self.th // 2)
        self.start = (1, 1)               # левый верхний угол
        self.score = 0; self.lives = 3; self.level = 1; self.frame = 0
        self.new_level()

    def new_level(self):
        """Пельметы по всем открытым тайлам, герои — на исходные позиции."""
        self.pellets = {(x, y) for y in range(1, self.th - 1)
                        for x in range(1, self.tw - 1) if not self.walls[y][x]}
        # energizer-пельметы в трёх углах — они включают режим испуга
        self.powers = {(self.tw - 2, 1), (1, self.th - 2),
                       (self.tw - 2, self.th - 2)}
        self.pellets |= self.powers
        hx, hy = self.house    # в доме призраков пельметов не бывает
        self.pellets -= {(hx + dx, hy + dy) for dx in (-1, 0, 1)
                         for dy in (-1, 0, 1)}
        self.pac = self.start
        self.pac_dir = (1, 0)
        self.fright = 0        # кадров оставшегося испуга призраков
        self.dying = 0
        # три стиля: почти «BFS к pacman», средняя тяга и ленивое блуждание
        styles = (((255, 80, 80), 0.92), ((255, 140, 190), 0.5), ((90, 200, 255), 0.25))
        self.ghosts = [Ghost(self.house, c, p) for c, p in styles]

    def update(self):
        self.frame += 1
        if self.dying:                 # мигание после поимки, затем респавн
            self.dying -= 1
            if not self.dying:
                self.pac = self.start; self.pac_dir = (1, 0); self.fright = 0
                for g in self.ghosts:
                    g.pos = self.house; g.dormant = 30
            return
        if self.fright:
            self.fright -= 1
        if self.frame % MOVE_EVERY:
            return
        # один BFS от pacman: и путь к ближайшей пельмете, и поле для призраков
        field, path = bfs(self.walls, self.pac, lambda t: t in self.pellets)
        # обход призраков: если следующий шаг опасен, ищем путь в обход
        if path and not self.fright:
            gx, gy = path[0]
            danger = {(gx, gy), (gx + 1, gy), (gx - 1, gy),
                      (gx, gy + 1), (gx, gy - 1)}
            if any(not g.dormant and g.pos in danger for g in self.ghosts):
                blocked = [row[:] for row in self.walls]
                for g in self.ghosts:      # тайлы рядом с призраками — стенки
                    if not g.dormant:
                        x, y = g.pos
                        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                            if 0 <= x + dx < self.tw and 0 <= y + dy < self.th:
                                blocked[y + dy][x + dx] = True
                _, alt = bfs(blocked, self.pac, lambda t: t in self.pellets)
                path = alt or path         # обхода нет — идём как шло
        if path:
            nxt = path[0]
            self.pac_dir = (nxt[0] - self.pac[0], nxt[1] - self.pac[1])
            self.pac = nxt
        if self.pac in self.pellets:   # съел пельмету
            self.pellets.discard(self.pac)
            if self.pac in self.powers:
                self.powers.discard(self.pac)
                self.score += 50
                self.fright = 120      # призраки паникуют ~6 секунд
            else:
                self.score += 10
        if not self.pellets:           # уровень зачищен — новый расклад
            self.level += 1
            self.new_level()
            return
        for g in self.ghosts:          # ход призраков + проверка столкновений
            self.step_ghost(g, field)
            if g.dormant or g.pos != self.pac:
                continue
            if self.fright:
                self.score += 200      # съели призрака
                g.pos = self.house
                g.dormant = 40 + self.fright   # отсижится до конца паники
            else:
                self.lives -= 1
                self.dying = DIE_TICKS         # мигание и респавн
                if self.lives <= 0:            # жизни кончились — новая игра
                    self.lives = 3; self.score = 0
                break

    def step_ghost(self, g, field):
        if g.dormant:
            g.dormant -= 1
            return
        cadence = max(3, 5 - self.level)           # с уровнем быстрее, но не догоняя
        if self.frame % (cadence + 1 if self.fright else cadence):
            return
        nbs = [(g.pos[0] + dx, g.pos[1] + dy) for dx, dy in DIRS
               if not self.walls[g.pos[1] + dy][g.pos[0] + dx]]
        if not nbs:
            return
        key = lambda n: (field.get(n, 10 ** 6), random.random())
        if self.fright:
            g.pos = max(nbs, key=key)              # прочь от pacman
        elif random.random() < g.pull:
            g.pos = min(nbs, key=key)              # вниз по BFS-полю к pacman
        else:
            g.pos = random.choice(nbs)             # случайное блуждание

    def draw(self):
        cells = [[('  ', None)] * self.tw for _ in range(self.th)]
        wall = rgb((70, 90, 220))
        blink = (self.frame // 5) % 2 == 0
        for y in range(self.th):
            for x in range(self.tw):
                if self.walls[y][x]:
                    cells[y][x] = ('██', wall)
                elif (x, y) in self.pellets:
                    if (x, y) in self.powers:
                        if blink:
                            cells[y][x] = ('● ', rgb((255, 225, 120), True))
                    else:
                        cells[y][x] = ('· ', rgb((235, 205, 160)))
        # призраки (pacman рисуем поверх всего)
        fright_blink = self.fright < 40 and (self.frame // 4) % 2 == 0
        for g in self.ghosts:
            x, y = g.pos
            if g.dormant:
                col = rgb((130, 130, 150))
            elif self.fright:
                col = rgb((255, 255, 255), True) if fright_blink \
                    else rgb((80, 100, 255), True)
            else:
                col = rgb(g.color, True)
            cells[y][x] = ('◆ ', col)
        if not (self.dying and (self.frame // 2) % 2):   # мигание при смерти
            x, y = self.pac
            cells[y][x] = (PAC_CHAR[self.pac_dir] + ' ', rgb((255, 220, 40), True))
        out = ['\033[H']
        for row in cells:
            out.append(''.join(c + t if c else t for t, c in row) + '\033[0m\n')
        # статусная строка: счёт, жизни, уровень и режим
        text, col = (('Пойман!', (255, 60, 60)) if self.dying else
                     (('ПРИЗРАКИ В ПАНИКЕ', (120, 140, 255)) if self.fright else
                      ('охота за пельметами', (140, 140, 140))))
        base = f" Счёт: {self.score}   Жизни: {'♥' * max(0, self.lives)}   " \
               f"Уровень: {self.level}"
        status = base + '   ' + rgb(col, True) + text + '\033[0m' \
            if len(base) + 3 + len(text) <= self.w else base[:self.w]
        out.append(status + '\033[0m\n')
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
                game = Game(w, h)        # пересоздаём сцену при resize
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
