import os
import pygame
import math
from enum import Enum
import faulthandler
from utils import spritesheets

faulthandler.enable()

NUM_TILES = 15


EVENTS = {
    "PLAYER_IDLE": pygame.USEREVENT + 1,
    "PLAYER_MOVE": pygame.USEREVENT + 2,
    "BUBBLE": pygame.USEREVENT + 3,
}


class Tile(pygame.sprite.Sprite):
    class EXPLODE_DIR(Enum):
        CENTER = 0
        RIGHT = 1
        LEFT = 2
        DOWN = 3
        UP = 4

    def __init__(self, row, col, size, tile_sprite, explode_sprites):
        super(Tile, self).__init__()
        self.row = row
        self.col = col
        self.size = size
        self.explode_sprites = explode_sprites
        self.tile_sprite = tile_sprite
        self.image_idx = -1
        self.image = self.tile_sprite
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.col * self.size, self.row * self.size)
        self.has_bubble = False
        self.explode_dir = -1
        self.exploded_count = 0

    def update(self, grid, reset):  # type: ignore
        if reset:
            self.exploded_count -= 1
            if self.exploded_count == 0:
                self.image = self.tile_sprite
                self.explode_dir = -1
                self.image_idx = 0

        else:
            for group in grid.tile_exploded_groups:
                if group[0].has(self):
                    if pygame.time.get_ticks() - group[1] <= 350:
                        self.image_idx = 2
                    elif pygame.time.get_ticks() - group[1] <= 400:
                        self.image_idx = 1
                    elif pygame.time.get_ticks() - group[1] <= 450:
                        self.image_idx = 0

            base_tile = self.tile_sprite.copy()
            if self.explode_dir == Tile.EXPLODE_DIR.DOWN:
                base_tile.blit(self.explode_sprites[self.image_idx][0], (0, 0))
                self.image = base_tile
            elif self.explode_dir == Tile.EXPLODE_DIR.RIGHT:
                base_tile.blit(self.explode_sprites[self.image_idx][1], (0, 0))
            elif self.explode_dir == Tile.EXPLODE_DIR.UP:
                base_tile.blit(self.explode_sprites[self.image_idx][2], (0, 0))
            elif self.explode_dir == Tile.EXPLODE_DIR.LEFT:
                base_tile.blit(self.explode_sprites[self.image_idx][3], (0, 0))
            # will add center sprite later
            elif self.explode_dir == Tile.EXPLODE_DIR.CENTER:
                base_tile.blit(self.explode_sprites[self.image_idx][0], (0, 0))
            self.image = base_tile
        self.exploded_count -= 0


class Grid:
    def __init__(self, grid_size, screen_size, tile_sprites, explode_sprites):
        self.grid_size = grid_size
        self.tile_size = screen_size / self.grid_size
        self.tile_group = pygame.sprite.Group()
        self.tile_exploded_groups = []
        self.bubble_groups = []
        self.__tiles = [
            [
                Tile(row, col, self.tile_size, tile_sprites[0], explode_sprites)
                if (row + col) % 2 == 0
                else Tile(row, col, self.tile_size, tile_sprites[1], explode_sprites)
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

    def explode_tiles(self, group_idx):
        group = pygame.sprite.Group()
        for bubble in self.bubble_groups[group_idx][0]:
            self.__tiles[bubble.row][bubble.col].explode_dir = Tile.EXPLODE_DIR.CENTER
            if not group.has(self.__tiles[bubble.row][bubble.col]):
                self.__tiles[bubble.row][bubble.col].exploded_count += 1
            group.add(self.__tiles[bubble.row][bubble.col])

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
                        self.__tiles[row][col].explode_dir = Tile.EXPLODE_DIR(j + 1)
                        if not group.has(self.__tiles[row][col]):
                            self.__tiles[row][col].exploded_count += 1
                        group.add(self.__tiles[row][col])

        self.tile_exploded_groups.append([group, pygame.time.get_ticks()])

    def get_tile(self, row, col):
        return self.__tiles[row][col]

    def get_coord(self, x, y):
        row = int((y + math.ceil(self.tile_size / 2)) / self.tile_size)
        col = int((x + math.ceil(self.tile_size / 2)) / self.tile_size)
        return (row, col)

    def update(self):
        delete_bubble_groups = []
        delete_tile_exploded_groups = []

        for idx, bubble_group in enumerate(self.bubble_groups):
            bubble_group[0].update()
            if pygame.time.get_ticks() - bubble_group[1] >= 3000:
                for bubble in bubble_group[0].sprites():
                    self.toggle_bubble(bubble.row, bubble.col)
                self.explode_tiles(idx)
                bubble_group[0].empty()
                delete_bubble_groups.append(bubble_group)

        for group in delete_bubble_groups:
            self.bubble_groups.remove(group)

        for tile_group in self.tile_exploded_groups:
            if pygame.time.get_ticks() - tile_group[1] >= 500:
                tile_group[0].update(self, reset=True)
                tile_group[0].empty()
                delete_tile_exploded_groups.append(tile_group)
            else:
                tile_group[0].update(self, reset=False)

        for group in delete_tile_exploded_groups:
            self.tile_exploded_groups.remove(group)


class Bubble(pygame.sprite.Sprite):
    class BubbleType(Enum):
        DEFAULT = 0

    def __init__(self, row, col, player_id, explosion_range, bubble_sprites):
        super(Bubble, self).__init__()
        self.player_id = player_id
        self.bubble_sprites = bubble_sprites
        self.row = row
        self.col = col
        self.image_idx = 0
        self.image = bubble_sprites["idle"][0]
        self.rect = self.image.get_rect()
        self.explosion_range = explosion_range
        self.animation_timer = pygame.time.get_ticks()

    def update(self):  # type: ignore
        self.animate()
        tile_size = self.rect.width
        self.rect = self.image.get_rect(
            center=(
                self.col * tile_size + (tile_size / 2),
                self.row * tile_size + (tile_size / 2),
            )
        )

    def animate(self):
        if pygame.time.get_ticks() - self.animation_timer >= 200:
            self.animation_timer = pygame.time.get_ticks()
            self.image_idx = (
                self.image_idx + 1
                if self.image_idx < len(self.bubble_sprites["idle"]) - 2
                else 0
            )
            self.image = self.bubble_sprites["idle"][self.image_idx]


class Player(pygame.sprite.Sprite):
    class Characters(Enum):
        DEFAULT = 0

    def __init__(self, id, vel, player_sprites):
        super(Player, self).__init__()
        self.id = id
        self.player_sprites = player_sprites
        self.sprite_type = "idle"
        self.image = self.player_sprites[self.sprite_type][0][0]
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
        self.sprite_flip_x = 0
        self.sprite_flip_y = 0

    def update(self, grid, pressed_keys, screen_size):  # type: ignore
        self.sprite_type = "idle" if len(pressed_keys) == 0 else "move"
        # resets the image index to 0 if the sprite_type changed, preventing an out of bounds error
        self.image_idx = self.image_idx % len(self.player_sprites[self.sprite_type])
        self.move(grid, pressed_keys, screen_size)
        self.animate()

        self.hitbox = pygame.Rect(
            self.rect.x + self.image.get_width() / 7,
            self.rect.y + self.image.get_height() * (3 / 4),
            self.rect.width - 2 * (self.image.get_width() / 7),
            self.image.get_height() / 4,
        )
        self.image = self.player_sprites[self.sprite_type][self.image_idx][
            self.sprite_flip_x
        ]

        # only for testing
        tile_size = self.rect.width
        pygame.draw.rect(
            self.image, pygame.Color(255, 0, 0), (0, 0, tile_size, tile_size), 1
        )

    def animate(self):
        if pygame.time.get_ticks() - self.animation_timer >= 200:
            self.animation_timer = pygame.time.get_ticks()
            self.image_idx = (self.image_idx + 1) % len(
                self.player_sprites[self.sprite_type]
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
                self.sprite_flip_x = 1
            elif dx == -1:
                self.sprite_flip_x = 0
            self.rect.x += dx * self.vel
            self.rect.y += dy * self.vel

    def is_hit(self, grid):
        total_overlap_area = 0
        player_area = self.hitbox.width * self.hitbox.height

        for group in grid.tile_exploded_groups:
            for tile in group[0]:
                if self.hitbox.colliderect(tile.rect):
                    overlap_rect = self.hitbox.clip(tile.rect)
                    total_overlap_area += overlap_rect.width * overlap_rect.height
                    if total_overlap_area / player_area > 0.66:
                        return True
        return False

    def drop_bubble(self, grid, bubble_sprite):
        if self.num_bubbles > 0:
            coord = grid.get_coord(self.rect.x, self.rect.y)
            if not grid.has_bubble(*coord):
                grid.add_bubble(
                    Bubble(*coord, self.id, self.explosion_range, bubble_sprite)  # type: ignore
                )
                grid.toggle_bubble(*coord)


class GameObject:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.sprite_size = screen_width / NUM_TILES
        self.user_id = 0
        self.img_sprites = self.load_assets()
        self.grid = Grid(
            NUM_TILES,
            screen_width,
            self.img_sprites["tile"]["idle"],
            self.img_sprites["tile"]["explode"],
        )
        self.player_group = pygame.sprite.Group()
        self.player_group.add(Player(self.user_id, 8, self.img_sprites["player"]))
        self.clock = pygame.time.Clock()
        self.running = True
        self.pressed_keys = []

    def load_assets(self):
        sprite_sheets = {}
        img_sprites = {}

        sprite_sheets["characters"] = {}
        sprite_sheets["bubbles"] = {}
        sprite_sheets["tiles"] = {}

        img_sprites["tile"] = {}

        for root, _, files in os.walk("assets/spritesheets/"):
            for file in files:
                if root.split("/")[-2] == ("characters"):
                    sprite_sheets["characters"][
                        Player.Characters.DEFAULT
                    ] = spritesheets.Spritesheet(
                        os.path.join(os.path.curdir, root, file)
                    )
                    img_sprites["player"] = {}
                    img_sprites["player"]["idle"] = sprite_sheets["characters"][
                        Player.Characters.DEFAULT
                    ].get_sprites(
                        0,
                        18,
                        4,
                        self.sprite_size,
                        self.sprite_size,
                        include_flip_x=True,
                    )
                    img_sprites["player"]["move"] = sprite_sheets["characters"][
                        Player.Characters.DEFAULT
                    ].get_sprites(
                        1,
                        18,
                        4,
                        self.sprite_size,
                        self.sprite_size,
                        include_flip_x=True,
                    )

                elif root.endswith("bubbles"):
                    if file == "default.png":
                        sprite_sheets["bubbles"][
                            Bubble.BubbleType.DEFAULT
                        ] = spritesheets.Spritesheet(
                            os.path.join(os.path.curdir, root, file)
                        )
                        img_sprites["bubble"] = {}
                        img_sprites["bubble"]["idle"] = sprite_sheets["bubbles"][
                            Bubble.BubbleType.DEFAULT
                        ].get_sprites(
                            0,
                            8,
                            3,
                            self.sprite_size,
                            self.sprite_size,
                            pygame.Color(26, 122, 62, 255),
                            [pygame.Color(36, 82, 59)],
                        )
                    elif file == "explosion.png":
                        sprite_sheets["tiles"]["explode"] = spritesheets.Spritesheet(
                            os.path.join(os.path.curdir, root, file)
                        )
                        img_sprites["tile"]["explode"] = sprite_sheets["tiles"][
                            "explode"
                        ].get_sprites(
                            0,
                            3,
                            1,
                            self.sprite_size,
                            self.sprite_size,
                            include_rotate_cardinal=True,
                        )

                elif root.endswith("maps"):
                    sprite_sheets["tiles"] = spritesheets.Spritesheet(
                        os.path.join(os.path.curdir, root, file)
                    )
                    img_sprites["tile"]["idle"] = sprite_sheets["tiles"].get_sprites(
                        0, 2, 1, self.sprite_size, self.sprite_size
                    )

        return img_sprites

    def update(self):
        self.grid.update()
        self.player_group.update(self.grid, self.pressed_keys, self.screen.get_size())

        for player in self.player_group.sprites():
            if player.is_hit(self.grid):
                player.rect.x = 0
                player.rect.y = 0

    def draw(self):
        self.screen.fill("black")
        self.grid.tile_group.draw(self.screen)

        for tile_group in self.grid.tile_exploded_groups:
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
                                    self.grid, self.img_sprites["bubble"]
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
            self.clock.tick(60)
        self.terminate()

    def terminate(self):
        # will probably do more stuff here in the future
        pygame.quit()


game = GameObject(1200, 1200)
game.start()
