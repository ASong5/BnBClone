import pygame
import faulthandler
from utils import spritesheets

faulthandler.enable()

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
        self.has_balloon = False
        pygame.draw.rect(self.image, (255, 255, 255), (0, 0, self.size, self.size), 1)

    def update(self, reset):  # type: ignore
        if reset:
            self.image.fill(pygame.Color(0, 0, 0))
            pygame.draw.rect(self.image, (255, 255, 255), (0, 0, self.size, self.size), 1)
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
                            balloon_to_add.row == balloon.row + offset
                            and balloon_to_add.col == balloon.col
                        )
                        or (
                            balloon_to_add.row == balloon.row - offset
                            and balloon_to_add.col == balloon.col
                        )
                        or (
                            balloon_to_add.col == balloon.col + offset
                            and balloon_to_add.row == balloon.row
                        )
                        or (
                            balloon_to_add.col == balloon.col - offset
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
        print('explode')
        group = pygame.sprite.Group()
        for balloon in self.balloon_groups[group_idx][0]:
            for i in range(balloon.explosion_range):
                if balloon.row + i < self.gridSize:
                    group.add(self.__tiles[balloon.row + i][balloon.col])
                if balloon.row - i >= 0:
                    group.add(self.__tiles[balloon.row - i][balloon.col])
                if balloon.col + i < self.gridSize:
                    group.add(self.__tiles[balloon.row][balloon.col + i])
                if balloon.col - i >= 0:
                    group.add(self.__tiles[balloon.row][balloon.col - i])
        self.tile_exploded_groups.append([group, pygame.time.get_ticks()])

    def update(self):
        pass


class Balloon(pygame.sprite.Sprite):
    def __init__(self, row, col, player_id):
        super(Balloon, self).__init__()
        self.player_id = player_id
        self.row = row
        self.col = col
        self.image_idx = 0
        self.image = balloon_sprites[0]
        self.rect = self.image.get_rect()
        self.explosion_range = 4

    def update(self):  # type: ignore
        self.rect = self.image.get_rect(
            center=(
                self.row * tile_size + (tile_size / 2),
                self.col * tile_size + (tile_size / 2),
            )
        )

    def animate(self):
        self.image_idx = (
            self.image_idx + 1 if self.image_idx < len(balloon_sprites) - 1 else 0
        )
        self.image


class Player(pygame.sprite.Sprite):
    def __init__(self, id, vel):
        super(Player, self).__init__()
        self.id = id
        self.image = player_sprites[0]
        self.image_idx = 0
        self.rect = self.image.get_rect()
        self.rect.x = self.rect.center[0]
        self.rect.y = self.rect.center[1]
        self.vel = vel
        self.num_balloons = 1
        pygame.time.set_timer(EVENTS["PLAYER_IDLE"], 200)

    def update(self):  # type: ignore
        player.move()

    def animate(self):
        self.image_idx = (
            self.image_idx + 1 if self.image_idx < len(player_sprites) - 1 else 0
        )
        self.image = player_sprites[self.image_idx]

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
                            self.rect.x += self.vel
                case pygame.K_LEFT:
                    if self.rect.x - self.vel >= 0:
                        new_pos = (self.rect.x - self.vel, self.rect.y)
                        new_coord = self.getTile(*new_pos)
                        if self.getTile(
                            self.rect.x, self.rect.y
                        ) == new_coord or not grid.has_balloon(*new_coord):
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
                grid.add_balloon(Balloon(*coord, self.id))
                grid.toggle_balloon(*coord)

    def getTile(self, x, y):
        row = int((x + self.image.get_width() / 2) / tile_size)
        col = int((y + self.image.get_height() / 2) / tile_size)
        return (row, col)


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
player_sprites = player_sprite_sheet.get_sprites(0, 18, 4, tile_size, tile_size)
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
player = Player(1, 5)
player_group = pygame.sprite.Group()
player.add(player_group)

pressedKeys = []

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == EVENTS["PLAYER_IDLE"]:
            player.animate()
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

    to_delete = []

    for idx, balloon_group in enumerate(grid.balloon_groups):
        balloon_group[0].update()
        if pygame.time.get_ticks() - balloon_group[1] >= 3000:
            for balloon in balloon_group[0].sprites():
                grid.toggle_balloon(balloon.row, balloon.col)
                grid.explode_tiles(idx)
            balloon_group[0].empty()
            to_delete.append(balloon_group)

    for group in to_delete:
        grid.balloon_groups.remove(group)
    player_group.update()
    for tile_group in grid.tile_exploded_groups:
        if pygame.time.get_ticks() - tile_group[1] >= 1000:
            tile_group[0].update(reset=True)
            tile_group[0].empty()
        else:
            tile_group[0].update(reset=False)

    screen.fill("black")
    grid.tile_group.draw(screen)

    for tile_group in grid.tile_exploded_groups:
        tile_group[0].draw(screen)
    for balloon_group in grid.balloon_groups:
        balloon_group[0].draw(screen)

    player_group.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
