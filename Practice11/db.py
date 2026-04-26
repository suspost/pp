# db.py
# Хранение результатов игроков (таблица лидеров, личные рекорды)

import psycopg2
from psycopg2.extras import RealDictCursor
from config import *
import os
from datetime import datetime

class Database:
    """Класс для подключения к PostgreSQL и выполнения запросов (игроки, сессии, рекорды)."""
    def __init__(self, dbname="snake_game", user="postgres", password="arai 123", host="localhost", port="5432"):
        # Параметры подключения (можно переопределить через переменные окружения)
        self.conn_params = {
            "dbname": os.getenv("DB_NAME", dbname),
            "user": os.getenv("DB_USER", user),
            "password": os.getenv("DB_PASSWORD", password),
            "host": os.getenv("DB_HOST", host),
            "port": os.getenv("DB_PORT", port),
        }
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Устанавливает соединение с БД. При ошибке выводит сообщение и оставляет self.conn = None."""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            print("Database connected successfully.")
        except psycopg2.OperationalError as e:
            print(f"Database connection failed: {e}")
            self.conn = None

    def create_tables(self):
        """Создаёт таблицы players и game_sessions, если их ещё нет."""
        if not self.conn:
            return
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id       SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id            SERIAL PRIMARY KEY,
                    player_id     INTEGER REFERENCES players(id),
                    score         INTEGER   NOT NULL,
                    level_reached INTEGER   NOT NULL,
                    played_at     TIMESTAMP DEFAULT NOW()
                );
            """)
            self.conn.commit()

    def get_or_create_player(self, username):
        """Возвращает ID игрока. Если такого имени нет – создаёт новую запись."""
        if not self.conn:
            return None
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM players WHERE username = %s;", (username,))
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute("INSERT INTO players (username) VALUES (%s) RETURNING id;", (username,))
            player_id = cur.fetchone()[0]
            self.conn.commit()
            return player_id

    def save_session(self, username, score, level_reached):
        """Сохраняет результат одной игры (очки и достигнутый уровень)."""
        if not self.conn:
            return False
        player_id = self.get_or_create_player(username)
        if player_id is None:
            return False
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO game_sessions (player_id, score, level_reached) VALUES (%s, %s, %s);",
                (player_id, score, level_reached),
            )
            self.conn.commit()
            return True

    def get_top_scores(self, limit=10):
        """Возвращает топ-N рекордов (имя, очки, уровень, дата) в виде списка словарей."""
        if not self.conn:
            return []
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT p.username, gs.score, gs.level_reached, gs.played_at
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                ORDER BY gs.score DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

    def get_personal_best(self, username):
        """Возвращает максимальный счёт игрока (0, если игрок ещё не играл)."""
        if not self.conn:
            return 0
        player_id = self.get_or_create_player(username)
        if player_id is None:
            return 0
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(score) FROM game_sessions WHERE player_id = %s;",
                (player_id,),
            )
            row = cur.fetchone()
            return row[0] or 0

    def close(self):
        """Закрывает соединение с БД."""
        if self.conn:
            self.conn.close()