#!/usr/bin/env python3
"""Spinner collection — 36 spinners, switch by pressing letter keys. No deps."""

import sys, os, time, math, re, unicodedata

# --- Windows: включить ANSI-escape в консоли ---
if os.name == 'nt':
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.SetConsoleMode(k.GetStdHandle(-11), 7)
    except Exception:
        pass

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[1;36m"
GREEN  = "\033[1;32m"
YELLOW = "\033[1;33m"

ANSI_RE = re.compile(r'\033\[[0-9;]*m')

def strip_ansi(s): return ANSI_RE.sub('', s)

def disp_w(s):
    w = 0
    for ch in strip_ansi(s):
        w += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return w

def pad_to(s, width):
    return s + ' ' * max(0, width - disp_w(s))

def F(s):
    return s.split() if ' ' in s else list(s)

# ------------- КОЛЛЕКЦИЯ СПИННЕРОВ -------------
SPINNERS = [
    ("line",      F("|/-\\")),
    ("line2",     F("-\\|/")),
    ("dots",      ["   ", ".  ", ".. ", "..."]),
    ("grow",      F(".oO@")),
    ("pulse",     F("-+=*+=+")),
    ("arrow",     F("←↖↑↗→↘↓↙")),
    ("arrow2",    F("↑↗→↘↓↙←↖")),
    ("plus",      F("+x+.")),
    ("numbers",   F("1234")),
    ("letters",   F("ABCD")),
    ("abc",       F("abc123")),
    ("brackets",  F("[ ] { } < >")),
    ("blocks",    F("▁▃▄▅▆▇█▇▆▅▄▃")),
    ("pulseblk",  F("░▒▓█▓▒░")),
    ("bar",       F("▏▎▍▌▋▊▉█")),
    ("quad",      F("▖▘▝▗")),
    ("halfsq",    F("◧◨◩◪")),
    ("box",       F("◰◳◲◱")),
    ("tri",       F("◢◣◤◥")),
    ("circle",    F("◐◓◑◒")),
    ("circle2",   F("◜◝◞◟")),
    ("growdot",   F("·•●•·")),
    ("blink",     F("●○")),
    ("diamond",   F("◇◆")),
    ("braille",   F("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")),
    ("braille2",  F("⣾⣽⣻⢿⡿⣟⣯⣷")),
    ("moon",      F("🌑🌒🌓🌔🌕🌖🌗🌘")),      # 🌙 луна
    ("earth",     F("🌍🌎🌏")),
    ("clock",     F("🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛")),
    ("weather",   F("☀☁🌧⛈🌩")),
    ("heart",     F("❤🧡💛💚💙💜")),
    ("colors",    F("🔴🟠🟡🟢🔵🟣")),
    ("faces",     F("😀😃😄😁😆")),
    ("sparkle",   F("✨💫⭐🌟")),
    ("wave",      F("▁▂▃▄▅▆▇█▇▆▅▄▃▂")),
    ("braille3",  F("⠁⠂⠄⡀⢀⠠⠐⠈")),
]

KEYS = list("abcdefghijklmnopqrstuvwxyz0123456789")

# --- Кириллица -> латиница (по физическим позициям клавиш) ---
CYR_TO_LAT = {
    'й':'q','ц':'w','у':'e','к':'r','е':'t','н':'y','г':'u','ш':'i','щ':'o','з':'p',
    'ф':'a','ы':'s','в':'d','а':'f','п':'g','р':'h','о':'j','л':'k','д':'l',
    'я':'z','ч':'x','с':'c','м':'v','и':'b','т':'n','ь':'m',
    'х':'[','ъ':']',
}

# ------------- КЛАВИАТУРА БЕЗ ЗАВИСИМОСТЕЙ -------------
class Keyboard:
    def __init__(self):
        self.win = (os.name == 'nt')
    def __enter__(self):
        if not self.win:
            import termios, tty
            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        return self
    def __exit__(self, *a):
        if not self.win:
            import termios
            try: termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
            except Exception: pass
    def read(self):
        if self.win:
            import msvcrt
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch == '\x03':
                    raise KeyboardInterrupt
                if ch in ('\x00', '\xe0'):
                    if msvcrt.kbhit(): msvcrt.getwch()
                    return None
                return ch
            return None
        import select
        r, _, _ = select.select([sys.stdin], [], [], 0)
        if not r: return None
        ch = sys.stdin.read(1)
        if ch == '\x1b':  # съесть escape-последовательность (стрелки)
            while True:
                r, _, _ = select.select([sys.stdin], [], [], 0.005)
                if not r: break
                sys.stdin.read(1)
            return None
        return ch

# ------------- ПРИЛОЖЕНИЕ -------------
class App:
    def __init__(self):
        self.idx = 0
        self.frame = 0
        self.paused = False
        self.hue = 0.0

    def hue_color(self):
        t = self.hue
        r = int(127 + 127*math.sin(t))
        g = int(127 + 127*math.sin(t + 2.094))
        b = int(127 + 127*math.sin(t + 4.188))
        return f"\033[38;2;{r};{g};{b}m"

    def handle(self, ch):
        if ch == ' ':
            self.paused = not self.paused
            return
        low = ch.lower()
        k = CYR_TO_LAT.get(low, low)
        if k == '[':
            self.idx = (self.idx - 1) % len(SPINNERS); return
        if k == ']':
            self.idx = (self.idx + 1) % len(SPINNERS); return
        if k in KEYS and KEYS.index(k) < len(SPINNERS):
            self.idx = KEYS.index(k)

    def draw(self, w, h):
        color = self.hue_color()
        out = ["\033[H"]

        # header
        name, frames = SPINNERS[self.idx]
        key = KEYS[self.idx]
        head = (f" {BOLD}{CYAN}Spinner{RESET}: {BOLD}{name}{RESET}"
                f"    key: {BOLD}{YELLOW}{key}{RESET}"
                f"    [{self.idx+1}/{len(SPINNERS)}]")
        if self.paused:
            head += f"    {YELLOW}[PAUSED]{RESET}"
        out.append("\033[2K" + head + "\n")
        out.append("\033[2K\n")

        # big spinner
        sym = frames[self.frame % len(frames)]
        pad = max(0, (w - disp_w(sym)) // 2)
        out.append("\033[2K" + " " * pad + color + BOLD + sym + RESET + "\n")
        out.append("\033[2K\n")

        # legend
        col_w = 22
        cols = max(1, w // col_w)
        rows = (len(SPINNERS) + cols - 1) // cols
        for r in range(rows):
            line = ""
            for c in range(cols):
                i = c * rows + r
                if i >= len(SPINNERS):
                    line += " " * col_w
                    continue
                nm, fr = SPINNERS[i]
                k = KEYS[i]
                s = fr[self.frame % len(fr)]
                marker = f"{GREEN}▶{RESET}" if i == self.idx else " "
                body = f"{marker} {BOLD}{k}{RESET} {s} {nm}"
                line += pad_to(body, col_w)
            out.append("\033[2K" + line + "\n")

        # footer
        out.append("\033[2K\n")
        out.append(f"\033[2K {DIM}буква/цифра — выбрать · пробел — пауза · "
                   f"[ ] — листать · Ctrl+C — выход{RESET}\n")

        sys.stdout.write("".join(out))
        sys.stdout.flush()

    def run(self):
        # alt-screen + hide cursor + clear
        sys.stdout.write("\033[?1049h\033[?25l\033[2J\033[H")
        sys.stdout.flush()
        try:
            with Keyboard() as kb:
                while True:
                    try:
                        sz = os.get_terminal_size()
                        w, h = sz.columns, sz.lines
                    except OSError:
                        w, h = 80, 24
                    self.draw(w, h)
                    ch = kb.read()
                    if ch:
                        self.handle(ch)
                    if not self.paused:
                        self.frame += 1
                        self.hue += 0.04
                    time.sleep(0.07)
        except KeyboardInterrupt:
            pass
        finally:
            sys.stdout.write(RESET + "\033[?25h\033[?1049l")
            sys.stdout.flush()

if __name__ == "__main__":
    App().run()