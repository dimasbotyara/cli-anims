import math, random, time, sys, os

def main():
    try:
        sz = os.get_terminal_size()
        w, h = sz.columns, sz.lines - 1
    except OSError:
        w, h = 80, 24
    chars = ['.', '*', '+', '·']
    flakes = []
    for _ in range(180):
        flakes.append([
            random.uniform(0, w), random.uniform(0, h),
            random.uniform(0.3, 2.0), random.uniform(0, 6.28),
            random.choice(chars),
        ])
    t = 0.0
    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            grid = [[' ']*w for _ in range(h)]
            col  = [[None]*w for _ in range(h)]
            for f in flakes:
                f[1] += f[2] * 0.2
                f[0] += math.sin(t + f[3]) * 0.4
                if f[1] >= h:
                    f[1] = -0.5
                    f[0] = random.uniform(0, w)
                if f[0] < 0:    f[0] += w
                elif f[0] >= w: f[0] -= w
                px, py = int(f[0]), int(f[1])
                if 0 <= px < w and 0 <= py < h:
                    b = 180 + int(75 * (f[2] / 2.0))
                    grid[py][px] = f[4]
                    col[py][px]  = f"\033[38;2;{b};{b};{b}m"
            out = ["\033[H"]
            for y in range(h):
                row = []
                for x in range(w):
                    c = col[y][x]
                    row.append((c or '') + grid[y][x])
                out.append(''.join(row) + '\033[0m\n')
            sys.stdout.write(''.join(out))
            sys.stdout.flush()
            t += 0.1
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')

if __name__ == "__main__":
    main()
