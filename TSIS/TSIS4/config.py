# config.py
# Глобальные настройки игры: размеры, цвета, константы механик

import pygame

# Размер окна
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Игровое поле (сетка)
GRID_WIDTH = 20
GRID_HEIGHT = 15
CELL_SIZE = 30
GAME_AREA_TOP = 70
GAME_AREA_LEFT = (WINDOW_WIDTH - GRID_WIDTH * CELL_SIZE) // 2

# Цвета (RGB)
COLOR_BACKGROUND = (20, 20, 30)
COLOR_TEXT = (220, 220, 220)
COLOR_TEXT_DIM = (120, 120, 140)
COLOR_SUCCESS = (0, 200, 100)
COLOR_HIGHLIGHT = (255, 80, 80)
COLOR_BORDER = (80, 80, 100)
COLOR_HEADER_BG = (40, 40, 50)
COLOR_BUTTON_BG = (60, 60, 80)
COLOR_BUTTON_HOVER = (90, 90, 120)
COLOR_BUTTON_TEXT = (255, 255, 255)
COLOR_GRID_LINE = (60, 60, 70)
COLOR_OBSTACLE = (100, 70, 50)

# Змея
COLOR_SNAKE_DEFAULT = (0, 200, 100)
COLOR_SNAKE_HEAD = (0, 230, 120)

# Еда
COLOR_FOOD_NORMAL = (0, 200, 0)
COLOR_FOOD_GOLD = (255, 215, 0)
COLOR_FOOD_DISAPPEARING = (200, 100, 255)
COLOR_POISON = (200, 0, 100)

# Бонусы
COLOR_POWERUP_SPEED = (0, 255, 255)
COLOR_POWERUP_SLOW = (255, 100, 0)
COLOR_POWERUP_SHIELD = (100, 200, 255)

# Шрифты (инициализируются в main, но здесь объявлены)
FONT_TITLE = None
FONT_LARGE = None
FONT_MEDIUM = None
FONT_SMALL = None

# Направления движения
class Direction:
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

# Типы еды
class FoodType:
    NORMAL = 0
    GOLD = 1
    DISAPPEARING = 2
    POISON = 3

# Типы бонусов
class PowerUpType:
    SPEED = 0
    SLOW = 1
    SHIELD = 2

# Игровые константы
BASE_SPEED = 250              # мс между движениями на уровне 1
MIN_SPEED = 80
MAX_SPEED = 500
LEVEL_UP_SCORE = 50           # очков для повышения уровня
OBSTACLE_START_LEVEL = 3      # с какого уровня появляются препятствия
POWERUP_SPAWN_INTERVAL = 10000 # мс между появлением бонусов
POWERUP_LIFETIME = 8000        # сколько бонус висит на поле
POWERUP_DURATION = 5000        # сколько действует активный бонус
FOOD_SPAWN_INTERVAL = 2000     # интервал добавления новой еды (если меньше 3)
DISAPPEARING_FOOD_LIFETIME = 5000