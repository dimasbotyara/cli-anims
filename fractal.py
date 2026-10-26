import math, time, sys, os

CX = -0.7436438870371587   # "Seahorse Valley"
CY =  0.1318259042053119

def escape(cre, cim, max_iter):
    zr = zi = 0.0
    for i in range(max_iter):
        zr, zi = zr*zr - zi*zi + cre, 2*zr*zi + cim
        if zr*zr + zi*zi > 4:
            return i
    return max_iter

def main():
    try:
        sz = os.get_terminal_size()
        w, h = sz.columns, sz.lines - 1
    except OSError:
        w, h = 80, 24
    aspect = w / (2 * h)   # символ ~2x выше, чем шире
    zoom = 0.8
    max_iter = 70
    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            scale = 3.0 / zoom
            yr = scale / aspect
            x0, y0 = CX - scale/2, CY - yr/2
            buf = []
            for py in range(h):
                cim = y0 + (py + 0.5) / h * yr
                row = []
                for px in range(w):
                    cre = x0 + (px + 0.5) / w * scale
                    i = escape(cre, cim, max_iter)
                    if i >= max_iter:
                        row.append('\033[48;2;0;0;0m ')
                    else:
                        t = (i / max_iter) * 6.28
                        r = int(127 + 127*math.sin(t))
                        g = int(127 + 127*math.sin(t + 2.09))
                        b = int(127 + 127*math.sin(t + 4.19))
                        row.append(f'\033[48;2;{r};{g};{b}m ')
                buf.append(''.join(row) + '\033[0m\n')
            sys.stdout.write('\033[H' + ''.join(buf))
            sys.stdout.flush()
            zoom *= 1.08
            if zoom > 1e7:
                zoom = 0.8
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')

if __name__ == "__main__":
    main()
