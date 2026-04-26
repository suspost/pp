"""
snake.py — Extended Snake (Practice 8 base + all new tasks)

Features added on top of the Practice 8 base:
  ✔ Randomly generated food with different weights (values 1, 3, 5)
  ✔ Food disappears after a timeout (timer shown above food)
  ✔ Wall / border collision → Game Over
  ✔ Food never spawns on a wall or on the snake body
  ✔ Levels: every 5 points eaten → next level
  ✔ Speed increases with each level
  ✔ HUD: score + level counter always visible

Controls:
  Arrow keys / WASD — steer
  R               — restart after Game Over
  ESC             — quit
"""

import pygame
import random
import sys

# ──────────────────────────────────────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────────────────────────────────────

CELL        = 24          # grid cell size in pixels
COLS        = 25          # grid columns  (play area)
ROWS        = 20          # grid rows
HUD_HEIGHT  = 52          # pixels reserved at the top for HUD

WIN_W       = COLS * CELL
WIN_H       = ROWS * CELL + HUD_HEIGHT

FPS_BASE    = 8           # starting FPS (snake moves once per frame)
FPS_PER_LVL = 2           # extra FPS added each level
FPS_MAX     = 22          # cap so the game stays playable

FOOD_TIMEOUT_SEC  = 6.0   # seconds before food disappears
LEVEL_THRESHOLD   = 5     # points needed to advance one level

# ── Palette ────────────────────────────────────────────────────────────────────
BG          = (13,  17,  23)
GRID_LINE   = (22,  28,  36)
WALL_COL    = (45,  55,  72)
WALL_EDGE   = (80,  95, 115)
SNAKE_HEAD  = (80, 220, 120)
SNAKE_BODY  = (50, 170,  90)
SNAKE_OUT   = (30, 100,  55)
HUD_BG      = (18,  24,  32)
HUD_LINE    = (40,  55,  70)
WHITE       = (230, 235, 240)
GRAY        = (110, 120, 135)
RED         = (220,  65,  65)

# Food appearance by weight value
FOOD_STYLES = {
    1:  {"color": (255, 180,  40), "outline": (200, 130,  20), "label": "1"},   # gold
    3:  {"color": ( 80, 190, 255), "outline": ( 40, 130, 210), "label": "3"},   # blue
    5:  {"color": (240,  80, 130), "outline": (180,  40,  80), "label": "5"},   # pink
}
FOOD_WEIGHTS = [1, 1, 1, 3, 3, 5]   # weighted pool: 1 is most common


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────

def cell_rect(col: int, row: int) -> pygame.Rect:
    """Return the pixel Rect for a grid cell (accounting for HUD)."""
    return pygame.Rect(col * CELL, HUD_HEIGHT + row * CELL, CELL, CELL)


def fps_for_level(level: int) -> int:
    return min(FPS_BASE + (level - 1) * FPS_PER_LVL, FPS_MAX)


def font(size: int) -> pygame.font.Font:
    return pygame.font.SysFont("consolas,monospace", size, bold=True)


# ──────────────────────────────────────────────────────────────────────────────
#  Food class
# ──────────────────────────────────────────────────────────────────────────────

class Food:
    def __init__(self, col: int, row: int, value: int):
        self.col   = col
        self.row   = row
        self.value = value
        self.style = FOOD_STYLES[value]
        self.born  = pygame.time.get_ticks()       # ms when spawned
        self.timeout_ms = int(FOOD_TIMEOUT_SEC * 1000)

    def time_left_sec(self) -> float:
        elapsed = pygame.time.get_ticks() - self.born
        return max(0.0, (self.timeout_ms - elapsed) / 1000.0)

    def is_expired(self) -> bool:
        return pygame.time.get_ticks() - self.born >= self.timeout_ms

    def draw(self, surf: pygame.Surface):
        r    = cell_rect(self.col, self.row)
        col  = self.style["color"]
        out  = self.style["outline"]
        secs = self.time_left_sec()

        # Blink fast when < 2 seconds left
        if secs < 2.0 and int(secs * 4) % 2 == 0:
            return   # skip drawing = blink effect

        # Circle food with outline
        cx, cy = r.centerx, r.centery
        pygame.draw.circle(surf, out, (cx, cy), CELL // 2 - 1)
        pygame.draw.circle(surf, col, (cx, cy), CELL // 2 - 3)

        # Value label
        lbl = font(12).render(self.style["label"], True, (20, 20, 20))
        surf.blit(lbl, lbl.get_rect(center=(cx, cy)))

        # Timer arc — thin ring showing time remaining
        frac    = secs / FOOD_TIMEOUT_SEC
        if frac > 0:
            import math
            angle_start = -math.pi / 2
            angle_end   = angle_start + 2 * math.pi * frac
            steps       = max(3, int(30 * frac))
            pts         = [(cx, cy)]
            for i in range(steps + 1):
                a = angle_start + (angle_end - angle_start) * i / steps
                pts.append((cx + math.cos(a) * (CELL // 2 - 1),
                             cy + math.sin(a) * (CELL // 2 - 1)))
            if len(pts) >= 3:
                # Draw as thin arc using lines
                for i in range(1, len(pts) - 1):
                    pygame.draw.line(surf, (255, 255, 255, 80),
                                     pts[i], pts[i + 1], 1)


# ──────────────────────────────────────────────────────────────────────────────
#  Game state
# ──────────────────────────────────────────────────────────────────────────────

class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        # Snake starts in the middle, moving right
        mid_col = COLS // 2
        mid_row = ROWS // 2
        self.snake   = [(mid_col, mid_row),
                        (mid_col - 1, mid_row),
                        (mid_col - 2, mid_row)]
        self.dir     = (1, 0)    # (dc, dr)
        self.next_dir = (1, 0)
        self.score   = 0
        self.level   = 1
        self.foods   : list = []
        self.alive   = True
        self.spawn_food()

    # ── Input ──────────────────────────────────────────────────────────────────

    def handle_key(self, key):
        if not self.alive:
            return
        mapping = {
            pygame.K_UP:    (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN:  (0,  1), pygame.K_s: (0,  1),
            pygame.K_LEFT:  (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1,  0), pygame.K_d: (1,  0),
        }
        if key in mapping:
            nd = mapping[key]
            # Prevent 180° reversal
            if (nd[0] != -self.dir[0]) or (nd[1] != -self.dir[1]):
                self.next_dir = nd

    # ── Food spawning ──────────────────────────────────────────────────────────

    def _occupied_cells(self) -> set:
        """Cells that are walls or snake body — food must not spawn here."""
        occupied = set(self.snake)
        # Border wall cells
        for c in range(COLS):
            occupied.add((c, 0))
            occupied.add((c, ROWS - 1))
        for r in range(ROWS):
            occupied.add((0, r))
            occupied.add((COLS - 1, r))
        # Existing food positions
        for f in self.foods:
            occupied.add((f.col, f.row))
        return occupied

    def spawn_food(self):
        occupied = self._occupied_cells()
        free = [(c, r)
                for c in range(1, COLS - 1)
                for r in range(1, ROWS - 1)
                if (c, r) not in occupied]
        if not free:
            return   # board is full — rare edge case
        col, row = random.choice(free)
        value    = random.choice(FOOD_WEIGHTS)
        self.foods.append(Food(col, row, value))

    # ── Step (one snake move) ─────────────────────────────────────────────────

    def step(self):
        if not self.alive:
            return

        self.dir = self.next_dir
        head     = self.snake[0]
        new_head = (head[0] + self.dir[0], head[1] + self.dir[1])
        nc, nr   = new_head

        # ── Wall collision ────────────────────────────────────────────────────
        if nc <= 0 or nc >= COLS - 1 or nr <= 0 or nr >= ROWS - 1:
            self.alive = False
            return

        # ── Self collision ────────────────────────────────────────────────────
        if new_head in self.snake:
            self.alive = False
            return

        # Move snake forward
        self.snake.insert(0, new_head)

        # ── Check food collision ───────────────────────────────────────────────
        eaten = None
        for f in self.foods:
            if (f.col, f.row) == new_head:
                eaten = f
                break

        if eaten:
            self.score += eaten.value
            self.foods.remove(eaten)
            # Don't pop tail — snake grows
            self._check_level_up()
            self.spawn_food()
        else:
            self.snake.pop()   # normal move — remove tail

        # ── Expire timed-out food ─────────────────────────────────────────────
        before = len(self.foods)
        self.foods = [f for f in self.foods if not f.is_expired()]
        # If food was removed by timeout, spawn a new one
        if len(self.foods) < before:
            self.spawn_food()

        # Always keep at least one food on the board
        if not self.foods:
            self.spawn_food()

    def _check_level_up(self):
        new_level = self.score // LEVEL_THRESHOLD + 1
        if new_level > self.level:
            self.level = new_level

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surf: pygame.Surface):
        surf.fill(BG)
        self._draw_grid(surf)
        self._draw_walls(surf)
        self._draw_foods(surf)
        self._draw_snake(surf)
        self._draw_hud(surf)
        if not self.alive:
            self._draw_game_over(surf)

    def _draw_grid(self, surf):
        for c in range(COLS):
            x = c * CELL
            pygame.draw.line(surf, GRID_LINE, (x, HUD_HEIGHT), (x, WIN_H))
        for r in range(ROWS + 1):
            y = HUD_HEIGHT + r * CELL
            pygame.draw.line(surf, GRID_LINE, (0, y), (WIN_W, y))

    def _draw_walls(self, surf):
        # Top/bottom walls
        for c in range(COLS):
            for r in [0, ROWS - 1]:
                r2 = cell_rect(c, r)
                pygame.draw.rect(surf, WALL_COL, r2)
                pygame.draw.rect(surf, WALL_EDGE, r2, 1)
        # Left/right walls
        for r in range(1, ROWS - 1):
            for c in [0, COLS - 1]:
                r2 = cell_rect(c, r)
                pygame.draw.rect(surf, WALL_COL, r2)
                pygame.draw.rect(surf, WALL_EDGE, r2, 1)

    def _draw_foods(self, surf):
        for f in self.foods:
            f.draw(surf)

    def _draw_snake(self, surf):
        for i, (c, r) in enumerate(self.snake):
            rect = cell_rect(c, r).inflate(-2, -2)
            col  = SNAKE_HEAD if i == 0 else SNAKE_BODY
            pygame.draw.rect(surf, col, rect, border_radius=5)
            pygame.draw.rect(surf, SNAKE_OUT, rect, 1, border_radius=5)
            # Eyes on head
            if i == 0:
                dc, dr = self.dir
                ex = rect.centerx + dc * 5
                ey = rect.centery + dr * 5
                # Two small eyes perpendicular to direction
                perp = (-dr, dc)
                pygame.draw.circle(surf, (15, 15, 15),
                                   (ex + perp[0] * 4, ey + perp[1] * 4), 3)
                pygame.draw.circle(surf, (15, 15, 15),
                                   (ex - perp[0] * 4, ey - perp[1] * 4), 3)

    def _draw_hud(self, surf):
        # HUD background
        pygame.draw.rect(surf, HUD_BG, (0, 0, WIN_W, HUD_HEIGHT))
        pygame.draw.line(surf, HUD_LINE, (0, HUD_HEIGHT), (WIN_W, HUD_HEIGHT), 2)

        f_big  = font(26)
        f_sml  = font(14)

        # Score
        score_lbl = f_sml.render("SCORE", True, GRAY)
        score_val = f_big.render(str(self.score), True, WHITE)
        surf.blit(score_lbl, (16, 6))
        surf.blit(score_val, (16, 22))

        # Level
        lvl_lbl = f_sml.render("LEVEL", True, GRAY)
        lvl_val = f_big.render(str(self.level), True, (80, 220, 120))
        surf.blit(lvl_lbl, (140, 6))
        surf.blit(lvl_val, (140, 22))

        # Speed
        spd_lbl = f_sml.render("SPEED", True, GRAY)
        spd_val = f_big.render(f"{fps_for_level(self.level)} fps", True, (80, 180, 255))
        surf.blit(spd_lbl, (240, 6))
        surf.blit(spd_val, (240, 22))

        # Next level progress bar
        pts_in_level  = self.score % LEVEL_THRESHOLD
        bar_w  = WIN_W - 360 - 16
        bar_x  = 360
        bar_y  = 18
        bar_h  = 16
        if bar_w > 0:
            pygame.draw.rect(surf, (35, 45, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            fill = int(bar_w * pts_in_level / LEVEL_THRESHOLD)
            if fill > 0:
                pygame.draw.rect(surf, (80, 220, 120), (bar_x, bar_y, fill, bar_h), border_radius=4)
            pygame.draw.rect(surf, HUD_LINE, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
            nxt = f_sml.render(f"next lvl {pts_in_level}/{LEVEL_THRESHOLD}", True, GRAY)
            surf.blit(nxt, (bar_x + 4, bar_y + 1))

    def _draw_game_over(self, surf):
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))

        cx, cy = WIN_W // 2, WIN_H // 2
        f_big  = font(48)
        f_med  = font(22)
        f_sml  = font(17)

        go  = f_big.render("GAME  OVER", True, RED)
        sc  = f_med.render(f"Score: {self.score}   Level: {self.level}", True, WHITE)
        rst = f_sml.render("Press  R  to restart   |   ESC  to quit", True, GRAY)

        surf.blit(go,  go.get_rect(center=(cx, cy - 50)))
        surf.blit(sc,  sc.get_rect(center=(cx, cy + 10)))
        surf.blit(rst, rst.get_rect(center=(cx, cy + 50)))


# ──────────────────────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Snake — Extended")
    clock  = pygame.time.Clock()
    game   = Game()

    while True:
        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_r and not game.alive:
                    game = Game()
                game.handle_key(event.key)

        # ── Update ────────────────────────────────────────────────────────────
        game.step()

        # ── Draw ──────────────────────────────────────────────────────────────
        game.draw(screen)
        pygame.display.flip()

        # Speed is determined by current level
        clock.tick(fps_for_level(game.level))


if __name__ == "__main__":
    main()