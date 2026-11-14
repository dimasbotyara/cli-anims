#!/usr/bin/env python3
"""Муравьи Лэнгтона. Space — пауза, Q — выход."""

import os, sys, time


def read_key():
    # Неблокирующее чтение клавиши; если stdin — не терминал, клавиш нет
    if not sys.stdin.isatty():
        return None
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


# Правила муравьёв: строка из L/R задаёт поворот для каждого состояния клетки
RULES = ("RL", "RLR", "LLRR", "LRRRRRLLR")

# Цвет клетки для каждого состояния (0..8 — у правила LRRRRRLLR девять состояний);
# состояние 0 — пустое поле
PALETTE = [
    None,
    (60, 62, 78),
    (70, 130, 250),
    (85, 215, 140),
    (245, 205, 85),
    (250, 95, 125),
    (185, 100, 250),
    (230, 230, 230),
    (120, 220, 230),
]

# Смещения по направлениям: вверх, вправо, вниз, влево
DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)


class Ant:
    __slots__ = ('x', 'y', 'dir', 'rule', 'color')

    def __init__(self, x, y, rule, color):
        self.x = x
        self.y = y
        self.dir = 0               # все муравьи стартуют в одну сторону — вверх
        self.rule = rule
        self.color = color


class Langton:
    """Одно тороидальное поле на всех муравьёв; клетка хранит число-состояние."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.grid = [0] * (w * h)
        # расставляем муравьёв по полю, каждому достаётся своё правило
        places = [
            (w // 2, h // 2),
            (w // 4, h // 3),
            (3 * w // 4, h // 3),
            (w // 2, 3 * h // 4),
        ]
        bright = [
            (255, 255, 255), (255, 230, 110),
            (110, 255, 190), (255, 150, 255),
        ]
        self.ants = []
        for i, rule in enumerate(RULES):
            x, y = places[i % len(places)]
            self.ants.append(Ant(x % w, y % h, rule, bright[i % len(bright)]))

    def _step_ant(self, ant):
        # шаг муравья: поворот по правилу, перекраска клетки, движение вперёд
        w, h = self.w, self.h
        state = self.grid[ant.y * w + ant.x]
        if ant.rule[state % len(ant.rule)] == 'L':
            ant.dir = (ant.dir - 1) % 4
        else:
            ant.dir = (ant.dir + 1) % 4
        self.grid[ant.y * w + ant.x] = (state + 1) % len(ant.rule)
        ant.x = (ant.x + DX[ant.dir]) % w      # тор: заворот по краям
        ant.y = (ant.y + DY[ant.dir]) % h

    def update(self):
        # несколько шагов за кадр, чтобы узор рос бодро
        for _ in range(12):
            for ant in self.ants:
                self._step_ant(ant)

    def draw(self):
        w, h = self.w, self.h
        # клетки, где стоят муравьи, рисуем поверх узора ярким символом
        tops = {(a.x, a.y): a.color for a in self.ants}
        out = ["\033[H"]
        for y in range(h):
            row = []
            base = y * w
            for x in range(w):
                c = tops.get((x, y))
                if c is not None:
                    row.append(f"\033[1;38;2;{c[0]};{c[1]};{c[2]}m@")
                    continue
                s = self.grid[base + x]
                if s == 0:
                    row.append(' ')
                else:
                    p = PALETTE[s]
                    row.append(f"\033[38;2;{p[0]};{p[1]};{p[2]}m█")
            row.append('\033[0m\n')
            out.append(''.join(row))
        return ''.join(out)


def main():
    # cbreak-режим для клавиш; если stdin — не терминал, работаем без клавиш
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
    paused = False
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w = max(2, sz.columns)
                h = max(2, sz.lines - 1)
            except OSError:
                w, h = 80, 24
            # при смене размера терминала пересоздаём сцену
            if (w, h) != last_size or scene is None:
                scene = Langton(w, h)
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
