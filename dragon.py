#!/usr/bin/env python3
"""Кривая дракона. Ctrl+C — выход."""

import os, sys, time

MAX_DEPTH = 13      # предельная глубина, после неё сброс
STEP_TIME = 8.0     # секунд на одну глубину


def grow(seq):
    """Поколение поворотов: seq + R + зеркальный реверс seq."""
    return seq + ['R'] + ['L' if c == 'R' else 'R' for c in reversed(seq)]


def walk(seq):
    """Черепашка: проходим повороты, возвращаем мировые точки."""
    # 0=вправо, 1=вниз, 2=влево, 3=вверх
    dxs, dys = (1, 0, -1, 0), (0, 1, 0, -1)
    x = y = head = 0
    pts = [(0, 0)]
    for t in seq:
        head = (head + (1 if t == 'R' else -1)) % 4
        x += dxs[head]
        y += dys[head]
        pts.append((x, y))
    return pts


def bounds(pts):
    """Габариты кривой: (x0, y0, ширина, высота)."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, y0 = min(xs), min(ys)
    return x0, y0, max(1, max(xs) - x0), max(1, max(ys) - y0)


def hsv(h, v):
    """HSV (s=1) -> RGB: оттенок для градиента по длине кривой."""
    i = int(h * 6.0) % 6
    f = h * 6.0 - int(h * 6.0)
    q, t = v * (1.0 - f), v * f
    r, g, b = ((v, t, 0), (q, v, 0), (0, v, t),
               (0, q, v), (t, 0, v), (v, 0, q))[i]
    return int(r * 255), int(g * 255), int(b * 255)


def main():
    # стартовая глубина: дракон сразу заметен, дальше растёт до предела
    depth = 5
    seq = []
    for _ in range(depth):
        seq = grow(seq)
    pts = walk(seq)
    bx0, by0, bw, bh = bounds(pts)
    flash = 0.0        # вспышка на переходе между глубинами
    phase = 0.0        # медленное вращение оттенка
    next_step = time.monotonic() + STEP_TIME
    last = time.monotonic()
    size = None
    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            now = time.monotonic()
            dt = min(0.1, now - last)
            last = now

            # размер терминала; при изменении перерисовываем с очисткой
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines
            except OSError:
                w, h = 80, 24
            if (w, h) != size:
                size = (w, h)
                sys.stdout.write("\033[2J")

            # каждые ~8 секунд — следующая глубина, на переходе вспышка
            if now >= next_step:
                next_step = now + STEP_TIME
                depth += 1
                if depth > MAX_DEPTH:
                    depth = 1
                    seq = ['R']
                else:
                    seq = grow(seq)
                pts = walk(seq)
                bx0, by0, bw, bh = bounds(pts)
                flash = 1.0

            flash *= 0.80
            phase = (phase + dt * 0.06) % 1.0

            # масштаб под терминал; аспект символов 1:2 — вертикальная
            # клетка покрывает две мировые единицы (шаг по вертикали x2)
            s = min((w - 6) / bw, 2.0 * (h - 4) / bh)
            ox = (w - bw * s) / 2.0 - bx0 * s
            oy = (h - bh * s / 2.0) / 2.0 - by0 * s / 2.0

            # палитра кадра: градиент по длине кривой + вспышка к белому
            n = len(pts)
            pal = []
            for j in range(256):
                r, g, b = hsv(((j / 255.0) * 0.85 + phase) % 1.0,
                              0.45 + 0.55 * j / 255.0)
                if flash > 0.01:
                    r = int(r + (255 - r) * flash)
                    g = int(g + (255 - g) * flash)
                    b = int(b + (255 - b) * flash)
                pal.append("\033[38;2;%d;%d;%dm" % (r, g, b))

            grid = [[' '] * w for _ in range(h)]
            colr = [[None] * w for _ in range(h)]
            # ячейки всех точек кривой
            cells = [(int(px * s + ox), int(py * s / 2.0 + oy))
                     for px, py in pts]
            # шаг черепашки всегда по одной оси — заполняем отрезки целиком,
            # чтобы кривая выглядела непрерывной при любом масштабе
            for i in range(1, n):
                x0, y0 = cells[i - 1]
                x1, y1 = cells[i]
                c = pal[int(i * 255.0 / (n - 1))]
                if y0 == y1:
                    for x in range(min(x0, x1), max(x0, x1) + 1):
                        if 0 <= x < w and 0 <= y0 < h:
                            grid[y0][x] = '*'
                            colr[y0][x] = c
                else:
                    for y in range(min(y0, y1), max(y0, y1) + 1):
                        if 0 <= x0 < w and 0 <= y < h:
                            grid[y][x0] = '*'
                            colr[y][x0] = c

            # подпись текущей глубины в левом верхнем углу
            dim = "\033[38;2;110;110;120m"
            for i, ch in enumerate("глубина %d/%d" % (depth, MAX_DEPTH)):
                if i < w:
                    grid[0][i] = ch
                    colr[0][i] = dim

            # кадр ровно по высоте терминала, без \n на последней строке
            out = ["\033[H"]
            for y in range(h):
                row = []
                for x in range(w):
                    c = colr[y][x]
                    row.append(' ' if c is None else c + grid[y][x])
                row.append("\033[0m\033[K")
                out.append("".join(row))
                if y < h - 1:
                    out.append("\n")
            sys.stdout.write("".join(out))
            sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
