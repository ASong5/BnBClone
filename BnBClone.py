import pygame
import math
from enum import Enum
import faulthandler
from utils import spritesheets
from utils.types import Assets, Bubbles, Characters, Explosions

faulthandler.enable()
pygame.init()
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 1200
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


NUM_TILES = 15


EVENTS = {
    "PLAYER_IDLE": pygame.USEREVENT + 1,
    "PLAYER_MOVE": pygame.USEREVENT + 2,
    "BUBBLE": pygame.USEREVENT + 3,
}


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


class Grid:
    def __init__(self, grid_size, screen_size, tile_sprites):
        self.grid_size = grid_size
        self.tile_size = screen_size / self.grid_size
        self.tile_group = pygame.sprite.Group()
        self.explosion_group = []
        self.bubble_groups = []
        self.__tiles = [
            [
                Tile(row, col, self.tile_size, tile_sprites[0][0])
                if (row + col) % 2 == 0
                else Tile(row, col, self.tile_size, tile_sprites[0][1])
                for col in range(self.grid_size)
            ]
            for row in range(self.grid_size)
        ]

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                self.tile_group.add(self.__tiles[row][col])

    def toggle_bubble(self, row, col):
        self.__tiles[row][col].has_bubble = not self.__tiles[row][col].has_bubble

    def has_bubble(self, row, col):
        return self.__tiles[row][col].has_bubble

    def add_bubble(self, bubble_to_add):
        groups_to_merge = set()
        for bubbles, _ in self.bubble_groups:
            for bubble in bubbles.sprites():
                for offset in range(bubble.explosion_range):
                    if (
                        (
                            bubble_to_add.row == bubble.row + offset + 1
                            and bubble_to_add.col == bubble.col
                        )
                        or (
                            bubble_to_add.row == bubble.row - offset - 1
                            and bubble_to_add.col == bubble.col
                        )
                        or (
                            bubble_to_add.col == bubble.col + offset + 1
                            and bubble_to_add.row == bubble.row
                        )
                        or (
                            bubble_to_add.col == bubble.col - offset - 1
                            and bubble_to_add.row == bubble.row
                        )
                    ):
                        groups_to_merge.add(bubbles)
                        break

        if len(groups_to_merge) > 0:
            first_group = list(groups_to_merge)[0]
            for other_group in list(groups_to_merge)[1:]:
                if other_group in [group for group, _ in self.bubble_groups]:
                    for sprite in other_group.sprites():
                        first_group.add(sprite)
                    self.bubble_groups = [
                        grp_info
                        for grp_info in self.bubble_groups
                        if grp_info[0] != other_group
                    ]
            first_group.add(bubble_to_add)

        else:
            group = pygame.sprite.Group()
            group.add(bubble_to_add)
            self.bubble_groups.append([group, pygame.time.get_ticks()])

    def explode_tiles(self, group_idx, asset):
        group = pygame.sprite.Group()
        for bubble in self.bubble_groups[group_idx][0]:
            explosion = Explosion(
                asset, bubble.row, bubble.col, Explosion.EXPLODE_DIR.CENTER, self.tile_size
            )
            group.add(explosion)

            for i in range(bubble.explosion_range):
                for j in range(4):
                    dx, dy = 0, 0
                    if j == 0:
                        dx = i + 1
                    elif j == 1:
                        dx = -(i + 1)
                    elif j == 2:
                        dy = i + 1
                    elif j == 3:
                        dy = -(i + 1)

                    row = bubble.row + dy
                    col = bubble.col + dx

                    if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
                        explosion = Explosion(
                            asset, row, col, Explosion.EXPLODE_DIR(j + 1), self.tile_size
                        )
                        group.add(explosion)

        self.explosion_group.append([group, pygame.time.get_ticks()])

    def get_tile(self, row, col):
        return self.__tiles[row][col]

    def get_coord(self, x, y):
        row = int((y + math.ceil(self.tile_size / 2)) / self.tile_size)
        col = int((x + math.ceil(self.tile_size / 2)) / self.tile_size)
        return (row, col)

    # TODO: create an AssetStore class to hold all the assets, and use that insead of passing in assets to various methods/constructors
    def update(self, explosion_asset):
        delete_bubble_groups = []
        delete_tile_exploded_groups = []

        for idx, bubble_group in enumerate(self.bubble_groups):
            bubble_group[0].update()
            if pygame.time.get_ticks() - bubble_group[1] >= 3000:
                for bubble in bubble_group[0].sprites():
                    self.toggle_bubble(bubble.row, bubble.col)
                self.explode_tiles(idx, explosion_asset)
                bubble_group[0].empty()
                delete_bubble_groups.append(bubble_group)

        for group in delete_bubble_groups:
            self.bubble_groups.remove(group)

        for group in self.explosion_group:
            if pygame.time.get_ticks() - group[1] >= 500:
                group[0].empty()
                delete_tile_exploded_groups.append(group)
            else:
                group[0].update()

        for group in delete_tile_exploded_groups:
            self.explosion_group.remove(group)


class EntityObject(pygame.sprite.Sprite):
    def __init__(self, image, entity_type):
        super(EntityObject, self).__init__()
        self.entity_type = entity_type
        self.image = image
        self.rect = self.image.get_rect()


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


class Asset:
    def __init__(self, frames, asset_type, asset_name):
        self.frames = frames
        self.asset_type = asset_type
        self.asset_name = asset_name
        self.animation = AnimationComponent(frames, asset_type)
        self.current_frame = self.get_current_frame()

    def get_current_frame(self, entity=None):
        return self.animation.get_frame(entity)


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


class GameObject:
    def __init__(self, screen_width):
        self.screen = SCREEN
        self.sprite_size = screen_width / NUM_TILES
        self.user_id = 0
        self.assets = self.load_assets()
        self.grid = Grid(
            NUM_TILES,
            screen_width,
            self.assets[Assets.TILE]["default"].frames,
        )
        self.player_group = pygame.sprite.Group()
        self.player_group.add(
            Player(self.user_id, 4, self.assets[Assets.CHARACTER][Characters.DEFAULT])
        )
        self.clock = pygame.time.Clock()
        self.running = True
        self.pressed_keys = []

    def update(self):
        for asset_type, asset_dict in self.assets.items():
            for _, asset in asset_dict.items():
                if (
                    isinstance(asset, Asset)
                    and asset_type in AnimationComponent.mappings
                ):
                    asset.animation.update_frame(
                        AnimationComponent.mappings[asset_type]["animation_duration"]
                    )
        self.grid.update(self.assets[Assets.EXPLOSION][Explosions.DEFAULT])
        self.player_group.update(self.grid, self.pressed_keys, self.screen.get_size())

        for player in self.player_group.sprites():
            if player.is_hit(self.grid):
                player.rect.x = 0
                player.rect.y = 0

    def load_assets(self):
        assets = {}
        spritesheet_list = spritesheets.Spritesheets("assets/spritesheets")
        for asset_type, asset_dict in spritesheet_list.sheets.items():
            for asset_name, asset_data in asset_dict.items():
                asset_spritesheet = asset_data.get("spritesheet")
                if asset_spritesheet:
                    if asset_type not in assets:
                        assets[asset_type] = {}
                    new_asset = Asset(
                        asset_spritesheet.get_sprites(
                            self.sprite_size, self.sprite_size
                        ),
                        asset_type,
                        asset_name,
                    )
                    assets[asset_type][asset_name] = new_asset
        return assets

    def draw(self):
        self.screen.fill("black")
        self.grid.tile_group.draw(self.screen)

        for tile_group in self.grid.explosion_group:
            tile_group[0].draw(self.screen)

        for bubble_group in self.grid.bubble_groups:
            bubble_group[0].draw(self.screen)

        self.player_group.draw(self.screen)

        # only for testing
        pygame.draw.rect(
            self.screen,
            pygame.Color(0, 255, 0),
            self.player_group.sprites()[0].hitbox,
            1,
        )
        pygame.display.flip()

    def start(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if (
                        event.key == pygame.K_UP
                        or event.key == pygame.K_DOWN
                        or event.key == pygame.K_RIGHT
                        or event.key == pygame.K_LEFT
                    ):
                        self.pressed_keys.append(event.key)
                    if event.key == pygame.K_SPACE:
                        for player in self.player_group.sprites():
                            if player.id == self.user_id:
                                player.drop_bubble(
                                    self.grid,
                                    self.assets[Assets.BUBBLE][Bubbles.DEFAULT],
                                )
                elif event.type == pygame.KEYUP:
                    if (
                        event.key == pygame.K_UP
                        or event.key == pygame.K_DOWN
                        or event.key == pygame.K_RIGHT
                        or event.key == pygame.K_LEFT
                    ):
                        self.pressed_keys.remove(event.key)

            self.update()
            self.draw()
            self.clock.tick(165)
        self.terminate()

    def terminate(self):
        # will probably do more stuff here in the future
        pygame.quit()


game = GameObject(SCREEN_WIDTH)
game.start()
