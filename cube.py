import math, time, sys, os

W, H = 80, 30
DIST = 4.0

def rotate(p, ax, ay):
    x, y, z = p
    cy, sy = math.cos(ay), math.sin(ay)
    x, z = x * cy + z * sy, -x * sy + z * cy
    cx, sx = math.cos(ax), math.sin(ax)
    y, z = y * cx - z * sx, y * sx + z * cx
    return x, y, z

def line(g, x0, y0, x1, y1, ch='#'):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx, sx = abs(x1 - x0), (1 if x0 < x1 else -1)
    dy, sy = -abs(y1 - y0), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        if 0 <= x0 < W and 0 <= y0 < H:
            g[y0 * W + x0] = ch
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy

def main():
    global W, H
    try:
        sz = os.get_terminal_size()
        W, H = sz.columns, sz.lines - 1
    except OSError:
        pass

    verts = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
             (-1,-1, 1),(1,-1, 1),(1,1, 1),(-1,1, 1)]
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
             (0,4),(1,5),(2,6),(3,7)]

    scale = min(W, H * 2) * 0.35
    ax, ay = 0.0, 0.0
    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            grid = [' '] * (W * H)
            proj = []
            for v in verts:
                x, y, z = rotate(v, ax, ay)
                f = DIST / (DIST + z)
                proj.append((W / 2 + x * f * scale,
                             H / 2 - y * f * scale * 0.5))
            for a, b in edges:
                line(grid, *proj[a], *proj[b])
            sys.stdout.write("\033[H" + "\n".join(
                "".join(grid[y*W:(y+1)*W]) for y in range(H)))
            sys.stdout.flush()
            ax += 0.04
            ay += 0.07
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\n")

if __name__ == "__main__":
    main()