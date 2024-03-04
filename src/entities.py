import pygame
from utils.types import Assets
from enum import Enum

class AnimationComponent:
    mappings = {
        Assets.CHARACTER: {
            "animation_type": {
                "idle": -1,
                "move_down": 0,
                "move_up": 1,
                "move_side": 2,
            },
            "animation_duration": 200,
        },
        Assets.BUBBLE: {"idle": 0, "animation_duration": 200},
        Assets.EXPLOSION: {"animation_type": {
            "explode": 2, "fizzle_one": 1, "fizzle_two": 0
        }, "animation_duration": [400, 430, 475]},
    }

    def __init__(self, frames, asset_type):
        self.frames = frames
        self.animation_type_idx = 0
        self.frame_idx = 0
        self.asset_type = asset_type
        self.timer = pygame.time.get_ticks()

    def update_frame(self, time_per_frame):
        self.frame_idx = self.frame_idx % len(self.frames[self.animation_type_idx])
        offset = 1 if self.asset_type == Assets.BUBBLE else 0

        if isinstance(time_per_frame, list) and self.asset_type == Assets.EXPLOSION:
            idx = len(time_per_frame) - 1
            for time in time_per_frame:
                time_elapsed = pygame.time.get_ticks() - self.timer
                if time_elapsed <= time:
                    self.frame_idx = idx
                    break
                idx -= 1

        elif isinstance(time_per_frame, int):
            if pygame.time.get_ticks() - self.timer >= time_per_frame:
                self.timer = pygame.time.get_ticks()
                self.frame_idx = (self.frame_idx + 1) % (
                    len(self.frames[self.animation_type_idx]) - offset
                )

    def get_frame(self, entity=None):
        if isinstance(entity, Player):
            if (
                entity.animation_state
                != self.mappings[Assets.CHARACTER]["animation_type"]["idle"]
            ):
                self.animation_type_idx = entity.animation_state
            if (
                entity.animation_state
                == self.mappings[Assets.CHARACTER]["animation_type"]["move_side"]
            ):
                return self.frames[self.animation_type_idx][self.frame_idx][
                    entity.sprite_flip_x
                ]
            elif (
                entity.animation_state
                == self.mappings[Assets.CHARACTER]["animation_type"]["idle"]
            ):
                return self.frames[self.animation_type_idx][0][entity.sprite_flip_x]
            else:
                return self.frames[self.animation_type_idx][self.frame_idx][
                    entity.sprite_flip_x
                ]

        elif isinstance(entity, Explosion):
            if entity.explosion_dir == Explosion.EXPLODE_DIR.DOWN:
                return self.frames[0][self.frame_idx][0]
            elif entity.explosion_dir == Explosion.EXPLODE_DIR.RIGHT:
                return self.frames[0][self.frame_idx][1]
            elif entity.explosion_dir == Explosion.EXPLODE_DIR.UP:
                return self.frames[0][self.frame_idx][2]
            elif entity.explosion_dir == Explosion.EXPLODE_DIR.LEFT:
                return self.frames[0][self.frame_idx][3]
            elif entity.explosion_dir == Explosion.EXPLODE_DIR.CENTER:
                return self.frames[0][self.frame_idx][0]

        else:
            return self.frames[self.animation_type_idx][self.frame_idx]
class EntityObject(pygame.sprite.Sprite):
    def __init__(self, image, entity_type):
        super(EntityObject, self).__init__()
        self.entity_type = entity_type
        self.image = image
        self.rect = self.image.get_rect()

class Tile(pygame.sprite.Sprite):
    def __init__(self, row, col, size, tile_sprite):
        super(Tile, self).__init__()
        self.row = row
        self.col = col
        self.size = size
        self.tile_sprite = tile_sprite
        self.image_idx = -1
        self.image = self.tile_sprite
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.col * self.size, self.row * self.size)
        self.has_bubble = False

    def update(self):  # type: ignore
        pass

class Bubble(pygame.sprite.Sprite):
    def __init__(self, row, col, player_id, explosion_range, asset):
        super(Bubble, self).__init__()
        self.asset = asset
        self.player_id = player_id
        self.row = row
        self.col = col
        self.image = self.asset.get_current_frame()
        self.rect = self.image.get_rect()
        self.explosion_range = explosion_range

    def update(self):  # type: ignore
        self.image = self.asset.get_current_frame()
        tile_size = self.rect.width
        self.rect = self.image.get_rect(
            center=(
                self.col * tile_size + (tile_size / 2),
                self.row * tile_size + (tile_size / 2),
            )
        )

class Explosion(pygame.sprite.Sprite):
    class EXPLODE_DIR(Enum):
        CENTER = 0
        RIGHT = 1
        LEFT = 2
        DOWN = 3
        UP = 4

    def __init__(self, asset, row, col, explosion_dir, size):
        super(Explosion, self).__init__()
        self.timer = pygame.time.get_ticks()
        self.asset = asset
        self.asset.animation.timer = self.timer
        self.explosion_dir = explosion_dir
        #self.animation_state = AnimationComponent.mappings[Assets.EXPLOSION]["animation_type"]["explode"] 
        self.image = self.asset.get_current_frame(self)
        self.row = row
        self.col = col
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.col * size, self.row * size)

    def update(self):  # type: ignore
        self.asset.animation.timer = self.timer
        self.image = self.asset.get_current_frame(self)


class Player(pygame.sprite.Sprite):
    def __init__(self, id, vel, asset):
        super(Player, self).__init__()
        self.asset = asset
        self.id = id
        self.sprite_flip_x = 0
        self.animation_state = AnimationComponent.mappings[Assets.CHARACTER][
            "animation_type"
        ]["idle"]
        self.image = asset.get_current_frame(self)
        self.image_idx = 0
        self.rect = self.image.get_rect()
        self.hitbox = pygame.Rect(
            self.rect.x + self.image.get_width() / 7,
            self.rect.y + self.image.get_height() * (3 / 4),
            self.rect.width - 2 * (self.image.get_width() / 7),
            self.image.get_height() / 4,
        )
        self.vel = vel
        self.num_bubbles = 1
        self.explosion_range = 7
        self.animation_timer = pygame.time.get_ticks()

    def update(self, grid, pressed_keys, screen_size):  # type: ignore
        self.image = self.asset.get_current_frame(self)
        self.move(grid, pressed_keys, screen_size)

        self.hitbox = pygame.Rect(
            self.rect.x + self.image.get_width() / 7,
            self.rect.y + self.image.get_height() * (3 / 4),
            self.rect.width - 2 * (self.image.get_width() / 7),
            self.image.get_height() / 4,
        )

        # only for testing
        tile_size = self.rect.width
        pygame.draw.rect(
            self.image, pygame.Color(255, 0, 0), (0, 0, tile_size, tile_size), 1
        )

    def move(self, grid, pressed_keys, screen_size):
        if len(pressed_keys) > 0:
            match pressed_keys[-1]:
                case pygame.K_RIGHT:
                    self.move_in_direction(grid, screen_size, 1, 0)
                case pygame.K_LEFT:
                    self.move_in_direction(grid, screen_size, -1, 0)
                case pygame.K_UP:
                    self.move_in_direction(grid, screen_size, 0, -1)
                case pygame.K_DOWN:
                    self.move_in_direction(grid, screen_size, 0, 1)
        else:
            self.animation_state = AnimationComponent.mappings[Assets.CHARACTER][
                "animation_type"
            ]["idle"]

    def move_in_direction(self, grid, screen_size, dx, dy):
        new_pos = (self.rect.x + dx * self.vel, self.rect.y + dy * self.vel)
        new_coord = grid.get_coord(*new_pos)
        if (
            grid.get_coord(self.rect.x, self.rect.y) == new_coord
            or not grid.has_bubble(*new_coord)
        ) and (
            0 <= new_pos[0] <= screen_size[0] - self.image.get_width()
            and 0 <= new_pos[1] <= screen_size[1] - self.image.get_height()
        ):
            if dx == 1:
                self.animation_state = AnimationComponent.mappings[Assets.CHARACTER][
                    "animation_type"
                ]["move_side"]
                self.sprite_flip_x = 1
            elif dx == -1:
                self.animation_state = AnimationComponent.mappings[Assets.CHARACTER][
                    "animation_type"
                ]["move_side"]
                self.sprite_flip_x = 0
            elif dy == 1:
                self.animation_state = AnimationComponent.mappings[Assets.CHARACTER][
                    "animation_type"
                ]["move_down"]
                self.sprite_flip_x = 0
            elif dy == -1:
                self.animation_state = AnimationComponent.mappings[Assets.CHARACTER][
                    "animation_type"
                ]["move_up"]
                self.sprite_flip_x = 0

            self.rect.x += dx * self.vel
            self.rect.y += dy * self.vel

    def is_hit(self, grid):
        total_overlap_area = 0
        player_area = self.hitbox.width * self.hitbox.height

        for group in grid.explosion_group:
            for tile in group[0]:
                if self.hitbox.colliderect(tile.rect):
                    overlap_rect = self.hitbox.clip(tile.rect)
                    total_overlap_area += overlap_rect.width * overlap_rect.height
                    if total_overlap_area / player_area > 0.66:
                        return True
        return False

    def drop_bubble(self, grid, asset):
        if self.num_bubbles > 0:
            coord = grid.get_coord(self.rect.x, self.rect.y)
            if not grid.has_bubble(*coord):
                grid.add_bubble(
                    Bubble(*coord, self.id, self.explosion_range, asset)  # type: ignore
                )
                grid.toggle_bubble(*coord)

