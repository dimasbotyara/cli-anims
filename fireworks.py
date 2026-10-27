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
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'grav', 'drag')
    def __init__(self, x, y, vx, vy, life, color, grav, drag):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.life = life; self.max_life = life
        self.color = color
        self.grav = grav; self.drag = drag


class Fireworks:
    # типы взрывов: (гравитация, торможение, скорость, жизнь)
    STYLES = [
        (0.020, 0.985, 1.00, 1.00),   # обычный — искры падают
        (0.048, 0.982, 0.85, 1.10),   # тяжёлый — быстро сыплется вниз
        (0.000, 0.945, 1.50, 1.20),   # зависает — разлетается и замирает
    ]

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.particles = []
        self.rockets = []
        self.glow = {}   # (x, y) -> [r, g, b] — остывающие следы

    def launch(self):
        x = random.randint(self.w // 8, 7 * self.w // 8)
        y = float(self.h - 1)
        vy = -random.uniform(0.7, 1.4)
        power = random.uniform(0.85, 1.3)   # разброс размера взрыва
        color = random.choice([
            (255, 90, 90), (255, 210, 90), (255, 255, 120),
            (90, 255, 90), (90, 210, 255), (210, 90, 255),
            (255, 255, 255),
        ])
        self.rockets.append([x, y, vy, color, power])

    def burst(self, x, y, color, power):
        grav, drag, spd_k, life_k = random.choice(self.STYLES)
        for _ in range(int(random.randint(40, 75) * power)):
            ang = random.random() * math.tau
            spd = random.uniform(0.22, 0.75) * power * spd_k
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd * 0.6   # поправка на вытянутость символов
            life = int(random.randint(20, 45) * life_k)
            g = grav * random.uniform(0.75, 1.25) if grav else random.uniform(0.0, 0.002)
            d = drag + random.uniform(-0.004, 0.004)
            self.particles.append(Particle(x, y, vx, vy, life, color, g, d))

    def update(self):
        new_rockets = []
        for r in self.rockets:
            r[0] += random.uniform(-0.15, 0.15)
            r[1] += r[2]
            explode_at = random.randint(max(3, self.h // 6), max(4, self.h // 2))
            if r[1] < explode_at:
                self.burst(r[0], r[1], r[3], r[4])
            else:
                new_rockets.append(r)
        self.rockets = new_rockets

        alive = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += p.grav
            p.vx *= p.drag
            p.vy *= p.drag
            p.life -= 1
            if p.life > 0 and 0 <= p.x < self.w and 0 <= p.y < self.h:
                alive.append(p)
                x, y = int(p.x), int(p.y)
                t = p.life / p.max_life
                self.glow[(x, y)] = [c * (0.3 + 0.45 * t) for c in p.color]
        self.particles = alive

        # следы гаснут постепенно, а не исчезают вместе с частицей
        if self.glow:
            faded = {}
            for (x, y), c in self.glow.items():
                nc = [v * 0.8 for v in c]
                if max(nc) >= 32:
                    faded[(x, y)] = nc
            self.glow = faded

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
                hot = t * t * 0.6                      # белое ядро в начале жизни
                e = 0.45 + 0.55 * t                    # яркость держится дольше
                r_ = min(255, int((c[0] * (1 - hot) + 255 * hot) * e))
                g_ = min(255, int((c[1] * (1 - hot) + 255 * hot) * e))
                b_ = min(255, int((c[2] * (1 - hot) + 255 * hot) * e))
                grid[y][x] = '*' if t > 0.7 else '·'
                colors[y][x] = f"\033[1;38;2;{r_};{g_};{b_}m"
        for (x, y), c in self.glow.items():
            if grid[y][x] != ' ':
                continue
            r_, g_, b_ = (min(255, int(v)) for v in c)
            grid[y][x] = '.'
            colors[y][x] = f"\033[38;2;{r_};{g_};{b_}m"
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
                if random.random() < 0.075:
                    fw.launch()
                    if random.random() < 0.12:   # иногда по два сразу
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
