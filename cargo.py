#!/usr/bin/env python3
"""Фейковый `cargo build` — с большой базой пакетов и настоящими цветами cargo."""

import random
import sys
import time

# --- ANSI ---
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[1;32m"
YELLOW = "\033[1;33m"
RED    = "\033[1;31m"
CYAN   = "\033[1;36m"

VERB_W = 12  # ширина выравнивания глагола (как в настоящем cargo)

# --- БАЗА ПАКЕТОВ ---
REAL_CRATES = """serde serde_json serde_derive serde_yaml serde_urlencoded
tokio tokio-util tokio-stream tokio-macros tokio-rustls tokio-tungstenite
syn quote proc-macro2 unicode-ident
futures futures-util futures-core futures-executor futures-io futures-task
futures-channel futures-sink futures-macro
rand rand_core rand_chacha rand_distr
rayon rayon-core
crossbeam crossbeam-utils crossbeam-channel crossbeam-epoch crossbeam-deque
thiserror thiserror-impl anyhow
clap clap_derive clap_builder clap_lex anstream anstyle anstyle-parse
log env_logger tracing tracing-core tracing-subscriber tracing-attributes tracing-log
hashbrown indexmap ahash smallvec parking_lot parking_lot_core lock_api
mio bytes http hyper hyper-util hyper-tls hyper-rustls h2 http-body http-body-util
reqwest url percent-encoding idna form_urlencoded
regex regex-syntax aho-corasick memchr
byteorder base64 hex
num-traits num-integer num-bigint num-cpus num-format bitflags
once_cell lazy_static cfg-if libc cc autocfg
pin-project pin-project-lite pin-utils slab either itertools petgraph
chrono time uuid getrandom
wasm-bindgen js-sys web-sys wasm-bindgen-futures wasm-bindgen-macro
wasm-bindgen-backend wasm-bindgen-shared
derive_more strum strum_macros displaydoc nom pest pest_derive
inkwell llvm-sys ring rustls webpki webpki-roots native-tls openssl openssl-sys
openssl-probe openssl-macros foreign-types foreign-types-shared
async-trait async-stream async-channel async-lock async-io async-executor
tower tower-service tower-http
sqlx sqlx-core sqlx-macros sqlx-postgres sqlx-mysql sqlx-sqlite
diesel diesel_derives
actix-web actix-rt actix-http actix-service actix-codec actix-router actix-utils actix-macros
axum axum-core warp tungstenite
sentry sentry-core sentry-types sentry-backtrace
rustls-pemfile rustls-native-certs rustls-webpki
encoding_rs urlencoding
glob walkdir ignore
tempfile filetime
dirs dirs-sys which atty is-terminal
termcolor console indicatif dialoguer
image png jpeg-decoder gif tiff
rodio cpal symphonia
wgpu wgpu-core wgpu-hal wgpu-types naga
winit glutin gl glium glfw
bevy bevy_ecs bevy_utils bevy_app bevy_reflect
rapier2d rapier3d nalgebra glam cgmath parry2d parry3d
imageproc lyon rusttype ab_glyph fontdue ttf-parser
flate2 miniz_oxide crc32fast adler
zstd bzip2 xz2 brotli
rusqlite libsqlite3-sys
mimalloc tikv-jemallocator
pprof backtrace addr2line gimli object
bindgen cexpr clang-sys
zstd-sys bzip2-sys
pyo3 pyo3-macros pyo3-ffi
napi napi-derive napi-build
""".split()

GEN_PREFIX = [
    "async", "serde", "tokio", "rust", "quick", "fast", "mini", "micro",
    "hyper", "proto", "net", "web", "sync", "data", "json", "yaml", "toml",
    "xml", "log", "time", "num", "crypto", "hash", "rand", "iter", "error",
    "test", "auto", "macro", "core", "util", "smart", "flex", "flow",
    "glow", "wave", "spark", "drift", "echo", "pulse", "blaze",
]
GEN_SUFFIX = [
    "rs", "core", "util", "macros", "derive", "sys", "bindings", "impl",
    "traits", "types", "helpers", "common", "async", "stream", "sync",
    "net", "web", "ffi", "kit", "lib", "tools", "api", "sdk", "proto",
    "codec", "parser", "format", "registry", "runtime", "engine",
]


def gen_version():
    major = random.choice([0, 0, 0, 1, 1, 1, 2, 3])
    minor = random.randint(0, 30)
    patch = random.randint(0, 40)
    if major == 0 and minor == 0 and patch == 0:
        patch = 1
    if random.random() < 0.08:
        tag = "alpha" if random.random() < 0.5 else "beta"
        return f"{major}.{minor}.{patch}-{tag}.{random.randint(1, 5)}"
    return f"{major}.{minor}.{patch}"


def bump_version(v):
    base = v.split("-")[0]
    parts = base.split(".")
    if len(parts) != 3:
        return base
    parts[2] = str(int(parts[2]) + random.randint(1, 5))
    return ".".join(parts)


def build_db(n):
    names = set(REAL_CRATES)
    tries = 0
    while len(names) < n and tries < n * 6:
        tries += 1
        if random.random() < 0.55:
            names.add(f"{random.choice(GEN_PREFIX)}-{random.choice(GEN_SUFFIX)}")
        else:
            names.add(f"{random.choice(GEN_PREFIX)}{random.randint(1, 99)}")
    return [{"name": nm, "version": gen_version()} for nm in sorted(names)]


def verb(label, color=GREEN):
    return f"{color}{label:>{VERB_W}}{RESET}"


def fake_warning(c):
    msgs = [
        ("unused import: `std::io::Write`", "src/lib.rs"),
        ("unused variable: `x`", "src/main.rs"),
        ("function `foo` is never used", "src/util.rs"),
        ("struct `Bar` is never constructed", "src/types.rs"),
        ("variable does not need to be mutable", "src/lib.rs"),
        ("unused `std::result::Result` that must be used", "src/api.rs"),
        ("field `baz` is never read", "src/config.rs"),
    ]
    msg, file = random.choice(msgs)
    print(f"{YELLOW}warning{RESET}: {msg}", flush=True)
    print(f"  {DIM}-->{RESET} {c['name']}/{file}:"
          f"{random.randint(3, 400)}:{random.randint(1, 80)}", flush=True)
    print(flush=True)


def run_build():
    sys.stdout.write("\033[2J\033[H\033[?25h")  # очистка + курсор видим
    sys.stdout.flush()

    total = random.randint(400, 900)
    crates = build_db(total)

    # --- 1. Updating index ---
    print(f"{verb('Updating')} crates.io index", flush=True)
    time.sleep(random.uniform(0.7, 1.6))

    # --- 2. Locking ---
    print(f"{verb('Locking')} {len(crates)} packages to latest compatible versions", flush=True)
    for _ in range(random.randint(6, 14)):
        c = random.choice(crates)
        newer = bump_version(c["version"])
        print(f"{'':>{VERB_W}}{GREEN}Adding{RESET} {BOLD}{c['name']}{RESET} "
              f"v{c['version']} {DIM}(available: v{newer}){RESET}", flush=True)
        time.sleep(random.uniform(0.01, 0.06))
    time.sleep(0.3)

    # --- 3. Downloading ---
    print(f"{verb('Downloading')} crates ...", flush=True)
    shown = random.sample(crates, min(random.randint(50, 120), len(crates)))
    t0 = time.time()
    for c in shown:
        line = f"{verb('Downloaded')} {BOLD}{c['name']}{RESET} v{c['version']}"
        sys.stdout.write("\033[2K\r" + line)
        sys.stdout.flush()
        time.sleep(random.uniform(0.008, 0.035))
    dl = time.time() - t0
    sys.stdout.write("\033[2K\r" +
                     f"{verb('Downloaded')} {len(crates)} crates in {dl:.2f}s\n")
    sys.stdout.flush()

    # --- 4. Compiling (тяжёлые крейты сначала, как в реальности) ---
    heavy = {"proc-macro2", "quote", "syn", "serde", "serde_derive",
             "tokio-macros", "tokio", "serde_json", "futures-util", "indexmap"}
    head = [c for c in crates if c["name"] in heavy]
    tail = [c for c in crates if c["name"] not in heavy]
    random.shuffle(tail)
    n_compile = min(len(head) + len(tail), random.randint(120, 280))
    ordered = (head + tail)[:n_compile]

    warn_gap = random.randint(20, 50)
    t0 = time.time()
    for i, c in enumerate(ordered):
        print(f"{verb('Compiling')} {BOLD}{c['name']}{RESET} v{c['version']}", flush=True)
        time.sleep(random.uniform(0.04, 0.35))
        if i > 0 and i % warn_gap == 0 and random.random() < 0.6:
            fake_warning(c)
    time.sleep(0.5)

    elapsed = time.time() - t0
    print(f"{verb('Finished')} `release` profile [optimized] target(s) in "
          f"{elapsed:.2f}s", flush=True)
    time.sleep(0.6)

    # --- 5. Запуск «приложения» ---
    bin_name = random.choice(["awesome-app", "hyperfast-server", "cli-magic",
                              "rocket-cli", "matrix-rain", "tiny-agent"])
    print(f"{verb('Running')} `target/release/{bin_name}`", flush=True)
    print()
    ver = f"{random.randint(1,3)}.0.{random.randint(0,9)}"
    for _ in range(3):
        print(f"   {CYAN}INFO{RESET} starting {bin_name} v{ver} ...", flush=True)
        time.sleep(random.uniform(0.2, 0.5))
    port = random.choice([3000, 4000, 8000, 8080, 9000])
    print(f"   {CYAN}INFO{RESET} listening on {DIM}http://127.0.0.1:{port}{RESET}", flush=True)

def main():
    build_no = 1
    try:
        while True:
            # лёгкий «разделитель» между сборками
            print(f"\n{DIM}---- build #{build_no} ----{RESET}")

            run_build()                      # один полный цикл
            build_no += 1

            # пауза, чтобы не спамило бесконечно
            time.sleep(random.uniform(1.5, 3.5))

    except KeyboardInterrupt:
        sys.stdout.write(RESET + "\n")
        print(f"{RED}error{RESET}: build interrupted")
        sys.exit(130)
    finally:
        sys.stdout.write(RESET)
        sys.stdout.flush()


if __name__ == "__main__":
    main()