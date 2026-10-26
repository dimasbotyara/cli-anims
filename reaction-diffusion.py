#!/usr/bin/env python3
"""Gray-Scott reaction-diffusion в терминале. Pure stdlib, truecolor.

Управление:
  1-8  — пресеты (coral, mitosis, worms, solitons, spirals, bubbles, spots, waves)
  R    — перезапустить симуляцию
  Space— пауза
  Q    — выход
"""

import os
import sys
import time
import random

# (имя, feed rate f, kill rate k) — классические значения Gray-Scott
PRESETS = {
    '1': ('coral',    0.0545, 0.062),
    '2': ('mitosis',  0.0367, 0.0649),
    '3': ('worms',    0.0580, 0.0650),
    '4': ('solitons', 0.0300, 0.0620),
    '5': ('spirals',  0.0140, 0.0540),
    '6': ('bubbles',  0.0980, 0.0570),
    '7': ('spots',    0.0350, 0.0650),
    '8': ('waves',    0.0140, 0.0470),
}


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


def make_grid(w, h):
    """A = 1 везде, B = 0, но несколько случайных «затравок» в центре."""
    A = [1.0] * (w * h)
    B = [0.0] * (w * h)
    n_seeds = max(3, w * h // 900)
    for _ in range(n_seeds):
        cx = random.randint(w // 4, 3 * w // 4)
        cy = random.randint(h // 4, 3 * h // 4)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                x = (cx + dx) % w
                y = (cy + dy) % h
                if abs(dx) + abs(dy) <= 2:
                    B[y * w + x] = 0.8
                    A[y * w + x] = 0.2
    return A, B


def step(A, B, w, h, f, k, iters=3):
    """N итераций Gray-Scott с 9-точечным лапласианом и wrap-around."""
    DA, DB, dt = 1.0, 0.5, 1.0
    wm1, hm1 = w - 1, h - 1
    for _ in range(iters):
        A2 = A[:]
        B2 = B[:]
        for y in range(h):
            yw = y * w
            ym1 = (y - 1 if y > 0 else hm1) * w
            yp1 = (y + 1 if y < hm1 else 0) * w
            for x in range(w):
                xm1 = x - 1 if x > 0 else wm1
                xp1 = x + 1 if x < wm1 else 0
                i = yw + x
                a = A[i]
                b = B[i]

                lapA = (0.2 * (A[yw + xm1] + A[yw + xp1] + A[ym1 + x] + A[yp1 + x])
                        + 0.05 * (A[ym1 + xm1] + A[ym1 + xp1] + A[yp1 + xm1] + A[yp1 + xp1])
                        - a)
                lapB = (0.2 * (B[yw + xm1] + B[yw + xp1] + B[ym1 + x] + B[yp1 + x])
                        + 0.05 * (B[ym1 + xm1] + B[ym1 + xp1] + B[yp1 + xm1] + B[yp1 + xp1])
                        - b)

                abb = a * b * b
                A2[i] = a + (DA * lapA - abb + f * (1.0 - a)) * dt
                B2[i] = b + (DB * lapB + abb - (k + f) * b) * dt
        A, B = A2, B2
    return A, B


def color_of(b):
    """Концентрация B → RGB. Плавный переход: тёмно-синий → бирюза → белый."""
    v = b * 2.5
    if v < 0.0:
        v = 0.0
    elif v > 1.0:
        v = 1.0
    if v < 0.4:
        t = v / 0.4
        return int(8 + 40 * t), int(10 + 40 * t), int(35 + 80 * t)
    elif v < 0.75:
        t = (v - 0.4) / 0.35
        return int(48 + 130 * t), int(50 + 180 * t), int(115 + 80 * t)
    else:
        t = (v - 0.75) / 0.25
        return int(178 + 77 * t), int(230 + 25 * t), int(195 + 60 * t)


def main():
    fd = sys.stdin.fileno()
    old = None
    if os.name != 'nt':
        import termios, tty
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)

    sys.stdout.write("\033[?25l\033[2J")

    preset_key = '1'
    paused = False
    A = B = None
    last_size = None

    try:
        while True:
            try:
                sz = os.get_terminal_size()
                tw, th = sz.columns, sz.lines - 1
            except OSError:
                tw, th = 80, 24

            if tw < 10 or th < 5:
                sys.stdout.write("\033[H\033[2J" + "Терминал слишком маленький\n")
                sys.stdout.flush()
                time.sleep(0.3)
                continue

            # half-block: 2 пикселя по вертикали на 1 терминальную клетку
            grid_w, grid_h = tw, th * 2

            if (grid_w, grid_h) != last_size or A is None:
                w, h = grid_w, grid_h
                A, B = make_grid(w, h)
                last_size = (grid_w, grid_h)

            # --- ввод ---
            key = read_key()
            if key == 'q':
                break
            if key == ' ':
                paused = not paused
            elif key == 'r':
                A, B = make_grid(w, h)
            elif key in PRESETS:
                preset_key = key
                A, B = make_grid(w, h)

            name, f, k = PRESETS[preset_key]

            # --- шаг симуляции ---
            if not paused:
                A, B = step(A, B, w, h, f, k, iters=3)

            # --- рендер ---
            out = ["\033[H"]
            for ty in range(th):
                y1 = ty * 2
                y2 = ty * 2 + 1
                row = []
                for x in range(w):
                    b1 = B[y1 * w + x]
                    b2 = B[y2 * w + x]
                    r1, g1, bl1 = color_of(b1)
                    r2, g2, bl2 = color_of(b2)
                    row.append(
                        f"\033[38;2;{r1};{g1};{bl1}m"
                        f"\033[48;2;{r2};{g2};{bl2}m"
                        f"\u2580"  # ▀ upper half block
                    )
                row.append("\033[0m")
                out.append("".join(row) + "\n")

            status = (f" {name:<8} f={f:.4f}  k={f:.4f}  "
                      f"[1-8 preset · R reset · Space pause · Q quit]")
            # f в строке статуса — исправим ниже, чтобы не дублировать
            status = (f" {name:<8} f={f:.4f}  k={k:.4f}  "
                      f"\033[2m[1-8 preset · R reset · Space pause · Q quit]\033[0m")
            if paused:
                status = "\033[1;33m[PAUSED]\033[0m " + status
            out.append("\033[2K" + status)

            sys.stdout.write("".join(out))
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        if old is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
