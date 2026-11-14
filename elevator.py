#!/usr/bin/env python3
"""Elevator — самоиграющие лифты (SCAN). Space — пауза, Q — выход."""

import os, sys, random, time

FRAME = 0.05        # длительность кадра
MOVE_EVERY = 2      # тик механики лифтов каждые N кадров
DOOR_TICKS = 5      # сколько тиков двери остаются открытыми
CAP = 4             # вместимость кабины
LIFT_COLORS = ((80, 220, 255), (255, 170, 80))
SHAFT_DIM = (95, 105, 135)


def rgb(c, bold=False):
    return f"\033[{'1;' if bold else ''}38;2;{c[0]};{c[1]};{c[2]}m"


def read_key():
    """Неблокирующее чтение клавиши; None, если нажатий нет."""
    try:
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
    except Exception:
        return None          # stdin не tty или закрыт — играем без клавиш


class Lift:
    def __init__(self, idx):
        self.idx = idx
        self.pos = 0
        self.dir = 1          # +1 вверх, -1 вниз: SCAN держит курс до упора
        self.door = 0         # тиков до закрытия дверей (0 — закрыты)
        self.pax = []         # этажи назначения пассажиров в кабине


class Building:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.floors = max(5, min(10, h - 1))   # этажи + статус-строка
        self.corridor = max(0, w - 14)         # место для ожидающих справа
        self.waiting = [[] for _ in range(self.floors)]   # (куда, кадр прихода)
        self.lifts = [Lift(0), Lift(1)]
        self.lifts[0].pos = 0
        self.lifts[1].pos = self.floors - 1
        self.lifts[1].dir = -1
        self.transported = 0
        self.boarded = 0
        self.total_wait = 0.0
        self.frame = 0

    # --- логика ---
    def targets(self, lift):
        """Этажи-цели: назначения пассажиров в кабине + ожидающие (если есть место)."""
        t = set(lift.pax)
        if len(lift.pax) < CAP:
            for f in range(self.floors):
                if self.waiting[f]:
                    t.add(f)
        return t

    def service(self, lift):
        """Высадка мгновенно, посадка — по одному пассажиру за тик."""
        staying = [d for d in lift.pax if d != lift.pos]
        self.transported += len(lift.pax) - len(staying)
        lift.pax = staying
        q = self.waiting[lift.pos]
        if q and lift.door > 0 and len(lift.pax) < CAP:
            dest, born = q.pop(0)
            # ожидание в секундах: тик механики = MOVE_EVERY кадров
            self.total_wait += (self.frame - born) * MOVE_EVERY * FRAME
            self.boarded += 1
            lift.pax.append(dest)

    def step_lift(self, lift):
        if lift.door > 0:                  # двери открыты — обслуживаем этаж
            lift.door -= 1
            self.service(lift)
            return
        want_off = lift.pos in lift.pax    # кому здесь выходить
        want_on = bool(self.waiting[lift.pos]) and len(lift.pax) < CAP
        if want_off or want_on:
            lift.door = DOOR_TICKS         # скобки раскрываются
            self.service(lift)
            return
        # SCAN: продолжаем курс; разворот — только когда впереди целей нет
        t = self.targets(lift)
        ahead = [x for x in t if (x - lift.pos) * lift.dir > 0]
        if ahead:
            lift.pos += lift.dir
        elif t:
            lift.dir = -lift.dir
            lift.pos += lift.dir
        lift.pos = max(0, min(self.floors - 1, lift.pos))

    def maybe_spawn(self):
        """Пассажир приходит на случайный этаж со случайным «куда»."""
        if random.random() >= 0.05:
            return
        f = random.randrange(self.floors)
        cap = max(1, self.corridor // 2 - 1)
        if len(self.waiting[f]) < cap:
            d = random.randrange(self.floors - 1)
            if d >= f:
                d += 1                     # «куда» не равно «откуда»
            self.waiting[f].append((d, self.frame))

    def update(self):
        self.frame += 1
        self.maybe_spawn()
        if self.frame % MOVE_EVERY:
            return
        for lift in self.lifts:
            self.step_lift(lift)

    # --- отрисовка ---
    def draw(self):
        out = ['\033[H']
        dim = rgb(SHAFT_DIM)
        for f in range(self.floors - 1, -1, -1):   # вид сбоку, сверху вниз
            row = [f"{f:>2} "]
            for lift in self.lifts:
                if lift.pos == f:
                    col = rgb(LIFT_COLORS[lift.idx], True)
                    mid = '█' + str(min(9, len(lift.pax)))   # кабина и пассажиры
                    if lift.door:
                        row.append(col + f' {mid} ')         # двери открыты
                    else:
                        row.append(col + f'[{mid}]')         # двери закрыты
                else:
                    row.append(dim + '[  ]')                 # пустая шахта
            row.append('│')
            # ожидающие пассажиры: цвет — направление их «куда»
            shown = self.waiting[f][:self.corridor // 2]
            for dest, _born in shown:
                c = (95, 235, 130) if dest > f else (255, 115, 115)
                row.append(rgb(c, True) + 'i ')
            out.append(''.join(row) + '\033[0m\033[K\n')
        # статусная строка: перевезено, среднее ожидание, состояние лифтов
        avg = self.total_wait / self.boarded if self.boarded else 0.0
        info = '  '.join(
            f"Л{i + 1}: эт.{l.pos}{'↑' if l.dir > 0 else '↓'}"
            + (f' {len(l.pax)}чел' if l.pax else '')
            + (' двери' if l.door else '')
            for i, l in enumerate(self.lifts))
        line = f" Перевезено: {self.transported} · Ср. ожидание: {avg:.1f}с · {info}"
        out.append('\033[2m' + line[:self.w] + '\033[0m\033[K\n')
        return ''.join(out)


def main():
    fd = sys.stdin.fileno()
    old = None
    if os.name != 'nt':
        try:                             # stdin не tty — работаем без клавиш
            import termios, tty
            old = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            old = None
    sys.stdout.write("\033[?25l\033[2J")
    scene = None
    last_size = None
    paused = False
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = sz.columns, sz.lines - 1
            except OSError:
                w, h = 80, 24
            if (w, h) != last_size or scene is None:
                scene = Building(w, h)   # пересоздаём сцену при resize
                last_size = (w, h)
            k = read_key()
            if k == 'q':
                break
            if k == ' ':
                paused = not paused
            if not paused:
                scene.update()
            sys.stdout.write(scene.draw())
            sys.stdout.flush()
            time.sleep(FRAME)
    except KeyboardInterrupt:
        pass
    finally:
        if old is not None:
            try:
                import termios
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            except Exception:
                pass
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == '__main__':
    main()
