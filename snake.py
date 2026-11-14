#!/usr/bin/env python3
"""Snake с проходимыми стенами (тор). Управление: стрелки / WASD, R — рестарт, Q — выход."""

import os, sys, random, time

W, H = 40, 20

# --- Скорость ---
TICK = 0.15   # постоянная, без ускорения


def read_key():
    if os.name == 'nt':
        import msvcrt
        if not msvcrt.kbhit():
            return None
        ch = msvcrt.getwch()
        if ch in ('\x00', '\xe0'):
            if msvcrt.kbhit():
                return {'H': 'up', 'P': 'down', 'K': 'left', 'M': 'right'}.get(msvcrt.getwch())
            return None
        return ch.lower()

    import select
    fd = sys.stdin.fileno()
    if not select.select([fd], [], [], 0)[0]:
        return None
    data = os.read(fd, 32)
    # первый распарсенный ключ приоритетнее (иначе «стрелка+буква» вернёт букву)
    i = 0
    while i < len(data):
        b = data[i]
        if b == 0x1b and i + 2 < len(data) and data[i + 1:i + 2] in (b'[', b'O'):
            key = {'A': 'up', 'B': 'down', 'C': 'right', 'D': 'left'}.get(chr(data[i + 2]))
            if key:
                return key
            i += 3
        elif b == 0x1b:
            i += 1
        else:
            return chr(b).lower()
    return None


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.body = [(W // 2, H // 2), (W // 2 - 1, H // 2), (W // 2 - 2, H // 2)]
        self.dir = (1, 0)
        self.next_dir = (1, 0)
        self.food = self.new_food()
        self.score = 0
        self.dead = False
        self.won = False
        self.acc = 0.0

    def new_food(self):
        # еда появляется только на свободной клетке; None — поле заполнено
        free = [(x, y) for y in range(H) for x in range(W)
                if (x, y) not in self.body]
        return random.choice(free) if free else None

    def step(self):
        # запрет разворота на 180°
        if self.next_dir != (-self.dir[0], -self.dir[1]):
            self.dir = self.next_dir

        hx, hy = self.body[0]
        nx, ny = hx + self.dir[0], hy + self.dir[1]
        # 💫 проходим через стены — заворачиваем
        nx %= W
        ny %= H

        if (nx, ny) in self.body[:-1]:
            self.dead = True
            return

        self.body.insert(0, (nx, ny))
        if (nx, ny) == self.food:
            self.score += 1
            self.food = self.new_food()
            if self.food is None:   # змейка заняла всё поле
                self.won = True
            # никакого ускорения — TICK постоянный
        else:
            self.body.pop()

    def draw(self):
        out = ["\033[H"]
        out.append("+" + "-" * W + "+\n")

        grid = [[' '] * W for _ in range(H)]
        if self.food is not None:
            fx, fy = self.food
            grid[fy][fx] = '\033[1;31m●\033[0m'
        for i, (x, y) in enumerate(self.body):
            if i == 0:
                grid[y][x] = '\033[1;32m@\033[0m'
            elif i == len(self.body) - 1:
                grid[y][x] = '\033[2;32mo\033[0m'
            else:
                grid[y][x] = '\033[32mo\033[0m'

        for row in grid:
            out.append("|" + "".join(row) + "|\n")
        out.append("+" + "-" * W + "+\n")

        if self.won:
            out.append(f" Score: {self.score}   \033[1;33mYOU WIN — R restart / Q quit\033[0m\n")
        elif self.dead:
            out.append(f" Score: {self.score}   \033[1;31mGAME OVER — R restart / Q quit\033[0m\n")
        else:
            out.append(f" Score: {self.score}   \033[2m"
                       f"Arrows/WASD move  ·  R restart  ·  Q quit\033[0m\n")
        sys.stdout.write("".join(out))
        sys.stdout.flush()


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
    game = Snake()
    last = time.time()
    try:
        while True:
            now = time.time()
            dt = now - last
            last = now

            # поле фиксировано (42x23 кадр) — на меньшем окне не рисуем
            try:
                sz = os.get_terminal_size()
                tw, thh = sz.columns, sz.lines
            except OSError:
                tw, thh = 80, 24
            if tw < W + 2 or thh < H + 3:
                sys.stdout.write("\033[H\033[2J"
                                 f"Терминал слишком маленький (нужно минимум {W + 2}x{H + 3})\n")
                sys.stdout.flush()
                time.sleep(0.3)
                continue

            k = read_key()
            if k == 'q':
                break
            if game.dead or game.won:
                if k == 'r':
                    game.reset()
            else:
                if k in ('up', 'w'):
                    game.next_dir = (0, -1)
                elif k in ('down', 's'):
                    game.next_dir = (0, 1)
                elif k in ('left', 'a'):
                    game.next_dir = (-1, 0)
                elif k in ('right', 'd'):
                    game.next_dir = (1, 0)
                elif k == 'r':
                    game.reset()

                game.acc += dt
                while game.acc >= TICK and not game.dead:
                    game.acc -= TICK
                    game.step()

            game.draw()
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        if old is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()