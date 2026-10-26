import math, time, sys

def main():
    w, h = 80, 22  # фиксированный размер как в оригинале
    zbuf = [0.0] * (w * h)
    buf = [' '] * (w * h)
    A = B = 0.0
    ramp = ".,-~:;=!*#$@"

    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            for i in range(w * h):
                buf[i] = ' '
                zbuf[i] = 0.0

            j = 0.0
            while j < math.tau:
                i_ = 0.0
                while i_ < math.tau:
                    c = math.sin(i_);  d = math.cos(j)
                    e = math.sin(A);   f = math.sin(j); g = math.cos(A)
                    hh = d + 2
                    D = 1.0 / (c * hh * e + f * g + 5)
                    l = math.cos(i_); m = math.cos(B); n = math.sin(B)
                    t = c * hh * g - f * e
                    x = int(40 + 30 * D * (l * hh * m - t * n))
                    y = int(12 + 15 * D * (l * hh * n + t * m))
                    o = x + w * y
                    N = int(8 * ((f * e - c * d * g) * m - c * d * e - f * g - l * d * n))
                    if 0 <= x < w and 0 <= y < h and 0 <= o < w * h and D > zbuf[o]:
                        zbuf[o] = D
                        buf[o] = ramp[max(0, min(len(ramp) - 1, N))]
                    i_ += 0.02
                j += 0.07

            out = []
            for k in range(h):
                out.append(''.join(buf[k*w:(k+1)*w]))
                out.append('\n')
            sys.stdout.write('\033[H' + ''.join(out))
            sys.stdout.flush()
            A += 0.04
            B += 0.02
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')

if __name__ == "__main__":
    main()