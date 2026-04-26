# persistence.py
# Модуль для работы с файлами: загрузка/сохранение настроек и рекордов

import json
import os

# Имена файлов для хранения данных
SETTINGS_FILE = "settings.json"
LEADERBOARD_FILE = "leaderboard.json"

# Стандартные настройки на случай, если файл отсутствует или повреждён
DEFAULT_SETTINGS = {
    "sound": True,
    "car_color": "Red",
    "difficulty": "Normal"  # Easy, Normal, Hard
}

def load_settings():
    """Загружает настройки из JSON-файла. При ошибке возвращает настройки по умолчанию."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass   # если файл битый, просто игнорируем
    return DEFAULT_SETTINGS.copy()   # возвращаем копию, чтобы не менять оригинал

def save_settings(settings):
    """Сохраняет настройки в JSON-файл (красивое форматирование)."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def load_leaderboard():
    """Загружает таблицу рекордов (список словарей). При ошибке — пустой список."""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []

def save_score(name, score, distance):
    """
    Сохраняет новый результат в таблицу лидеров.
    - Сортирует по убыванию очков.
    - Оставляет только топ-10 записей.
    """
    lb = load_leaderboard()
    lb.append({"name": name, "score": int(score), "distance": int(distance)})
    # Сортировка: чем больше очков, тем выше позиция
    lb = sorted(lb, key=lambda x: x["score"], reverse=True)[:10]
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(lb, f, indent=4)