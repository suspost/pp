"""
tools.py — Вспомогательные инструменты для приложения рисования.
Содержит: карандаш, ластик, линия, заливка, текст, история (undo), сохранение.
"""

import pygame
from collections import deque
from datetime import datetime


# ─────────────────────────────────────────────
#  КАРАНДАШ
# ─────────────────────────────────────────────

def draw_pencil(surface, prev_pos, curr_pos, color, size):
    """
    Рисует непрерывную линию между двумя точками.
    Вызывается на каждом кадре, пока зажата кнопка мыши.

    :param surface:   холст, на котором рисуем
    :param prev_pos:  предыдущая позиция мыши (x, y)
    :param curr_pos:  текущая позиция мыши (x, y)
    :param color:     цвет линии (R, G, B)
    :param size:      толщина линии в пикселях
    """
    if prev_pos and curr_pos:
        pygame.draw.line(surface, color, prev_pos, curr_pos, size)
        # Круг в каждой точке — убирает «разрывы» при быстром движении мыши
        pygame.draw.circle(surface, color, curr_pos, size // 2)


# ─────────────────────────────────────────────
#  ЛАСТИК
# ─────────────────────────────────────────────

CANVAS_BG_COLOR = (255, 255, 255)  # цвет фона холста (белый)

def draw_eraser(surface, prev_pos, curr_pos, size):
    """
    Ластик — работает как карандаш, но рисует цветом фона (белым),
    тем самым «стирая» нарисованное.

    Размер ластика в 2 раза больше активного размера кисти —
    так удобнее стирать крупные области.

    :param surface:   холст
    :param prev_pos:  предыдущая позиция мыши
    :param curr_pos:  текущая позиция мыши
    :param size:      базовый размер кисти (будет удвоен)
    """
    if prev_pos and curr_pos:
        eraser_size = size * 2  # ластик крупнее кисти
        pygame.draw.line(surface, CANVAS_BG_COLOR, prev_pos, curr_pos, eraser_size)
        pygame.draw.circle(surface, CANVAS_BG_COLOR, curr_pos, eraser_size // 2)


def draw_eraser_cursor(screen, mouse_pos, size, canvas_top):
    """
    Рисует визуальный курсор ластика — серый кружок с крестиком.
    Помогает пользователю видеть зону стирания ДО нажатия кнопки мыши.

    Отображается только когда мышь находится на холсте (не в тулбаре).

    :param screen:      экран pygame
    :param mouse_pos:   текущая позиция мыши на экране (x, y)
    :param size:        базовый размер кисти
    :param canvas_top:  Y-координата верхней границы холста (= высота тулбара)
    """
    if mouse_pos[1] < canvas_top:
        return  # мышь над тулбаром — курсор не нужен

    eraser_radius = size  # радиус = size (диаметр = size*2, как в draw_eraser)
    cx, cy = mouse_pos

    # Серый контур кружка — границы ластика
    pygame.draw.circle(screen, (150, 150, 150), (cx, cy), eraser_radius, 1)

    # Маленький крестик в центре для точного позиционирования
    cross = 4
    pygame.draw.line(screen, (150, 150, 150), (cx - cross, cy), (cx + cross, cy), 1)
    pygame.draw.line(screen, (150, 150, 150), (cx, cy - cross), (cx, cy + cross), 1)


# ─────────────────────────────────────────────
#  ПРЯМАЯ ЛИНИЯ
# ─────────────────────────────────────────────

def draw_line_preview(temp_surface, start_pos, end_pos, color, size):
    """
    Рисует линию на временном прозрачном холсте — «живой предпросмотр».
    Слой очищается каждый кадр, поэтому линия «тянется» за мышью.

    :param temp_surface: прозрачная поверхность (SRCALPHA) поверх холста
    :param start_pos:    начальная точка (зафиксирована при нажатии мыши)
    :param end_pos:      текущее положение мыши
    :param color:        цвет линии
    :param size:         толщина
    """
    temp_surface.fill((0, 0, 0, 0))  # сбрасываем предыдущий предпросмотр
    pygame.draw.line(temp_surface, color, start_pos, end_pos, size)


def commit_line(canvas, start_pos, end_pos, color, size):
    """
    Окончательно рисует линию на основном холсте при отпускании мыши.
    """
    pygame.draw.line(canvas, color, start_pos, end_pos, size)


# ─────────────────────────────────────────────
#  ЗАЛИВКА (FLOOD-FILL)
# ─────────────────────────────────────────────

def flood_fill(surface, start_x, start_y, fill_color):
    """
    Алгоритм заливки замкнутой области методом BFS (обход в ширину).

    Начинает с пикселя (start_x, start_y) и закрашивает все соседние
    пиксели того же цвета, пока не упрётся в границу другого цвета.

    Используем поверхностные методы get_at() / set_at() без доп. библиотек.

    :param surface:    pygame.Surface — основной холст
    :param start_x:    X точки клика
    :param start_y:    Y точки клика
    :param fill_color: цвет, которым заполняем область (R, G, B)
    """
    width, height = surface.get_size()

    # Запоминаем исходный цвет, который будем заменять
    target_color = surface.get_at((start_x, start_y))[:3]

    # Если цвет уже совпадает — ничего не делаем (иначе будет бесконечный цикл)
    if target_color == tuple(fill_color[:3]):
        return

    queue = deque([(start_x, start_y)])
    visited = {(start_x, start_y)}

    surface.lock()  # блокируем поверхность для быстрого попиксельного доступа

    while queue:
        x, y = queue.popleft()

        # Выход за пределы холста
        if x < 0 or x >= width or y < 0 or y >= height:
            continue

        # Пиксель другого цвета — граница, не закрашиваем
        if surface.get_at((x, y))[:3] != target_color:
            continue

        surface.set_at((x, y), fill_color)  # закрашиваем пиксель

        # Добавляем 4 соседних пикселя (только по сторонам, без диагоналей)
        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))

    surface.unlock()


# ─────────────────────────────────────────────
#  ИСТОРИЯ ДЕЙСТВИЙ (UNDO / ОТМЕНА)
# ─────────────────────────────────────────────

class HistoryManager:
    """
    Менеджер истории для функции «Отменить» (Ctrl+Z).

    После каждого завершённого штриха делает снимок холста.
    При отмене восстанавливает последний сохранённый снимок.

    Используем deque с ограничением maxlen, чтобы не съесть всю память:
    при переполнении старые снимки автоматически удаляются.
    """

    def __init__(self, max_steps=20):
        """
        :param max_steps: максимальная глубина истории отмены
        """
        self.history = deque(maxlen=max_steps)

    def save(self, canvas):
        """
        Сохраняет снимок холста в историю.
        Вызывать после каждого завершённого действия (отпустил мышь и т.п.).

        :param canvas: текущий pygame.Surface холста
        """
        self.history.append(canvas.copy())

    def undo(self, canvas):
        """
        Восстанавливает предыдущий снимок холста.

        :param canvas: холст, который нужно «откатить»
        :return: True если отмена выполнена, False если история пуста
        """
        if not self.history:
            return False  # нечего отменять

        snapshot = self.history.pop()
        canvas.blit(snapshot, (0, 0))  # перерисовываем холст из снимка
        return True


# ─────────────────────────────────────────────
#  ТЕКСТОВЫЙ ИНСТРУМЕНТ
# ─────────────────────────────────────────────

class TextTool:
    """
    Инструмент ввода текста на холст.

    Жизненный цикл:
      1. Клик мышью → фиксируем позицию курсора, активируем режим ввода.
      2. Пользователь печатает → символы появляются в реальном времени.
      3. Enter  → текст рендерится на основной холст и режим завершается.
      4. Escape → ввод отменяется без изменения холста.
    """

    def __init__(self):
        self.active   = False
        self.text     = ""
        self.position = (0, 0)
        self.color    = (0, 0, 0)
        self.font_size = 24
        # SysFont — системный шрифт, не требует внешних файлов
        self.font = pygame.font.SysFont("arial", self.font_size)

    def start(self, pos, color):
        """Начинаем ввод текста в точке pos."""
        self.active   = True
        self.text     = ""
        self.position = pos
        self.color    = color

    def add_char(self, char):
        """Добавляем введённый символ в строку."""
        if self.active:
            self.text += char

    def backspace(self):
        """Удаляем последний символ по нажатию Backspace."""
        if self.active and self.text:
            self.text = self.text[:-1]

    def commit(self, canvas):
        """
        Рендерим итоговый текст на основной холст.
        Вызывается при нажатии Enter.
        """
        if self.active and self.text:
            rendered = self.font.render(self.text, True, self.color)
            canvas.blit(rendered, self.position)
        self.cancel()

    def cancel(self):
        """Сбрасываем состояние без изменения холста (Escape)."""
        self.active = False
        self.text   = ""

    def draw_preview(self, screen, canvas_offset=(0, 0)):
        """
        Рисует предпросмотр текущего текста и мигающий курсор поверх холста.
        Вызывается каждый кадр, пока active == True.

        :param screen:        основной экран pygame
        :param canvas_offset: смещение холста (x, y) — обычно (0, высота тулбара)
        """
        if not self.active:
            return

        preview = self.font.render(self.text, True, self.color)
        x = self.position[0] + canvas_offset[0]
        y = self.position[1] + canvas_offset[1]
        screen.blit(preview, (x, y))

        # Мигающий курсор — меняет видимость каждые 500 мс
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            cursor_x = x + preview.get_width() + 2
            pygame.draw.line(screen, self.color,
                             (cursor_x, y),
                             (cursor_x, y + self.font_size), 2)


# ─────────────────────────────────────────────
#  СОХРАНЕНИЕ ХОЛСТА
# ─────────────────────────────────────────────

def save_canvas(surface):
    """
    Сохраняет холст как PNG с временны́м штампом в имени файла.
    Вызывается по Ctrl+S.

    Пример: canvas_2025-05-14_12-30-45.png

    :param surface: pygame.Surface для сохранения
    :return:        имя сохранённого файла
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename  = f"canvas_{timestamp}.png"
    pygame.image.save(surface, filename)
    print(f"[Сохранено] {filename}")
    return filename