# cli-anims

A collection of terminal animations in pure Python: no dependencies, just the standard library and ANSI truecolor.

## Running

```bash
python3 donut.py
python3 blackhole.py
python3 clock.py
```

Press `Ctrl+C` to quit; interactive animations also support `Q`. The canvas automatically adapts to your terminal size.

Requires Python 3.8+, a UTF-8 terminal with 24-bit color support (Linux, macOS, Termux, Windows Terminal).
If you see garbled characters, check your locale: `export LANG=en_US.UTF-8`.

## New animations

| File | What it shows | Controls |
| --- | --- | --- |
| `aquarium.py` | Aquarium: fish, bubbles, seaweed, seashells | `Space` — pause, `Q` — quit |
| `blackhole.py` | Black hole with an accretion disk, photon ring and gravitational lensing | `Ctrl+C` |
| `boids.py` | Flock of birds (boids) with glowing trails | `Space` — pause, `Q` — quit |
| `clock.py` | Analog braille-dot clock plus digital time and date | `Ctrl+C` |
| `dvd.py` | Classic bouncing DVD logo with a rainbow trail and sparks | `Space` — pause, `Q` — quit |
| `lorenz.py` | Lorenz attractor — a rotating glowing butterfly | `Ctrl+C` |
| `metaballs.py` | Floating glowing metaball blobs | `Ctrl+C` |
| `rain.py` | Rainy night: downpour, lightning flashes and ripples on the water | `Ctrl+C` |
| `spirograph.py` | Spirograph: a hypotrochoid drawn as a glowing line | `Ctrl+C` |
| `tree.py` | Growing tree with changing seasons, stars and falling leaves | `Ctrl+C` |
| `tunnel.py` | Endless neon tunnel | `Ctrl+C` |

## More animations

| File | What it shows | Controls |
| --- | --- | --- |
| `bouncing-cube.py` | 2D bouncing ASCII cube | `T` — trail, `G` — trajectory, `Space`, `Q` |
| `cargo.py` | `cargo build` parody with authentic cargo colors | `Ctrl+C` |
| `cube.py` | Rotating ASCII cube | `Ctrl+C` |
| `dna.py` | Rotating DNA helix | `Ctrl+C` |
| `donut.py` | Classic 3D donut | `Ctrl+C` |
| `fire.py` | Pixel fire | `Ctrl+C` |
| `fireworks.py` | Fireworks | `Space` — pause, `Q` — quit |
| `fractal.py` | Infinite Mandelbrot zoom | `Ctrl+C` |
| `game-of-life.py` | Conway's Game of Life | `Ctrl+C` |
| `globe.py` | Rotating procedural globe | `Space` — pause, `Q` — quit |
| `htop.py` | `htop` parody | `Ctrl+C` |
| `matrix.py` | Digital rain from The Matrix | `Ctrl+C` |
| `plasma.py` | Plasma | `Ctrl+C` |
| `pong.py` | Pong against the AI | `W/S` or `↑/↓`, `R` — restart, `Q` |
| `reaction-diffusion.py` | Gray-Scott reaction-diffusion | `1`–`8` — presets, `R`, `Space`, `Q` |
| `snake.py` | Snake (walls wrap around) | arrows / `WASD`, `R` — restart, `Q` |
| `snow.py` | Snowfall | `Ctrl+C` |
| `sortvis.py` | Sorting algorithm visualizer | `1`–`5`, `R` — shuffle, `Space`, `Q` |
| `spinner.py` | Spinner collection | letter/digit — select, `Space` — pause, `[` `]` — browse, `Ctrl+C` |
| `warp.py` | Starfield flight | `Ctrl+C` |

## Even more animations

| File | What it shows | Controls |
| --- | --- | --- |
| `burning-ship.py` | Burning Ship fractal slowly zooming into the hull | `Ctrl+C` |
| `city.py` | Night skyline: flickering windows, moon phases, meteors, a passing plane | `Ctrl+C` |
| `dragon.py` | Glowing dragon curve, folding one level deeper every few seconds | `Ctrl+C` |
| `elevator.py` | Two elevators with the SCAN algorithm serving passengers | `Space` — pause, `Q` — quit |
| `galton.py` | Galton board: balls through pegs building a Gaussian histogram | `Space` — pause, `Q` — quit |
| `julia.py` | Julia set with the `c` parameter orbiting the Mandelbrot cardioid | `Ctrl+C` |
| `koch.py` | Rotating Koch snowflake with animated depth | `Ctrl+C` |
| `langton.py` | Langton's ants with different rule strings on a torus | `Space` — pause, `Q` — quit |
| `maze.py` | Maze generation (recursive backtracker) and BFS solving | `Space` — pause, `Q` — quit |
| `pacman.py` | Self-playing Pac-Man with three ghosts and frightened mode | `Space` — pause, `Q` — quit |
| `pendulum.py` | Three double pendulums diverging from tiny differences (chaos) | `Ctrl+C` |
| `sandpile.py` | Abelian sandpile with avalanche counter | `Ctrl+C` |
| `slime-mold.py` | Physarum slime mold weaving glowing transport networks | `Ctrl+C` |
| `solar-system.py` | Planets on Keplerian orbits, Saturn's rings, a comet with a tail | `Ctrl+C` |
| `spectrum.py` | Fake audio spectrum analyzer with peak-hold caps and a track ticker | `Space` — pause, `Q` — quit |
| `tetris.py` | Tetris playing itself with a heuristic AI | `Space` — pause, `Q` — quit |
| `traffic.py` | Road intersection: cars queueing on a working traffic light cycle | `Space` — pause, `Q` — quit |
| `typewriter.py` | Someone typing Python snippets in vim, with syntax highlighting and typos | `Ctrl+C` |
| `waves.py` | Interference of drifting wave sources on water | `Ctrl+C` |
