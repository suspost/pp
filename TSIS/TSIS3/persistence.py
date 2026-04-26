"""
persistence.py — Сохранение/загрузка таблицы лидеров и настроек в/из JSON.
"""

import json
import os

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "sound": True,
    "car_color": "red",       # red | blue | green | yellow
    "difficulty": "normal",   # easy | normal | hard
}

# ── Настройки ──────────────────────────────────────────────────────────────
def load_settings() -> dict:
    """
    Загружает настройки из settings.json.
    Если файла нет или он повреждён – возвращает DEFAULT_SETTINGS.
    Недостающие ключи добавляются (обратная совместимость).
    """
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                data.setdefault(k, v)
            return data
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_SETTINGS)

def save_settings(settings: dict) -> None:
    """Сохраняет настройки в settings.json."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except IOError as e:
        print(f"[persistence] Could not save settings: {e}")

# ── Таблица лидеров ────────────────────────────────────────────────────────
def load_leaderboard() -> list:
    """
    Загружает список рекордов.
    Каждая запись: {'name': str, 'score': int, 'distance': int, 'coins': int}
    """
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, IOError):
            pass
    return []

def save_leaderboard(entries: list) -> None:
    """Сохраняет таблицу лидеров в JSON."""
    try:
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(entries, f, indent=2)
    except IOError as e:
        print(f"[persistence] Could not save leaderboard: {e}")

def add_leaderboard_entry(name: str, score: int, distance: int, coins: int) -> list:
    """
    Добавляет новый результат в таблицу лидеров.
    Логика:
    1. Загрузить текущие записи.
    2. Добавить новую.
    3. Отсортировать по убыванию score.
    4. Оставить только топ-10.
    5. Сохранить и вернуть обновлённый список.
    """
    entries = load_leaderboard()
    entries.append({"name": name, "score": score, "distance": distance, "coins": coins})
    entries.sort(key=lambda e: e["score"], reverse=True)
    entries = entries[:10]
    save_leaderboard(entries)
    return entries