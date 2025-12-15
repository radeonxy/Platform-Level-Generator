import pygame
import random
from dataclasses import dataclass
from typing import Optional, List, Tuple

# =========================
# Configuration
# =========================

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
TILE_SIZE = 32 #la grille de tuiles 32x32 pix

#distribute tiles wide and high
LEVEL_TILES_W = WINDOW_WIDTH // TILE_SIZE #integer division
LEVEL_TILES_H = WINDOW_HEIGHT // TILE_SIZE

FPS = 60

# Tile types
EMPTY = 0
GROUND = 1
COIN = 2
SPIKE = 3


@dataclass
class LevelConfig:
    width: int = LEVEL_TILES_W
    height: int = LEVEL_TILES_H

    min_ground_y: int = LEVEL_TILES_H - 6  # min ground height (index from top)
    max_ground_y: int = LEVEL_TILES_H - 2  # max ground height
    max_step: int = 1  # max height diff between columns
    max_hole: int = 3  # max width of holes
    #min_hole: int = 3
    hole_prob: float = 0.12 #12% chance pour avoir un trou
    coin_prob: float = 0.25 #25% pour une pièce
    spike_prob: float = 0.08 #8% pour un spike


class LevelGenerator:
    """Constructive level generator with simple constraints:
    - Limited hole width
    - Limited ground height difference between adjacent columns
    - Random coins and spikes
    """

    def __init__(self, config: Optional[LevelConfig] = None, seed: Optional[int] = None):
        self.config = config or LevelConfig()
        self.random = random.Random(seed)

    def generate_grid(self):
        c = self.config
        grid = [[EMPTY for _ in range(c.width)] for _ in range(c.height)]

        # Start ground height near the bottom
        ground_y = c.max_ground_y

        hole_remaining = 0
        ground_after_hole = 0  # track ground columns required before next hole

        for x in range(c.width):
            # Avoid holes at very start and very end
            can_have_hole = 2 <= x <= c.width - 4

            # Decide whether to start a new hole
            if can_have_hole and hole_remaining == 0:
                if ground_after_hole > 0:
                    ground_after_hole -= 1
                elif self.random.random() < c.hole_prob:
                    hole_remaining = self.random.randint(2, c.max_hole)
                    # ensure hole is not too big to jump
                    max_jump_tiles = 3
                    hole_remaining = min(hole_remaining, max_jump_tiles)
                    ground_after_hole = 1  # require 1 ground column before next hole

            # If we're in a hole, skip ground for this column
            if hole_remaining > 0:
                hole_remaining -= 1
                continue

            # Adjust ground height (limited step)
            possible_deltas = [-1, 0, 1]
            self.random.shuffle(possible_deltas)
            for delta in possible_deltas:
                new_height = ground_y + delta
                if c.min_ground_y <= new_height <= c.max_ground_y and abs(new_height - ground_y) <= c.max_step:
                    ground_y = new_height
                    break

            # Fill ground from ground_y to bottom
            for y in range(ground_y, c.height):
                grid[y][x] = GROUND

            # Add coins above ground
            coin_y = ground_y - 2
            if coin_y >= 0 and self.random.random() < c.coin_prob:
                grid[coin_y][x] = COIN

            # Add spikes on ground (just above base ground)
            spike_y = ground_y - 0
            if spike_y >= 0 and self.random.random() < c.spike_prob:
                # if grid[spike_y][x] == EMPTY:
                grid[spike_y][x] = SPIKE

        # Ensure first and last columns are safe, with solid ground
        for x in (0, 1, c.width - 1, c.width - 2):
            ground_y = c.max_ground_y
            for y in range(ground_y, c.height):
                grid[y][x] = GROUND
            # clear everything above
            for y in range(0, ground_y):
                grid[y][x] = EMPTY

        return grid


class Level:
    def __init__(self, generator: LevelGenerator):
        self.generator = generator
        self.grid = generator.generate_grid()
        self.solid_rects: List[pygame.Rect] = []
        self.coin_rects: List[pygame.Rect] = []
        self.spike_rects: List[pygame.Rect] = []
        self._build_from_grid()

    def _build_from_grid(self):
        self.solid_rects.clear()
        self.coin_rects.clear()
        self.spike_rects.clear()

        for y, row in enumerate(self.grid):
            for x, tile in enumerate(row):
                world_rect = pygame.Rect(
                    x * TILE_SIZE,
                    y * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE
                )
                if tile == GROUND:
                    self.solid_rects.append(world_rect)
                elif tile == COIN:
                    self.coin_rects.append(world_rect)
                elif tile == SPIKE:
                    # Spike is both solid (for collision) and hazardous
                   # self.solid_rects.append(world_rect)
                    self.spike_rects.append(world_rect)

    def draw(self, surface: pygame.Surface):
        # Background
        surface.fill((135, 206, 235))  # sky color

        # Draw ground
        for rect in self.solid_rects:
            pygame.draw.rect(surface, (80, 50, 20), rect)

        # Draw coins
        for rect in self.coin_rects:
            center = rect.center
            radius = rect.width // 3
            pygame.draw.circle(surface, (255, 215, 0), center, radius)

        # Draw spikes (triangles)
        for rect in self.spike_rects:
            points = [
                (rect.centerx, rect.top),
                (rect.left, rect.bottom),
                (rect.right, rect.bottom),
            ]
            pygame.draw.polygon(surface, (200, 0, 0), points)


class Player(pygame.sprite.Sprite):
    def __init__(self, spawn_pos: Tuple[int, int]):
        super().__init__()
        w = int(TILE_SIZE * 1.4)
        h = int(TILE_SIZE * 1.4)

        #self.image = pygame.Surface((w, h))
        #self.image.fill((30, 144, 255))

        self.image=pygame.image.load("player.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (w, h))

        self.rect = self.image.get_rect()
        self.rect.midbottom = spawn_pos

        self.vel_x = 0.0
        self.vel_y = 0.0
        self.speed = 5
        self.jump_force = -12
        self.gravity = 0.6
        self.max_fall_speed = 18
        self.on_ground = False

    def handle_input(self, keys):
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:
            self.vel_x = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.vel_y = self.jump_force
            self.on_ground = False

    def _move_axis(self, dx: float, dy: float, solids: List[pygame.Rect]):
        # Horizontal movement
        self.rect.x += dx
        for tile in solids:
            if self.rect.colliderect(tile):
                if dx > 0:
                    self.rect.right = tile.left
                elif dx < 0:
                    self.rect.left = tile.right

        # Vertical movement
        self.rect.y += dy
        self.on_ground = False
        for tile in solids:
            if self.rect.colliderect(tile):
                if dy > 0:
                    self.rect.bottom = tile.top
                    self.vel_y = 0
                    self.on_ground = True
                elif dy < 0:
                    self.rect.top = tile.bottom
                    self.vel_y = 0

    def update(self, solids: List[pygame.Rect]):
        # Apply gravity
        self.vel_y += self.gravity
        if self.vel_y > self.max_fall_speed:
            self.vel_y = self.max_fall_speed

        self._move_axis(self.vel_x, self.vel_y, solids)

#difficulty scaler
def make_config_for_level(level: int) -> LevelConfig:
    return LevelConfig(
        hole_prob=min(0.10 + level * 0.01, 0.35),
        max_hole=min(2 + level // 3, 6),
        max_step=min(1 + level // 5, 3),
        spike_prob=min(0.05 + level * 0.01, 0.25),
        coin_prob=max(0.25 - level * 0.01, 0.10),
    )


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Procedural Platformer (Phase 1)")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 24)

        self.level_config = LevelConfig()
        self.level_generator = LevelGenerator(self.level_config)
        self.level_index = 1
        self.score = 0

        self.level = Level(self.level_generator)
        self.player = self._create_player()

        self.running = True

    def _create_player(self) -> Player:
        # Spawn player slightly above ground in first column
        ground_y_pixels = self.level_config.max_ground_y * TILE_SIZE
        spawn_x = TILE_SIZE * 2
        spawn_y = ground_y_pixels
        return Player((spawn_x, spawn_y))

    '''def reset_level(self, new_random_seed: bool = False):
        if new_random_seed:
            seed = random.randint(0, 1_000_000)
            self.level_generator = LevelGenerator(self.level_config, seed=seed)
        self.level = Level(self.level_generator)
        self.player = self._create_player()'''

    def reset_level(self, new_random_seed: bool = False):
        self.level_config = make_config_for_level(self.level_index)

        seed = None
        if new_random_seed:
            seed = random.randint(0, 1_000_000)

        self.level_generator = LevelGenerator(self.level_config, seed=seed)
        self.level = Level(self.level_generator)
        self.player = self._create_player()

    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update(self.level.solid_rects)

        # Collect coins
        new_coin_rects: List[pygame.Rect] = []
        for rect in self.level.coin_rects:
            if self.player.rect.colliderect(rect):
                self.score += 1
            else:
                new_coin_rects.append(rect)
        self.level.coin_rects = new_coin_rects

        # Check spikes / death
        for rect in self.level.spike_rects:
            if self.player.rect.colliderect(rect):
                self.score = max(0, self.score - 3)
                self.reset_level(new_random_seed=False)
                break

        # Fall off bottom of level = death
        if self.player.rect.top > WINDOW_HEIGHT:
            self.score = max(0, self.score - 1)
            self.reset_level(new_random_seed=False)

        # Reach far right side = "finish level" and generate a new one
        if self.player.rect.right >= WINDOW_WIDTH - TILE_SIZE:
            self.level_index += 1
            self.reset_level(new_random_seed=True)

    def draw_ui(self):
        text = "Level: {}   Score: {}".format(self.level_index, self.score)
        text2 = "LEFT/RIGHT ou Q/D pour bouger, SPACE/UP pour sauter, N: nouveau niveau, ESC: quitter"
        surf = self.font.render(text, True, (0, 0, 0))
        surf2 = self.font.render(text2, True, (0, 0, 0))
        self.screen.blit(surf, (20, 20))
        self.screen.blit(surf2, (20, 50))

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_n:
                        self.level_index += 1
                        self.reset_level(new_random_seed=True)

            # self.update(dt)
            # self.level.draw(self.screen)
            # self.draw_ui()
            # pygame.display.flip()

            self.update(dt)
            self.level.draw(self.screen)

            # AJOUTER LE JOUEUR 
            self.screen.blit(self.player.image, self.player.rect)

            self.draw_ui()
            pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    Game().run()
