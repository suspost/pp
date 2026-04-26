# game.py
# Основная логика змейки: движение, еда, бонусы, препятствия, уровни, коллизии

import pygame
import random
import math
from config import *
from db import Database
from settings import load_settings, save_settings
from datetime import datetime

# ========== ВСПОМОГАТЕЛЬНЫЕ UI ЭЛЕМЕНТЫ ==========

class Button:
    """Кнопка с текстом, подсветкой при наведении и обработкой кликов."""
    def __init__(self, x, y, width, height, text, font=FONT_MEDIUM):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.hovered = False
        self.visible = True

    def draw(self, screen):
        if not self.visible:
            return
        color = COLOR_BUTTON_HOVER if self.hovered else COLOR_BUTTON_BG
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_BORDER, self.rect, 2, border_radius=8)
        text_surf = self.font.render(self.text, True, COLOR_BUTTON_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        """Возвращает True, если кнопка была нажата."""
        if not self.visible:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class TextInput:
    """Поле ввода текста с курсором и ограничением длины."""
    def __init__(self, x, y, width, height, font=FONT_MEDIUM, max_length=20):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.max_length = max_length
        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def draw(self, screen):
        color = COLOR_BUTTON_HOVER if self.active else COLOR_BUTTON_BG
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        pygame.draw.rect(screen, COLOR_BORDER, self.rect, 2, border_radius=6)
        display_text = self.text
        text_surf = self.font.render(display_text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        # Обрезаем текст, если он не помещается
        if text_rect.width > self.rect.width - 20:
            text_rect.right = self.rect.right - 10
            screen.blit(text_surf, text_rect)
        else:
            screen.blit(text_surf, text_rect)
        # Мигающий курсор
        if self.active and self.cursor_visible:
            cursor_x = text_rect.right + 2
            pygame.draw.line(screen, COLOR_TEXT, (cursor_x, self.rect.top + 8), (cursor_x, self.rect.bottom - 8), 2)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < self.max_length and event.unicode.isprintable():
                self.text += event.unicode
            return True
        return False

    def update(self, dt):
        """Обновление таймера курсора (мигание каждые 500 мс)."""
        self.cursor_timer += dt
        if self.cursor_timer > 500:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible

# ========== ОСНОВНОЙ КЛАСС ИГРЫ ==========

class SnakeGame:
    """Управляет змейкой, едой, бонусами, препятствиями, уровнями и коллизиями."""
    def __init__(self, username, db, settings):
        self.username = username
        self.db = db
        self.settings = settings
        self.snake_color = settings.get("snake_color", COLOR_SNAKE_DEFAULT)
        self.grid_overlay = settings.get("grid_overlay", False)
        self.sound_enabled = settings.get("sound", True)
        self.personal_best = db.get_personal_best(username) if db else 0
        self.reset_game()

    def reset_game(self):
        """Сбрасывает всё состояние для новой игры."""
        self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]          # начальная позиция
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.score = 0
        self.level = 1
        self.game_over = False
        self.speed = BASE_SPEED                                     # задержка между движениями (мс)
        self.last_move_time = pygame.time.get_ticks()
        self.foods = []                                             # список словарей с едой
        self.powerup = None                                         # активный бонус на поле
        self.powerup_active = None                                  # тип действующего бонуса
        self.powerup_start_time = 0
        self.powerup_spawn_time = pygame.time.get_ticks()
        self.obstacles = set()
        self.shield_active = False
        self.last_food_spawn = pygame.time.get_ticks()
        self.spawn_food()

    def spawn_food(self):
        """Создаёт новую еду на свободной клетке. Тип зависит от вероятности и уровня."""
        if len(self.foods) >= 3:
            return
        pos = self.random_free_position()
        if pos is None:
            return
        rand = random.random()
        if rand < 0.1:
            food_type = FoodType.GOLD
        elif rand < 0.25:
            food_type = FoodType.DISAPPEARING
        elif rand < 0.4 and self.level >= 2:
            food_type = FoodType.POISON
        else:
            food_type = FoodType.NORMAL
        lifetime = DISAPPEARING_FOOD_LIFETIME if food_type == FoodType.DISAPPEARING else None
        self.foods.append({"pos": pos, "type": food_type, "spawned_at": pygame.time.get_ticks(), "lifetime": lifetime})

    def spawn_powerup(self):
        """Создаёт бонус (ускорение, замедление, щит) на случайной свободной клетке."""
        if self.powerup is not None:
            return
        pos = self.random_free_position()
        if pos is None:
            return
        ptype = random.choice([PowerUpType.SPEED, PowerUpType.SLOW, PowerUpType.SHIELD])
        self.powerup = {"pos": pos, "type": ptype, "spawned_at": pygame.time.get_ticks()}

    def random_free_position(self):
        """Ищет случайную клетку, не занятую змеёй, препятствиями, едой или бонусом."""
        occupied = set(self.snake) | self.obstacles
        for food in self.foods:
            occupied.add(food["pos"])
        if self.powerup:
            occupied.add(self.powerup["pos"])
        for _ in range(200):
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in occupied:
                return (x, y)
        # Если долго не находим – возвращаем любую свободную клетку
        free = [(x, y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT) if (x, y) not in occupied]
        if free:
            return random.choice(free)
        return None

    def generate_obstacles(self):
        """Генерирует препятствия (камни/стены) начиная с определённого уровня."""
        if self.level < OBSTACLE_START_LEVEL:
            self.obstacles = set()
            return
        count = 5 + self.level * 2
        occupied = set(self.snake)
        for food in self.foods:
            occupied.add(food["pos"])
        if self.powerup:
            occupied.add(self.powerup["pos"])
        obstacles = set()
        for _ in range(count * 5):
            if len(obstacles) >= count:
                break
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)
            if (x, y) in occupied or (x, y) in obstacles:
                continue
            # Проверка, не заблокирует ли препятствие змею (BFS)
            if self.traps_snake(self.snake[0], obstacles | {(x, y)}):
                continue
            obstacles.add((x, y))
        self.obstacles = obstacles

    def traps_snake(self, head, obstacles):
        """BFS-проверка: не заперта ли голова змеи препятствиями (доступно <10 клеток)."""
        visited = set()
        queue = [head]
        visited.add(head)
        free_count = 0
        while queue and free_count < 50:
            cx, cy = queue.pop(0)
            free_count += 1
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    if (nx, ny) not in obstacles and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
        return free_count < 10

    def handle_event(self, event):
        """Обрабатывает нажатия клавиш для изменения направления или паузы."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                if self.direction != Direction.DOWN:
                    self.next_direction = Direction.UP
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                if self.direction != Direction.UP:
                    self.next_direction = Direction.DOWN
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                if self.direction != Direction.RIGHT:
                    self.next_direction = Direction.LEFT
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                if self.direction != Direction.LEFT:
                    self.next_direction = Direction.RIGHT
            elif event.key in (pygame.K_p, pygame.K_ESCAPE):
                return "pause"
        return None

    def update(self):
        """Основной игровой цикл (движение, коллизии, спавн, уровни). Вызывается 60 раз в секунду."""
        if self.game_over:
            return

        now = pygame.time.get_ticks()

        # ---- Истечение срока жизни бонуса на поле ----
        if self.powerup and now - self.powerup["spawned_at"] > POWERUP_LIFETIME:
            self.powerup = None

        # ---- Истечение активного бонуса (кроме щита) ----
        if self.powerup_active and self.powerup_active != PowerUpType.SHIELD:
            if now - self.powerup_start_time > POWERUP_DURATION:
                self.powerup_active = None
                self.speed = max(MIN_SPEED, BASE_SPEED - self.level * 10)

        # ---- Спавн нового бонуса, если прошёл интервал ----
        if self.powerup is None and now - self.powerup_spawn_time > POWERUP_SPAWN_INTERVAL:
            self.spawn_powerup()
            self.powerup_spawn_time = now

        # ---- Удаление исчезающей еды (disappearing) ----
        new_foods = []
        for food in self.foods:
            if food["lifetime"] and now - food["spawned_at"] > food["lifetime"]:
                continue
            new_foods.append(food)
        self.foods = new_foods

        # ---- Периодическое добавление новой еды (максимум 3 штуки) ----
        if now - self.last_food_spawn > FOOD_SPAWN_INTERVAL:
            self.spawn_food()
            self.last_food_spawn = now

        # ---- Движение змеи по таймеру (self.speed мс) ----
        if now - self.last_move_time < self.speed:
            return
        self.last_move_time = now
        self.direction = self.next_direction

        # ---- Вычисление новой головы ----
        head_x, head_y = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)

        # ---- Столкновение со стенами ----
        if new_head[0] < 0 or new_head[0] >= GRID_WIDTH or new_head[1] < 0 or new_head[1] >= GRID_HEIGHT:
            if self.shield_active:
                self.shield_active = False
                self.powerup_active = None
                # Эффект "выхода с другой стороны"
                new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)
            else:
                self.game_over = True
                return

        # ---- Столкновение с собой ----
        if new_head in self.snake:
            if self.shield_active:
                self.shield_active = False
                self.powerup_active = None
                # Удаляем столкнувшийся сегмент, если это не хвост
                if new_head in self.snake[:-1]:
                    self.snake.remove(new_head)
            else:
                self.game_over = True
                return

        # ---- Столкновение с препятствием ----
        if new_head in self.obstacles:
            if self.shield_active:
                self.shield_active = False
                self.powerup_active = None
                self.obstacles.discard(new_head)   # щит разрушает препятствие
            else:
                self.game_over = True
                return

        self.snake.insert(0, new_head)

        # ---- Поедание еды ----
        ate = False
        eaten_idx = None
        for i, food in enumerate(self.foods):
            if food["pos"] == new_head:
                ftype = food["type"]
                if ftype == FoodType.NORMAL:
                    self.score += 10
                elif ftype == FoodType.GOLD:
                    self.score += 20
                elif ftype == FoodType.DISAPPEARING:
                    self.score += 15
                elif ftype == FoodType.POISON:
                    self.score = max(0, self.score - 5)
                    # Отравленная еда укорачивает змею на 2 сегмента
                    if len(self.snake) > 2:
                        self.snake.pop()
                        self.snake.pop()
                    else:
                        self.game_over = True
                        return
                ate = True
                eaten_idx = i
                break

        if eaten_idx is not None:
            self.foods.pop(eaten_idx)
            self.spawn_food()

        # ---- Поедание бонуса ----
        if self.powerup and self.powerup["pos"] == new_head:
            ptype = self.powerup["type"]
            self.powerup_active = ptype
            self.powerup_start_time = pygame.time.get_ticks()
            self.powerup = None
            self.powerup_spawn_time = pygame.time.get_ticks()
            if ptype == PowerUpType.SPEED:
                self.speed = max(MIN_SPEED, self.speed - 50)   # увеличиваем скорость
            elif ptype == PowerUpType.SLOW:
                self.speed = min(MAX_SPEED, self.speed + 50)   # замедляем
            elif ptype == PowerUpType.SHIELD:
                self.shield_active = True
            ate = True

        # Если ничего не съели – удаляем хвост
        if not ate:
            self.snake.pop()

        # ---- Повышение уровня (каждые LEVEL_UP_SCORE очков) ----
        new_level = 1 + self.score // LEVEL_UP_SCORE
        if new_level > self.level:
            self.level = new_level
            self.speed = max(MIN_SPEED, BASE_SPEED - self.level * 10)   # игра ускоряется с уровнем
            self.generate_obstacles()   # добавляем препятствия

    def draw(self, screen):
        """Отрисовка игрового поля, змеи, еды, бонусов, препятствий и интерфейса."""
        screen.fill(COLOR_BACKGROUND)

        # --- Верхняя панель (счёт, уровень, рекорд, игрок) ---
        pygame.draw.rect(screen, COLOR_HEADER_BG, (0, 0, WINDOW_WIDTH, GAME_AREA_TOP))
        y_center = GAME_AREA_TOP // 2

        score_text = FONT_MEDIUM.render(f"Score: {self.score}", True, COLOR_TEXT)
        screen.blit(score_text, (20, y_center - score_text.get_height() // 2))

        level_text = FONT_MEDIUM.render(f"Level: {self.level}", True, COLOR_TEXT)
        screen.blit(level_text, (200, y_center - level_text.get_height() // 2))

        best_text = FONT_SMALL.render(f"Personal Best: {self.personal_best}", True, COLOR_TEXT_DIM)
        screen.blit(best_text, (340, y_center - best_text.get_height() // 2))

        user_text = FONT_SMALL.render(f"Player: {self.username}", True, COLOR_TEXT_DIM)
        screen.blit(user_text, (540, y_center - user_text.get_height() // 2))

        # Индикатор активного бонуса
        if self.powerup_active:
            names = {PowerUpType.SPEED: "Speed", PowerUpType.SLOW: "Slow", PowerUpType.SHIELD: "Shield"}
            colors = {PowerUpType.SPEED: COLOR_POWERUP_SPEED, PowerUpType.SLOW: COLOR_POWERUP_SLOW, PowerUpType.SHIELD: COLOR_POWERUP_SHIELD}
            name = names[self.powerup_active]
            color = colors[self.powerup_active]
            if self.powerup_active != PowerUpType.SHIELD:
                remaining = max(0, (POWERUP_DURATION - (pygame.time.get_ticks() - self.powerup_start_time)) // 1000)
                name += f" ({remaining}s)"
            ptext = FONT_SMALL.render(name, True, color)
            screen.blit(ptext, (680, y_center - ptext.get_height() // 2))

        # --- Игровая область (сетка) ---
        game_rect = pygame.Rect(GAME_AREA_LEFT, GAME_AREA_TOP, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)
        pygame.draw.rect(screen, COLOR_BORDER, game_rect, 3)

        if self.grid_overlay:
            for x in range(GRID_WIDTH + 1):
                pygame.draw.line(screen, COLOR_GRID_LINE,
                                 (GAME_AREA_LEFT + x * CELL_SIZE, GAME_AREA_TOP),
                                 (GAME_AREA_LEFT + x * CELL_SIZE, GAME_AREA_TOP + GRID_HEIGHT * CELL_SIZE))
            for y in range(GRID_HEIGHT + 1):
                pygame.draw.line(screen, COLOR_GRID_LINE,
                                 (GAME_AREA_LEFT, GAME_AREA_TOP + y * CELL_SIZE),
                                 (GAME_AREA_LEFT + GRID_WIDTH * CELL_SIZE, GAME_AREA_TOP + y * CELL_SIZE))

        # --- Препятствия (серые квадраты) ---
        for ox, oy in self.obstacles:
            rect = pygame.Rect(GAME_AREA_LEFT + ox * CELL_SIZE, GAME_AREA_TOP + oy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, COLOR_OBSTACLE, rect)
            pygame.draw.rect(screen, (80, 80, 80), rect, 1)

        # --- Еда (круги: зелёная, золотая, исчезающая, яд) ---
        for food in self.foods:
            fx, fy = food["pos"]
            center = (GAME_AREA_LEFT + fx * CELL_SIZE + CELL_SIZE // 2, GAME_AREA_TOP + fy * CELL_SIZE + CELL_SIZE // 2)
            ftype = food["type"]
            if ftype == FoodType.NORMAL:
                pygame.draw.circle(screen, COLOR_FOOD_NORMAL, center, CELL_SIZE // 2 - 2)
            elif ftype == FoodType.GOLD:
                pygame.draw.circle(screen, COLOR_FOOD_GOLD, center, CELL_SIZE // 2 - 2)
                pygame.draw.circle(screen, (255, 255, 200), center, CELL_SIZE // 2 - 5, 2)
            elif ftype == FoodType.DISAPPEARING:
                # Эффект затухания (альфа-канал эмулируется смешиванием)
                alpha = max(0.3, 1.0 - (pygame.time.get_ticks() - food["spawned_at"]) / food["lifetime"])
                color = tuple(int(c * alpha + 255 * (1 - alpha)) for c in COLOR_FOOD_DISAPPEARING)
                pygame.draw.circle(screen, COLOR_FOOD_DISAPPEARING, center, CELL_SIZE // 2 - 2)
            elif ftype == FoodType.POISON:
                pygame.draw.polygon(screen, COLOR_POISON, [
                    (center[0], center[1] - CELL_SIZE // 2 + 2),
                    (center[0] + CELL_SIZE // 2 - 2, center[1]),
                    (center[0], center[1] + CELL_SIZE // 2 - 2),
                    (center[0] - CELL_SIZE // 2 + 2, center[1]),
                ])

        # --- Бонус (пульсирующий круг) ---
        if self.powerup:
            px, py = self.powerup["pos"]
            center = (GAME_AREA_LEFT + px * CELL_SIZE + CELL_SIZE // 2, GAME_AREA_TOP + py * CELL_SIZE + CELL_SIZE // 2)
            colors = {PowerUpType.SPEED: COLOR_POWERUP_SPEED, PowerUpType.SLOW: COLOR_POWERUP_SLOW, PowerUpType.SHIELD: COLOR_POWERUP_SHIELD}
            color = colors[self.powerup["type"]]
            radius = CELL_SIZE // 2 - 2
            pulse = math.sin(pygame.time.get_ticks() / 200) * 3
            pygame.draw.circle(screen, color, center, int(radius + pulse))

        # --- Змея (сегменты, голова светлее) ---
        for i, (sx, sy) in enumerate(self.snake):
            rect = pygame.Rect(GAME_AREA_LEFT + sx * CELL_SIZE, GAME_AREA_TOP + sy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            color = self.snake_color if i > 0 else COLOR_SNAKE_HEAD
            pygame.draw.rect(screen, color, rect.inflate(-1, -1), border_radius=4)
            if i == 0:   # глаза
                pygame.draw.rect(screen, (255, 255, 255), rect.inflate(-6, -6), border_radius=2)

        # --- Щит вокруг головы (если активен) ---
        if self.shield_active:
            sx, sy = self.snake[0]
            center = (GAME_AREA_LEFT + sx * CELL_SIZE + CELL_SIZE // 2, GAME_AREA_TOP + sy * CELL_SIZE + CELL_SIZE // 2)
            pygame.draw.circle(screen, COLOR_POWERUP_SHIELD, center, CELL_SIZE, 2)

        # --- Оверлей GAME OVER (если игра окончена) ---
        if self.game_over:
            self.draw_game_over_overlay(screen)

    def draw_game_over_overlay(self, screen):
        """Затемнение экрана и текст окончания игры."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        go_text = FONT_LARGE.render("GAME OVER", True, COLOR_HIGHLIGHT)
        screen.blit(go_text, go_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40)))
        score_text = FONT_MEDIUM.render(f"Final Score: {self.score}", True, COLOR_TEXT)
        screen.blit(score_text, score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10)))
        prompt = FONT_SMALL.render("Press ENTER for menu or R to retry", True, COLOR_TEXT_DIM)
        screen.blit(prompt, prompt.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50)))

    def save_result(self):
        """Сохраняет результат игры в БД и обновляет личный рекорд."""
        if self.db and self.db.conn:
            self.db.save_session(self.username, self.score, self.level)
            new_best = self.db.get_personal_best(self.username)
            self.personal_best = new_best