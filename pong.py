#!/usr/bin/env python3
"""Pong vs AI. Управление: W/S или ↑/↓. R — рестарт, Q — выход."""

import os, sys, random, time

W, H = 60, 22
PADDLE_H = 4
WIN_SCORE = 10


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
    result = None
    i = 0
    while i < len(data):
        b = data[i]
        if b == 0x1b and i + 2 < len(data) and data[i + 1:i + 2] in (b'[', b'O'):
            k = {'A': 'up', 'B': 'down', 'C': 'right', 'D': 'left'}.get(chr(data[i + 2]))
            if k:
                result = k
            i += 3
        elif b == 0x1b:
            i += 1
        else:
            result = chr(b).lower()
            i += 1
    return result


class Pong:
    def __init__(self):
        self.reset()

    def reset(self):
        self.p1 = H // 2 - PADDLE_H // 2
        self.p2 = H // 2 - PADDLE_H // 2
        self.bx = W // 2
        self.by = H // 2
        self.vx = random.choice((-1, 1))
        self.vy = random.choice((-1, 1)) * 0.6
        self.s1 = 0
        self.s2 = 0
        self.speed = 0.5   # базовая скорость мяча (клеток/сек)
        self.acc = 0.0

    def serve(self, direction):
        self.bx = W // 2
        self.by = H // 2
        self.vx = direction
        self.vy = random.choice((-1, 1)) * 0.6
        self.speed = 0.5
        self.acc = 0.0

    def step(self, dt):
        self.acc += dt
        while self.acc >= 1.0 / self.speed / 20:  # ~20 шагов в секунду при speed=0.5
            self.acc -= 1.0 / self.speed / 20
            self.bx += self.vx * 0.4
            self.by += self.vy * 0.4

        # стены сверху/снизу
        if self.by < 0:
            self.by = 0
            self.vy = abs(self.vy)
        elif self.by > H - 1:
            self.by = H - 1
            self.vy = -abs(self.vy)

        # ракетка игрока (x=1)
        if self.vx < 0 and self.bx <= 1:
            if self.p1 <= self.by <= self.p1 + PADDLE_H - 1:
                self.vx = abs(self.vx)
                self.speed = min(2.0, self.speed + 0.05)
                # подкрутка от края ракетки
                hit = (self.by - self.p1) / (PADDLE_H - 1) * 2 - 1
                self.vy = max(-1.2, min(1.2, self.vy + hit * 0.3))
            elif self.bx < 0:
                self.s2 += 1
                if self.s2 >= WIN_SCORE:
                    self.dead = True
                else:
                    self.serve(1)
                return

        # ракетка ИИ (x=W-2)
        if self.vx > 0 and self.bx >= W - 2:
            if self.p2 <= self.by <= self.p2 + PADDLE_H - 1:
                self.vx = -abs(self.vx)
                self.speed = min(2.0, self.speed + 0.05)
                hit = (self.by - self.p2) / (PADDLE_H - 1) * 2 - 1
                self.vy = max(-1.2, min(1.2, self.vy + hit * 0.3))
            elif self.bx > W - 1:
                self.s1 += 1
                if self.s1 >= WIN_SCORE:
                    self.dead = True
                else:
                    self.serve(-1)
                return

    def draw(self):
        out = ["\033[H"]
        out.append(f" Score: \033[1;32m{self.s1}\033[0m : \033[1;31m{self.s2}\033[0m\n")
        grid = [[' '] * W for _ in range(H)]
        # ракетки
        for i in range(PADDLE_H):
            if 0 <= self.p1 + i < H:
                grid[self.p1 + i][1] = '\033[1;32m|\033[0m'
            if 0 <= self.p2 + i < H:
                grid[self.p2 + i][W - 2] = '\033[1;31m|\033[0m'
        # мяч
        bx, by = int(self.bx), int(self.by)
        if 0 <= bx < W and 0 <= by < H:
            grid[by][bx] = '\033[1;97m●\033[0m'
        for row in grid:
            out.append("|" + "".join(row) + "|\n")
        out.append(f"\033[2mW/S — двигать · R — рестарт · Q — выход\033[0m\n")
        sys.stdout.write("".join(out))
        sys.stdout.flush()

    def run(self):
        self.dead = False
        fd = sys.stdin.fileno()
        old = None
        if os.name != 'nt':
            import termios, tty
            old = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        sys.stdout.write("\033[?25l\033[2J")
        last = time.time()
        try:
            while True:
                now = time.time()
                dt = now - last
                last = now
                if dt > 0.1:
                    dt = 0.1

                k = read_key()
                if k == 'q':
                    break
                if k == 'r':
                    self.reset()
                if not self.dead:
                    if k in ('up', 'w') and self.p1 > 0:
                        self.p1 -= 1
                    elif k in ('down', 's') and self.p1 + PADDLE_H < H:
                        self.p1 += 1
                    # ИИ: двигается к мячу с задержкой
                    target = self.by - PADDLE_H // 2
                    if random.random() < 0.35:  # лёгкая задержка
                        if self.p2 < target and self.p2 + PADDLE_H < H:
                            self.p2 += 1
                        elif self.p2 > target and self.p2 > 0:
                            self.p2 -= 1
                    self.step(dt)
                self.draw()
                time.sleep(0.015)
        except KeyboardInterrupt:
            pass
        finally:
            if old is not None:
                import termios
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    Pong().run()
