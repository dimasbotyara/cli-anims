import random, time, sys, os

PALETTE = [
    (7,7,7),(31,7,7),(47,15,7),(71,15,7),(87,23,7),(103,31,7),
    (119,31,7),(143,39,7),(159,47,7),(175,63,7),(191,71,7),(199,71,7),
    (223,79,7),(223,87,7),(223,87,7),(215,95,7),(215,95,7),(215,103,15),
    (207,111,15),(207,119,15),(207,127,15),(207,135,23),(199,135,23),
    (199,143,23),(199,151,31),(191,159,31),(191,159,31),(191,167,39),
    (191,167,39),(191,175,47),(183,175,47),(183,183,47),(183,183,55),
    (207,207,111),(223,223,159),(239,239,199),(255,255,255),
]
MAX = len(PALETTE) - 1

def main():
    try:
        sz = os.get_terminal_size()
        w, h = sz.columns, sz.lines - 1
    except OSError:
        w, h = 80, 24

    fire = [0] * (w * h)
    for x in range(w):
        fire[(h - 1) * w + x] = MAX  # нижний ряд — источник

    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            for y in range(1, h):
                for x in range(w):
                    val = fire[y * w + x]
                    if val == 0:
                        fire[(y - 1) * w + x] = 0
                        continue
                    r = random.randint(0, 3)
                    dst_x = max(0, min(w - 1, x - r + 1))
                    decay = random.randint(1, 2)
                    fire[(y - 1) * w + dst_x] = max(0, val - decay)

            buf = []
            for y in range(h):
                for x in range(w):
                    r, g, b = PALETTE[fire[y * w + x]]
                    buf.append(f"\033[48;2;{r};{g};{b}m ")
                buf.append("\033[0m\n")
            sys.stdout.write("\033[H" + "".join(buf))
            sys.stdout.flush()
            time.sleep(0.045)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\n")

if __name__ == "__main__":
    main()