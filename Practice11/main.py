# main.py
# Главный цикл приложения: управление состояниями (меню, игра, настройки, таблица лидеров)

import pygame
import sys
from datetime import datetime
from config import *
from db import Database
from settings import load_settings, save_settings
from game import SnakeGame, Button, TextInput

pygame.init()

class App:
    def __init__(self):
        pygame.display.set_caption("Snake Game - TSIS3")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "MENU"                 # MENU / PLAYING / GAME_OVER / LEADERBOARD / SETTINGS
        self.db = Database()
        self.settings = load_settings()
        self.username = ""
        self.current_game = None
        self.leaderboard_data = []

        # UI элементы
        self.menu_buttons = []
        self.game_over_buttons = []
        self.leaderboard_back = None
        self.settings_buttons = []
        self.username_input = None
        self.color_preview = None

        self._init_menu_ui()
        self._init_game_over_ui()
        self._init_leaderboard_ui()
        self._init_settings_ui()

    # ---------- Инициализация UI ----------
    def _init_menu_ui(self):
        bx = WINDOW_WIDTH // 2 - 100
        by = 260
        self.menu_buttons = [
            Button(bx, by, 200, 45, "Play"),
            Button(bx, by + 60, 200, 45, "Leaderboard"),
            Button(bx, by + 120, 200, 45, "Settings"),
            Button(bx, by + 180, 200, 45, "Quit"),
        ]
        self.username_input = TextInput(WINDOW_WIDTH // 2 - 100, 200, 200, 40, max_length=15)
        self.username_input.text = self.username

    def _init_game_over_ui(self):
        bx = WINDOW_WIDTH // 2 - 100
        by = 400
        self.game_over_buttons = [
            Button(bx, by, 200, 45, "Retry"),
            Button(bx, by + 60, 200, 45, "Main Menu"),
        ]

    def _init_leaderboard_ui(self):
        self.leaderboard_back = Button(WINDOW_WIDTH // 2 - 60, WINDOW_HEIGHT - 70, 120, 40, "Back")

    def _init_settings_ui(self):
        bx = WINDOW_WIDTH // 2 - 100
        by = 200
        self.settings_buttons = [
            Button(bx, by, 200, 40, "Toggle Grid"),
            Button(bx, by + 55, 200, 40, "Toggle Sound"),
            Button(bx, by + 110, 200, 40, "Change Snake Color"),
            Button(bx, by + 180, 200, 40, "Save & Back"),
        ]
        self.color_preview = pygame.Rect(bx + 210, by + 110, 40, 40)

    # ---------- Главный цикл ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(60)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        self.db.close()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.state == "MENU":
                self.username_input.handle_event(event)
                self.username = self.username_input.text.strip()
                for i, btn in enumerate(self.menu_buttons):
                    if btn.handle_event(event):
                        if i == 0:   # Play
                            if self.username:
                                self.start_game()
                            else:
                                self.username_input.active = True
                        elif i == 1: # Leaderboard
                            self.load_leaderboard()
                            self.state = "LEADERBOARD"
                        elif i == 2: # Settings
                            self.state = "SETTINGS"
                        elif i == 3: # Quit
                            self.running = False

            elif self.state == "PLAYING":
                result = self.current_game.handle_event(event)
                if result == "pause":
                    self.state = "MENU"

            elif self.state == "GAME_OVER":
                for i, btn in enumerate(self.game_over_buttons):
                    if btn.handle_event(event):
                        if i == 0:
                            self.start_game()
                        elif i == 1:
                            self.state = "MENU"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.start_game()
                    elif event.key == pygame.K_RETURN:
                        self.state = "MENU"

            elif self.state == "LEADERBOARD":
                if self.leaderboard_back.handle_event(event):
                    self.state = "MENU"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "MENU"

            elif self.state == "SETTINGS":
                for i, btn in enumerate(self.settings_buttons):
                    if btn.handle_event(event):
                        if i == 0:
                            self.settings["grid_overlay"] = not self.settings.get("grid_overlay", False)
                        elif i == 1:
                            self.settings["sound"] = not self.settings.get("sound", True)
                        elif i == 2:
                            self.cycle_snake_color()
                        elif i == 3:
                            save_settings(self.settings)
                            self.state = "MENU"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    save_settings(self.settings)
                    self.state = "MENU"

    def cycle_snake_color(self):
        """Перебор предустановленных цветов змеи."""
        presets = [
            [0, 200, 100],   # зелёный
            [0, 150, 255],   # синий
            [255, 100, 50],  # оранжевый
            [200, 50, 200],  # фиолетовый
            [255, 200, 50],  # жёлтый
            [255, 50, 100],  # красный
            [100, 255, 255], # голубой
        ]
        current = self.settings.get("snake_color", [0, 200, 100])
        if current in presets:
            idx = (presets.index(current) + 1) % len(presets)
        else:
            idx = 0
        self.settings["snake_color"] = presets[idx]

    def start_game(self):
        """Запускает новую игру с текущим именем и настройками."""
        if not self.username:
            return
        self.current_game = SnakeGame(self.username, self.db, self.settings)
        self.current_game.generate_obstacles()
        self.state = "PLAYING"

    def load_leaderboard(self):
        """Загружает топ-10 результатов из БД."""
        self.leaderboard_data = self.db.get_top_scores(10)

    def update(self, dt):
        if self.state == "PLAYING" and self.current_game:
            self.current_game.update()
            if self.current_game.game_over:
                self.current_game.save_result()
                self.state = "GAME_OVER"
        elif self.state == "MENU":
            self.username_input.update(dt)

    def draw(self):
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "PLAYING":
            self.current_game.draw(self.screen)
        elif self.state == "GAME_OVER":
            self.current_game.draw(self.screen)
            self.draw_game_over_screen()
        elif self.state == "LEADERBOARD":
            self.draw_leaderboard()
        elif self.state == "SETTINGS":
            self.draw_settings()
        pygame.display.flip()

    # ---------- Отрисовка экранов ----------
    def draw_menu(self):
        self.screen.fill(COLOR_BACKGROUND)
        title = FONT_TITLE.render("SNAKE GAME", True, COLOR_SUCCESS)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 100)))
        sub = FONT_MEDIUM.render("Enter your username:", True, COLOR_TEXT)
        self.screen.blit(sub, sub.get_rect(center=(WINDOW_WIDTH // 2, 170)))
        self.username_input.draw(self.screen)
        if not self.username:
            warn = FONT_SMALL.render("Please enter a username to play", True, COLOR_HIGHLIGHT)
            self.screen.blit(warn, warn.get_rect(center=(WINDOW_WIDTH // 2, 250)))
        for btn in self.menu_buttons:
            btn.draw(self.screen)
        db_status = FONT_SMALL.render("DB: Connected" if self.db.conn else "DB: Offline", True, COLOR_SUCCESS if self.db.conn else COLOR_HIGHLIGHT)
        self.screen.blit(db_status, (20, WINDOW_HEIGHT - 30))
        hint = FONT_SMALL.render("Arrow keys / WASD to move  |  P / ESC to pause", True, COLOR_TEXT_DIM)
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30)))

    def draw_game_over_screen(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        go = FONT_TITLE.render("GAME OVER", True, COLOR_HIGHLIGHT)
        self.screen.blit(go, go.get_rect(center=(WINDOW_WIDTH // 2, 180)))
        score = FONT_LARGE.render(f"Score: {self.current_game.score}", True, COLOR_TEXT)
        self.screen.blit(score, score.get_rect(center=(WINDOW_WIDTH // 2, 260)))
        level = FONT_MEDIUM.render(f"Level Reached: {self.current_game.level}", True, COLOR_TEXT)
        self.screen.blit(level, level.get_rect(center=(WINDOW_WIDTH // 2, 310)))
        best = self.db.get_personal_best(self.username)
        pb = FONT_MEDIUM.render(f"Personal Best: {best}", True, COLOR_SUCCESS)
        self.screen.blit(pb, pb.get_rect(center=(WINDOW_WIDTH // 2, 350)))
        for btn in self.game_over_buttons:
            btn.draw(self.screen)

    def draw_leaderboard(self):
        self.screen.fill(COLOR_BACKGROUND)
        title = FONT_TITLE.render("LEADERBOARD", True, COLOR_SUCCESS)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 60)))
        # Заголовки таблицы
        header_y = 120
        cols = [(80, "Rank"), (200, "Username"), (120, "Score"), (120, "Level"), (180, "Date")]
        x = 60
        for width, text in cols:
            h = FONT_MEDIUM.render(text, True, COLOR_TEXT_DIM)
            self.screen.blit(h, (x, header_y))
            x += width
        pygame.draw.line(self.screen, COLOR_BORDER, (40, header_y + 35), (WINDOW_WIDTH - 40, header_y + 35), 2)

        for i, row in enumerate(self.leaderboard_data):
            y = 165 + i * 38
            rank_color = COLOR_SUCCESS if i == 0 else COLOR_TEXT if i < 3 else COLOR_TEXT_DIM
            rank = FONT_MEDIUM.render(str(i + 1), True, rank_color)
            self.screen.blit(rank, (60, y))
            x = 60 + 200
            user = FONT_MEDIUM.render(row["username"], True, COLOR_TEXT)
            self.screen.blit(user, (x - 120, y))
            score = FONT_MEDIUM.render(str(row["score"]), True, COLOR_TEXT)
            self.screen.blit(score, (x + 20, y))
            level = FONT_MEDIUM.render(str(row["level_reached"]), True, COLOR_TEXT)
            self.screen.blit(level, (x + 140, y))
            date_str = row["played_at"].strftime("%Y-%m-%d %H:%M") if isinstance(row["played_at"], datetime) else str(row["played_at"])[:16]
            date = FONT_SMALL.render(date_str, True, COLOR_TEXT_DIM)
            self.screen.blit(date, (x + 260, y + 4))

        if not self.leaderboard_data:
            empty = FONT_MEDIUM.render("No scores yet. Be the first!", True, COLOR_TEXT_DIM)
            self.screen.blit(empty, empty.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))
        self.leaderboard_back.draw(self.screen)

    def draw_settings(self):
        self.screen.fill(COLOR_BACKGROUND)
        title = FONT_TITLE.render("SETTINGS", True, COLOR_SUCCESS)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 80)))
        for i, btn in enumerate(self.settings_buttons):
            btn.draw(self.screen)
            label = ""
            color = COLOR_TEXT
            if i == 0:
                label = "ON" if self.settings.get("grid_overlay", False) else "OFF"
                color = COLOR_SUCCESS if self.settings.get("grid_overlay", False) else COLOR_HIGHLIGHT
            elif i == 1:
                label = "ON" if self.settings.get("sound", True) else "OFF"
                color = COLOR_SUCCESS if self.settings.get("sound", True) else COLOR_HIGHLIGHT
            elif i == 2:
                pygame.draw.rect(self.screen, self.settings.get("snake_color", [0, 200, 100]), self.color_preview, border_radius=6)
                pygame.draw.rect(self.screen, COLOR_BORDER, self.color_preview, 2, border_radius=6)
            if label:
                lbl = FONT_MEDIUM.render(label, True, color)
                self.screen.blit(lbl, (btn.rect.right + 15, btn.rect.centery - lbl.get_height() // 2))
        hint = FONT_SMALL.render("Changes saved automatically on exit", True, COLOR_TEXT_DIM)
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30)))

if __name__ == "__main__":
    app = App()
    app.run()