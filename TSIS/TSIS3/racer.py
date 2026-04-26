# racer.py
# Основной игровой движок: физика, спавн объектов, коллизии, эффекты

import pygame
import random
import time
from ui import COLORS, FONTS

# Константы дороги (фиксированные границы)
ROAD_LEFT = 150
ROAD_RIGHT = 650
ROAD_WIDTH = ROAD_RIGHT - ROAD_LEFT
FINISH_DISTANCE = 5000   # сколько метров нужно проехать для победы

class GameEngine:
    """Управляет всеми игровыми сущностями и правилами."""
    def __init__(self, settings, width, height):
        self.settings = settings   # словарь с настройками (сложность, цвет машины, звук)
        self.width = width
        self.height = height
        self.reset()

    def reset(self):
        """Сбрасывает игру до начального состояния (новая игра)."""
        # --- Сложность определяет базовую скорость движения мира ---
        diff_map = {"Easy": 4, "Normal": 6, "Hard": 9}
        self.base_speed = diff_map.get(self.settings["difficulty"], 6)
        self.scroll_speed = self.base_speed

        # --- Игровая статистика ---
        self.score = 0
        self.distance = 0        # пройденное расстояние в метрах
        self.coins = 0
        self.lives = 1
        self.state = "PLAYING"    # PLAYING / WIN / GAME_OVER

        # --- Машина игрока ---
        self.player = pygame.Rect(self.width//2 - 20, self.height - 120, 40, 70)
        self.player_color = COLORS.get(self.settings["car_color"].lower(), COLORS["red"])

        # --- Списки динамических объектов ---
        self.traffic = []      # встречные автомобили
        self.obstacles = []    # препятствия (барьеры, масло, лежачие полицейские)
        self.powerups = []     # бонусы (Nitro, Shield, Repair)
        self.coin_list = []    # монеты

        # --- Эффекты power-up ---
        self.active_powerup = None
        self.powerup_timer = 0
        self.shield_active = False

    def update(self, keys):
        """Один шаг игры: управление, движение, коллизии, смена состояний."""
        if self.state != "PLAYING":
            return

        # 1. Управление машиной (стрелки + ограничения по краям дороги и границам экрана)
        p_speed = 7
        if keys[pygame.K_LEFT] and self.player.left > ROAD_LEFT:
            self.player.x -= p_speed
        if keys[pygame.K_RIGHT] and self.player.right < ROAD_RIGHT:
            self.player.x += p_speed
        if keys[pygame.K_UP] and self.player.top > 0:
            self.player.y -= p_speed
        if keys[pygame.K_DOWN] and self.player.bottom < self.height:
            self.player.y += p_speed

        # 2. Текущая скорость мира = базовая + бонус за дистанцию (каждые 1000 метров +1)
        #    + ускорение от Nitro (×1.5)
        current_speed = self.scroll_speed + (self.distance // 1000)
        if self.active_powerup == "Nitro":
            current_speed *= 1.5

        # 3. Накопление дистанции и очков
        self.distance += current_speed / 10
        self.score = (self.coins * 50) + int(self.distance)

        # 4. Проверка победы
        if self.distance >= FINISH_DISTANCE:
            self.state = "WIN"
            return

        # 5. Таймер активного бонуса (для Nitro и Repair; Shield снимается при первом ударе)
        if self.active_powerup and time.time() > self.powerup_timer:
            self.active_powerup = None

        # 6. Спавн новых объектов и обновление существующих
        self._spawn_entities()
        self._update_entities(current_speed)
        self._check_collisions()

    def _spawn_entities(self):
        """Генерирует новые объекты на дороге с проверкой безопасности (не спавнить на игрока)."""
        def is_safe(rect):
            # Нельзя создавать объект, если он пересекается с машиной игрока (с запасом по Y)
            if rect.colliderect(self.player.inflate(20, 200)):
                return False
            # И если пересекается с уже существующими объектами (с запасом)
            for e in self.traffic + self.obstacles:
                if rect.colliderect(e['rect'].inflate(20, 50)):
                    return False
            return True

        # Частота спавна растёт с дистанцией (игра постепенно ускоряется)
        spawn_rate = 0.02 + (self.distance / 100000)

        # --- Встречный транспорт ---
        if random.random() < spawn_rate:
            w, h = 40, 70
            rect = pygame.Rect(random.randint(ROAD_LEFT+10, ROAD_RIGHT-w-10), -100, w, h)
            if is_safe(rect):
                self.traffic.append({
                    "rect": rect,
                    "speed": random.randint(2, 5),   # собственная скорость машины
                    "color": random.choice([COLORS["blue"], COLORS["green"], COLORS["grey"]])
                })

        # --- Препятствия (разные типы: обычный барьер, масло, лежачий полицейский, движущийся барьер) ---
        if random.random() < spawn_rate * 0.8:
            obs_type = random.choice(["barrier", "oil", "speed_bump", "moving_barrier"])
            w = 50 if obs_type == "oil" else 70
            h = 50 if obs_type == "oil" else 20
            rect = pygame.Rect(random.randint(ROAD_LEFT+10, ROAD_RIGHT-w-10), -100, w, h)
            if is_safe(rect):
                self.obstacles.append({
                    "rect": rect,
                    "type": obs_type,
                    "dir": random.choice([-1, 1])    # для moving_barrier – направление движения по горизонтали
                })

        # --- Power-ups (редко) ---
        if random.random() < 0.005:
            rect = pygame.Rect(random.randint(ROAD_LEFT+20, ROAD_RIGHT-40), -50, 30, 30)
            if is_safe(rect):
                p_type = random.choice(["Nitro", "Shield", "Repair"])
                self.powerups.append({"rect": rect, "type": p_type, "spawn_time": time.time()})

        # --- Монеты ---
        if random.random() < 0.03:
            rect = pygame.Rect(random.randint(ROAD_LEFT+20, ROAD_RIGHT-40), -50, 20, 20)
            if is_safe(rect):
                self.coin_list.append(rect)

    def _update_entities(self, scroll):
        """Перемещение всех объектов вниз по экрану и удаление вышедших."""
        # Транспорт: обычная скорость + собственная
        for t in self.traffic[:]:
            t['rect'].y += scroll + t['speed']
            if t['rect'].y > self.height:
                self.traffic.remove(t)

        # Препятствия: scroll + для движущихся – горизонтальное движение
        for o in self.obstacles[:]:
            o['rect'].y += scroll
            if o['type'] == "moving_barrier":
                o['rect'].x += 2 * o['dir']
                # Отскок от границ дороги
                if o['rect'].left < ROAD_LEFT or o['rect'].right > ROAD_RIGHT:
                    o['dir'] *= -1
            if o['rect'].y > self.height:
                self.obstacles.remove(o)

        # Power-ups: scroll + таймаут 8 секунд (исчезают, если не подобраны)
        for p in self.powerups[:]:
            p['rect'].y += scroll
            if time.time() - p['spawn_time'] > 8 or p['rect'].y > self.height:
                self.powerups.remove(p)

        # Монеты
        for c in self.coin_list[:]:
            c.y += scroll
            if c.y > self.height:
                self.coin_list.remove(c)

    def _check_collisions(self):
        """Обработка всех столкновений: аварии, бонусы, монеты."""
        # --- Столкновения с машинами ---
        for t in self.traffic[:]:
            if self.player.colliderect(t['rect']):
                self._handle_crash(t, self.traffic)

        # --- Столкновения с препятствиями ---
        for o in self.obstacles[:]:
            if self.player.colliderect(o['rect']):
                if o['type'] == "oil":
                    self.score -= 50          # штраф за масло
                    self.obstacles.remove(o)
                elif o['type'] == "speed_bump":
                    # лежачий полицейский – только визуально (можно добавить тряску камеры)
                    pass
                else:
                    self._handle_crash(o, self.obstacles)

        # --- Подбор power-ups ---
        for p in self.powerups[:]:
            if self.player.colliderect(p['rect']):
                self.active_powerup = p['type']
                self.powerups.remove(p)
                if p['type'] == "Nitro":
                    self.powerup_timer = time.time() + 5
                elif p['type'] == "Shield":
                    self.shield_active = True
                    self.powerup_timer = time.time() + 999   # щит действует до первого удара
                elif p['type'] == "Repair":
                    self.lives = 2          # восстанавливаем до максимума (2 жизни)
                    self.powerup_timer = time.time() + 2   # короткое отображение в UI
                    self.active_powerup = "Repaired!"

        # --- Подбор монет ---
        for c in self.coin_list[:]:
            if self.player.colliderect(c):
                self.coins += 1
                self.coin_list.remove(c)

    def _handle_crash(self, entity, group_list):
        """
        Общая логика аварии.
        - Если активен щит – он поглощает удар и ломается.
        - Иначе теряется жизнь; при нуле жизней – GAME OVER.
        """
        if self.shield_active:
            self.shield_active = False
            self.active_powerup = None
            if entity in group_list:
                group_list.remove(entity)
        else:
            self.lives -= 1
            if entity in group_list:
                group_list.remove(entity)
            if self.lives <= 0:
                self.state = "GAME_OVER"

    def draw(self, surface):
        """Отрисовка всей игры на экране."""
        # --- Дорога и разметка ---
        pygame.draw.rect(surface, COLORS["road"], (ROAD_LEFT, 0, ROAD_WIDTH, self.height))
        # Две прерывистые линии разметки (эффект движения за счёт сдвига по Y)
        for x in [ROAD_LEFT + ROAD_WIDTH//3, ROAD_LEFT + 2*ROAD_WIDTH//3]:
            for y in range(0, self.height, 60):
                if (y + int(self.distance * 10) % 60) % 120 < 60:
                    pygame.draw.rect(surface, COLORS["white"], (x - 2, y + (int(self.distance * 10) % 60) - 60, 4, 60))

        # --- Монеты (жёлтые круги) ---
        for c in self.coin_list:
            pygame.draw.circle(surface, COLORS["yellow"], c.center, 10)

        # --- Препятствия (разная отрисовка в зависимости от типа) ---
        for o in self.obstacles:
            if o['type'] == "oil":
                pygame.draw.ellipse(surface, COLORS["black"], o['rect'])
            elif o['type'] == "speed_bump":
                pygame.draw.rect(surface, COLORS["yellow"], o['rect'], border_radius=5)
            else:   # барьер или движущийся барьер
                pygame.draw.rect(surface, COLORS["orange"], o['rect'])
                # полоски на барьере
                for i in range(0, o['rect'].width, 15):
                    pygame.draw.rect(surface, COLORS["white"], (o['rect'].x + i, o['rect'].y, 10, o['rect'].height))

        # --- Встречные машины ---
        for t in self.traffic:
            pygame.draw.rect(surface, t['color'], t['rect'], border_radius=8)

        # --- Power-ups (круги с первой буквой) ---
        for p in self.powerups:
            if p['type'] == "Shield":
                color = COLORS["cyan"]
            elif p['type'] == "Nitro":
                color = COLORS["magenta"]
            else:
                color = COLORS["green"]
            pygame.draw.circle(surface, color, p['rect'].center, 15)
            txt = FONTS['small'].render(p['type'][0], True, COLORS["white"])
            surface.blit(txt, txt.get_rect(center=p['rect'].center))

        # --- Машина игрока (прямоугольник со скошенными углами) ---
        pygame.draw.rect(surface, self.player_color, self.player, border_radius=8)
        pygame.draw.rect(surface, COLORS["cyan"], (self.player.x+5, self.player.y+10, 30, 20))   # лобовое стекло

        # Если активен щит – рисуем полупрозрачный круг вокруг машины
        if self.shield_active:
            pygame.draw.circle(surface, (100, 200, 255), self.player.center, 40, width=3)

        # --- Боковые панели (статистика слева и справа) ---
        pygame.draw.rect(surface, COLORS["bg"], (0, 0, ROAD_LEFT, self.height))
        pygame.draw.rect(surface, COLORS["bg"], (ROAD_RIGHT, 0, self.width - ROAD_RIGHT, self.height))

        # Левый блок: SCORE, DIST, GOAL, LIVES
        surface.blit(FONTS['small'].render("SCORE", True, COLORS["yellow"]), (10, 20))
        surface.blit(FONTS['med'].render(str(self.score), True, COLORS["white"]), (10, 50))
        surface.blit(FONTS['small'].render("DIST", True, COLORS["cyan"]), (10, 100))
        surface.blit(FONTS['med'].render(f"{int(self.distance)}m", True, COLORS["white"]), (10, 130))
        rem = max(0, FINISH_DISTANCE - int(self.distance))
        surface.blit(FONTS['small'].render(f"Goal: {rem}m", True, COLORS["grey"]), (10, 170))
        surface.blit(FONTS['small'].render("LIVES", True, COLORS["red"]), (10, 220))
        surface.blit(FONTS['med'].render(str(self.lives), True, COLORS["white"]), (10, 250))

        # Правый блок: активный power-up
        surface.blit(FONTS['small'].render("POWER-UP", True, COLORS["magenta"]), (ROAD_RIGHT + 10, 20))
        if self.active_powerup:
            txt = self.active_powerup
            if txt == "Nitro":
                txt += f" {int(self.powerup_timer - time.time())}s"
            surface.blit(FONTS['small'].render(txt, True, COLORS["white"]), (ROAD_RIGHT + 10, 50))
        else:
            surface.blit(FONTS['small'].render("None", True, COLORS["grey"]), (ROAD_RIGHT + 10, 50))