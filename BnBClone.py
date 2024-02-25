import os
import pygame
from enum import Enum
import faulthandler
from utils import spritesheets

faulthandler.enable()

NUM_TILES = 15


class Characters(Enum):
    DEFAULT = 0


class Bubbles(Enum):
    DEFAULT = 0


EVENTS = {
    "PLAYER_IDLE": pygame.USEREVENT + 1,
    "PLAYER_MOVE": pygame.USEREVENT + 2,
    "BUBBLE": pygame.USEREVENT + 3,
}


class Tile(pygame.sprite.Sprite):
    def __init__(self, row, col, size):
        super(Tile, self).__init__()
        self.row = row
        self.col = col
        self.size = size
        self.image = pygame.Surface((size, size))
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.col * self.size, self.row * self.size)
        self.has_bubble = False
        self.is_exploded = False
        pygame.draw.rect(self.image, (255, 255, 255), (0, 0, self.size, self.size), 1)

    def update(self, grid, reset):  # type: ignore
        if reset:
            self.image.fill(pygame.Color(0, 0, 0))
            pygame.draw.rect(
                self.image, (255, 255, 255), (0, 0, self.size, self.size), 1
            )
            self.is_exploded = False
        else:
            self.image.fill(pygame.Color(0, 0, 0))
            pygame.draw.rect(
                self.image, (255, 255, 255), (0, 0, self.size, self.size), 1
            )
            for group in grid.tile_exploded_groups:
                if group[0].has(self):
                    self.is_exploded = True
                    self.image.fill(pygame.Color(255, 0, 0))


class Grid:
    def __init__(self, grid_size, screen_size):
        self.grid_size = grid_size
        self.tile_size = screen_size / self.grid_size
        self.tile_group = pygame.sprite.Group()
        self.tile_exploded_groups = []
        self.bubble_groups = []
        self.__tiles = [
            [Tile(row, col, self.tile_size) for col in range(self.grid_size)]
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
            group.add(self.__tiles[bubble.row][bubble.col])
            for i in range(bubble.explosion_range):
                if bubble.row + i + 1 < self.grid_size:
                    group.add(self.__tiles[bubble.row + i + 1][bubble.col])
                if bubble.row - i - 1 >= 0:
                    group.add(self.__tiles[bubble.row - i - 1][bubble.col])
                if bubble.col + i + 1 < self.grid_size:
                    group.add(self.__tiles[bubble.row][bubble.col + i + 1])
                if bubble.col - i - 1 >= 0:
                    group.add(self.__tiles[bubble.row][bubble.col - i - 1])
        self.tile_exploded_groups.append([group, pygame.time.get_ticks()])

    def get_tile(self, row, col):
        return self.__tiles[row][col]

    def update(self):
        pass

class Bubble(pygame.sprite.Sprite):
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
    def __init__(self, id, vel, player_sprites):
        super(Player, self).__init__()
        self.id = id
        self.player_sprites = player_sprites
        self.image = self.player_sprites["idle"][0][0]
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
        self.sprite_flip = 1

    def update(self, grid, pressed_keys, screen_size):  # type: ignore
        self.move(grid, pressed_keys, screen_size)
        self.animate(pressed_keys)

        self.hitbox = pygame.Rect(
            self.rect.x + self.image.get_width() / 7,
            self.rect.y + self.image.get_height() * (3 / 4),
            self.rect.width - 2 * (self.image.get_width() / 7),
            self.image.get_height() / 4,
        )

        tile_size = self.rect.width

        # only for testing
        pygame.draw.rect(
            self.image, pygame.Color(255, 0, 0), (0, 0, tile_size, tile_size), 1
        )

    def animate(self, pressed_keys):
        if pygame.time.get_ticks() - self.animation_timer >= 200:
            sprite_type = (
                self.player_sprites["idle"]
                if len(pressed_keys) == 0
                else self.player_sprites["move"]
            )
            self.animation_timer = pygame.time.get_ticks()
            self.image_idx = (
                self.image_idx + 1 if self.image_idx < len(sprite_type) - 1 else 0
            )
            self.image = sprite_type[self.image_idx][self.sprite_flip]



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
        new_coord = self.get_tile(*new_pos, grid)
        if (
            self.get_tile(self.rect.x, self.rect.y, grid) == new_coord
            or not grid.has_bubble(*new_coord)
        ) and (
            0 <= new_pos[0] <= screen_size[0] - self.image.get_width()
            and 0 <= new_pos[1] <= screen_size[1] - self.image.get_height()
        ):
            if dx == 1:
                self.sprite_flip = 1
            elif dx == -1:
                self.sprite_flip = 0          
            self.rect.x += dx * self.vel
            self.rect.y += dy * self.vel


    # might put this in its own utiliy/engine module
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
            coord = self.get_tile(self.rect.x, self.rect.y, grid)
            if not grid.has_bubble(*coord):
                grid.add_bubble(
                    Bubble(*coord, self.id, self.explosion_range, bubble_sprite)
                )
                grid.toggle_bubble(*coord)

    def get_tile(self, x, y, grid):
        row = int((y + self.image.get_height() / 2) / grid.tile_size)
        col = int((x + self.image.get_width() / 2) / grid.tile_size)
        return (row, col)


class GameObject:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.grid = Grid(NUM_TILES, screen_width)
        self.user_id = 0
        self.img_sprites = self.load_assets()
        self.player_group = pygame.sprite.Group()
        self.player_group.add(Player(self.user_id, 5, self.img_sprites["player"]))
        self.clock = pygame.time.Clock()
        self.running = True
        self.pressed_keys = []

    def load_assets(self):
        sprite_sheets = {}
        img_sprites = {}
        sprite_sheets["characters"] = {}
        sprite_sheets["bubbles"] = {}
        for root, _, files in os.walk("assets/spritesheets/"):
            for file in files:
                if root.split("/")[-2] == ("characters"):
                    sprite_sheets["characters"][
                        Characters.DEFAULT
                    ] = spritesheets.Spritesheet(
                        os.path.join(os.path.curdir, root, file)
                    )
                    img_sprites["player"] = {}
                    img_sprites["player"]["idle"] = sprite_sheets[
                        "characters"
                    ][Characters.DEFAULT].get_sprites(
                        0,
                        18,
                        4,
                        self.grid.tile_size,
                        self.grid.tile_size,
                        include_flip=True,
                    )
                    img_sprites["player"]["move"] = sprite_sheets[
                        "characters"
                    ][Characters.DEFAULT].get_sprites(
                        1,
                        18,
                        4,
                        self.grid.tile_size,
                        self.grid.tile_size,
                        include_flip=True,
                    )

                elif root.endswith("bubbles"):
                    sprite_sheets["bubbles"][
                        Bubbles.DEFAULT
                    ] = spritesheets.Spritesheet(
                        os.path.join(os.path.curdir, root, file)
                    )
                    img_sprites["bubble"] = {}
                    img_sprites["bubble"]["idle"] = sprite_sheets["bubbles"][
                        Bubbles.DEFAULT
                    ].get_sprites(
                        0,
                        8,
                        3,
                        self.grid.tile_size,
                        self.grid.tile_size,
                        pygame.Color(26, 122, 62, 255),
                        [pygame.Color(36, 82, 59)],
                    )
        
        return img_sprites

        
    def update(self):
        delete_bubble_groups = []
        delete_tile_exploded_groups = []

        for idx, bubble_group in enumerate(self.grid.bubble_groups):
            bubble_group[0].update()
            if pygame.time.get_ticks() - bubble_group[1] >= 3000:
                for bubble in bubble_group[0].sprites():
                    self.grid.toggle_bubble(bubble.row, bubble.col)
                self.grid.explode_tiles(idx)
                bubble_group[0].empty()
                delete_bubble_groups.append(bubble_group)

        for group in delete_bubble_groups:
            self.grid.bubble_groups.remove(group)

        self.player_group.update(self.grid, self.pressed_keys, self.screen.get_size())

        for tile_group in self.grid.tile_exploded_groups:
            if pygame.time.get_ticks() - tile_group[1] >= 500:
                tile_group[0].update(self.grid, reset=True)
                tile_group[0].empty()
                delete_tile_exploded_groups.append(tile_group)
            else:
                tile_group[0].update(self.grid, reset=False)

        for group in delete_tile_exploded_groups:
            self.grid.tile_exploded_groups.remove(group)

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
