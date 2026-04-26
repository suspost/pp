"""
paint.py — Главный модуль приложения для рисования на Pygame.

Запуск:
    python paint.py

Управление:
    Левая кнопка мыши  — рисовать / использовать инструмент
    1 / 2 / 3          — размер кисти (2 / 5 / 10 пикселей)
    E                  — ластик
    P                  — карандаш
    L                  — линия
    F                  — заливка
    T                  — текст
    Ctrl + Z           — отменить последнее действие
    Ctrl + S           — сохранить холст как .png
    Delete             — очистить холст
    Escape             — выйти из текстового режима
    Enter              — подтвердить текст
"""

import pygame
import sys

from tools import (
    draw_pencil,
    draw_eraser,
    draw_eraser_cursor,
    draw_line_preview,
    commit_line,
    flood_fill,
    save_canvas,
    TextTool,
    HistoryManager,
    CANVAS_BG_COLOR,
)

# ─────────────────────────────────────────────
#  КОНСТАНТЫ
# ─────────────────────────────────────────────

WINDOW_WIDTH   = 1100
WINDOW_HEIGHT  = 700
TOOLBAR_HEIGHT = 64       # высота панели инструментов сверху
CANVAS_TOP     = TOOLBAR_HEIGHT

BRUSH_SIZES = [2, 5, 10]  # маленький / средний / большой (пиксели)

# Цветовая палитра (RGB)
PALETTE = [
    (0,   0,   0),    # чёрный
    (255, 255, 255),  # белый
    (220, 50,  50),   # красный
    (50,  180, 50),   # зелёный
    (50,  50,  220),  # синий
    (255, 200, 0),    # жёлтый
    (255, 130, 0),    # оранжевый
    (160, 0,   200),  # фиолетовый
    (0,   200, 200),  # голубой
    (139, 69,  19),   # коричневый
]

# Цвета интерфейса
COLOR_TOOLBAR  = (44,  48,  56)   # тёмный фон тулбара
COLOR_SELECTED = (255, 208, 56)   # жёлтая рамка активного элемента
COLOR_BTN      = (72,  78,  90)   # обычная кнопка
COLOR_CANVAS   = CANVAS_BG_COLOR  # белый холст

# Список инструментов в порядке отображения
TOOLS = ["pencil", "line", "eraser", "fill", "text"]

# Подписи кнопок инструментов
TOOL_LABELS = {
    "pencil": "✏  Карандаш",
    "line":   "╱  Линия",
    "eraser": "⬜ Ластик",
    "fill":   "⬛ Заливка",
    "text":   "T  Текст",
}

# Горячие клавиши для инструментов
TOOL_KEYS = {
    pygame.K_p: "pencil",
    pygame.K_l: "line",
    pygame.K_e: "eraser",
    pygame.K_f: "fill",
    pygame.K_t: "text",
}


# ─────────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────

def draw_toolbar(screen, font, active_tool, brush_idx, active_color, save_msg):
    """
    Отрисовывает всю панель инструментов:
      — кнопки инструментов с подписями
      — кнопки выбора размера кисти
      — палитру цветов
      — уведомление о сохранении / отмене

    :param screen:      экран pygame
    :param font:        шрифт для подписей
    :param active_tool: текущий инструмент (строка-ключ)
    :param brush_idx:   индекс активного размера (0/1/2)
    :param active_color:текущий цвет рисования (R, G, B)
    :param save_msg:    строка уведомления (пустая = не показывать)
    """
    # Фон тулбара
    pygame.draw.rect(screen, COLOR_TOOLBAR, (0, 0, WINDOW_WIDTH, TOOLBAR_HEIGHT))

    # ── Кнопки инструментов ──────────────────
    btn_w, btn_h = 114, 38
    for i, tool in enumerate(TOOLS):
        x = 8 + i * (btn_w + 5)
        y = 13
        rect = pygame.Rect(x, y, btn_w, btn_h)
        color = COLOR_SELECTED if tool == active_tool else COLOR_BTN
        pygame.draw.rect(screen, color, rect, border_radius=7)

        # Текст кнопки: тёмный на выделенной, светлый на обычной
        txt_color = (30, 30, 30) if tool == active_tool else (210, 210, 210)
        label = font.render(TOOL_LABELS[tool], True, txt_color)
        screen.blit(label, (x + 7, y + 10))

    # ── Кнопки размера кисти ─────────────────
    size_labels = ["1: S", "2: M", "3: L"]
    for i, lbl in enumerate(size_labels):
        x = 600 + i * 56
        y = 13
        rect = pygame.Rect(x, y, 50, 38)
        color = COLOR_SELECTED if i == brush_idx else COLOR_BTN
        pygame.draw.rect(screen, color, rect, border_radius=7)
        txt_color = (30, 30, 30) if i == brush_idx else (210, 210, 210)
        screen.blit(font.render(lbl, True, txt_color), (x + 8, y + 10))

    # ── Кнопка «Отменить» ────────────────────
    undo_rect = pygame.Rect(775, 13, 62, 38)
    pygame.draw.rect(screen, COLOR_BTN, undo_rect, border_radius=7)
    screen.blit(font.render("↩ Undo", True, (210, 210, 210)), (780, 23))

    # ── Кнопка «Очистить» ────────────────────
    clear_rect = pygame.Rect(843, 13, 70, 38)
    pygame.draw.rect(screen, COLOR_BTN, clear_rect, border_radius=7)
    screen.blit(font.render("Del Clr", True, (210, 210, 210)), (848, 23))

    # ── Палитра цветов ───────────────────────
    sw = 26  # размер одного образца цвета
    for i, clr in enumerate(PALETTE):
        x = 922 + i * (sw + 3)
        y = 17
        rect = pygame.Rect(x, y, sw, sw)
        pygame.draw.rect(screen, clr, rect)
        # Рамка: жёлтая — выбранный, серая — остальные
        border_color = COLOR_SELECTED if clr == active_color else (120, 120, 120)
        border_w     = 2            if clr == active_color else 1
        pygame.draw.rect(screen, border_color, rect, border_w)

    # ── Уведомление (сохранение / отмена) ────
    if save_msg:
        msg = font.render(save_msg, True, (100, 255, 130))
        screen.blit(msg, (10, TOOLBAR_HEIGHT + 5))


def get_canvas_pos(mouse_pos):
    """Переводит экранные координаты в координаты холста (убирает тулбар)."""
    return (mouse_pos[0], mouse_pos[1] - CANVAS_TOP)


def is_on_canvas(mouse_pos):
    """True, если мышь на холсте, а не в тулбаре."""
    return mouse_pos[1] >= CANVAS_TOP


# ─────────────────────────────────────────────
#  ГЛАВНЫЙ ЦИКЛ
# ─────────────────────────────────────────────

def main():
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("🎨 Paint — Pygame")

    ui_font = pygame.font.SysFont("arial", 14)

    # ── Холст ────────────────────────────────
    canvas_height = WINDOW_HEIGHT - CANVAS_TOP
    canvas = pygame.Surface((WINDOW_WIDTH, canvas_height))
    canvas.fill(COLOR_CANVAS)

    # ── Временный слой предпросмотра (прозрачный) ──
    temp_surface = pygame.Surface((WINDOW_WIDTH, canvas_height), pygame.SRCALPHA)
    temp_surface.fill((0, 0, 0, 0))

    # ── Менеджер истории для Undo ─────────────
    history = HistoryManager(max_steps=20)
    history.save(canvas)  # сохраняем начальное состояние (чистый холст)

    # ── Инструменты и состояние ──────────────
    active_tool  = "pencil"
    brush_idx    = 1
    active_color = PALETTE[0]

    drawing    = False
    prev_pos   = None
    line_start = None

    text_tool = TextTool()

    save_message = ""
    save_timer   = 0

    clock = pygame.time.Clock()

    # ─────────────────────────────────────────
    #  ОСНОВНОЙ ИГРОВОЙ ЦИКЛ
    # ─────────────────────────────────────────
    while True:
        dt = clock.tick(60)  # 60 FPS

        # Таймер уведомления
        if save_timer > 0:
            save_timer -= dt
            if save_timer <= 0:
                save_message = ""

        # ── Обработка событий ────────────────
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ── Клавиши ──────────────────────
            if event.type == pygame.KEYDOWN:

                ctrl = event.mod & pygame.KMOD_CTRL  # зажат ли Ctrl

                # Ctrl+S — сохранить
                if event.key == pygame.K_s and ctrl:
                    fname = save_canvas(canvas)
                    save_message = f"Сохранено: {fname}"
                    save_timer = 3000

                # Ctrl+Z — отменить последнее действие
                elif event.key == pygame.K_z and ctrl:
                    if history.undo(canvas):
                        save_message = "Действие отменено"
                        save_timer = 1500

                # Delete — очистить холст
                elif event.key == pygame.K_DELETE and not text_tool.active:
                    history.save(canvas)          # сохраняем перед очисткой
                    canvas.fill(COLOR_CANVAS)
                    save_message = "Холст очищен"
                    save_timer = 1500

                # Переключение размера кисти
                elif event.key == pygame.K_1:
                    brush_idx = 0
                elif event.key == pygame.K_2:
                    brush_idx = 1
                elif event.key == pygame.K_3:
                    brush_idx = 2

                # Горячие клавиши инструментов (когда текст не активен)
                elif not text_tool.active and event.key in TOOL_KEYS:
                    active_tool = TOOL_KEYS[event.key]

                # Ввод текста
                elif text_tool.active:
                    if event.key == pygame.K_RETURN:
                        history.save(canvas)      # сохраняем перед изменением
                        text_tool.commit(canvas)
                    elif event.key == pygame.K_ESCAPE:
                        text_tool.cancel()
                    elif event.key == pygame.K_BACKSPACE:
                        text_tool.backspace()
                    elif event.unicode:
                        text_tool.add_char(event.unicode)

            # ── Нажатие кнопки мыши ──────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mpos = pygame.mouse.get_pos()

                # — Клик в тулбаре —
                if not is_on_canvas(mpos):
                    btn_w = 114
                    # Кнопки инструментов
                    for i, tool in enumerate(TOOLS):
                        r = pygame.Rect(8 + i * (btn_w + 5), 13, btn_w, 38)
                        if r.collidepoint(mpos):
                            active_tool = tool

                    # Кнопки размера
                    for i in range(3):
                        r = pygame.Rect(600 + i * 56, 13, 50, 38)
                        if r.collidepoint(mpos):
                            brush_idx = i

                    # Кнопка Undo
                    if pygame.Rect(775, 13, 62, 38).collidepoint(mpos):
                        if history.undo(canvas):
                            save_message = "Действие отменено"
                            save_timer = 1500

                    # Кнопка Очистить
                    if pygame.Rect(843, 13, 70, 38).collidepoint(mpos):
                        history.save(canvas)
                        canvas.fill(COLOR_CANVAS)
                        save_message = "Холст очищен"
                        save_timer = 1500

                    # Палитра цветов
                    sw = 26
                    for i, clr in enumerate(PALETTE):
                        r = pygame.Rect(922 + i * (sw + 3), 17, sw, sw)
                        if r.collidepoint(mpos):
                            active_color = clr

                # — Клик на холсте —
                else:
                    cpos = get_canvas_pos(mpos)
                    bsize = BRUSH_SIZES[brush_idx]

                    if active_tool == "pencil":
                        history.save(canvas)   # снимок ДО штриха
                        drawing  = True
                        prev_pos = cpos

                    elif active_tool == "eraser":
                        history.save(canvas)   # снимок ДО стирания
                        drawing  = True
                        prev_pos = cpos

                    elif active_tool == "line":
                        history.save(canvas)   # снимок ДО линии
                        drawing    = True
                        line_start = cpos

                    elif active_tool == "fill":
                        history.save(canvas)   # снимок ДО заливки
                        flood_fill(canvas, cpos[0], cpos[1], active_color)

                    elif active_tool == "text":
                        if text_tool.active:
                            history.save(canvas)
                            text_tool.commit(canvas)
                        text_tool.start(cpos, active_color)

            # ── Отпускание кнопки мыши ───────
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mpos = pygame.mouse.get_pos()

                if drawing and is_on_canvas(mpos):
                    cpos  = get_canvas_pos(mpos)
                    bsize = BRUSH_SIZES[brush_idx]

                    if active_tool == "line" and line_start:
                        # Фиксируем линию на основном холсте
                        commit_line(canvas, line_start, cpos, active_color, bsize)
                        temp_surface.fill((0, 0, 0, 0))

                # Сбрасываем флаги рисования
                drawing    = False
                prev_pos   = None
                line_start = None

        # ── Непрерывный ввод мыши ────────────
        if drawing:
            mpos  = pygame.mouse.get_pos()
            if is_on_canvas(mpos):
                cpos  = get_canvas_pos(mpos)
                bsize = BRUSH_SIZES[brush_idx]

                if active_tool == "pencil":
                    draw_pencil(canvas, prev_pos, cpos, active_color, bsize)
                    prev_pos = cpos

                elif active_tool == "eraser":
                    # Ластик рисует белым (цвет фона), стирая содержимое
                    draw_eraser(canvas, prev_pos, cpos, bsize)
                    prev_pos = cpos

                elif active_tool == "line" and line_start:
                    draw_line_preview(temp_surface, line_start, cpos, active_color, bsize)

        # ── Отрисовка кадра ──────────────────

        # 1. Фон окна
        screen.fill((230, 230, 235))

        # 2. Основной холст
        screen.blit(canvas, (0, CANVAS_TOP))

        # 3. Слой предпросмотра линии (прозрачный)
        screen.blit(temp_surface, (0, CANVAS_TOP))

        # 4. Курсор ластика — рисуется ПОВЕРХ всего (когда ластик активен)
        if active_tool == "eraser" and not drawing:
            mpos  = pygame.mouse.get_pos()
            bsize = BRUSH_SIZES[brush_idx]
            draw_eraser_cursor(screen, mpos, bsize, CANVAS_TOP)

        # 5. Предпросмотр текста с мигающим курсором
        text_tool.draw_preview(screen, canvas_offset=(0, CANVAS_TOP))

        # 6. Тулбар (поверх всего — перекрывает верхний край холста)
        draw_toolbar(screen, ui_font, active_tool, brush_idx, active_color, save_message)

        pygame.display.flip()


# ─────────────────────────────────────────────
#  ТОЧКА ВХОДА
# ─────────────────────────────────────────────
if __name__ == "__main__":
    main()