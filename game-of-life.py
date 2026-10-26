import random, time, sys, os

LIVE = '\033[1;92m#'
DEAD = '\033[2;90m.'

def new_grid(w, h):
    return [[random.random() < 0.3 for _ in range(w)] for _ in range(h)]

def step(grid, w, h):
    new = [[False] * w for _ in range(h)]
    pop = 0
    for y in range(h):
        row = grid[y]
        for x in range(w):
            n = 0
            for dy in (-1, 0, 1):
                ny = (y + dy) % h
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    n += grid[ny][(x + dx) % w]
            alive = row[x]
            new[y][x] = (n in (2, 3)) if alive else (n == 3)
            pop += new[y][x]
    return new, pop

def main():
    try:
        sz = os.get_terminal_size()
        w, h = sz.columns, sz.lines - 1
    except OSError:
        w, h = 80, 24

    grid = new_grid(w, h)
    gen = 0

    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            buf = []
            for y in range(h):
                row = grid[y]
                buf.append(''.join(LIVE if c else DEAD for c in row))
                buf.append('\033[0m\n')
            header = f" Life — gen {gen} "
            sys.stdout.write('\033[H' + header + ' ' * max(0, w - len(header)) + '\n')
            sys.stdout.write(''.join(buf[:h - 1]))
            sys.stdout.flush()

            grid, pop = step(grid, w, h)
            gen += 1

            if pop == 0 or pop == w * h or gen % 200 == 0:
                grid = new_grid(w, h)
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')

if __name__ == "__main__":
    main()