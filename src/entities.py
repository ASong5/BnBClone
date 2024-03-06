import pygame
from item import BubbleItem
from utils.types import Assets, Bubbles, Characters, Explosions
import utils.animations
from enum import Enum


class EntityObject(pygame.sprite.Sprite):
    def __init__(self, image, entity_type):
        super(EntityObject, self).__init__()
        self.entity_type = entity_type
        self.image = image
        self.rect = self.image.get_rect()


class Bubble(pygame.sprite.Sprite):
    def __init__(self, asset_store, row, col, player_id, explosion_range):
        super(Bubble, self).__init__()
        self.asset = asset_store["spritesheets"][Assets.BUBBLE][Bubbles.DEFAULT]
        self.player_id = player_id
        self.row = row
        self.col = col
        self.image = self.asset.get_current_frame()
        self.size = self.image.get_width()
        self.rect = self.image.get_rect(
            center=(
                self.col * self.size + (self.size / 2),
                self.row * self.size + (self.size / 2),
            )
        )
        self.explosion_range = explosion_range

    def update(self):  # type: ignore
        self.image = self.asset.get_current_frame()
        


class Explosion(pygame.sprite.Sprite):
    class EXPLODE_DIR(Enum):
        CENTER = 0
        RIGHT = 1
        LEFT = 2
        DOWN = 3
        UP = 4

    def __init__(self, asset_store, row, col, explosion_dir, size):
        super(Explosion, self).__init__()
        self.timer = pygame.time.get_ticks()
        self.asset = asset_store["spritesheets"][Assets.EXPLOSION][Explosions.DEFAULT]
        self.asset.animation.timer = self.timer
        self.explosion_dir = explosion_dir
        # self.animation_state = AnimationComponent.mappings[Assets.EXPLOSION]["animation_type"]["explode"]
        self.image = self.asset.get_current_frame(self)
        self.row = row
        self.col = col
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.col * size, self.row * size)

    def update(self):  # type: ignore
        self.asset.animation.timer = self.timer
        self.image = self.asset.get_current_frame(self)


class Player(pygame.sprite.Sprite):
    def __init__(self, asset_store, id, vel):
        super(Player, self).__init__()
        self.asset = asset_store["spritesheets"][Assets.CHARACTER][Characters.DEFAULT]
        self.id = id
        self.sprite_flip_x = 0
        self.animation_state = utils.animations.AnimationComponent.mappings[
            Assets.CHARACTER
        ]["animation_type"]["idle"]
        self.image = self.asset.get_current_frame(self)
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

    def update(self, grid, grid_size, pressed_keys):  # type: ignore
        self.image = self.asset.get_current_frame(self)
        self.move(grid, grid_size, pressed_keys)

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

    def move(self, grid, grid_size, pressed_keys):
        if len(pressed_keys) > 0:
            match pressed_keys[-1]:
                case pygame.K_RIGHT:
                    self.move_in_direction(grid, grid_size, 1, 0)
                case pygame.K_LEFT:
                    self.move_in_direction(grid, grid_size, -1, 0)
                case pygame.K_UP:
                    self.move_in_direction(grid, grid_size, 0, -1)
                case pygame.K_DOWN:
                    self.move_in_direction(grid, grid_size, 0, 1)
        else:
            self.animation_state = utils.animations.AnimationComponent.mappings[
                Assets.CHARACTER
            ]["animation_type"]["idle"]

    def move_in_direction(self, grid, grid_size, dx, dy):
        new_pos = (self.rect.x + dx * self.vel, self.rect.y + dy * self.vel)
        new_coord = grid.get_coord(*new_pos)
        if dx == 1:
            self.animation_state = utils.animations.AnimationComponent.mappings[
                Assets.CHARACTER
            ]["animation_type"]["move_side"]
            self.sprite_flip_x = 1
        elif dx == -1:
            self.animation_state = utils.animations.AnimationComponent.mappings[
                Assets.CHARACTER
            ]["animation_type"]["move_side"]
            self.sprite_flip_x = 0
        elif dy == 1:
            self.animation_state = utils.animations.AnimationComponent.mappings[
                Assets.CHARACTER
            ]["animation_type"]["move_down"]
            self.sprite_flip_x = 0
        elif dy == -1:
            self.animation_state = utils.animations.AnimationComponent.mappings[
                Assets.CHARACTER
            ]["animation_type"]["move_up"]
            self.sprite_flip_x = 0

        if (
            grid.get_coord(self.rect.x, self.rect.y) == new_coord
            or not grid.has_bubble(*new_coord)
        ) and (
            0 <= new_pos[0] <= grid_size - self.image.get_width()
            and 0 <= new_pos[1] <= grid_size - self.image.get_height()
            and not grid.has_obstacle(*new_coord)
        ):
            self.rect.x += dx * self.vel
            self.rect.y += dy * self.vel

    def is_collide(self, grid):
        total_overlap_area = 0
        player_area = self.hitbox.width * self.hitbox.height
        # TODO: include bubble group to check when playes collides with bubbles as well
        groups = [group[0] for group in grid.explosion_group] + [grid.item_group]
        collided_sprites = []

        for group in groups:
            for sprite in group:
                if self.hitbox.colliderect(sprite.rect):
                    overlap_rect = self.hitbox.clip(sprite.rect)
                    total_overlap_area += overlap_rect.width * overlap_rect.height
                    if total_overlap_area / player_area > 0.66:
                        collided_sprites.append(sprite)
        return collided_sprites

    def drop_bubble(self, grid, asset_store):
        curr_pos = grid.get_coord(self.rect.x, self.rect.y)
        if not grid.get_tile(curr_pos[0], curr_pos[1]).has_bubble:
            if self.num_bubbles > 0:
                coord = grid.get_coord(self.rect.x, self.rect.y)
                if not grid.has_bubble(*coord) and not grid.has_obstacle(*coord):
                    grid.add_bubble(
                        Bubble(asset_store, *coord, self.id, self.explosion_range)  # type: ignore
                    )
                    grid.toggle_bubble(*coord)

                self.num_bubbles -= 1

    def pick_up_item(self, item):
        if isinstance(item, BubbleItem):
            item.kill()
            self.num_bubbles += 1
