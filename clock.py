#!/usr/bin/env python3
"""Аналоговые часы на braille-точках + цифровое время. Ctrl+C — выход."""

import math
import os
import sys
import time

# биты точек braille: [строка внутри ячейки][столбец]
BRAILLE = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))

DAYS = ('ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС')
MONTHS = ('янв', 'фев', 'мар', 'апр', 'мая', 'июн',
          'июл', 'авг', 'сен', 'окт', 'ноя', 'дек')

DIAL = '\033[38;2;45;75;120m'
TICK_MIN = '\033[38;2;85;125;185m'
TICK_HOUR = '\033[1;38;2;150;195;255m'
HOUR = '\033[1;38;2;0;220;255m'
MINUTE = '\033[1;38;2;255;95;205m'
SECOND = '\033[1;38;2;255;70;70m'
HUB = '\033[1;38;2;255;255;255m'
TIME = '\033[1;38;2;130;230;255m'
DATE = '\033[2;38;2;120;140;175m'


class Braille:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.bits = [0] * (w * h)
        self.prio = [0] * (w * h)
        self.color = [None] * (w * h)

    def plot(self, x, y, prio, color):
        if not (0 <= x < self.w * 2 and 0 <= y < self.h * 4):
            return
        i = (y // 4) * self.w + x // 2
        bit = BRAILLE[y % 4][x % 2]
        if prio >= self.prio[i]:
            self.bits[i] |= bit
            if prio > self.prio[i]:
                self.prio[i] = prio
                self.color[i] = color

    def rows(self):
        out = []
        for y in range(self.h):
            row = []
            for x in range(self.w):
                i = y * self.w + x
                b = self.bits[i]
                row.append((chr(0x2800 + b) if b else ' ', self.color[i]))
            out.append(row)
        return out


def draw_hand(cv, cx, cy, ang, length, prio, color, width=1, dashed=False):
    steps = max(2, int(length * 2))
    step = 2 if dashed else 1
    for s in range(1, steps + 1, step):
        rr = s / 2
        x = int(round(cx + math.cos(ang) * rr))
        y = int(round(cy + math.sin(ang) * rr))
        cv.plot(x, y, prio, color)
        if width > 1:
            cv.plot(x + 1, y, prio, color)


def overlay(row, text, color_fn):
    start = (len(row) - len(text)) // 2
    for i, ch in enumerate(text):
        if 0 <= start + i < len(row):
            row[start + i] = (ch, color_fn(i))


def render(w, h):
    now = time.time()
    lt = time.localtime(now)

    if h >= 10:
        text_rows = 2
    elif h >= 5:
        text_rows = 1
    else:
        text_rows = 0
    ph = max(2, h - text_rows)

    cv = Braille(w, ph)
    W, H = w * 2, ph * 4
    cx, cy = W // 2, H // 2
    R = max(4, int(min(W, H) * 0.44))

    # циферблат
    for dr in (0, 1, 2):
        rr = R - dr
        for k in range(720):
            a = k / 720 * math.tau
            cv.plot(int(round(cx + math.cos(a) * rr)),
                    int(round(cy + math.sin(a) * rr)), 1, DIAL)

    # минутные и часовые деления
    for m in range(60):
        a = m / 60 * math.tau - math.pi / 2
        long_tick = (m % 5 == 0)
        depth = 5 if long_tick else 3
        color = TICK_HOUR if long_tick else TICK_MIN
        for rr in range(R - depth, R - 2):
            cv.plot(int(round(cx + math.cos(a) * rr)),
                    int(round(cy + math.sin(a) * rr)),
                    2, color)

    frac = now % 60
    a_sec = frac / 60 * math.tau - math.pi / 2
    a_min = (lt.tm_min + frac / 60) / 60 * math.tau - math.pi / 2
    a_hour = ((lt.tm_hour % 12) + lt.tm_min / 60 + frac / 3600) / 12 * math.tau - math.pi / 2

    draw_hand(cv, cx, cy, a_hour, R * 0.50, 3, HOUR, width=2)
    draw_hand(cv, cx, cy, a_min, R * 0.74, 4, MINUTE)
    draw_hand(cv, cx, cy, a_sec + math.pi, R * 0.16, 5, SECOND, dashed=True)
    draw_hand(cv, cx, cy, a_sec, R * 0.86, 5, SECOND, dashed=True)

    # ось
    for dx in (0, 1):
        for dy in (0, 1):
            cv.plot(cx + dx, cy + dy, 6, HUB)

    rows = cv.rows()

    time_s = f"{lt.tm_hour:02d}:{lt.tm_min:02d}:{lt.tm_sec:02d}"
    date_s = f"{DAYS[lt.tm_wday]} {lt.tm_mday:02d} {MONTHS[lt.tm_mon - 1]} {lt.tm_year}"

    def time_color(i):
        if time_s[i] == ':':
            if lt.tm_sec % 2 == 0:
                return '\033[1;38;2;255;215;80m'
            return '\033[2;38;2;110;95;40m'
        return TIME

    if text_rows == 2:
        date_row = [(' ', None)] * w
        time_row = [(' ', None)] * w
        overlay(date_row, date_s, lambda i: DATE)
        overlay(time_row, time_s, time_color)
        rows.append(date_row)
        rows.append(time_row)
    elif text_rows == 1:
        time_row = [(' ', None)] * w
        overlay(time_row, time_s, time_color)
        rows.append(time_row)

    out = []
    for row in rows:
        cur = None
        parts = []
        for ch, c in row:
            if c != cur:
                parts.append('\033[0m' if c is None else c)
                cur = c
            parts.append(ch)
        parts.append('\033[0m')
        out.append(''.join(parts))
    return '\033[H' + '\n'.join(out) + '\n'


def main():
    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            w = max(24, w)
            h = max(8, h)
            sys.stdout.write(render(w, h))
            sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')


if __name__ == '__main__':
    main()
