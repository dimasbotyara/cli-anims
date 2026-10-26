import math, random, time, sys, os

def main():
    try:
        sz = os.get_terminal_size()
        w, h = sz.columns, sz.lines - 1
    except OSError:
        w, h = 80, 24
    cx, cy = w / 2, h / 2

    N = 220
    stars = [[random.uniform(-1, 1), random.uniform(-1, 1),
              random.uniform(0.05, 1.0)] for _ in range(N)]

    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            buf = [[' '] * w for _ in range(h)]
            col = [[None] * w for _ in range(h)]

            for s in stars:
                x, y, z = s
                px = int(cx + (x / z) * cx * 0.55)
                py = int(cy + (y / z) * cy * 0.55)

                if z < 0.25:
                    c, ch = '\033[1;97m', '@'
                elif z < 0.45:
                    c, ch = '\033[1;37m', '*'
                elif z < 0.7:
                    c, ch = '\033[37m', '+'
                else:
                    c, ch = '\033[2;37m', '.'

                if 0 <= px < w and 0 <= py < h:
                    buf[py][px] = ch
                    col[py][px] = c

                s[2] -= 0.025
                if s[2] <= 0.03:
                    s[0] = random.uniform(-1, 1)
                    s[1] = random.uniform(-1, 1)
                    s[2] = 1.0

            out = []
            for y in range(h):
                for x in range(w):
                    c = col[y][x]
                    out.append((c or '') + buf[y][x])
                out.append('\033[0m\n')
            sys.stdout.write('\033[H' + ''.join(out))
            sys.stdout.flush()
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')

if __name__ == "__main__":
    main()