"""Pick and run one terminal animation."""
from pathlib import Path
import subprocess
import sys

try:
    import curses
except ImportError:
    curses = None


def menu(screen, animations):
    screen.keypad(True)
    title, highlight = curses.A_BOLD, curses.A_REVERSE
    if curses.has_colors():
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
        title |= curses.color_pair(1)
        highlight = curses.color_pair(2) | curses.A_BOLD

    selected = first = 0
    while True:
        height, width = screen.getmaxyx()
        screen.erase()
        if height >= 4 and width >= 4:
            rows = height - 3
            first = max(0, min(first, selected), selected - rows + 1)
            screen.addnstr(0, 0, f'CLI // ANIMS     {selected + 1}/{len(animations)}', width - 1, title)
            for row, path in enumerate(animations[first:first + rows], 2):
                active = first + row - 2 == selected
                label = ('> ' if active else '  ') + path.stem
                screen.addnstr(row, 0, label, width - 1, highlight if active else 0)
            screen.addnstr(height - 1, 0, '↑↓ выбрать   Enter запустить   Q выйти', width - 1, title)
        screen.refresh()
        key = screen.getch()
        if key in (curses.KEY_UP, curses.KEY_DOWN):
            selected = (selected + (1 if key == curses.KEY_DOWN else -1)) % len(animations)
        elif key in (10, 13, curses.KEY_ENTER):
            return animations[selected]
        elif key in (ord('q'), ord('Q'), 27):
            return None


def choose(animations):
    if curses and sys.stdin.isatty() and sys.stdout.isatty():
        try:
            return curses.wrapper(menu, animations)
        except curses.error:
            pass  # Terminal cannot display the interactive menu.
    for number, path in enumerate(animations, 1):
        print(f'{number:2}. {path.stem}')
    while True:
        answer = input('Номер анимации (Q — выход): ').strip()
        if answer.lower() == 'q':
            return None
        try:
            number = int(answer)
        except ValueError:
            number = 0
        if 1 <= number <= len(animations):
            return animations[number - 1]
        print(f'Введите число от 1 до {len(animations)}.')


def main():
    launcher = Path(__file__).resolve()
    animations = sorted(p for p in launcher.parent.glob('*.py') if p != launcher)
    try:
        path = choose(animations)
        if path:
            return subprocess.run([sys.executable, str(path)]).returncode
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        if sys.stdout.isatty():
            print('\033[0m\033[?25h\033[2J\033[H', end='', flush=True)


if __name__ == '__main__':
    sys.exit(main())
