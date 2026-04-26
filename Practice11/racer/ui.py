# ui.py
# Модуль пользовательского интерфейса: цвета, шрифты, отрисовка текста и кнопок

import pygame

# Словарь цветов в формате RGB для удобного доступа
COLORS = {
    "bg": (30, 30, 30),          # фон меню
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "grey": (100, 100, 100),
    "dark_grey": (50, 50, 50),
    "red": (220, 50, 50),
    "green": (50, 220, 50),
    "blue": (50, 100, 220),
    "yellow": (240, 240, 50),
    "cyan": (50, 220, 220),
    "magenta": (255, 0, 255),
    "orange": (255, 165, 0),
    "road": (80, 80, 80)         # цвет асфальта
}

FONTS = {}   # глобальный словарь для загруженных шрифтов

def init_fonts():
    """Инициализирует шрифты трёх размеров. Вызывается один раз при старте игры."""
    FONTS['large'] = pygame.font.SysFont("Arial", 48, bold=True)
    FONTS['med'] = pygame.font.SysFont("Arial", 32, bold=True)
    FONTS['small'] = pygame.font.SysFont("Arial", 24)

def draw_text(surface, text, font_key, color, center_pos):
    """
    Универсальная функция для вывода текста.
    - surface: куда рисовать (экран)
    - font_key: 'large'/'med'/'small'
    - color: цвет из COLORS
    - center_pos: координаты центра текста (x, y)
    Возвращает прямоугольник, который занял текст (для коллизий, если нужно).
    """
    txt_surf = FONTS[font_key].render(text, True, color)
    rect = txt_surf.get_rect(center=center_pos)
    surface.blit(txt_surf, rect)
    return rect

class Button:
    """Простая интерактивная кнопка с текстом и подсветкой при наведении мыши."""
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text

    def draw(self, surface, mouse_pos):
        """
        Отрисовка кнопки:
        - серый фон (светлее при наведении)
        - белая рамка
        - текст по центру
        """
        color = COLORS["grey"] if self.rect.collidepoint(mouse_pos) else COLORS["dark_grey"]
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, COLORS["white"], self.rect, 2, border_radius=10)
        draw_text(surface, self.text, 'med', COLORS["white"], self.rect.center)

    def is_clicked(self, mouse_pos, mouse_click):
        """
        Проверяет, была ли кнопка нажата.
        mouse_click = True в момент нажатия левой кнопки мыши.
        """
        return self.rect.collidepoint(mouse_pos) and mouse_click