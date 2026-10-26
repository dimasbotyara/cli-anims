import random, time, sys, os

PROCS = ["systemd","kthreadd","kworker/0:1","python3","node","cargo","rustc",
         "code","vim","sshd","bash","zsh","htop","pipewire","Xorg","firefox",
         "chrome","discord","postgres","redis-server","nginx","dockerd","steam"]
USERS = ["root","u0","user","www-data","postgres","git"]

class Proc:
    def __init__(self, pid):
        self.pid = pid
        self.user = random.choice(USERS)
        self.pri = random.choice([20,20,20,15,10,39])
        self.ni  = random.choice([0,0,0,-5,5])
        self.virt = random.randint(1000, 5000000)
        self.res  = random.randint(100, self.virt)
        self.state = random.choice("RSSSD")
        self.cpu = random.uniform(0, 30)
        self.mem = random.uniform(0, 10)
        self.time_cs = random.randint(0, 50000)
        self.name = random.choice(PROCS)
    def tick(self):
        self.cpu = max(0, min(100, self.cpu + random.uniform(-4, 4)))
        self.mem = max(0, min(50,  self.mem + random.uniform(-0.6, 0.6)))
        self.time_cs += int(self.cpu / 10) + random.randint(0, 2)
        self.state = "R" if self.cpu > 5 else random.choice("SSSD")
        if random.random() < 0.003:
            self.name = random.choice(PROCS)

def fmt_kb(kb):
    if kb > 1024*1024: return f"{kb/1048576:.1f}G"
    if kb > 1024:      return f"{kb/1024:.0f}M"
    return f"{kb}K"

def fmt_time(cs):
    s = cs / 100
    return f"{int(s)//60}:{s%60:05.2f}"

def bar(frac, width=20, ch="|"):
    n = int(round(width * max(0, min(1, frac))))
    return ch * n + " " * (width - n)

def main():
    try:
        sz = os.get_terminal_size()
        w, h = sz.columns, sz.lines
    except OSError:
        w, h = 100, 28
    n_cores = 8
    cores = [random.uniform(0, 30) for _ in range(n_cores)]
    mem_total, mem_used = 16384, 6000
    swap_total, swap_used = 8192, 100
    procs = [Proc(1000 + i) for i in range(h - 14)]
    pid = 5000
    tick = 0
    sys.stdout.write("\033[?25l\033[2J")
    try:
        while True:
            for i in range(n_cores):
                cores[i] = max(0, min(100, cores[i] + random.uniform(-15, 15)))
            mem_used  = max(2000, min(mem_total-500, mem_used  + random.uniform(-150, 150)))
            swap_used = max(0,    min(swap_total,    swap_used + random.uniform(-5, 5)))
            for p in procs: p.tick()
            procs.sort(key=lambda p: p.cpu, reverse=True)
            if tick % 15 == 0:
                procs.pop()
                procs.insert(0, Proc(pid)); pid += 1

            out = ["\033[H"]
            out.append(f"\033[1;36m{time.strftime('%H:%M:%S')}\033[0m  "
                       f"\033[1;37mup {tick//30+1}d 4:20\033[0m  "
                       f"load: {random.uniform(0.3,2.5):.2f} "
                       f"{random.uniform(0.3,2.5):.2f} "
                       f"{random.uniform(0.3,2.5):.2f}\n")
            out.append(f" Tasks: {180+tick%7}, 345 thr; 2 running\n")
            mp = mem_used/mem_total
            out.append(f" Mem\033[1;32m[{bar(mp)}]\033[0m {mem_used:.0f}/{mem_total}M\n")
            sp = swap_used/swap_total
            out.append(f" Swp\033[1;33m[{bar(sp)}]\033[0m {swap_used:.0f}/{swap_total}M\n\n")
            for i, cpu in enumerate(cores):
                c = "32" if cpu < 60 else "33" if cpu < 85 else "31"
                out.append(f" {i}\033[1;{c}m[{bar(cpu/100)}]\033[0m {cpu:5.1f}%\n")
            out.append("\n\033[7m  PID USER      PRI  NI   VIRT    RES S  CPU%  MEM%  TIME+    Command\033[0m\n")
            for p in procs[:h-14]:
                out.append(f" {p.pid:>5} {p.user:<9} {p.pri:>3} {p.ni:>3} "
                           f"{fmt_kb(p.virt):>6} {fmt_kb(p.res):>6} {p.state} "
                           f"{p.cpu:>5.1f} {p.mem:>5.1f} {fmt_time(p.time_cs):>8}  {p.name}\n")
            sys.stdout.write(''.join(out))
            sys.stdout.flush()
            tick += 1
            time.sleep(0.3)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\n")

if __name__ == "__main__":
    main()
