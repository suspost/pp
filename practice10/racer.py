import pygame
import random
import sys

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
YELLOW = (255, 215, 0)
GRAY = (100, 100, 100)

ROAD_LEFT = 80
ROAD_RIGHT = 420

class PlayerCar(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 70), pygame.SRCALPHA)
        pygame.draw.rect(self.image, RED, (0, 0, 40, 70), border_radius=6)
        pygame.draw.rect(self.image, WHITE, (5, 5, 30, 20), border_radius=3)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)
        self.speed = 5

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > ROAD_LEFT:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < ROAD_RIGHT:
            self.rect.x += self.speed

class EnemyCar(pygame.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()
        self.image = pygame.Surface((40, 70), pygame.SRCALPHA)
        color = random.choice([(0, 100, 200), (0, 180, 0), (180, 0, 180)])
        pygame.draw.rect(self.image, color, (0, 0, 40, 70), border_radius=6)
        pygame.draw.rect(self.image, WHITE, (5, 45, 30, 20), border_radius=3)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(ROAD_LEFT, ROAD_RIGHT - 40)
        self.rect.y = -80
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Coin(pygame.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (12, 12), 12)
        pygame.draw.circle(self.image, (200, 160, 0), (12, 12), 12, 2)
        font = pygame.font.SysFont("Arial", 14, bold=True)
        label = font.render("$", True, (120, 80, 0))
        self.image.blit(label, (6, 4))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(ROAD_LEFT, ROAD_RIGHT - 24)
        self.rect.y = -30
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class RoadStripe:
    def __init__(self):
        self.y = 0
        self.gap = 60

    def update(self, speed):
        self.y = (self.y + speed) % self.gap

    def draw(self, surface):
        x = SCREEN_WIDTH // 2 - 4
        y = self.y - self.gap
        while y < SCREEN_HEIGHT:
            pygame.draw.rect(surface, WHITE, (x, y, 8, 30))
            y += self.gap

def draw_road(surface):
    surface.fill(GRAY)
    pygame.draw.rect(surface, (50, 50, 50), (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_HEIGHT))
    pygame.draw.rect(surface, WHITE, (ROAD_LEFT - 5, 0, 5, SCREEN_HEIGHT))
    pygame.draw.rect(surface, WHITE, (ROAD_RIGHT, 0, 5, SCREEN_HEIGHT))

def draw_hud(surface, font, score, coins_collected):
    score_text = font.render(f"Score: {score}", True, WHITE)
    surface.blit(score_text, (10, 10))
    coin_text = font.render(f"Coins: {coins_collected}", True, YELLOW)
    surface.blit(coin_text, (SCREEN_WIDTH - coin_text.get_width() - 10, 10))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Racer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 22, bold=True)
    big_font = pygame.font.SysFont("Arial", 48, bold=True)

    all_sprites = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    coin_group = pygame.sprite.Group()

    player = PlayerCar()
    all_sprites.add(player)
    stripe = RoadStripe()

    score = 0
    coins_collected = 0
    scroll_speed = 4
    enemy_spawn_timer = 0
    coin_spawn_timer = 0
    game_over = False

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    main()
                    return

        if not game_over:
            score += 1
            if score % 500 == 0:
                scroll_speed = min(scroll_speed + 1, 12)

            enemy_spawn_timer += 1
            if enemy_spawn_timer >= max(40, 80 - score // 200):
                enemy = EnemyCar(scroll_speed)
                enemy_group.add(enemy)
                all_sprites.add(enemy)
                enemy_spawn_timer = 0

            coin_spawn_timer += 1
            if coin_spawn_timer >= random.randint(90, 180):
                coin = Coin(scroll_speed)
                coin_group.add(coin)
                all_sprites.add(coin)
                coin_spawn_timer = 0

            all_sprites.update()
            stripe.update(scroll_speed)

            if pygame.sprite.spritecollide(player, enemy_group, False):
                game_over = True

            collected = pygame.sprite.spritecollide(player, coin_group, True)
            coins_collected += len(collected)

        draw_road(screen)
        stripe.draw(screen)
        all_sprites.draw(screen)
        draw_hud(screen, font, score // 10, coins_collected)

        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            over_text = big_font.render("GAME OVER", True, RED)
            score_text = font.render(f"Score: {score // 10} | Coins: {coins_collected}", True, WHITE)
            restart = font.render("Press R to restart", True, GREEN)
            screen.blit(over_text, over_text.get_rect(center=(SCREEN_WIDTH//2, 180)))
            screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH//2, 250)))
            screen.blit(restart, restart.get_rect(center=(SCREEN_WIDTH//2, 310)))

        pygame.display.flip()

if __name__ == "__main__":
    main()