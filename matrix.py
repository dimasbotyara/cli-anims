import random, time, sys, os

# Набор ASCII: буквы, цифры, пунктуация (без пробела и кавычек-ловушек)
CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    "!@#$%^&*()_+-=[]{}|;:<>?,./~"
)

# Градиент яркости хвоста: [очень тусклый] -> [яркий] -> [белая голова]
# ANSI: 22 = обычная яркость, 2 = тусклый, 32 = зелёный, 92 = ярко-зелёный, 97 = белый
TRAIL = [
    "\033[2;32m",   # тёмно-зелёный (дальний хвост)
    "\033[32m",     # обычный зелёный
    "\033[1;32m",   # ярко-зелёный
    "\033[1;92m",   # очень яркий зелёный
]
HEAD = "\033[1;97m"  # белая голова капли
TRAIL_LEN = len(TRAIL)

def main():
    try:
        sz = os.get_terminal_size()
        w, h = sz.columns, sz.lines - 1
    except OSError:
        w, h = 80, 24

    # Для каждой колонки: позиция головы + задержка (чтобы капли не синхронно падали)
    drops = [random.randint(-h, 0) for _ in range(w)]
    speeds = [random.choice((1, 1, 1, 2)) for _ in range(w)]  # иногда быстрее
    glyphs = [random.choice(CHARS) for _ in range(w)]         # текущий символ головы

    out = sys.stdout
    out.write("\033[?25l\033[2J")  # спрятать курсор + очистка
    try:
        while True:
            for x in range(w):
                head = drops[x]

                # 1) Гасим самый дальний сегмент хвоста (стираем "призрак")
                tail_end = head - TRAIL_LEN
                if 0 <= tail_end < h:
                    out.write(f"\033[{tail_end + 1};{x + 1}H ")
                elif 0 <= tail_end - 1 < h:
                    # на случай, если хвост чуть сдвинулся — тоже затрём
                    out.write(f"\033[{tail_end};{x + 1}H ")

                # 2) Рисуем хвост от тусклого к яркому
                for i, color in enumerate(TRAIL):
                    y = head - (TRAIL_LEN - i)
                    if 0 <= y < h:
                        out.write(f"\033[{y + 1};{x + 1}H{color}{random.choice(CHARS)}")

                # 3) Рисуем голову (яркий белый символ)
                if 0 <= head < h:
                    # иногда меняем символ головы — эффект "перебора"
                    if random.random() < 0.15:
                        glyphs[x] = random.choice(CHARS)
                    out.write(f"\033[{head + 1};{x + 1}H{HEAD}{glyphs[x]}")

                # 4) Двигаем каплю вниз
                drops[x] += speeds[x]
                if head - TRAIL_LEN > h:
                    drops[x] = random.randint(-25, -5)
                    speeds[x] = random.choice((1, 1, 1, 2))

            out.write("\033[0m")
            out.flush()
            time.sleep(0.06)
    except KeyboardInterrupt:
        pass
    finally:
        out.write("\033[0m\033[?25h\n")

if __name__ == "__main__":
    main()