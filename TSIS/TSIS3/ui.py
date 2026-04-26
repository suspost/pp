"""
ui.py — Все экраны, не связанные с игровым процессом:
Главное меню, Настройки, Таблица лидеров, Game Over, Ввод имени.
Отрисовка через чистый Pygame (без внешних библиотек).
"""

import pygame
import sys

# ── Палитра цветов ───────────────────────────────────────────────────────────
BG_DARK     = (15,  15,  25)   # тёмный фон
ROAD_GRAY   = (40,  40,  55)   # цвет дороги
WHITE       = (255, 255, 255)
YELLOW      = (255, 220,  50)
CYAN        = ( 80, 230, 230)
GREEN       = ( 70, 220, 100)
RED         = (220,  60,  60)
ORANGE      = (255, 150,  40)
GRAY        = (120, 120, 140)
DARK_GRAY   = ( 50,  50,  70)
HIGHLIGHT   = ( 60,  60,  90)  # цвет кнопки при наведении

CAR_COLORS = {
    "red":    (220,  60,  60),
    "blue":   ( 60, 120, 220),
    "green":  ( 50, 200,  80),
    "yellow": (255, 210,  40),
}

def _font(size: int) -> pygame.font.Font:
    """Возвращает шрифт с заданным размером (жирное начертание)."""
    return pygame.font.SysFont("consolas,monospace", size, bold=True)

def _draw_button(surf, rect, text, hover=False, color=None):
    """
    Универсальная отрисовка кнопки.
    - rect: прямоугольник кнопки
    - hover: True если мышь над кнопкой (меняет цвет)
    - color: явный цвет фона (если не указан, то DARK_GRAY или HIGHLIGHT)
    """
    col = color if color else (HIGHLIGHT if hover else DARK_GRAY)
    pygame.draw.rect(surf, col, rect, border_radius=8)
    pygame.draw.rect(surf, CYAN, rect, 2, border_radius=8)
    label = _font(22).render(text, True, WHITE)
    surf.blit(label, label.get_rect(center=rect.center))

def _mouse_over(rect) -> bool:
    """Проверяет, находится ли мышь над заданным прямоугольником."""
    return rect.collidepoint(pygame.mouse.get_pos())

# ── Экран ввода имени пользователя ──────────────────────────────────────────
def username_screen(screen: pygame.Surface) -> str:
    """
    Запрашивает имя игрока перед началом игры.
    Логика:
    - Отрисовка поля ввода, курсора в виде "|"
    - Обработка клавиш: буквы, Backspace, Enter
    - При пустом имени выводится ошибка
    - Возвращает введённое имя (обрезает пробелы)
    """
    clock = pygame.time.Clock()
    name = ""
    W, H = screen.get_size()
    error = ""

    while True:
        screen.fill(BG_DARK)
        # Заголовок
        t = _font(46).render("TSIS 3  RACER", True, YELLOW)
        screen.blit(t, t.get_rect(center=(W // 2, H // 4)))

        prompt = _font(26).render("Enter your name:", True, WHITE)
        screen.blit(prompt, prompt.get_rect(center=(W // 2, H // 2 - 40)))

        # Поле ввода
        box = pygame.Rect(W // 2 - 160, H // 2, 320, 48)
        pygame.draw.rect(screen, DARK_GRAY, box, border_radius=6)
        pygame.draw.rect(screen, CYAN, box, 2, border_radius=6)
        txt = _font(28).render(name + "|", True, CYAN)   # курсор
        screen.blit(txt, txt.get_rect(center=box.center))

        btn = pygame.Rect(W // 2 - 80, H // 2 + 80, 160, 46)
        _draw_button(screen, btn, "START", _mouse_over(btn), GREEN)

        if error:
            err = _font(20).render(error, True, RED)
            screen.blit(err, err.get_rect(center=(W // 2, H // 2 + 150)))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if name.strip():
                        return name.strip()
                    else:
                        error = "Name cannot be empty!"
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 16 and event.unicode.isprintable():
                        name += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn.collidepoint(event.pos):
                    if name.strip():
                        return name.strip()
                    else:
                        error = "Name cannot be empty!"

# ── Главное меню ───────────────────────────────────────────────────────────
def main_menu(screen: pygame.Surface) -> str:
    """
    Отображает главное меню с кнопками.
    Возвращает одну из строк: 'play', 'leaderboard', 'settings', 'quit'.
    Логика:
    - Рисует фон дороги
    - Рисует 4 кнопки
    - При клике по кнопке возвращает соответствующее действие
    """
    clock = pygame.time.Clock()
    W, H = screen.get_size()
    BW, BH = 220, 50
    cx = W // 2

    buttons = [
        (pygame.Rect(cx - BW // 2, H // 2 - 10, BW, BH), "PLAY",        "play"),
        (pygame.Rect(cx - BW // 2, H // 2 + 70, BW, BH), "LEADERBOARD", "leaderboard"),
        (pygame.Rect(cx - BW // 2, H // 2 + 150, BW, BH),"SETTINGS",    "settings"),
        (pygame.Rect(cx - BW // 2, H // 2 + 230, BW, BH),"QUIT",        "quit"),
    ]

    while True:
        screen.fill(BG_DARK)
        _draw_road_bg(screen, W, H)   # декоративная дорога на фоне

        title = _font(52).render("TSIS 3  RACER", True, YELLOW)
        screen.blit(title, title.get_rect(center=(cx, H // 4)))
        sub = _font(20).render("Advanced Driving · Power-Ups · Leaderboard", True, GRAY)
        screen.blit(sub, sub.get_rect(center=(cx, H // 4 + 54)))

        for rect, label, _ in buttons:
            _draw_button(screen, rect, label, _mouse_over(rect))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, _, action in buttons:
                    if rect.collidepoint(event.pos):
                        return action
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

def _draw_road_bg(surf, W, H):
    """Рисует простую дорогу на фоне меню (только для декорации)."""
    road_left  = W // 2 - 140
    road_right = W // 2 + 140
    pygame.draw.rect(surf, ROAD_GRAY, (road_left, 0, road_right - road_left, H))
    for y in range(0, H, 60):
        pygame.draw.rect(surf, YELLOW, (W // 2 - 6, y, 12, 30))

# ── Экран настроек ──────────────────────────────────────────────────────────
def settings_screen(screen: pygame.Surface, settings: dict) -> dict:
    """
    Позволяет изменить звук, цвет машины, сложность.
    Возвращает изменённый словарь настроек (сохраняет вызывающий код).
    Логика:
    - Копирует переданные настройки
    - Рисует переключатель звука, палитру цветов, три кнопки сложности
    - При клике изменяет соответствующий ключ в копии
    - Кнопка BACK возвращает обновлённый словарь
    """
    import copy
    s = copy.deepcopy(settings)
    clock = pygame.time.Clock()
    W, H = screen.get_size()
    cx = W // 2

    car_colors_list  = ["red", "blue", "green", "yellow"]
    difficulties     = ["easy", "normal", "hard"]

    back_btn = pygame.Rect(cx - 80, H - 80, 160, 46)

    while True:
        screen.fill(BG_DARK)

        title = _font(38).render("SETTINGS", True, CYAN)
        screen.blit(title, title.get_rect(center=(cx, 60)))

        # ----- Звук: переключатель ON/OFF -----
        y = 140
        label = _font(24).render("Sound:", True, WHITE)
        screen.blit(label, (cx - 200, y))
        tog_rect = pygame.Rect(cx + 20, y - 4, 120, 38)
        tog_col  = GREEN if s["sound"] else RED
        pygame.draw.rect(screen, tog_col, tog_rect, border_radius=6)
        tog_txt = _font(22).render("ON" if s["sound"] else "OFF", True, WHITE)
        screen.blit(tog_txt, tog_txt.get_rect(center=tog_rect.center))

        # ----- Цвет машины: цветовые образцы -----
        SWATCH_Y = 210
        label = _font(24).render("Car Color:", True, WHITE)
        screen.blit(label, (cx - 200, SWATCH_Y))
        for i, col_name in enumerate(car_colors_list):
            cr = pygame.Rect(cx + 10 + i * 52, SWATCH_Y - 4, 44, 38)
            pygame.draw.rect(screen, CAR_COLORS[col_name], cr, border_radius=5)
            if s["car_color"] == col_name:
                pygame.draw.rect(screen, WHITE, cr, 3, border_radius=5)  # обводка выбранного

        # ----- Сложность: три кнопки -----
        y = 290
        label = _font(24).render("Difficulty:", True, WHITE)
        screen.blit(label, (cx - 200, y))
        diff_rects = []
        for i, diff in enumerate(difficulties):
            dr = pygame.Rect(cx + 10 + i * 95, y - 4, 88, 38)
            diff_rects.append((dr, diff))
            active = s["difficulty"] == diff
            pygame.draw.rect(screen, HIGHLIGHT if active else DARK_GRAY, dr, border_radius=6)
            pygame.draw.rect(screen, CYAN, dr, 2, border_radius=6)
            dtxt = _font(20).render(diff.upper(), True, YELLOW if active else WHITE)
            screen.blit(dtxt, dtxt.get_rect(center=dr.center))

        note = _font(17).render("Settings are saved automatically.", True, GRAY)
        screen.blit(note, note.get_rect(center=(cx, H - 120)))

        _draw_button(screen, back_btn, "BACK", _mouse_over(back_btn))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return s
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if tog_rect.collidepoint(mx, my):
                    s["sound"] = not s["sound"]
                for i, col_name in enumerate(car_colors_list):
                    cr = pygame.Rect(cx + 10 + i * 52, SWATCH_Y - 4, 44, 38)
                    if cr.collidepoint(mx, my):
                        s["car_color"] = col_name
                for dr, diff in diff_rects:
                    if dr.collidepoint(mx, my):
                        s["difficulty"] = diff
                if back_btn.collidepoint(mx, my):
                    return s

# ── Таблица лидеров ─────────────────────────────────────────────────────────
def leaderboard_screen(screen: pygame.Surface, entries: list) -> None:
    """
    Отображает топ-10 записей из таблицы рекордов.
    Логика:
    - Рисует заголовок и шапку таблицы
    - Если entries пуст – выводит сообщение
    - Иначе выводит до 10 строк (имя, очки, дистанция, монеты)
    - Кнопка BACK и клавиша ESC возвращают в меню
    """
    clock = pygame.time.Clock()
    W, H = screen.get_size()
    cx = W // 2
    back_btn = pygame.Rect(cx - 80, H - 70, 160, 46)

    while True:
        screen.fill(BG_DARK)
        title = _font(38).render("LEADERBOARD", True, YELLOW)
        screen.blit(title, title.get_rect(center=(cx, 50)))

        # Шапка таблицы
        hdr = _font(18).render(
            f"{'#':<3}  {'NAME':<16}  {'SCORE':>7}  {'DIST(m)':>8}  {'COINS':>5}", True, CYAN)
        screen.blit(hdr, (cx - 240, 100))
        pygame.draw.line(screen, GRAY, (cx - 240, 124), (cx + 240, 124), 1)

        if not entries:
            msg = _font(22).render("No scores yet — be the first!", True, GRAY)
            screen.blit(msg, msg.get_rect(center=(cx, H // 2)))
        else:
            for i, e in enumerate(entries[:10]):
                col = YELLOW if i == 0 else (GRAY if i >= 3 else WHITE)
                row = _font(19).render(
                    f"{i+1:<3}  {e['name']:<16}  {e['score']:>7}  {e['distance']:>8}  {e['coins']:>5}",
                    True, col)
                screen.blit(row, (cx - 240, 135 + i * 34))

        _draw_button(screen, back_btn, "BACK", _mouse_over(back_btn))
        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.collidepoint(event.pos):
                    return

# ── Экран Game Over ─────────────────────────────────────────────────────────
def game_over_screen(screen: pygame.Surface, score: int, distance: int,
                     coins: int) -> str:
    """
    Показывает итоги после завершения игры.
    Возвращает 'retry' (начать заново) или 'menu' (вернуться в главное меню).
    Логика:
    - Отрисовка заголовка GAME OVER
    - Отображение полученных очков, дистанции, монет
    - Две кнопки: RETRY и MAIN MENU
    - Клавиши R (retry) и ESC (menu) для удобства
    """
    clock = pygame.time.Clock()
    W, H = screen.get_size()
    cx = W // 2

    retry_btn = pygame.Rect(cx - 180, H // 2 + 120, 160, 50)
    menu_btn  = pygame.Rect(cx +  20, H // 2 + 120, 160, 50)

    while True:
        screen.fill(BG_DARK)

        title = _font(52).render("GAME  OVER", True, RED)
        screen.blit(title, title.get_rect(center=(cx, H // 4)))

        stats = [
            f"Score    : {score}",
            f"Distance : {distance} m",
            f"Coins    : {coins}",
        ]
        for i, line in enumerate(stats):
            s = _font(26).render(line, True, WHITE)
            screen.blit(s, s.get_rect(center=(cx, H // 2 - 20 + i * 44)))

        _draw_button(screen, retry_btn, "RETRY",     _mouse_over(retry_btn), GREEN)
        _draw_button(screen, menu_btn,  "MAIN MENU", _mouse_over(menu_btn))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if retry_btn.collidepoint(event.pos):
                    return "retry"
                if menu_btn.collidepoint(event.pos):
                    return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "retry"
                if event.key == pygame.K_ESCAPE:
                    return "menu"