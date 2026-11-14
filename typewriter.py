#!/usr/bin/env python3
"""Typewriter — кто-то печатает код в vim. Ctrl+C — выход."""

import os, re, sys, time, random

# --- палитра подсветки (ANSI truecolor) ---
RST   = "\033[0m"
C_KW  = "\033[38;2;198;140;255m"    # ключевые слова — фиолетовый
C_STR = "\033[38;2;130;220;120m"    # строки — зелёный
C_COM = "\033[38;2;122;122;122m"    # комментарии — серый
C_NUM = "\033[38;2;255;166;80m"     # числа — оранжевый
C_TXT = "\033[38;2;205;212;222m"    # обычный код
C_DIM = "\033[38;2;112;120;132m"    # шапка и строка статуса
C_CUR = "\033[38;2;240;240;240m"    # блочный курсор

# токенизатор: строки -> комментарии -> ключевые слова -> числа ->
# незакрытая строка (её тоже красим, пока она печатается)
TOKEN_RE = re.compile(
    r"('''.*?'''|\"\"\".*?\"\"\"|'[^'\n]*'|\"[^\"\n]*\")"
    r"|(#[^\n]*)"
    r"|\b(def|class|return|if|elif|else|for|while|in|is|not|and|or"
    r"|import|from|as|try|except|finally|with|lambda|yield|pass"
    r"|break|continue|None|True|False"
    r"|print|len|range|int|str|input|random|enumerate)\b"
    r"|\b(\d+(?:\.\d+)?)\b"
    r"|('(?:[^'\n]*)\Z|\"(?:[^\"\n]*)\Z)"
)


def highlight(line):
    """Красит одну строку кода согласно токенизатору."""
    out = []
    pos = 0
    for m in TOKEN_RE.finditer(line):
        if m.start() > pos:
            out.append(C_TXT + line[pos:m.start()])
        txt = m.group(0)
        if m.group(1) is not None or m.group(5) is not None:
            out.append(C_STR + txt)          # строка, в том числе незакрытая
        elif m.group(2) is not None:
            out.append(C_COM + txt)          # комментарий
        elif m.group(3) is not None:
            out.append(C_KW + txt)           # ключевое слово
        else:
            out.append(C_NUM + txt)          # число
        pos = m.end()
    if pos < len(line):
        out.append(C_TXT + line[pos:])
    return "".join(out)


# --- встроенные сниппеты: (имя файла, исходник) ---
SNIPPETS = [
    ("main.py", '''def quicksort(xs):
    """Быстрая сортировка на списковых включениях."""
    if len(xs) <= 1:
        return xs
    pivot = xs[len(xs) // 2]
    left = [x for x in xs if x < pivot]
    mid = [x for x in xs if x == pivot]
    right = [x for x in xs if x > pivot]
    return quicksort(left) + mid + quicksort(right)

nums = [5, 2, 9, 1, 7, 3, 8, 6, 4, 0]
print(quicksort(nums))
'''),
    ("fib.py", '''from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    """Числа Фибоначчи с мемоизацией."""
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

for i in range(1, 21):
    print(i, fib(i))
'''),
    ("guess.py", '''import random

secret = random.randint(1, 100)
tries = 0
while True:
    guess = int(input("Твоё число от 1 до 100: "))
    tries += 1
    if guess < secret:
        print("Больше!")
    elif guess > secret:
        print("Меньше!")
    else:
        print("Угадал за", tries, "попыток")
        break
'''),
    ("search.py", '''def binary_search(xs, target):
    """Бинарный поиск по отсортированному списку."""
    lo, hi = 0, len(xs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if xs[mid] == target:
            return mid
        if xs[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

data = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
print(binary_search(data, 15))
'''),
]


class Typewriter:
    """Печатает исходник посимвольно с человеческим ритмом и опечатками."""

    def __init__(self, name, code):
        self.name = name
        self.src = code
        self.buf = []      # символы, уже попавшие на экран (включая опечатки)
        self.pos = 0       # сколько символов исходника напечатано верно
        self.err = 0       # сколько ошибочных символов сейчас в конце буфера
        self.done = False

    def step(self):
        """Один «нажим клавиши»; возвращает паузу до следующего."""
        if self.err > 0:                       # заметил опечатку — стирает
            self.buf.pop()
            self.err -= 1
            return (random.uniform(0.10, 0.16) if self.err == 0
                    else random.uniform(0.04, 0.07))
        if self.pos >= len(self.src):          # сниппет допечатан
            self.done = True
            return 0.0
        ch = self.src[self.pos]
        # изредка — опечатка: пара лишних букв, потом несколько Backspace
        if (self.pos > 10 and ch.isalpha() and ch.isascii()
                and random.random() < 0.02):
            self.buf.append(random.choice("xzcvbnmrtk"))
            if random.random() < 0.6:
                self.buf.append(random.choice("xzcvbnmrt"))
                self.err = 2
            else:
                self.err = 1
            return random.uniform(0.09, 0.16)
        self.buf.append(ch)
        self.pos += 1
        if ch == "\n":                         # перевод строки — передышка
            return (random.uniform(0.28, 0.60) if random.random() < 0.3
                    else random.uniform(0.05, 0.14))
        if ch in "([{":
            return random.uniform(0.08, 0.15)  # перед скобкой — задумался
        if ch in ")]},:":
            return random.uniform(0.05, 0.11)
        if ch == " ":
            return random.uniform(0.01, 0.03)  # пробелы и отступы — быстро
        return random.uniform(0.02, 0.06)

    def draw(self, w, h, blink):
        """Кадр: шапка vim, код с подсветкой, курсор, строка статуса."""
        parts = "".join(self.buf).split("\n")
        max_code = max(1, h - 2)               # шапка и статус съедают по строке
        if len(parts) > max_code:              # скроллинг: виден хвост файла
            parts = parts[-max_code:]
        width = max(8, w - 2)
        out = ["\033[H",
               C_DIM + ("~ $ vim " + self.name)[:width] + RST + "\033[K\n"]
        last = len(parts) - 1
        for i, ln in enumerate(parts):
            s = highlight(ln[:width])
            if i == last and blink:            # мигающий блочный курсор
                s += C_CUR + "▌"
            out.append(s + RST + "\033[K\n")
        if self.done:
            stat = "-- готово: %s — Ctrl+C, чтобы выйти --" % self.name
        else:
            stat = "-- ВСТАВКА --"
        out.append(C_DIM + stat[:w] + RST + "\033[K\n")
        return "".join(out)


def main():
    sys.stdout.write("\033[?25l\033[2J")       # курсор спрятать, экран чистый
    idx = 0
    tw = Typewriter(*SNIPPETS[idx])
    last_size = None
    rest_until = None                          # конец паузы между сниппетами
    try:
        while True:
            try:
                sz = os.get_terminal_size()
                w, h = max(2, sz.columns), max(2, sz.lines - 1)
            except OSError:
                w, h = 80, 24
            if (w, h) != last_size:            # resize — перерисовка начисто
                last_size = (w, h)
                sys.stdout.write("\033[2J")
            blink = int(time.monotonic() * 2.5) % 2 == 0
            if tw.done:
                if rest_until is None:         # готовый код держится на экране
                    rest_until = time.monotonic() + random.uniform(1.6, 2.6)
                delay = 0.05
                if time.monotonic() >= rest_until:
                    idx = (idx + 1) % len(SNIPPETS)
                    tw = Typewriter(*SNIPPETS[idx])
                    rest_until = None
                    sys.stdout.write("\033[2J")
            else:
                delay = tw.step()              # темп задаёт сама печать
            sys.stdout.write(tw.draw(w, h, blink))
            sys.stdout.flush()
            time.sleep(max(delay, 0.0))
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\n")


if __name__ == "__main__":
    main()
