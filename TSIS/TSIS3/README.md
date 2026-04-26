# TSIS 3 — Racer Game

Advanced Driving · Lane Hazards · Power-Ups · Leaderboard

## Requirements

```bash
pip install pygame
```

## Run

```bash
cd TSIS3
python main.py
```

## Controls (in-game)

| Key | Action |
|-----|--------|
| ← / A | Move left |
| → / D | Move right |
| ESC | Return to menu |

## Project Structure

```
TSIS3/
├── main.py          # Entry point & screen orchestrator
├── racer.py         # Gameplay engine (road, cars, obstacles, power-ups, HUD)
├── ui.py            # All Pygame screens (Menu, Settings, Leaderboard, Game Over)
├── persistence.py   # JSON save/load for settings & leaderboard
├── settings.json    # Persisted settings (auto-created)
├── leaderboard.json # Persisted top-10 scores (auto-created)
└── assets/          # (place images/sounds here if desired)
```

## Features

### Gameplay
- **4-lane road** with smooth scrolling
- **Lane hazards**: oil spills (slow), potholes & barriers (crash)
- **Dynamic road events**: nitro strips, speed bumps, moving barriers
- **Traffic cars** — varied speeds, collision ends the run
- **Safe spawn logic** — obstacles never spawn on top of the player
- **Difficulty scaling** — speed, traffic density, and obstacle frequency all increase

### Coins (from Practice 10–11)
- Weighted values: 1 · 3 · 5 · 10
- Enemy speed increases with coins collected

### Power-Ups (new)
| Power-up | Effect | Duration |
|----------|--------|----------|
| **Nitro** (N) | Speed ×1.8 | 4 seconds |
| **Shield** (S) | Absorbs one collision | Until hit |
| **Repair** (R) | Clears nearest obstacle | Instant |

- Only one active at a time
- Disappear after timeout if uncollected
- HUD shows active power-up + remaining time

### Score
`Score = coins × 10 + distance ÷ 5 + power-up bonuses`

### Screens
1. **Main Menu** — Play · Leaderboard · Settings · Quit
2. **Username Entry** — typed name used in leaderboard
3. **Settings** — sound toggle · car color (4 choices) · difficulty (Easy/Normal/Hard)
4. **Game Over** — score · distance · coins · Retry / Main Menu
5. **Leaderboard** — top 10 with rank · name · score · distance · coins

### Persistence
- `settings.json` — loaded at startup, saved on any settings change
- `leaderboard.json` — updated after every run, top 10 kept
