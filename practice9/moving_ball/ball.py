import pygame

class Ball:
    def __init__(self, screen_width, screen_height):
        self.radius = 25
        self.color = (255, 0, 0)  # Красный
        self.step = 20
        
        # Начальная позиция (центр экрана)
        self.x = screen_width // 2
        self.y = screen_height // 2
        
        self.screen_width = screen_width
        self.screen_height = screen_height

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

    def move(self, dx, dy):
        # Вычисляем новые координаты
        new_x = self.x + dx
        new_y = self.y + dy

        # Проверка границ (учитываем радиус, чтобы мяч не вылезал краем)
        if self.radius <= new_x <= self.screen_width - self.radius:
            self.x = new_x
        if self.radius <= new_y <= self.screen_height - self.radius:
            self.y = new_y