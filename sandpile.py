#!/usr/bin/env python3
"""Абелева песочница. Ctrl+C — выход."""

import os, sys, time, random

TOPPLE_LIMIT = 4000   # максимум осыпаний за один кадр
FLASH_TIME = 1.5      # сколько секунд горит табло AVALANCHE!


class Sandpile:
    def __init__(self, w, h):
        # нечётное поле, вписанное в терминал (последняя строка — статус)
        fw = max(3, min(w - 2, 121))
        if fw % 2 == 0:
            fw -= 1
        fh = max(3, h - 2)
        if fh % 2 == 0:
            fh -= 1
        self.fw, self.fh = fw, fh
        self.w, self.h = w, h
        self.field = [[0] * fw for _ in range(fh)]
        self.unstable = set()      # клетки с >=4 зёрнами
        self.grains = 0            # всего брошено зёрен
        self.topples = 0           # всего осыпаний
        self.aval = 0              # осыпаний в текущей лавинной серии
        self.last_aval = 0         # размер последней серии (для табло)
        self.flash_until = 0.0

    def drop(self):
        # раз в кадр зерно в центр; изредка — целая горсть
        n = random.randint(3, 5) if random.random() < 0.08 else 1
        cx, cy = self.fw // 2, self.fh // 2
        f = self.field
        for _ in range(n):
            f[cy][cx] += 1
            self.grains += 1
            if f[cy][cx] >= 4:
                self.unstable.add((cx, cy))

    def topple(self):
        # осыпание: клетка с >=4 зёрнами раздаёт по одному четырём соседям;
        # зёрна за границей поля поглощаются; итерации ограничены кадром
        f, un = self.field, self.unstable
        done = 0
        while un and done < TOPPLE_LIMIT:
            x, y = un.pop()
            v = f[y][x]
            if v < 4:
                continue
            f[y][x] = v - 4
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.fw and 0 <= ny < self.fh:
                    nv = f[ny][nx] + 1
                    f[ny][nx] = nv
                    if nv >= 4:
                        un.add((nx, ny))
            if f[y][x] >= 4:
                un.add((x, y))
            done += 1
        self.topples += done
        self.aval += done
        if done > 50:
            self.flash_until = time.monotonic() + FLASH_TIME
        if not un:                 # серия закончилась
            if self.aval > 0:
                self.last_aval = self.aval
            self.aval = 0
        return done

    def _status(self, w):
        """Статусная строка: счётчики и табло AVALANCHE! (мигает)."""
        now = time.monotonic()
        txt = [("\033[38;2;120;120;135m", "зёрен: "),
               ("\033[38;2;220;220;225m", str(self.grains)),
               ("\033[38;2;120;120;135m", "   оползаний: "),
               ("\033[38;2;220;220;225m", str(self.topples))]
        active = bool(self.unstable)
        if (active and self.aval > 50) or now < self.flash_until:
            n = self.aval if active else self.last_aval
            # мигание между красным и жёлтым — «вспышка»
            if int(now * 8.0) % 2:
                c = "\033[1;38;2;255;90;45m"
            else:
                c = "\033[1;38;2;255;225;110m"
            txt.append((c, "   ⚠ AVALANCHE! ×%d" % n))
        out = []
        col = 0
        for c, s in txt:
            for ch in s:
                if col >= w:
                    break
                out.append(c + ch)
                col += 1
        return "".join(out)

    def draw(self):
        w, h = self.w, self.h
        grid = [[' '] * w for _ in range(h)]
        colr = [[None] * w for _ in range(h)]
        ox = (w - self.fw) // 2
        oy = max(0, (h - 1 - self.fh) // 2)
        # классические цвета: 1 зелёный, 2 жёлтый, 3 красный, >=4 белая пыль
        colors = ("\033[38;2;70;200;85m", "\033[38;2;240;215;60m",
                  "\033[38;2;235;75;60m", "\033[38;2;255;255;255m")
        chars = ('▒', '▓', '█', '█')
        f = self.field
        for y in range(self.fh):
            src, gout, cout = f[y], grid[y + oy], colr[y + oy]
            for x in range(self.fw):
                v = src[x]
                if v:
                    i = 3 if v > 3 else v - 1
                    gout[x + ox] = chars[i]
                    cout[x + ox] = colors[i]

        # кадр: поле + статусная строка последней строкой, без \n в конце
        out = ["\033[H"]
        for y in range(h - 1):
            row = []
            gout, cout = grid[y], colr[y]
            for x in range(w):
                c = cout[x]
                row.append(' ' if c is None else c + gout[x])
            row.append("\033[0m\033[K")
            out.append("".join(row))
            out.append("\n")
        out.append(self._status(w) + "\033[0m\033[K")
        return "".join(out)


def main():
    last = time.monotonic()
    size = None
    sp = None
    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            now = time.monotonic()
            last = now
            try:
                sz = os.get_terminal_size()
                w, h = max(5, sz.columns), max(3, sz.lines)
            except OSError:
                w, h = 80, 24
            if (w, h) != size or sp is None:
                # пересоздаём кучу под новый размер терминала
                sp = Sandpile(w, h)
                size = (w, h)
                sys.stdout.write("\033[2J")
            sp.drop()
            sp.topple()
            sys.stdout.write(sp.draw())
            sys.stdout.flush()
            time.sleep(0.035)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
