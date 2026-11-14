#!/usr/bin/env python3
"""Снежинка Коха. Ctrl+C — выход."""

import os, sys, time, math

TAU = math.tau
SQ3 = math.sqrt(3) / 2.0


def build_levels():
    """Сегменты (x1,y1,x2,y2) снежинки для глубин 0..4, радиус 1."""
    levels = []
    segs = []
    for d in range(5):
        if d == 0:
            # равносторонний треугольник вершиной вверх, обход против часовой
            ang = (math.pi / 2, math.pi / 2 + TAU / 3, math.pi / 2 + 2 * TAU / 3)
            p = [(math.cos(a), math.sin(a)) for a in ang]
            segs = [(p[i][0], p[i][1], p[(i + 1) % 3][0], p[(i + 1) % 3][1])
                    for i in range(3)]
        else:
            ns = []
            for x1, y1, x2, y2 in segs:
                dx, dy = (x2 - x1) / 3.0, (y2 - y1) / 3.0
                ax, ay = x1 + dx, y1 + dy           # треть отрезка
                bx, by = x1 + 2 * dx, y1 + 2 * dy   # две трети
                # зубец: среднее колено поворачиваем на -60 градусов
                ux, uy = bx - ax, by - ay
                px, py = ax + 0.5 * ux + SQ3 * uy, ay - SQ3 * ux + 0.5 * uy
                ns += [(x1, y1, ax, ay), (ax, ay, px, py),
                       (px, py, bx, by), (bx, by, x2, y2)]
            segs = ns
        levels.append(segs)
    return levels


def hsv(h, v):
    """HSV (s=1) -> RGB: оттенок градиента по углу сегмента."""
    i = int(h * 6.0) % 6
    f = h * 6.0 - int(h * 6.0)
    q, t = v * (1.0 - f), v * f
    r, g, b = ((v, t, 0), (q, v, 0), (0, v, t),
               (0, q, v), (t, 0, v), (v, 0, q))[i]
    return int(r * 255), int(g * 255), int(b * 255)


def bresenham(grid, colr, w, h, x0, y0, x1, y1, rgb):
    """Брезенхэм; цвета соседних точек складываются (нужно для кроссфейда)."""
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if 0 <= x0 < w and 0 <= y0 < h:
            grid[y0][x0] = '·'
            c = colr[y0][x0]
            if c is None:
                colr[y0][x0] = [rgb[0], rgb[1], rgb[2]]
            else:
                colr[y0][x0] = (min(255, c[0] + rgb[0]),
                                min(255, c[1] + rgb[1]),
                                min(255, c[2] + rgb[2]))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def draw_segs(segs, grid, colr, w, h, ang, s, hue_shift, k):
    """Растеризуем сегменты: поворот координат, масштаб, цвет по углу."""
    ca, sa = math.cos(ang), math.sin(ang)
    for x1, y1, x2, y2 in segs:
        rx1, ry1 = x1 * ca - y1 * sa, x1 * sa + y1 * ca
        rx2, ry2 = x2 * ca - y2 * sa, x2 * sa + y2 * ca
        # оттенок по углу сегмента (после поворота) + общий дрейф фазы
        hue = (math.atan2(ry2 - ry1, rx2 - rx1) / TAU + hue_shift) % 1.0
        r, g, b = hsv(hue, 1.0)
        # минус по вертикали: чтобы вершина снежинки смотрела вверх
        bresenham(grid, colr, w, h,
                  int(w / 2 + rx1 * s), int(h / 2 - ry1 * s / 2),
                  int(w / 2 + rx2 * s), int(h / 2 - ry2 * s / 2),
                  (int(r * k), int(g * k), int(b * k)))


def main():
    levels = build_levels()
    cur = 0            # текущая глубина
    prev = 0           # предыдущая (для плавной смены)
    fade = 1.0         # 1.0 -> новая глубина полностью проявлена
    ang = 0.0          # угол вращения всей снежинки
    hue_shift = 0.0    # дрейф палитры
    next_depth = time.monotonic() + 10.0
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

            # каждые ~10 секунд глубина +1, после 4 — сброс на 0
            if now >= next_depth:
                next_depth = now + 10.0
                prev, cur = cur, (cur + 1) % 5
                fade = 0.0
            fade = min(1.0, fade + dt / 1.2)   # плавная смена ~1.2 с
            ang += dt * 0.15                    # медленное вращение
            hue_shift = (hue_shift + dt * 0.02) % 1.0

            # вся снежинка лежит в радиусе 1 от центра (зубцы глубины 1 —
            # ровно на описанной окружности), запас берём небольшим;
            # вертикальная клетка покрывает две мировые единицы
            s = min((w - 6) / 2.3, (h - 3) / 1.15)

            grid = [[' '] * w for _ in range(h)]
            colr = [[None] * w for _ in range(h)]
            if fade < 1.0:
                # старая глубина гаснет, новая проявляется (аддитивно)
                draw_segs(levels[prev], grid, colr, w, h, ang, s,
                          hue_shift, 1.0 - fade)
            draw_segs(levels[cur], grid, colr, w, h, ang, s, hue_shift, fade)

            # подпись текущей глубины в левом верхнем углу
            for i, ch in enumerate("глубина %d" % cur):
                if i < w:
                    grid[0][i] = ch
                    colr[0][i] = [110, 110, 120]

            # кадр ровно по высоте терминала, без \n на последней строке
            out = ["\033[H"]
            for y in range(h):
                row = []
                for x in range(w):
                    c = colr[y][x]
                    row.append(' ' if c is None else
                               "\033[38;2;%d;%d;%dm%s" % (c[0], c[1], c[2],
                                                          grid[y][x]))
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
