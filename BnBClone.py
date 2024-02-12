import pygame
import copy
from typing_extensions import Protocol
import faulthandler
from utils import spritesheets

faulthandler.enable()

EVENTS = {
    "PLAYER_IDLE": pygame.USEREVENT + 1,
    "PLAYER_MOVE": pygame.USEREVENT + 2,
    "BUBBLE": pygame.USEREVENT + 3,
}


class _HasRect(Protocol):
    rect: pygame.Rect


class Tile(pygame.sprite.Sprite):
    def __init__(self, row, col, size):
        super(Tile, self).__init__()
        self.row = row
        self.col = col
        self.size = size
        self.image = pygame.Surface((size, size))
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.col * self.size, self.row * self.size)
        self.has_balloon = False
        self.is_exploded = False
        pygame.draw.rect(self.image, (255, 255, 255), (0, 0, self.size, self.size), 1)

    def update(self, reset):  # type: ignore
        if reset:
            self.image.fill(pygame.Color(0, 0, 0))
            pygame.draw.rect(
                self.image, (255, 255, 255), (0, 0, self.size, self.size), 1
            )
        else:
            for group in grid.tile_exploded_groups:
                if group[0].has(self):
                    self.image.fill(pygame.Color(255, 0, 0))


class Grid:
    def __init__(self, gridSize, tileSize):
        self.gridSize = gridSize
        self.tileSize = tileSize
        self.tile_group = pygame.sprite.Group()
        self.tile_exploded_groups = []
        self.balloon_groups = []
        self.__tiles = [
            [Tile(row, col, self.tileSize) for row in range(self.gridSize)]
            for col in range(self.gridSize)
        ]

        for row in range(self.gridSize):
            for col in range(self.gridSize):
                self.tile_group.add(self.__tiles[row][col])

    def toggle_balloon(self, row, col):
        self.__tiles[row][col].has_balloon = not self.__tiles[row][col].has_balloon

    def has_balloon(self, row, col):
        return self.__tiles[row][col].has_balloon

    def add_balloon(self, balloon_to_add):
        groups_to_merge = set()
        for balloons, _ in self.balloon_groups:
            for balloon in balloons.sprites():
                for offset in range(balloon.explosion_range):
                    if (
                        (
                            balloon_to_add.row == balloon.row + offset + 1
                            and balloon_to_add.col == balloon.col
                        )
                        or (
                            balloon_to_add.row == balloon.row - offset - 1
                            and balloon_to_add.col == balloon.col
                        )
                        or (
                            balloon_to_add.col == balloon.col + offset + 1
                            and balloon_to_add.row == balloon.row
                        )
                        or (
                            balloon_to_add.col == balloon.col - offset - 1
                            and balloon_to_add.row == balloon.row
                        )
                    ):
                        groups_to_merge.add(balloons)
                        break

        if len(groups_to_merge) > 0:
            first_group = list(groups_to_merge)[0]
            for other_group in list(groups_to_merge)[1:]:
                if other_group in [group for group, _ in self.balloon_groups]:
                    for sprite in other_group.sprites():
                        first_group.add(sprite)
                    self.balloon_groups = [
                        grp_info
                        for grp_info in self.balloon_groups
                        if grp_info[0] != other_group
                    ]
            first_group.add(balloon_to_add)

        else:
            group = pygame.sprite.Group()
            group.add(balloon_to_add)
            self.balloon_groups.append([group, pygame.time.get_ticks()])

    def explode_tiles(self, group_idx):
        group = pygame.sprite.Group()
        for balloon in self.balloon_groups[group_idx][0]:
            group.add(self.__tiles[balloon.row][balloon.col])
            for i in range(balloon.explosion_range):
                if balloon.row + i + 1 < self.gridSize:
                    group.add(self.__tiles[balloon.row + i + 1][balloon.col])
                if balloon.row - i - 1 >= 0:
                    group.add(self.__tiles[balloon.row - i - 1][balloon.col])
                if balloon.col + i + 1 < self.gridSize:
                    group.add(self.__tiles[balloon.row][balloon.col + i + 1])
                if balloon.col - i - 1 >= 0:
                    group.add(self.__tiles[balloon.row][balloon.col - i - 1])
        self.tile_exploded_groups.append([group, pygame.time.get_ticks()])

    def update(self):
        pass


class Balloon(pygame.sprite.Sprite):
    def __init__(self, row, col, player_id, explosion_range):
        super(Balloon, self).__init__()
        self.player_id = player_id
        self.row = row
        self.col = col
        self.image_idx = 0
        self.image = balloon_sprites[0]
        self.rect = self.image.get_rect()
        self.explosion_range = explosion_range
        self.animation_timer = pygame.time.get_ticks()

    def update(self):  # type: ignore
        self.animate()
        self.rect = self.image.get_rect(
            center=(
                self.row * tile_size + (tile_size / 2),
                self.col * tile_size + (tile_size / 2),
            )
        )

    def animate(self):
        if pygame.time.get_ticks() - self.animation_timer >= 200:
            self.animation_timer = pygame.time.get_ticks()
            self.image_idx = (
                self.image_idx + 1 if self.image_idx < len(balloon_sprites) - 2 else 0
            )
            self.image = balloon_sprites[self.image_idx]


class Player(pygame.sprite.Sprite):
    def __init__(self, id, vel):
        super(Player, self).__init__()
        self.id = id
        self.image = player_sprites[0][0]
        self.image_idx = 0
        self.rect = self.image.get_rect()

        self.hitbox = pygame.Rect(
            self.rect.x,
            self.rect.y + self.rect.height - tile_size / 3,
            self.rect.width,
            tile_size / 3,
        )       
        self.vel = vel
        self.num_balloons = 1
        self.explosion_range = 7
        self.animation_timer = pygame.time.get_ticks()
        self.sprite_flip = 1

    def update(self):  # type: ignore
        player.move()
        player.animate()
        self.hitbox = pygame.Rect(
            self.rect.x,
            self.rect.y + self.rect.height - tile_size / 3,
            self.rect.width,
            tile_size / 3,
        )
        pygame.draw.rect(
            self.image, pygame.Color(255, 0, 0), (0, 0, tile_size, tile_size), 1
        )

    def animate(self):
        if pygame.time.get_ticks() - self.animation_timer >= 200:
            sprite_type = (
                player_sprites if len(pressedKeys) == 0 else player_walk_sprites
            )
            self.animation_timer = pygame.time.get_ticks()
            self.image_idx = (
                self.image_idx + 1 if self.image_idx < len(sprite_type) - 1 else 0
            )
            self.image = sprite_type[self.image_idx][self.sprite_flip]

    def move(self):
        if len(pressedKeys) > 0:
            match pressedKeys[-1]:
                case pygame.K_RIGHT:
                    if (
                        self.rect.x + self.image.get_width() + self.vel
                        <= screen.get_width()
                    ):
                        new_pos = (self.rect.x + self.vel, self.rect.y)
                        new_coord = self.getTile(*new_pos)
                        if self.getTile(
                            self.rect.x, self.rect.y
                        ) == new_coord or not grid.has_balloon(*new_coord):
                            self.sprite_flip = 1
                            self.rect.x += self.vel
                case pygame.K_LEFT:
                    if self.rect.x - self.vel >= 0:
                        new_pos = (self.rect.x - self.vel, self.rect.y)
                        new_coord = self.getTile(*new_pos)
                        if self.getTile(
                            self.rect.x, self.rect.y
                        ) == new_coord or not grid.has_balloon(*new_coord):
                            self.sprite_flip = 0
                            self.rect.x -= self.vel

                case pygame.K_UP:
                    if self.rect.y - self.vel >= 0:
                        new_pos = (self.rect.x, self.rect.y - self.vel)
                        new_coord = self.getTile(*new_pos)
                        if self.getTile(
                            self.rect.x, self.rect.y
                        ) == new_coord or not grid.has_balloon(*new_coord):
                            self.rect.y -= self.vel

                case pygame.K_DOWN:
                    if (
                        self.rect.y + self.image.get_height() + self.vel
                        <= screen.get_height()
                    ):
                        new_pos = (self.rect.x, self.rect.y + self.vel)
                        new_coord = self.getTile(*new_pos)
                        if self.getTile(
                            self.rect.x, self.rect.y
                        ) == new_coord or not grid.has_balloon(*new_coord):
                            self.rect.y += self.vel

    def dropBalloon(self):
        if self.num_balloons > 0:
            coord = self.getTile(self.rect.x, self.rect.y)
            if not grid.has_balloon(*coord):
                grid.add_balloon(Balloon(*coord, self.id, self.explosion_range))
                grid.toggle_balloon(*coord)

    def isHit(self, sprite_one, sprite_two):
        return sprite_one.hitbox.colliderect(sprite_two.rect)

    #    def isHit(self):
    #        row, col = self.getTile(self.rect.x, self.rect.y)
    #        if grid.__tiles[row][col].is_exploded:
    #            tile_x_left_bound = row * tile_size
    #            tile_x_right_bound = tile_x_left_bound + tile_size
    #            tile_y_top_bound = col * tile_size
    #            tile_y_bottom_bound = tile_y_top_bound + tile_size
    #            player_right_bound = self.rect.x + tile_size
    #            player_left_bound = self.rect.x
    #            player_top_bound = self.image.get_height() -
    #            player_bottom_bound = self.rect.y + tile_size
    #            hit_threshold = tile_size / 3
    #
    #            if tile_x_right_bound - player_right_bound >= hit_threshold or\
    #            t
    #

    def getTile(self, x, y):
        row = int((x + self.image.get_width() / 2) / tile_size)
        col = int((y + self.image.get_height() / 2) / tile_size)
        return (row, col)


class player_hitbox_ratio(pygame.sprite.collide_rect_ratio):
    def __init__(self, ratio):
        super(player_hitbox_ratio, self).__init__(ratio)

    def __call__(self, left: Player, right: _HasRect) -> bool:  # type: ignore
        tmp_copy = copy.copy(left)
        tmp_copy.rect = left.hitbox.copy()
        tmp_width = left.hitbox.width
        tmp_height = left.hitbox.height
        res = super().__call__(tmp_copy, right)
        left.hitbox.width = tmp_width
        left.hitbox.height = tmp_height

        return res


pygame.init()
screen = pygame.display.set_mode((1200, 1200))
player_sprite_sheet = spritesheets.Spritesheet(
    "/home/pundrew/git/github/Projects/BnBClone/assets/spritesheets/robo/robo_ss.png"
)

balloon_sprite_sheet = spritesheets.Spritesheet(
    "/home/pundrew/git/github/Projects/BnBClone/assets/spritesheets/bubble.png"
)


NUM_TILES = 15
width, height = pygame.display.get_surface().get_size()
tile_size = height / NUM_TILES
player_sprites = player_sprite_sheet.get_sprites(
    0, 18, 4, tile_size, tile_size, include_flip=True
)
player_walk_sprites = player_sprite_sheet.get_sprites(
    1, 18, 4, tile_size, tile_size, include_flip=True
)
balloon_sprites = balloon_sprite_sheet.get_sprites(
    0,
    8,
    3,
    tile_size,
    tile_size,
    pygame.Color(26, 122, 62, 255),
    [pygame.Color(36, 82, 59)],
)
clock = pygame.time.Clock()
running = True

grid = Grid(NUM_TILES, tile_size)
player = Player(1, 4)
player_group = pygame.sprite.Group()
player.add(player_group)

pressedKeys = []

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if (
                event.key == pygame.K_UP
                or event.key == pygame.K_DOWN
                or event.key == pygame.K_RIGHT
                or event.key == pygame.K_LEFT
            ):
                pressedKeys.append(event.key)
            if event.key == pygame.K_SPACE:
                player.dropBalloon()
        elif event.type == pygame.KEYUP:
            if (
                event.key == pygame.K_UP
                or event.key == pygame.K_DOWN
                or event.key == pygame.K_RIGHT
                or event.key == pygame.K_LEFT
            ):
                pressedKeys.remove(event.key)

    delete_balloon_groups = []
    delete_tile_exploded_groups = []

    for idx, balloon_group in enumerate(grid.balloon_groups):
        balloon_group[0].update()
        if pygame.time.get_ticks() - balloon_group[1] >= 3000:
            for balloon in balloon_group[0].sprites():
                grid.toggle_balloon(balloon.row, balloon.col)
            grid.explode_tiles(idx)
            balloon_group[0].empty()
            delete_balloon_groups.append(balloon_group)

    for group in delete_balloon_groups:
        grid.balloon_groups.remove(group)

    player_group.update()
    for tile_group in grid.tile_exploded_groups:
        if (
            len(
                pygame.sprite.groupcollide(
                    player_group,
                    tile_group[0],
                    False,
                    False,
                    player_hitbox_ratio(0.66),
                )
            )
            > 0
        ):
            player.rect.x = 0
            player.rect.y = 0
        if pygame.time.get_ticks() - tile_group[1] >= 500:
            tile_group[0].update(reset=True)

            tile_group[0].empty()
            delete_tile_exploded_groups.append(tile_group)
        else:
            tile_group[0].update(reset=False)

    for group in delete_tile_exploded_groups:
        grid.tile_exploded_groups.remove(group)

    screen.fill("black")
    grid.tile_group.draw(screen)
    for tile_group in grid.tile_exploded_groups:
        tile_group[0].draw(screen)
    for balloon_group in grid.balloon_groups:
        balloon_group[0].draw(screen)

    player_group.draw(screen)
    pygame.draw.rect(screen, pygame.Color(0, 255, 0), player.hitbox, 1)
    pygame.draw.circle(screen, pygame.Color(0, 0, 255,), (player.rect.x, player.rect.y), 4)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
