#!/usr/bin/env python3
"""Fireworks. Space — пауза, Q — выход."""

import os, sys, random, time, math


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


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color')
    def __init__(self, x, y, vx, vy, life, color):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.life = life; self.max_life = life
        self.color = color


class Fireworks:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.particles = []
        self.rockets = []

    def launch(self):
        x = random.randint(self.w // 6, 5 * self.w // 6)
        y = float(self.h - 1)
        vy = -random.uniform(0.6, 1.2)
        color = random.choice([
            (255, 80, 80), (255, 200, 80), (255, 255, 80),
            (80, 255, 80), (80, 200, 255), (200, 80, 255),
        ])
        self.rockets.append([x, y, vy, color])

    def update(self):
        new_rockets = []
        for r in self.rockets:
            r[0] += random.uniform(-0.1, 0.1)
            r[1] += r[2]
            explode_at = random.randint(3, max(4, self.h // 3))
            if r[1] < explode_at:
                for _ in range(random.randint(35, 70)):
                    ang = random.random() * math.tau
                    spd = random.uniform(0.15, 0.65)
                    vx = math.cos(ang) * spd
                    vy = math.sin(ang) * spd
                    life = random.randint(8, 22)
                    self.particles.append(Particle(r[0], r[1], vx, vy, life, r[3]))
            else:
                new_rockets.append(r)
        self.rockets = new_rockets

        alive = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += 0.03   # гравитация
            p.vx *= 0.98
            p.vy *= 0.98
            p.life -= 1
            if p.life > 0 and 0 <= p.x < self.w and 0 <= p.y < self.h:
                alive.append(p)
        self.particles = alive

    def draw(self):
        grid = [[' '] * self.w for _ in range(self.h)]
        colors = [[None] * self.w for _ in range(self.h)]
        for r in self.rockets:
            x, y = int(r[0]), int(r[1])
            if 0 <= x < self.w and 0 <= y < self.h:
                grid[y][x] = '*'
                colors[y][x] = '\033[1;97m'
        for p in self.particles:
            x, y = int(p.x), int(p.y)
            if 0 <= x < self.w and 0 <= y < self.h:
                t = p.life / p.max_life
                c = p.color
                r_, g_, b_ = int(c[0] * t), int(c[1] * t), int(c[2] * t)
                grid[y][x] = '·'
                colors[y][x] = f"\033[1;38;2;{r_};{g_};{b_}m"
        out = ["\033[H"]
        for y in range(self.h):
            row = []
            for x in range(self.w):
                if grid[y][x] == ' ':
                    row.append(' ')
                else:
                    row.append(colors[y][x] + grid[y][x])
            row.append('\033[0m\n')
            out.append(''.join(row))
        return ''.join(out)


def main():
    fd = sys.stdin.fileno()
    old = None
    if os.name != 'nt':
        import termios, tty
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    sys.stdout.write("\033[?25l\033[2J")
    fw = None
    last_size = None
    paused = False
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            if (w, h) != last_size or fw is None:
                fw = Fireworks(w, h)
                last_size = (w, h)
            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused
            if not paused:
                if random.random() < 0.04:
                    fw.launch()
                fw.update()
            sys.stdout.write(fw.draw())
            sys.stdout.flush()
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        if old is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
