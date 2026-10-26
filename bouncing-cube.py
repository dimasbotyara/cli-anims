#!/usr/bin/env python3
"""2D bouncing ASCII cube. T — trail, G — trajectory, Space — pause, Q — quit."""

import os
import sys
import time

# Размер кубика (в символах). Соотношение ~2:1 для «квадратности» в терминале.
CW, CH = 8, 4
BLOCK = "█"


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


def simulate_bounces(x, y, vx, vy, tw, th, max_bounces=3):
    """Симулируем физику вперёд, возвращаем точки отскока (top-left куба)."""
    bounces = []
    fx, fy = float(x), float(y)
    fvx, fvy = float(vx), float(vy)
    steps = 0
    while len(bounces) < max_bounces and steps < 10000:
        steps += 1
        fx += fvx
        fy += fvy
        bounced = False
        if fx + CW > tw:
            fx = tw - CW - (fx + CW - tw)
            fvx = -fvx
            bounced = True
        elif fx < 0:
            fx = -fx
            fvx = -fvx
            bounced = True
        if fy + CH > th:
            fy = th - CH - (fy + CH - th)
            fvy = -fvy
            bounced = True
        elif fy < 0:
            fy = -fy
            fvy = -fvy
            bounced = True
        if bounced:
            bounces.append((fx, fy))
    return bounces


def draw_dotted(grid, tw, th, x0, y0, x1, y1, color):
    """Брезенхем, но рисуем каждый 3-й пиксель."""
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx, sx = abs(x1 - x0), (1 if x0 < x1 else -1)
    dy, sy = -abs(y1 - y0), (1 if y0 < y1 else -1)
    err = dx + dy
    i = 0
    while True:
        if 0 <= x0 < tw and 0 <= y0 < th and i % 3 == 0:
            grid[y0][x0] = (color, '·')
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy
        i += 1


def main():
    x, y = 20, 10
    vx, vy = 1, 1

    paused = False
    show_trail = True
    show_trajectory = False
    trail = []

    fd = sys.stdin.fileno()
    old = None
    if os.name != 'nt':
        import termios, tty
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)

    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                tw, th = sz.columns, sz.lines - 1
            except OSError:
                tw, th = 80, 24

            if tw < CW + 4 or th < CH + 2:
                sys.stdout.write("\033[H\033[2J")
                sys.stdout.write(f"Терминал слишком маленький (нужно минимум {CW+4}x{CH+2})\n")
                sys.stdout.flush()
                time.sleep(0.5)
                continue

            # клампим на случай ресайза
            x = max(0, min(tw - CW, x))
            y = max(0, min(th - CH, y))

            # --- ввод ---
            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused
            elif k == 't':
                show_trail = not show_trail
                trail.clear()
            elif k == 'g':
                show_trajectory = not show_trajectory

            # --- физика ---
            if not paused:
                if show_trail:
                    trail.append((x, y))
                    if len(trail) > 14:
                        trail.pop(0)

                x += vx
                y += vy

                # отражение от стен (с учётом «перелёта»)
                if x + CW > tw:
                    x = tw - CW - (x + CW - tw)
                    vx = -vx
                elif x < 0:
                    x = -x
                    vx = -vx

                if y + CH > th:
                    y = th - CH - (y + CH - th)
                    vy = -vy
                elif y < 0:
                    y = -y
                    vy = -vy

            # --- рендер ---
            grid = [[(' ', ' ')] * tw for _ in range(th)]

            # 1) trail — fading
            for i, (tx, ty) in enumerate(trail):
                b = int(50 + 130 * (i / max(1, len(trail) - 1)))
                color = f"\033[38;2;{b};{b};{b}m"
                for dy_ in range(CH):
                    for dx_ in range(CW):
                        gx, gy = tx + dx_, ty + dy_
                        if 0 <= gx < tw and 0 <= gy < th:
                            grid[gy][gx] = (color, '·')

            # 2) trajectory — 3 следующих отскока
            if show_trajectory:
                bounces = simulate_bounces(x, y, vx, vy, tw, th, 3)
                cx = x + CW / 2
                cy = y + CH / 2
                for bx, by in bounces:
                    bx2, by2 = bx + CW / 2, by + CH / 2
                    draw_dotted(grid, tw, th, cx, cy, bx2, by2, '\033[2;33m')
                    ix, iy = int(bx2), int(by2)
                    if 0 <= ix < tw and 0 <= iy < th:
                        grid[iy][ix] = ('\033[1;33m', '×')
                    cx, cy = bx2, by2

            # 3) кубик
            for dy_ in range(CH):
                for dx_ in range(CW):
                    gx, gy = x + dx_, y + dy_
                    if 0 <= gx < tw and 0 <= gy < th:
                        edge = (dx_ == 0 or dy_ == 0
                                or dx_ == CW - 1 or dy_ == CH - 1)
                        if edge:
                            grid[gy][gx] = ('\033[1;96m', BLOCK)
                        else:
                            grid[gy][gx] = ('\033[96m', BLOCK)

            # --- вывод ---
            out = ["\033[H"]
            for row in grid:
                buf = []
                for color, ch in row:
                    if ch == ' ':
                        buf.append(' ')
                    else:
                        buf.append(color + ch + '\033[0m')
                out.append(''.join(buf))
                out.append('\n')

            status = (f"Trail: {'ON ' if show_trail else 'OFF'}  ·  "
                      f"Trajectory: {'ON ' if show_trajectory else 'OFF'}  ·  ")
            if paused:
                status += "\033[1;33m[PAUSED]\033[0m"
            else:
                status += "\033[2mT — trail · G — trajectory · Space — pause · Q — quit\033[0m"
            out.append(status)
            sys.stdout.write(''.join(out))
            sys.stdout.flush()
            time.sleep(0.06)
    except KeyboardInterrupt:
        pass
    finally:
        if old is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
