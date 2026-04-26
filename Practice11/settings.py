# settings.py
# Загрузка и сохранение пользовательских настроек (цвет змейки, сетка, звук)

import json
import os

SETTINGS_FILE = "settings.json"

# Настройки по умолчанию (цвет змеи в формате RGB, сетка выключена, звук включён)
DEFAULT_SETTINGS = {
    "snake_color": [0, 200, 100],
    "grid_overlay": False,
    "sound": True,
}

def load_settings():
    """Загружает настройки из JSON-файла. Если файл повреждён или отсутствует – возвращает значения по умолчанию."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            # Добавляем недостающие ключи из DEFAULT_SETTINGS (на случай обновления игры)
            for key in DEFAULT_SETTINGS:
                if key not in data:
                    data[key] = DEFAULT_SETTINGS[key]
            return data
        except (json.JSONDecodeError, IOError):
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Сохраняет настройки в JSON-файл. Возвращает True при успехе, иначе False."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except IOError:
        return False