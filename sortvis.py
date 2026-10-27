#!/usr/bin/env python3
"""Sorting visualizer. 1-5 — алгоритм, R — перемешать, Space — пауза, Q — выход."""

import os, sys, math, random, time

ALGOS = ['bubble', 'insertion', 'selection', 'quick', 'merge']


def read_key():
    if os.name == 'nt':
        import msvcrt
        if not msvcrt.kbhit():
            return None
        return msvcrt.getwch().lower()
    import select
    fd = sys.stdin.fileno()
    if not select.select([fd], [], [], 0)[0]:
        return None
    data = os.read(fd, 32)
    return chr(data[0]).lower() if data else None


def gen(n):
    return [random.randint(1, 99) for _ in range(n)]


def bubble(a):
    n = len(a)
    for i in range(n):
        for j in range(n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
            yield (j, j + 1)


def insertion(a):
    for i in range(1, len(a)):
        j = i
        while j > 0 and a[j - 1] > a[j]:
            a[j - 1], a[j] = a[j], a[j - 1]
            yield (j - 1, j)
            j -= 1


def selection(a):
    n = len(a)
    for i in range(n):
        m = i
        for j in range(i + 1, n):
            if a[j] < a[m]:
                m = j
        if m != i:
            a[i], a[m] = a[m], a[i]
        yield (i, m)


def quick(a):
    stack = [(0, len(a) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        p = a[(lo + hi) // 2]
        i, j = lo, hi
        while i <= j:
            while a[i] < p:
                i += 1
            while a[j] > p:
                j -= 1
            if i <= j:
                a[i], a[j] = a[j], a[i]
                yield (i, j)
                i += 1
                j -= 1
        if lo < j:
            stack.append((lo, j))
        if i < hi:
            stack.append((i, hi))


def merge(a):
    def _m(lo, hi):
        if hi - lo < 1:
            return
        mid = (lo + hi) // 2
        yield from _m(lo, mid)
        yield from _m(mid + 1, hi)
        left = a[lo:mid + 1]
        right = a[mid + 1:hi + 1]
        i = j = 0
        k = lo
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                a[k] = left[i]; i += 1
            else:
                a[k] = right[j]; j += 1
            yield (k, k)
            k += 1
        while i < len(left):
            a[k] = left[i]; i += 1; k += 1
            yield (k - 1, k - 1)
        while j < len(right):
            a[k] = right[j]; j += 1; k += 1
            yield (k - 1, k - 1)
    yield from _m(0, len(a) - 1)


FUNCS = {'bubble': bubble, 'insertion': insertion,
         'selection': selection, 'quick': quick, 'merge': merge}


def color_for(v):
    t = v / 100.0
    r = int(127 + 128 * math.sin(t * math.tau))
    g = int(127 + 128 * math.sin(t * math.tau + 2.094))
    b = int(127 + 128 * math.sin(t * math.tau + 4.188))
    return f"\033[38;2;{r};{g};{b}m"


def main():
    fd = sys.stdin.fileno()
    old = None
    if os.name != 'nt':
        import termios, tty
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    sys.stdout.write("\033[?25l\033[2J")

    w, h = 80, 22
    algo = 'bubble'
    arr = gen(w - 2)
    gen_ = None
    paused = False
    swaps = 0
    done = False

    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 2
            except OSError:
                pass
            if len(arr) != w - 2:
                arr = gen(w - 2)
                gen_ = None
                done = False

            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused
            elif k == 'r':
                arr = gen(w - 2); gen_ = None; swaps = 0; done = False
            elif k and k.isdigit() and 1 <= int(k) <= len(ALGOS):
                algo = ALGOS[int(k) - 1]
                arr = gen(w - 2); gen_ = None; swaps = 0; done = False

            if not paused and not done:
                if gen_ is None:
                    gen_ = FUNCS[algo](arr)
                for _ in range(4):
                    try:
                        next(gen_)
                        swaps += 1
                    except StopIteration:
                        done = True
                        break

            max_v = max(arr) if arr else 1
            out = ["\033[H"]
            for y in range(h):
                threshold = (h - y) * max_v / h
                row = []
                for v in arr:
                    if v >= threshold:
                        row.append(color_for(v) + '█')
                    else:
                        row.append(' ')
                row.append('\033[0m\n')
                out.append(''.join(row))

            status = f" {algo.upper():<9}  swaps: {swaps:5d}  "
            if done:
                status += "\033[1;32mDONE\033[0m  "
            if paused:
                status += "\033[1;33mPAUSED\033[0m  "
            status += "\033[2m[1-5 algo · R shuffle · Space pause · Q quit]\033[0m"
            out.append("\033[2K" + status)
            sys.stdout.write(''.join(out))
            sys.stdout.flush()
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        if old is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
