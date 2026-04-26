import pygame
import math

pygame.init()

# Настройки экрана
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My Paint (Practice 10-11)")

# Палитра цветов
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
COLORS = [BLACK, RED, BLUE, GREEN, YELLOW]

# Инструменты и текущее состояние
current_color = BLACK
current_tool = 'pen' 
drawing = False
start_pos = (0,0)

screen.fill(WHITE)
pygame.display.flip()

clock = pygame.time.Clock()

def draw_menu():
    # Серый задний фон для меню
    pygame.draw.rect(screen, (200, 200, 200), (0, 0, WIDTH, 50))
    
    # Квадраты выбора цвета (Color Selection)
    for i, c in enumerate(COLORS):
        pygame.draw.rect(screen, c, (10 + i * 40, 10, 30, 30))
        # Выделение активного цвета (только если не выбран ластик)
        if current_color == c and current_tool != 'eraser':
            pygame.draw.rect(screen, BLACK, (10 + i * 40, 10, 30, 30), 2)
            
    # Кнопка ластика (Eraser) - Белый квадрат
    pygame.draw.rect(screen, WHITE, (220, 10, 30, 30))
    # Изображение буквы 'E' для ластика (визуальная индикация)
    font_icon = pygame.font.SysFont(None, 24)
    screen.blit(font_icon.render("E", True, BLACK), (228, 17))
    
    if current_tool == 'eraser':
        pygame.draw.rect(screen, BLACK, (220, 10, 30, 30), 2)
        
    # Инфо по горячим клавишам (UI)
    font = pygame.font.SysFont(None, 20)
    info = font.render(f"Tool: {current_tool} | Keys: P(Pen), E(Erase), R(Rect), C(Circle), S(Square), T(R.Tri), Y(Eq.Tri), H(Rhombus)", True, BLACK)
    screen.blit(info, (270, 15))

running = True
screen_copy = screen.copy() # Копия экрана для эффекта "перетаскивания" при рисовании Фигур

while running:
    draw_menu()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            # Управление горячими клавишами
            if event.key == pygame.K_p: current_tool = 'pen'
            elif event.key == pygame.K_e: current_tool = 'eraser'
            elif event.key == pygame.K_r: current_tool = 'rect' # Прямоугольник
            elif event.key == pygame.K_c: current_tool = 'circle' # Круг
            elif event.key == pygame.K_s: current_tool = 'square' # Квадрат
            elif event.key == pygame.K_t: current_tool = 'right_tri' # Прямоугольный треугольник (Right triangle)
            elif event.key == pygame.K_y: current_tool = 'eq_tri' # Равносторонний треугольник (Equilateral triangle)
            elif event.key == pygame.K_h: current_tool = 'rhombus' # Ромб (Rhombus)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                mouse_x, mouse_y = event.pos
                # Проверка клика по меню 
                if mouse_y <= 50:
                    # Выбор цвета
                    for i, c in enumerate(COLORS):
                        if 10 + i * 40 <= mouse_x <= 40 + i * 40:
                            current_color = c
                            if current_tool == 'eraser': current_tool = 'pen'
                    # Выбор ластика
                    if 220 <= mouse_x <= 250:
                        current_tool = 'eraser'
                else:
                    # Начало рисования
                    drawing = True
                    start_pos = event.pos
                    screen_copy = screen.copy() # Сохраняем фон
                    
        elif event.type == pygame.MOUSEMOTION:
            if drawing:
                mouse_pos = event.pos
                
                if current_tool == 'pen':
                    pygame.draw.line(screen, current_color, start_pos, mouse_pos, 5)
                    start_pos = mouse_pos # Обновляем старт для кисти
                    
                elif current_tool == 'eraser':
                    pygame.draw.circle(screen, WHITE, mouse_pos, 15) # Ластик - это просто белый круг
                    
                else:
                    # Все остальные фигуры
                    screen.blit(screen_copy, (0, 0)) # Сбрасываем на момент начала клика, чтобы рисунок не смазывался
                    w = mouse_pos[0] - start_pos[0]
                    h = mouse_pos[1] - start_pos[1]
                    
                    if current_tool == 'rect':
                        pygame.draw.rect(screen, current_color, (start_pos[0], start_pos[1], w, h), 2)
                        
                    elif current_tool == 'circle':
                        radius = int(math.hypot(w, h) / 2)
                        center = (start_pos[0] + w//2, start_pos[1] + h//2)
                        pygame.draw.circle(screen, current_color, center, radius, 2)
                        
                    elif current_tool == 'square':
                        # Квадрат берет максимальное значение между шириной и высотой мыши
                        side = max(abs(w), abs(h))
                        # Сохраняем направление мыши (вверх/вниз и вправо/влево)
                        sq_w = side if w > 0 else -side
                        sq_h = side if h > 0 else -side
                        pygame.draw.rect(screen, current_color, (start_pos[0], start_pos[1], sq_w, sq_h), 2)
                        
                    elif current_tool == 'right_tri':
                        # Прямоугольный треугольник (прямой угол на X начальном, Y конечном)
                        points = [start_pos, (start_pos[0], mouse_pos[1]), mouse_pos]
                        pygame.draw.polygon(screen, current_color, points, 2)
                        
                    elif current_tool == 'eq_tri':
                        # Равнобедренный/Равносторонний треугольник
                        mid_x = start_pos[0] + w/2
                        points = [(mid_x, start_pos[1]), (start_pos[0], mouse_pos[1]), (mouse_pos[0], mouse_pos[1])]
                        pygame.draw.polygon(screen, current_color, points, 2)
                        
                    elif current_tool == 'rhombus':
                        # Ромб
                        mid_x = start_pos[0] + w/2
                        mid_y = start_pos[1] + h/2
                        points = [(mid_x, start_pos[1]), (mouse_pos[0], mid_y), (mid_x, mouse_pos[1]), (start_pos[0], mid_y)]
                        pygame.draw.polygon(screen, current_color, points, 2)
                        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                drawing = False 

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
