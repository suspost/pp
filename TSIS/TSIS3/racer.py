"""
racer.py — Core gameplay: road, player, traffic, obstacles, coins, power-ups,
           HUD, and difficulty scaling.

Builds on the base from Practice 10 & 11:
  ✔ Player car movement (lane-based)
  ✔ Scrolling road with lane markings
  ✔ Weighted coins that spawn randomly
  ✔ Coin counter
  ✔ Enemy speed increases with coins collected

New in TSIS 3:
  ✔ Lane hazards (oil spills, slow zones)
  ✔ Dynamic road events (speed bumps, nitro strips, moving barriers)
  ✔ Traffic cars — collision ends run
  ✔ Road obstacles — barriers, potholes
  ✔ Safe-spawn logic
  ✔ Difficulty scaling (traffic density, obstacle frequency)
  ✔ Power-ups: Nitro · Shield · Repair
  ✔ Score = coins × value + distance bonus + power-up bonuses
  ✔ Distance meter with finish line
  ✔ Full HUD
"""

import pygame
import random
import math

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = (15,  15,  25)
ROAD_COL    = (40,  40,  55)
LANE_MARK   = (200, 200,  60)
SHOULDER    = (80,  60,  30)
WHITE       = (255, 255, 255)
YELLOW      = (255, 220,  50)
CYAN        = ( 80, 230, 230)
GREEN       = ( 70, 220, 100)
RED         = (220,  60,  60)
ORANGE      = (255, 150,  40)
PURPLE      = (180,  80, 220)
GRAY        = (120, 120, 140)
DARK_GRAY   = ( 50,  50,  70)

CAR_COLORS = {
    "red":    (220,  60,  60),
    "blue":   ( 60, 120, 220),
    "green":  ( 50, 200,  80),
    "yellow": (255, 210,  40),
}

# ── Road geometry ─────────────────────────────────────────────────────────────
LANE_COUNT  = 4
ROAD_W      = 300        # total road width in px
SHOULDER_W  = 40

CAR_W, CAR_H       = 36, 64
TRAFFIC_W, TRAFFIC_H = 36, 60
FINISH_DIST         = 3000   # meters to finish line


# ── Difficulty presets ────────────────────────────────────────────────────────
DIFF = {
    "easy":   {"base_speed": 4, "traffic_rate": 120, "obstacle_rate": 180,
               "coin_rate": 60,  "speed_inc": 0.003},
    "normal": {"base_speed": 5, "traffic_rate": 90,  "obstacle_rate": 120,
               "coin_rate": 80,  "speed_inc": 0.005},
    "hard":   {"base_speed": 7, "traffic_rate": 60,  "obstacle_rate": 80,
               "coin_rate": 100, "speed_inc": 0.008},
}

COIN_WEIGHTS = [(1, 50), (3, 30), (5, 15), (10, 5)]   # (value, weight)
POWERUP_TYPES = ["nitro", "shield", "repair"]
POWERUP_COLORS = {"nitro": ORANGE, "shield": CYAN, "repair": GREEN}
POWERUP_SYMBOLS = {"nitro": "N", "shield": "S", "repair": "R"}


def _font(size):
    return pygame.font.SysFont("consolas,monospace", size, bold=True)


def _weighted_coin():
    pool = []
    for val, w in COIN_WEIGHTS:
        pool.extend([val] * w)
    return random.choice(pool)


class Road:
    """Scrolling 4-lane road with shoulder stripes."""

    def __init__(self, screen_w, screen_h):
        self.W         = screen_w
        self.H         = screen_h
        self.ROAD_W    = ROAD_W          # expose for RoadEvent / other objects
        self.road_left = screen_w // 2 - ROAD_W // 2
        self.lane_w    = ROAD_W // LANE_COUNT
        self.stripe_y  = 0.0

        # Pre-compute lane centres (x)
        self.lane_cx = [
            self.road_left + self.lane_w * i + self.lane_w // 2
            for i in range(LANE_COUNT)
        ]

    def update(self, scroll_speed):
        self.stripe_y = (self.stripe_y + scroll_speed) % 60

    def draw(self, surf):
        # Shoulders
        pygame.draw.rect(surf, SHOULDER,
                         (self.road_left - SHOULDER_W, 0, SHOULDER_W, self.H))
        pygame.draw.rect(surf, SHOULDER,
                         (self.road_left + ROAD_W, 0, SHOULDER_W, self.H))
        # Road surface
        pygame.draw.rect(surf, ROAD_COL,
                         (self.road_left, 0, ROAD_W, self.H))
        # Lane dashes
        for i in range(1, LANE_COUNT):
            x = self.road_left + self.lane_w * i
            y = -60 + self.stripe_y
            while y < self.H:
                pygame.draw.rect(surf, LANE_MARK, (x - 2, int(y), 4, 30))
                y += 60
        # Road edges (solid)
        pygame.draw.rect(surf, YELLOW, (self.road_left - 4, 0, 4, self.H))
        pygame.draw.rect(surf, YELLOW, (self.road_left + ROAD_W, 0, 4, self.H))

    def lane_x(self, lane: int) -> int:
        return self.lane_cx[lane]

    def random_lane_x(self):
        return random.choice(self.lane_cx)

    def random_lane(self):
        return random.randint(0, LANE_COUNT - 1)


class PlayerCar:
    def __init__(self, road: Road, car_color: str):
        self.road     = road
        self.color    = CAR_COLORS.get(car_color, CAR_COLORS["red"])
        self.lane     = LANE_COUNT // 2     # start in middle-right lane
        self.x        = float(road.lane_x(self.lane))
        self.y        = float(road.H - 120)
        self.move_cd  = 0                   # lane-switch cooldown (frames)
        # Power-up state
        self.nitro    = False
        self.shield   = False
        self.nitro_timer  = 0
        self.shield_active = False

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if self.move_cd > 0:
            self.move_cd -= 1
            return
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.lane > 0:
            self.lane -= 1
            self.move_cd = 12
        elif (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.lane < LANE_COUNT - 1:
            self.lane += 1
            self.move_cd = 12

    def update(self):
        # Smooth horizontal slide
        target_x = self.road.lane_x(self.lane)
        self.x += (target_x - self.x) * 0.22

        # Nitro timer countdown
        if self.nitro_timer > 0:
            self.nitro_timer -= 1
            if self.nitro_timer == 0:
                self.nitro = False

    def rect(self):
        return pygame.Rect(int(self.x) - CAR_W // 2,
                           int(self.y) - CAR_H // 2,
                           CAR_W, CAR_H)

    def draw(self, surf):
        r = self.rect()
        # Body
        pygame.draw.rect(surf, self.color, r, border_radius=6)
        # Windshield
        wf = pygame.Rect(r.x + 6, r.y + 8, r.width - 12, 18)
        pygame.draw.rect(surf, (150, 220, 255), wf, border_radius=3)
        # Rear window
        rw = pygame.Rect(r.x + 6, r.bottom - 22, r.width - 12, 14)
        pygame.draw.rect(surf, (120, 190, 230), rw, border_radius=3)
        # Wheels
        for wx, wy in [(r.x - 4, r.y + 10), (r.right - 6, r.y + 10),
                       (r.x - 4, r.bottom - 22), (r.right - 6, r.bottom - 22)]:
            pygame.draw.rect(surf, (20, 20, 20), (wx, wy, 10, 16), border_radius=3)

        # Shield glow
        if self.shield_active:
            s = pygame.Surface((r.w + 20, r.h + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (*CYAN, 70), s.get_rect())
            surf.blit(s, (r.x - 10, r.y - 10))

        # Nitro flame
        if self.nitro:
            for i in range(3):
                fx = r.centerx + random.randint(-8, 8)
                fy = r.bottom + random.randint(4, 18)
                pygame.draw.circle(surf, ORANGE, (fx, fy), random.randint(4, 8))


class TrafficCar:
    COLORS = [(200, 80, 80), (80, 160, 200), (100, 200, 100),
              (200, 160, 40), (160, 80, 200), (200, 200, 80)]

    def __init__(self, x, color=None):
        self.x     = float(x)
        self.y     = -TRAFFIC_H
        self.color = color or random.choice(TrafficCar.COLORS)
        self.speed_mul = random.uniform(0.7, 1.2)

    def update(self, scroll_speed):
        self.y += scroll_speed * self.speed_mul

    def rect(self):
        return pygame.Rect(int(self.x) - TRAFFIC_W // 2,
                           int(self.y) - TRAFFIC_H // 2,
                           TRAFFIC_W, TRAFFIC_H)

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, self.color, r, border_radius=5)
        wf = pygame.Rect(r.x + 5, r.y + 6, r.width - 10, 16)
        pygame.draw.rect(surf, (140, 200, 240), wf, border_radius=3)
        for wx, wy in [(r.x - 4, r.y + 8), (r.right - 6, r.y + 8),
                       (r.x - 4, r.bottom - 20), (r.right - 6, r.bottom - 20)]:
            pygame.draw.rect(surf, (20, 20, 20), (wx, wy, 10, 14), border_radius=3)


class Coin:
    def __init__(self, x, y, value):
        self.x, self.y = float(x), float(y)
        self.value = value
        self.age   = 0

    def update(self, scroll_speed):
        self.y   += scroll_speed
        self.age += 1

    def rect(self):
        return pygame.Rect(int(self.x) - 12, int(self.y) - 12, 24, 24)

    def draw(self, surf):
        col = {1: YELLOW, 3: ORANGE, 5: CYAN, 10: PURPLE}.get(self.value, YELLOW)
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), 12)
        txt = _font(14).render(str(self.value), True, (20, 20, 20))
        surf.blit(txt, txt.get_rect(center=(int(self.x), int(self.y))))


class Obstacle:
    """Oil spill, pothole, or barrier."""
    TYPES = {
        "oil":     {"color": (30, 20, 50),  "w": 50, "h": 30,
                    "label": "OIL",  "effect": "slow"},
        "pothole": {"color": (20, 15, 10),  "w": 40, "h": 40,
                    "label": "HOLE", "effect": "damage"},
        "barrier": {"color": (200, 60, 0),  "w": 44, "h": 22,
                    "label": "!!!",  "effect": "damage"},
    }

    def __init__(self, x, y, kind):
        self.x, self.y = float(x), float(y)
        self.kind      = kind
        info           = self.TYPES[kind]
        self.w, self.h = info["w"], info["h"]
        self.color     = info["color"]
        self.label     = info["label"]
        self.effect    = info["effect"]

    def update(self, scroll_speed):
        self.y += scroll_speed

    def rect(self):
        return pygame.Rect(int(self.x) - self.w // 2,
                           int(self.y) - self.h // 2,
                           self.w, self.h)

    def draw(self, surf):
        r = self.rect()
        pygame.draw.ellipse(surf, self.color, r)
        pygame.draw.ellipse(surf, RED, r, 2)
        lbl = _font(13).render(self.label, True, RED)
        surf.blit(lbl, lbl.get_rect(center=r.center))


class PowerUp:
    TIMEOUT = 300   # frames until it disappears if not collected

    def __init__(self, x, y, kind):
        self.x, self.y = float(x), float(y)
        self.kind  = kind
        self.color = POWERUP_COLORS[kind]
        self.symbol = POWERUP_SYMBOLS[kind]
        self.age   = 0

    def update(self, scroll_speed):
        self.y   += scroll_speed
        self.age += 1

    def alive(self):
        return self.age < self.TIMEOUT

    def rect(self):
        return pygame.Rect(int(self.x) - 16, int(self.y) - 16, 32, 32)

    def draw(self, surf):
        r = self.rect()
        pulse = abs(math.sin(self.age * 0.08)) * 4
        pygame.draw.rect(surf, self.color,
                         r.inflate(int(pulse), int(pulse)), border_radius=6)
        pygame.draw.rect(surf, WHITE, r, 2, border_radius=6)
        txt = _font(18).render(self.symbol, True, WHITE)
        surf.blit(txt, txt.get_rect(center=r.center))


class RoadEvent:
    """Moving barrier or nitro strip — dynamic track events."""
    TYPES = {
        "nitro_strip": {"color": ORANGE, "w": ROAD_W, "h": 12},
        "speedbump":   {"color": (120, 90, 40), "w": ROAD_W, "h": 10},
        "mover":       {"color": RED,  "w": 80,  "h": 18},
    }

    def __init__(self, road: Road, kind):
        self.road  = road
        self.kind  = kind
        info       = self.TYPES[kind]
        self.w, self.h = info["w"], info["h"]
        self.color     = info["color"]
        self.x         = float(road.road_left + road.ROAD_W // 2) if kind != "mover" \
                         else float(road.road_left + 40)
        self.y         = float(-self.h)
        self.dir       = 1  # horizontal direction for mover

    def update(self, scroll_speed):
        self.y += scroll_speed
        if self.kind == "mover":
            self.x += self.dir * 2.5
            if self.x < self.road.road_left + self.w // 2 + 5:
                self.dir =  1
            if self.x > self.road.road_left + ROAD_W - self.w // 2 - 5:
                self.dir = -1

    def rect(self):
        return pygame.Rect(int(self.x) - self.w // 2,
                           int(self.y) - self.h // 2,
                           self.w, self.h)

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, self.color, r, border_radius=4)
        if self.kind == "nitro_strip":
            lbl = _font(13).render("NITRO STRIP", True, WHITE)
            surf.blit(lbl, lbl.get_rect(center=r.center))
        elif self.kind == "speedbump":
            lbl = _font(12).render("BUMP", True, (200, 200, 200))
            surf.blit(lbl, lbl.get_rect(center=r.center))
        elif self.kind == "mover":
            lbl = _font(13).render("BARRIER", True, WHITE)
            surf.blit(lbl, lbl.get_rect(center=r.center))


# ── Main Game Session ─────────────────────────────────────────────────────────

def run_game(screen: pygame.Surface, settings: dict,
             username: str) -> tuple:
    """
    Run one game session.
    Returns (score, distance_meters, coins_total).
    """
    clock   = pygame.time.Clock()
    W, H    = screen.get_size()
    diff    = DIFF[settings.get("difficulty", "normal")]

    road    = Road(W, H)
    player  = PlayerCar(road, settings.get("car_color", "red"))

    # State
    scroll_speed = diff["base_speed"]
    base_speed   = scroll_speed
    coins_list   = []  # list of Coin
    traffic      = []  # list of TrafficCar
    obstacles    = []  # list of Obstacle
    powerups     = []  # list of PowerUp
    events       = []  # list of RoadEvent

    coins_total  = 0
    score        = 0
    distance_px  = 0
    slow_timer   = 0          # frames of slow effect from oil
    active_pu    = None       # currently active power-up name
    active_pu_timer = 0
    pu_bonus     = 0

    frame        = 0
    running      = True
    crashed      = False
    finish       = False

    # Timers (in frames)
    traffic_timer  = diff["traffic_rate"]
    obstacle_timer = diff["obstacle_rate"]
    coin_timer     = diff["coin_rate"]
    event_timer    = 240
    pu_spawn_timer = 180

    def safe_spawn(x, y, w=40, h=50):
        """True if position is safe (not on top of player)."""
        pr = player.rect().inflate(20, 20)
        return not pr.colliderect(pygame.Rect(x - w // 2, y - h // 2, w, h))

    # ── Game loop ──────────────────────────────────────────────────────────────
    while running:
        dt = clock.tick(60)
        frame += 1

        # ── Events ──────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                import sys; pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # ── Input ───────────────────────────────────────────────────────────
        player.handle_input()

        # ── Difficulty scaling ───────────────────────────────────────────────
        scale = 1.0 + coins_total * diff["speed_inc"]
        current_speed = (base_speed * scale * 1.8) if (active_pu == "nitro") else \
                        (base_speed * scale * 0.5) if slow_timer > 0 else \
                        (base_speed * scale)
        current_speed = min(current_speed, base_speed * 3)

        # reduce spawn intervals as difficulty grows
        t_rate = max(30, int(diff["traffic_rate"]  / scale))
        o_rate = max(40, int(diff["obstacle_rate"] / scale))

        if slow_timer > 0:
            slow_timer -= 1

        # ── Active power-up countdown ────────────────────────────────────────
        if active_pu_timer > 0:
            active_pu_timer -= 1
            if active_pu_timer == 0:
                active_pu = None
                player.nitro = False

        # ── Spawning ─────────────────────────────────────────────────────────
        traffic_timer -= 1
        if traffic_timer <= 0:
            traffic_timer = t_rate
            lane = road.random_lane()
            lx   = road.lane_x(lane)
            if safe_spawn(lx, -TRAFFIC_H):
                traffic.append(TrafficCar(lx))

        obstacle_timer -= 1
        if obstacle_timer <= 0:
            obstacle_timer = o_rate
            lane = road.random_lane()
            lx   = road.lane_x(lane)
            if safe_spawn(lx, -60):
                kind = random.choice(["oil", "pothole", "barrier"])
                obstacles.append(Obstacle(lx, -40, kind))

        coin_timer -= 1
        if coin_timer <= 0:
            coin_timer = diff["coin_rate"]
            lx = road.random_lane_x()
            val = _weighted_coin()
            coins_list.append(Coin(lx, -20, val))

        pu_spawn_timer -= 1
        if pu_spawn_timer <= 0:
            pu_spawn_timer = random.randint(200, 400)
            if not powerups:   # at most one on road at a time
                lx   = road.random_lane_x()
                kind = random.choice(POWERUP_TYPES)
                powerups.append(PowerUp(lx, -20, kind))

        event_timer -= 1
        if event_timer <= 0:
            event_timer = random.randint(180, 360)
            kind = random.choice(["nitro_strip", "speedbump", "mover"])
            events.append(RoadEvent(road, kind))

        # ── Update all objects ────────────────────────────────────────────────
        road.update(current_speed)
        player.update()

        for t in traffic:    t.update(current_speed)
        for o in obstacles:  o.update(current_speed)
        for c in coins_list: c.update(current_speed)
        for p in powerups:   p.update(current_speed)
        for e in events:     e.update(current_speed)

        distance_px += current_speed
        dist_m = int(distance_px / 10)

        # ── Collision: traffic ────────────────────────────────────────────────
        pr = player.rect()
        for t in traffic[:]:
            if pr.colliderect(t.rect()):
                if player.shield_active:
                    player.shield_active = False
                    active_pu = None
                    traffic.remove(t)
                else:
                    crashed = True
                    running = False
                    break

        # ── Collision: obstacles ──────────────────────────────────────────────
        if running:
            for o in obstacles[:]:
                if pr.colliderect(o.rect()):
                    if o.effect == "slow" and not player.nitro:
                        slow_timer = 90
                        obstacles.remove(o)
                    elif o.effect == "damage":
                        if player.shield_active:
                            player.shield_active = False
                            active_pu = None
                            obstacles.remove(o)
                        else:
                            crashed = True
                            running = False
                            break

        # ── Collision: road events ────────────────────────────────────────────
        if running:
            for e in events[:]:
                if pr.colliderect(e.rect()):
                    if e.kind in ("nitro_strip", "speedbump"):
                        pass  # cosmetic only
                    elif e.kind == "mover":
                        if player.shield_active:
                            player.shield_active = False
                            active_pu = None
                        else:
                            crashed = True
                            running = False
                            break

        # ── Collect coins ─────────────────────────────────────────────────────
        for c in coins_list[:]:
            if pr.colliderect(c.rect()):
                coins_total += c.value
                score       += c.value * 10
                coins_list.remove(c)

        # ── Collect power-ups ─────────────────────────────────────────────────
        if active_pu is None:   # only one active at a time
            for p in powerups[:]:
                if pr.colliderect(p.rect()):
                    active_pu = p.kind
                    if p.kind == "nitro":
                        player.nitro       = True
                        active_pu_timer    = 60 * 4   # 4 seconds
                        pu_bonus          += 50
                    elif p.kind == "shield":
                        player.shield_active = True
                        active_pu_timer      = 60 * 20  # lasts until hit
                        pu_bonus            += 30
                    elif p.kind == "repair":
                        # Clears nearest obstacle if any
                        if obstacles:
                            obstacles.pop(0)
                        active_pu_timer = 1
                        pu_bonus       += 20
                    powerups.remove(p)
                    break

        # expire timed-out power-ups
        powerups = [p for p in powerups if p.alive()]

        # ── Cull off-screen objects ───────────────────────────────────────────
        traffic   = [t for t in traffic   if t.y < H + 100]
        obstacles = [o for o in obstacles if o.y < H + 100]
        coins_list= [c for c in coins_list if c.y < H + 100]
        events    = [e for e in events    if e.y < H + 100]

        # ── Finish line ───────────────────────────────────────────────────────
        if dist_m >= FINISH_DIST:
            finish  = True
            running = False

        # ── Score update ──────────────────────────────────────────────────────
        score = coins_total * 10 + dist_m // 5 + pu_bonus

        # ══ Draw ════════════════════════════════════════════════════════════
        screen.fill(BG)
        road.draw(screen)

        for e in events:      e.draw(screen)
        for o in obstacles:   o.draw(screen)
        for c in coins_list:  c.draw(screen)
        for p in powerups:    p.draw(screen)
        for t in traffic:     t.draw(screen)
        player.draw(screen)

        _draw_hud(screen, W, score, dist_m, coins_total,
                  active_pu, active_pu_timer, slow_timer, username,
                  current_speed, base_speed)

        pygame.display.flip()

    return score, dist_m, coins_total


def _draw_hud(surf, W, score, dist, coins,
              active_pu, pu_timer, slow_timer, username,
              spd, base_spd):
    f20 = _font(20)
    f16 = _font(16)

    # Left panel
    lines = [
        (f"Player : {username}", WHITE),
        (f"Score  : {score}",    YELLOW),
        (f"Coins  : {coins}",    CYAN),
        (f"Dist   : {dist} m",   GREEN),
        (f"Remain : {max(0, FINISH_DIST - dist)} m", GRAY),
    ]
    for i, (text, col) in enumerate(lines):
        s = f20.render(text, True, col)
        surf.blit(s, (8, 8 + i * 26))

    # Speed bar (right side)
    bar_x, bar_y = W - 110, 10
    bar_h = 120
    ratio = min(spd / (base_spd * 3), 1.0)
    pygame.draw.rect(surf, DARK_GRAY, (bar_x, bar_y, 20, bar_h), border_radius=4)
    fill_h = int(bar_h * ratio)
    col = ORANGE if ratio > 0.7 else GREEN
    pygame.draw.rect(surf, col,
                     (bar_x, bar_y + bar_h - fill_h, 20, fill_h), border_radius=4)
    pygame.draw.rect(surf, WHITE, (bar_x, bar_y, 20, bar_h), 1, border_radius=4)
    s = f16.render("SPD", True, GRAY)
    surf.blit(s, (bar_x - 4, bar_y + bar_h + 4))

    # Power-up display
    pu_y = 145
    if active_pu:
        col  = POWERUP_COLORS.get(active_pu, WHITE)
        secs = pu_timer // 60
        label = f16.render(
            f"{active_pu.upper()} {secs}s" if pu_timer > 1 else active_pu.upper(),
            True, col)
        pygame.draw.rect(surf, (30, 30, 50),
                         (4, pu_y, label.get_width() + 12, 26), border_radius=5)
        pygame.draw.rect(surf, col,
                         (4, pu_y, label.get_width() + 12, 26), 2, border_radius=5)
        surf.blit(label, (10, pu_y + 4))
        pu_y += 32

    if slow_timer > 0:
        s = f16.render("SLOWED!", True, PURPLE)
        surf.blit(s, (10, pu_y))

    # Controls reminder (bottom)
    hint = f16.render("← → / A D  move    ESC pause", True, GRAY)
    surf.blit(hint, hint.get_rect(bottomleft=(8, surf.get_height() - 6)))
