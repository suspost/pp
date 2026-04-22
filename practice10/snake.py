import pygame
import random
import sys

CELL = 20
COLS = 30
ROWS = 25
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL
FPS_BASE = 8
FPS_STEP = 2
FOOD_PER_LEVEL = 3

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GREEN = (0, 160, 0)
GREEN = (0, 200, 0)
RED = (220, 30, 30)
YELLOW = (255, 215, 0)
WALL_COLOR = (80, 80, 80)
BG_COLOR = (15, 15, 15)
GRID_COLOR = (25, 25, 25)

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

def draw_grid(surface):
    for x in range(0, WIDTH, CELL):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (WIDTH, y))

def draw_walls(surface):
    pygame.draw.rect(surface, WALL_COLOR, (0, 0, WIDTH, CELL))
    pygame.draw.rect(surface, WALL_COLOR, (0, HEIGHT-CELL, WIDTH, CELL))
    pygame.draw.rect(surface, WALL_COLOR, (0, 0, CELL, HEIGHT))
    pygame.draw.rect(surface, WALL_COLOR, (WIDTH - CELL, 0, CELL, HEIGHT))

def cell_rect(col, row):
    return pygame.Rect(col * CELL, row * CELL, CELL, CELL)

def random_food_position(snake_body):
    while True:
        col = random.randint(1, COLS - 2)
        row = random.randint(1, ROWS - 2)
        if (col, row) not in snake_body:
            return col, row

def draw_hud(surface, font, score, level):
    score_surf = font.render(f"Score: {score}", True, WHITE)
    level_surf = font.render(f"Level: {level}", True, YELLOW)
    surface.blit(score_surf, (CELL + 4, 2))
    surface.blit(level_surf, (WIDTH // 2 - level_surf.get_width() // 2, 2))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Snake")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 18, bold=True)
    big_font = pygame.font.SysFont("Consolas", 40, bold=True)

    snake = [(COLS // 2, ROWS // 2), (COLS // 2 - 1, ROWS // 2), (COLS // 2 - 2, ROWS // 2)]
    direction = RIGHT
    next_direction = RIGHT
    food = random_food_position(set(snake))
    score = 0
    level = 1
    food_eaten = 0
    fps = FPS_BASE
    game_over = False
    grow = False

    STEP_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(STEP_EVENT, 1000 // fps)

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and direction != DOWN:
                    next_direction = UP
                elif event.key == pygame.K_DOWN and direction != UP:
                    next_direction = DOWN
                elif event.key == pygame.K_LEFT and direction != RIGHT:
                    next_direction = LEFT
                elif event.key == pygame.K_RIGHT and direction != LEFT:
                    next_direction = RIGHT
                if event.key == pygame.K_r and game_over:
                    main()
                    return

            if event.type == STEP_EVENT and not game_over:
                direction = next_direction
                head_col, head_row = snake[0]
                dc, dr = direction
                new_head = (head_col + dc, head_row + dr)
                new_col, new_row = new_head

                if new_col <= 0 or new_col >= COLS - 1 or new_row <= 0 or new_row >= ROWS - 1:
                    game_over = True
                    continue

                if new_head in snake:
                    game_over = True
                    continue

                snake.insert(0, new_head)

                if new_head == food:
                    score += 10
                    food_eaten += 1
                    food = random_food_position(set(snake))
                    grow = True

                    if food_eaten >= FOOD_PER_LEVEL:
                        level += 1
                        food_eaten = 0
                        fps = FPS_BASE + (level - 1) * FPS_STEP
                        pygame.time.set_timer(STEP_EVENT, 1000 // fps)

                if grow:
                    grow = False
                else:
                    snake.pop()

        screen.fill(BG_COLOR)
        draw_grid(screen)
        draw_walls(screen)

        for i, (col, row) in enumerate(snake):
            color = GREEN if i == 0 else DARK_GREEN
            pygame.draw.rect(screen, color, cell_rect(col, row))
            pygame.draw.rect(screen, BLACK, cell_rect(col, row), 1)

        fx, fy = food
        pygame.draw.ellipse(screen, RED, cell_rect(fx, fy).inflate(-4, -4))

        draw_hud(screen, font, score, level)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            screen.blit(overlay, (0, 0))
            over = big_font.render("GAME OVER", True, RED)
            info = font.render(f"Score: {score} | Level: {level}", True, WHITE)
            restart = font.render("Press R to restart", True, YELLOW)
            screen.blit(over, over.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
            screen.blit(info, info.get_rect(center=(WIDTH//2, HEIGHT//2 + 10)))
            screen.blit(restart, restart.get_rect(center=(WIDTH//2, HEIGHT//2 + 50)))

        pygame.display.flip()

if __name__ == "__main__":
    main()