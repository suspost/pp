# main.py
# Точка входа в игру: меню, ввод имени, настройки, таблица лидеров, игровой цикл

import pygame
import sys
from persistence import load_settings, save_settings, load_leaderboard, save_score
from ui import COLORS, FONTS, init_fonts, draw_text, Button
from racer import GameEngine

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSIS3 - Advanced Racer")
clock = pygame.time.Clock()
init_fonts()   # загружаем шрифты один раз

def main():
    app_settings = load_settings()   # загружаем сохранённые настройки
    state = "MENU"                   # состояния: MENU, NAME_INPUT, SETTINGS, LEADERBOARD, PLAYING, GAME_OVER
    username = ""
    game = None

    while True:
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False

        # --- Обработка событий ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(app_settings)
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            if event.type == pygame.KEYDOWN:
                if state == "NAME_INPUT":
                    if event.key == pygame.K_RETURN and username.strip():
                        game = GameEngine(app_settings, WIDTH, HEIGHT)
                        state = "PLAYING"
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    else:
                        if len(username) < 12 and event.unicode.isprintable():
                            username += event.unicode

        screen.fill(COLORS["bg"])

        # ========== МЕНЮ ==========
        if state == "MENU":
            draw_text(screen, "PYTHON RACER", 'large', COLORS["yellow"], (WIDTH//2, 100))
            btn_play = Button(WIDTH//2 - 100, 220, 200, 50, "Play")
            btn_lb   = Button(WIDTH//2 - 100, 290, 200, 50, "Leaderboard")
            btn_set  = Button(WIDTH//2 - 100, 360, 200, 50, "Settings")
            btn_quit = Button(WIDTH//2 - 100, 430, 200, 50, "Quit")
            for b in (btn_play, btn_lb, btn_set, btn_quit):
                b.draw(screen, mouse_pos)
            if btn_play.is_clicked(mouse_pos, mouse_click):
                state = "NAME_INPUT"
                username = ""
            elif btn_lb.is_clicked(mouse_pos, mouse_click):
                state = "LEADERBOARD"
            elif btn_set.is_clicked(mouse_pos, mouse_click):
                state = "SETTINGS"
            elif btn_quit.is_clicked(mouse_pos, mouse_click):
                save_settings(app_settings)
                pygame.quit()
                sys.exit()

        # ========== ВВОД ИМЕНИ ==========
        elif state == "NAME_INPUT":
            draw_text(screen, "Enter Username:", 'large', COLORS["white"], (WIDTH//2, 200))
            draw_text(screen, username + "_", 'large', COLORS["yellow"], (WIDTH//2, 300))
            draw_text(screen, "Press ENTER to start", 'small', COLORS["grey"], (WIDTH//2, 400))

        # ========== НАСТРОЙКИ ==========
        elif state == "SETTINGS":
            draw_text(screen, "SETTINGS", 'large', COLORS["white"], (WIDTH//2, 50))
            draw_text(screen, f"Difficulty: {app_settings['difficulty']}", 'med', COLORS["white"], (250, 170))
            btn_diff = Button(450, 145, 150, 50, "Change")
            draw_text(screen, f"Car Color: {app_settings['car_color']}", 'med', COLORS["white"], (250, 270))
            btn_col  = Button(450, 245, 150, 50, "Change")
            draw_text(screen, f"Sound: {'ON' if app_settings['sound'] else 'OFF'}", 'med', COLORS["white"], (250, 370))
            btn_snd  = Button(450, 345, 150, 50, "Toggle")
            btn_back = Button(WIDTH//2 - 100, 500, 200, 50, "Save & Back")
            for b in (btn_diff, btn_col, btn_snd, btn_back):
                b.draw(screen, mouse_pos)
            if btn_diff.is_clicked(mouse_pos, mouse_click):
                opts = ["Easy", "Normal", "Hard"]
                app_settings["difficulty"] = opts[(opts.index(app_settings["difficulty"]) + 1) % 3]
            if btn_col.is_clicked(mouse_pos, mouse_click):
                opts = ["Red", "Blue", "Green"]
                app_settings["car_color"] = opts[(opts.index(app_settings["car_color"]) + 1) % 3]
            if btn_snd.is_clicked(mouse_pos, mouse_click):
                app_settings["sound"] = not app_settings["sound"]
            if btn_back.is_clicked(mouse_pos, mouse_click):
                save_settings(app_settings)
                state = "MENU"

        # ========== ТАБЛИЦА ЛИДЕРОВ ==========
        elif state == "LEADERBOARD":
            draw_text(screen, "TOP 10 SCORES", 'large', COLORS["yellow"], (WIDTH//2, 50))
            lb = load_leaderboard()
            y = 120
            draw_text(screen, f"{'Rank':<5} {'Name':<15} {'Score':<8} {'Dist'}", 'small', COLORS["cyan"], (WIDTH//2, y))
            y += 40
            for i, entry in enumerate(lb):
                txt = f"{i+1:<5} {entry['name']:<15} {entry['score']:<8} {entry['distance']}m"
                draw_text(screen, txt, 'small', COLORS["white"], (WIDTH//2, y))
                y += 30
            btn_back = Button(WIDTH//2 - 100, 520, 200, 50, "Back")
            btn_back.draw(screen, mouse_pos)
            if btn_back.is_clicked(mouse_pos, mouse_click):
                state = "MENU"

        # ========== ИГРОВОЙ ПРОЦЕСС ==========
        elif state == "PLAYING":
            keys = pygame.key.get_pressed()
            game.update(keys)
            game.draw(screen)
            # Если игра закончена (победа или поражение) – сохраняем результат и переключаемся на экран GAME_OVER
            if game.state in ("GAME_OVER", "WIN"):
                save_score(username, game.score, game.distance)
                state = "GAME_OVER"

        # ========== ЭКРАН ПОСЛЕ ИГРЫ (победа/поражение) ==========
        elif state == "GAME_OVER":
            game.draw(screen)   # рисуем последний кадр гонки
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))   # полупрозрачное затемнение
            screen.blit(overlay, (0, 0))
            title_color = COLORS["green"] if game.state == "WIN" else COLORS["red"]
            title_text = "VICTORY!" if game.state == "WIN" else "CRASHED!"
            draw_text(screen, title_text, 'large', title_color, (WIDTH//2, 150))
            draw_text(screen, f"Score: {game.score}", 'med', COLORS["white"], (WIDTH//2, 230))
            draw_text(screen, f"Distance: {int(game.distance)}m", 'med', COLORS["white"], (WIDTH//2, 280))
            draw_text(screen, f"Coins: {game.coins}", 'med', COLORS["yellow"], (WIDTH//2, 330))
            btn_retry = Button(WIDTH//2 - 160, 400, 150, 50, "Retry")
            btn_menu  = Button(WIDTH//2 + 10,  400, 150, 50, "Main Menu")
            btn_retry.draw(screen, mouse_pos)
            btn_menu.draw(screen, mouse_pos)
            if btn_retry.is_clicked(mouse_pos, mouse_click):
                game.reset()
                state = "PLAYING"
            elif btn_menu.is_clicked(mouse_pos, mouse_click):
                state = "MENU"

        pygame.display.flip()
        clock.tick(60)   # 60 кадров в секунду

if __name__ == "__main__":
    main()