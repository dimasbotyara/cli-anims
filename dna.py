import math, time, sys, os

def main():
    try:
        sz = os.get_terminal_size()
        w, h = sz.columns, sz.lines - 1
    except OSError:
        w, h = 80, 24

    cx = w // 2
    amp = max(1, w // 2 - 3)
    cycles = 3
    chars = "ATGC"
    frame = 0

    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            grid = [[' '] * w for _ in range(h)]
            col = [[None] * w for _ in range(h)]
            for y in range(h):
                phase = (y * cycles / h) * math.tau + frame * 0.08
                x1 = int(cx + math.sin(phase) * amp)
                x2 = int(cx + math.sin(phase + math.pi) * amp)
                d1 = math.cos(phase)
                d2 = -d1  # cos(phase+π) = -cos(phase)

                if 0 <= x1 < w:
                    c = '\033[1;92m' if d1 > 0.3 else ('\033[92m' if d1 > -0.3 else '\033[2;32m')
                    grid[y][x1] = chars[(y + frame) % 4]
                    col[y][x1] = c
                if 0 <= x2 < w:
                    c = '\033[1;96m' if d2 > 0.3 else ('\033[96m' if d2 > -0.3 else '\033[2;36m')
                    grid[y][x2] = chars[(y + frame + 2) % 4]
                    col[y][x2] = c

                lo, hi = min(x1, x2), max(x1, x2)
                for x in range(lo + 1, hi):
                    if 0 <= x < w and grid[y][x] == ' ':
                        grid[y][x] = '-'
                        col[y][x] = '\033[2;90m'

            buf = []
            for y in range(h):
                for x in range(w):
                    c = col[y][x]
                    buf.append((c if c else '') + grid[y][x])
                buf.append('\033[0m\n')
            sys.stdout.write('\033[H' + ''.join(buf))
            sys.stdout.flush()
            frame += 1
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')

if __name__ == "__main__":
    main()