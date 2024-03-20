import pygame
import math
import entities
from utils.types import Assets
from item import Item, BubbleItem


class Tile:
    def __init__(self, row, col, size):
        super(Tile, self).__init__()
        self.row = row
        self.col = col
        self.size = size
        self.has_bubble = False


class Grid:
    def __init__(self, grid_size, tile_size, asset_store, players, tile_map):
        self.grid_size = grid_size
        self.tile_size = tile_size
        self.tile_map = tile_map
        self.player_group = pygame.sprite.Group()
        self.player_group.add(players)
        self.explosion_groups = []
        self.item_group = pygame.sprite.Group()
        self.block_group = pygame.sprite.Group()
        self.bubble_groups = []
        self.obstacle_group = pygame.sprite.Group()
        self.trapped_bubble_group = pygame.sprite.Group()
        self.__tiles = [
            [Tile(row, col, self.tile_size) for col in range(self.grid_size)]
            for row in range(self.grid_size)
        ]

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.tile_map[row][col]:
                    asset_data = self.tile_map[row][col]
                    if asset_data[0] == Assets.BLOCKS:
                        self.block_group.add(
                            entities.Block(
                                asset_store, row, col, asset_data[1], self.tile_size
                            )
                        )
                    elif asset_data[0] == Assets.OBSTACLES:
                        self.obstacle_group.add(
                            entities.Obstacle(
                                asset_store,
                                row,
                                col,
                                asset_data[0],
                                asset_data[1],
                                self.tile_size,
                            )
                        )

    def toggle_bubble(self, row, col):
        self.__tiles[row][col].has_bubble = not self.__tiles[row][col].has_bubble

    def has_bubble(self, row, col):
        return self.__tiles[row][col].has_bubble

    def add_bubble(self, bubble_to_add):
        groups_to_merge = set()
        direction_to_ignore = set()
        for bubbles, _ in self.bubble_groups:
            for bubble in bubbles.sprites():
                for i in range(bubble.explosion_range):
                    for j in range(4):
                        if j in direction_to_ignore:
                            continue
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
                        obstacle = entities.Obstacle.get_obstacle(row, col)
                        if isinstance(obstacle, entities.Obstacle):
                            direction_to_ignore.add(j)

                        if bubble_to_add.row == row and bubble_to_add.col == col:
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

    def get_player(self, id):
        for player in self.player_group:
            if player.id == id:
                return player
        return None

    def drop_item(self, asset_store, row, col, item_type):
        self.item_group.add(BubbleItem(asset_store, row, col, item_type))

    def explode_tiles(self, group_idx, asset_store):
        group = pygame.sprite.Group()
        for bubble in self.bubble_groups[group_idx][0]:
            explosion = entities.Explosion(
                asset_store,
                bubble.row,
                bubble.col,
                entities.Explosion.EXPLODE_DIR.CENTER,
                self.tile_size,
            )
            group.add(explosion)

            direction_to_ignore = set()

            for i in range(bubble.explosion_range):
                for j in range(4):
                    if j in direction_to_ignore:
                        continue
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
                        obstacle = entities.Obstacle.get_obstacle(row, col)

                        if isinstance(obstacle, entities.Obstacle):
                            if isinstance(obstacle, entities.Block):
                                obstacle.explode(self.item_group)
                            direction_to_ignore.add(j)
                        else:
                            item = Item.get_item(row, col)
                            if item:
                                item.kill()
                            explosion = entities.Explosion(
                                asset_store,
                                row,
                                col,
                                entities.Explosion.EXPLODE_DIR(j + 1),
                                self.tile_size,
                            )
                            group.add(explosion)

        self.explosion_groups.append([group, pygame.time.get_ticks()])

    def get_tile(self, row, col):
        return self.__tiles[row][col]

    def get_coord(self, x, y):
        row = int((y + math.ceil(self.tile_size / 2)) / self.tile_size)
        col = int((x + math.ceil(self.tile_size / 2)) / self.tile_size)
        return (row, col)

    def update(self, asset_store):
        delete_bubble_groups = []
        delete_tile_exploded_groups = []

        for player in self.player_group.sprites():
            for sprite in player.is_collide(
                *[explosion_group[0] for explosion_group in self.explosion_groups],
                self.item_group,
                self.block_group,
            ):
                if isinstance(sprite, entities.Explosion):
                    player.trap_player(self)
                elif isinstance(sprite, Item):
                    player.pick_up_item(sprite)

        for idx, bubble_group in enumerate(self.bubble_groups):
            bubble_group[0].update()
            if pygame.time.get_ticks() - bubble_group[1] >= 3000:
                for bubble in bubble_group[0].sprites():
                    self.toggle_bubble(bubble.row, bubble.col)
                    player = self.get_player(bubble.player_id)
                    if player:
                        player.num_bubbles += 1
                self.explode_tiles(idx, asset_store)

                bubble_group[0].empty()
                delete_bubble_groups.append(bubble_group)

        for group in delete_bubble_groups:
            self.bubble_groups.remove(group)

        for group in self.explosion_groups:
            if pygame.time.get_ticks() - group[1] >= 500:
                group[0].empty()
                delete_tile_exploded_groups.append(group)
            else:
                group[0].update()

        for group in delete_tile_exploded_groups:
            self.explosion_groups.remove(group)

        self.trapped_bubble_group.update()
        self.item_group.update()
        self.block_group.update()
        self.obstacle_group.update()
