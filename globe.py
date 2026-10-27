#!/usr/bin/env python3
"""Rotating procedural globe. Space — пауза, Q — выход."""

import os, sys, math, time


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


def noise3(x, y, z):
    return (math.sin(x * 1.7 + y * 0.9)
            + math.sin(y * 2.1 + z * 1.3)
            + math.sin(z * 1.5 + x * 2.3)
            + math.sin(x * 0.7 - y * 1.1 - z * 0.5))


def is_land(x, y, z):
    v = noise3(x * 2, y * 2, z * 2) + 0.5 * noise3(x * 4 + 1, y * 4, z * 4)
    return v > 0.6


def main():
    fd = sys.stdin.fileno()
    old = None
    if os.name != 'nt':
        import termios, tty
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    sys.stdout.write("\033[?25l\033[2J")
    angle = 0.0
    paused = False
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 2
            except OSError:
                w, h = 80, 22

            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused
            if not paused:
                angle += 0.04

            R = max(2, min(w // 4, h) * 0.9)
            cx, cy = w / 2, h / 2
            grid = [[' '] * w for _ in range(h)]
            colors = [[None] * w for _ in range(h)]

            for py in range(h):
                y_screen = (py - cy) / (R * 0.5)
                for px in range(w):
                    x_screen = (px - cx) / R
                    r2 = x_screen * x_screen + y_screen * y_screen
                    if r2 > 1:
                        continue
                    z_screen = math.sqrt(1 - r2)

                    x = x_screen
                    y = -y_screen
                    z = z_screen

                    ca, sa = math.cos(angle), math.sin(angle)
                    x2 = x * ca + z * sa
                    z2 = -x * sa + z * ca
                    y2 = y

                    light = 0.35 + 0.65 * z_screen  # limb darkening

                    if is_land(x2, y2, z2):
                        r = int(40 * light)
                        g = int(200 * light)
                        b = int(80 * light)
                        ch = '▓'
                    else:
                        r = int(20 * light)
                        g = int(80 * light)
                        b = int(180 * light)
                        ch = '░'
                    grid[py][px] = ch
                    colors[py][px] = f"\033[38;2;{r};{g};{b}m"

            out = ["\033[H"]
            for y in range(h):
                row = []
                for x in range(w):
                    if grid[y][x] == ' ':
                        row.append(' ')
                    else:
                        row.append(colors[y][x] + grid[y][x])
                row.append('\033[0m\n')
                out.append(''.join(row))
            deg = math.degrees(angle) % 360
            out.append(f"\033[2K\033[2m 🌍 angle: {deg:3.0f}°   Space — пауза · Q — выход\033[0m")
            sys.stdout.write(''.join(out))
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
