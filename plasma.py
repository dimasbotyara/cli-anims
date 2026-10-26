import math, time, sys, os

def main():
    try:
        sz = os.get_terminal_size()
        cols, rows = sz.columns // 2, sz.lines - 1
    except OSError:
        cols, rows = 60, 20

    sys.stdout.write("\033[?25l\033[2J")
    t = 0.0
    try:
        while True:
            buf = []
            for y in range(rows):
                for x in range(cols):
                    v = (math.sin(x * 0.15 + t)
                         + math.sin(y * 0.20 + t * 0.7)
                         + math.sin((x + y) * 0.10 + t * 1.1)
                         + math.sin(math.sqrt(x * x + y * y) * 0.10 - t))
                    v = (v + 4) / 8  # 0..1
                    r = int(127 + 127 * math.sin(v * math.tau))
                    g = int(127 + 127 * math.sin(v * math.tau + 2.094))
                    b = int(127 + 127 * math.sin(v * math.tau + 4.188))
                    buf.append(f"\033[48;2;{r};{g};{b}m  ")
                buf.append("\033[0m\n")
            sys.stdout.write("\033[H" + "".join(buf))
            sys.stdout.flush()
            t += 0.15
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\n")

if __name__ == "__main__":
    main()