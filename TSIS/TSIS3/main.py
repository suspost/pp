"""
main.py — TSIS 3: Racer Game
Точка входа. Оркестрирует экраны с помощью модулей ui, racer и persistence.
Управление в игре:
  ← / A   влево
  → / D   вправо
  ESC     вернуться в главное меню
"""

import pygame
import sys

import persistence
import ui
import racer

def main():
    pygame.init()
    pygame.display.set_caption("TSIS 3 — Racer")

    W, H = 700, 800
    screen = pygame.display.set_mode((W, H))

    # Загружаем сохранённые настройки и таблицу лидеров
    settings    = persistence.load_settings()
    leaderboard = persistence.load_leaderboard()
    username    = ""

    # Конечный автомат состояний
    state = "menu"   # menu | username | play | leaderboard | settings

    while True:
        # --- Главное меню ---
        if state == "menu":
            choice = ui.main_menu(screen)
            if choice == "quit":
                pygame.quit()
                sys.exit()
            elif choice == "play":
                state = "username"
            elif choice == "leaderboard":
                state = "leaderboard"
            elif choice == "settings":
                state = "settings"

        # --- Ввод имени ---
        elif state == "username":
            username = ui.username_screen(screen)
            state    = "play"

        # --- Игровой процесс ---
        elif state == "play":
            # Запуск игровой сессии, получение результатов
            score, distance, coins = racer.run_game(screen, settings, username)

            # Сохраняем результат в таблицу лидеров
            leaderboard = persistence.add_leaderboard_entry(
                username, score, distance, coins)

            # Показываем экран Game Over и решаем, что делать дальше
            outcome = ui.game_over_screen(screen, score, distance, coins)
            if outcome == "retry":
                state = "play"      # начать новую игру
            else:
                state = "menu"      # вернуться в главное меню

        # --- Просмотр таблицы лидеров ---
        elif state == "leaderboard":
            ui.leaderboard_screen(screen, leaderboard)
            state = "menu"

        # --- Настройки ---
        elif state == "settings":
            settings = ui.settings_screen(screen, settings)
            persistence.save_settings(settings)   # сохраняем изменения
            state = "menu"

if __name__ == "__main__":
    main()