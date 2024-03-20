import random
from enum import Enum

import pygame

from item import BubbleItem, SpeedShoeItem, NeedleItem
from utils.types import Assets, Bubble_Trapped, Bubbles, Characters, Explosions, Items


class EntityObject(pygame.sprite.Sprite):
    def __init__(self, image, entity_type):
        super(EntityObject, self).__init__()
        self.entity_type = entity_type
        self.image = image
        self.rect = self.image.get_rect()


class TrappedBubble(pygame.sprite.Sprite):
    def __init__(self, asset_store, player, time_spawned):
        super(TrappedBubble, self).__init__()
        self.asset_store = asset_store
        self.asset = self.asset_store["spritesheets"][Assets.BUBBLE_TRAPPED][
            Bubble_Trapped.DEFAULT
        ]
        self.player = player
        self.image = pygame.transform.smoothscale_by(
            self.asset.get_current_frame(), 1.3
        )
        self.rect = self.image.get_rect()
        self.rect.centerx = self.player.rect.centerx
        self.rect.centery = self.player.rect.centery
        self.time_spawned = time_spawned

    def update(self):
        if self.player.is_trapped:
            self.rect.centerx = self.player.rect.centerx
            self.rect.centery = self.player.rect.centery

            self.image = pygame.transform.smoothscale_by(
                self.asset.get_current_frame(), 1.3
            )
            time_elapsed = pygame.time.get_ticks()

            if time_elapsed - self.time_spawned <= 1000:
                self.image.set_alpha(190)
            elif time_elapsed - self.time_spawned <= 5000:
                alpha_increment_per_ms = (255 - 190) / 4000
                elapsed_since_transition = time_elapsed - self.time_spawned - 1000
                alpha_value = min(
                    255, 190 + alpha_increment_per_ms * elapsed_since_transition
                )
                self.image.set_alpha(alpha_value)
            else:
                self.player.kill()
                self.kill()
        else:
            self.kill()


class Obstacle(pygame.sprite.Sprite):
    obstacles = {}

    def __init__(self, asset_store, row, col, obstacle_type, obstacle_name, tile_size):
        super(Obstacle, self).__init__()
        self.asset_store = asset_store
        self.asset = self.asset_store["static"][obstacle_type][obstacle_name]
        self.row = row
        self.col = col
        self.x_offset = self.asset.config.get("x_pos_offset")
        self.y_offset = self.asset.config.get("y_pos_offset")
        self.image = self.asset.image
        self.size = self.image.get_width()
        self.rect = self.image.get_rect(
            topleft=(
                self.col * self.size + (self.x_offset if self.x_offset else 0),
                self.row * self.size + (self.y_offset if self.y_offset else 0),
            )
        )
        self.tile_rect = pygame.Rect(
            self.col * tile_size, self.row * tile_size, tile_size, tile_size
        )

        Obstacle.obstacles[(row, col)] = self

    def update(self):  # type: ignore
        self.image = self.asset.image

    @classmethod
    def get_obstacle(cls, row, col):
        return cls.obstacles.get((row, col), None)


class Block(Obstacle):
    def __init__(self, asset_store, row, col, block_name, tile_size):
        super(Block, self).__init__(
            asset_store, row, col, Assets.BLOCKS, block_name, tile_size
        )

    def update(self):  # type: ignore
        self.image = self.asset.image

    def explode(self, group):
        self.kill()
        Block.obstacles.pop((self.row, self.col))
        item_drop_potential = random.random()
        if item_drop_potential < 0.25:
            item_type = random.choice(list(Items))
            if item_type == Items.BUBBLE:
                group.add(BubbleItem(self.asset_store, self.row, self.col, item_type))
            elif item_type == Items.SPEED_SHOE:
                group.add(
                    SpeedShoeItem(self.asset_store, self.row, self.col, item_type)
                )
            elif item_type == Items.NEEDLE:
                group.add(NeedleItem(self.asset_store, self.row, self.col, item_type))


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
    def __init__(self, asset_store, id, max_speed):
        super(Player, self).__init__()
        self.asset_store = asset_store
        self.asset = self.asset_store["spritesheets"][Assets.CHARACTER][
            Characters.DEFAULT
        ]
        self.id = id
        self.sprite_flip_x = 0
        self.animation_state = self.asset.get_animation_mapping("idle")
        self.image = self.asset.get_current_frame(
            idx=self.animation_state, flip_x=self.sprite_flip_x
        )
        self.image_idx = 0
        self.rect = self.image.get_frect()
        self.hitbox = pygame.Rect(
            self.rect.x + self.image.get_width() / 7,
            self.rect.y + self.image.get_height() * (3 / 4),
            self.rect.width - 2 * (self.image.get_width() / 7),
            self.image.get_height() / 4,
        )
        self.is_trapped = False

        self.max_speed = max_speed
        self.vel = self.max_speed
        self.num_bubbles = 1

        self.explosion_range = 7
        self.animation_timer = pygame.time.get_ticks()

        self.inventory = []

    def update(self, grid, grid_size, pressed_keys):  # type: ignore
        self.image = self.asset.get_current_frame(
            idx=self.animation_state
            if not self.is_trapped
            else self.asset.get_animation_mapping("trapped"),
            flip_x=self.sprite_flip_x,
        )
        if not self.is_trapped:
            self.vel = self.max_speed

        self.move(grid, grid_size, pressed_keys)

        self.hitbox = pygame.Rect(
            self.rect.x + self.image.get_width() / 7,
            self.rect.y + self.image.get_height() * (3 / 4),
            self.rect.width - 2 * (self.image.get_width() / 7),
            self.image.get_height() / 4,
        )

    #        tile_size = self.rect.width
    #        pygame.draw.rect(
    #            self.image, pygame.Color(255, 0, 0), (0, 0, tile_size, tile_size), 1
    #        )

    def use_item(self, idx):
        if 0 <= idx < len(self.inventory):
            if self.inventory[idx].activate(self):
                self.inventory.pop(idx)

    def trap_player(self, grid):
        if not self.is_trapped:
            grid.trapped_bubble_group.add(
                TrappedBubble(self.asset_store, self, pygame.time.get_ticks())
            )
            self.is_trapped = True
            self.sprite_flip_x = False
            self.vel = 0.05

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
            self.animation_state = self.asset.get_animation_mapping(
                "idle" if not self.is_trapped else "trapped"
            )

    def move_in_direction(self, grid, grid_size, dx, dy):
        new_pos = (self.rect.x + dx * self.vel, self.rect.y + dy * self.vel)
        new_coord = grid.get_coord(*new_pos)
        if not self.is_trapped:
            if dx == 1:
                self.animation_state = self.asset.get_animation_mapping("move_side")
                self.sprite_flip_x = 1
            elif dx == -1:
                self.animation_state = self.asset.get_animation_mapping("move_side")
                self.sprite_flip_x = 0
            elif dy == 1:
                self.animation_state = self.asset.get_animation_mapping("move_down")
                self.sprite_flip_x = 0
            elif dy == -1:
                self.animation_state = self.asset.get_animation_mapping("move_up")
                self.sprite_flip_x = 0

        tmp_x = self.rect.x
        tmp_y = self.rect.y

        self.rect.x += dx * self.vel
        self.rect.y += dy * self.vel
        self.hitbox = pygame.Rect(
            self.rect.x + self.rect.width / 7,
            self.rect.y + self.rect.height * (3 / 4),
            self.rect.width - 2 * (self.rect.width / 7),
            self.rect.height / 4,
        )

        collided_groups = self.is_collide(
            grid.obstacle_group,
            grid.block_group,
        )
        if not (
            (
                grid.get_coord(tmp_x, tmp_y) == new_coord
                or not grid.has_bubble(*new_coord)
            )
            and (
                0 <= new_pos[0] <= grid_size - self.rect.width
                and 0 <= new_pos[1] <= grid_size - self.rect.height
            )
        ):
            self.rect.x = tmp_x
            self.rect.y = tmp_y

        if collided_groups:
            self.rect.x = tmp_x
            self.rect.y = tmp_y
            for entity in collided_groups:
                threshold = self.rect.height / 3
                entity_rect = (
                    entity.tile_rect if isinstance(entity, Obstacle) else entity.rect
                )
                if dx == 1 or dx == -1:
                    if entity_rect.y + self.rect.height - self.rect.y <= threshold:
                        self.rect.y += 1
                    elif self.rect.y + self.rect.height - entity_rect.y <= threshold:
                        self.rect.y -= 1
                elif dy == 1 or dy == -1:
                    if entity_rect.x + self.rect.width - self.rect.x <= threshold:
                        self.rect.x += 1
                    elif self.rect.x + self.rect.width - entity_rect.x <= threshold:
                        self.rect.x -= 1

    def is_collide(self, *groups):
        total_overlap_area = 0
        collided_sprites = []
        for group in groups:
            player_area = self.hitbox.width * self.hitbox.height
            for sprite in group:
                rect = self.hitbox
                sprite_rect = sprite.rect
                if isinstance(sprite, Bubble):
                    threshold = 0.5
                elif isinstance(sprite, Obstacle):
                    player_area = self.rect.width * self.rect.height
                    sprite_rect = sprite.tile_rect
                    rect = self.rect
                    threshold = 0.01
                else:
                    threshold = 0.66
                if rect.colliderect(sprite_rect):
                    overlap_rect = rect.clip(sprite_rect)
                    total_overlap_area += overlap_rect.width * overlap_rect.height
                    if total_overlap_area / player_area > threshold:
                        collided_sprites.append(sprite)
        return collided_sprites

    def drop_bubble(self, grid, asset_store):
        curr_pos = grid.get_coord(self.rect.x, self.rect.y)
        if not grid.get_tile(curr_pos[0], curr_pos[1]).has_bubble:
            if self.num_bubbles > 0:
                coord = grid.get_coord(self.rect.x, self.rect.y)
                if not grid.has_bubble(*coord):
                    grid.add_bubble(
                        Bubble(asset_store, *coord, self.id, self.explosion_range)  # type: ignore
                    )
                    grid.toggle_bubble(*coord)
                self.num_bubbles -= 1

    def pick_up_item(self, item):
        item.acquire(self)
