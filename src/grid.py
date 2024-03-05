import pygame
import math
from entities import Explosion
from utils.types import Assets, Maps


class Tile:
    def __init__(self, row, col, size):
        super(Tile, self).__init__()
        self.row = row
        self.col = col
        self.size = size
        self.has_bubble = False
        self.has_obstacle = False


class Grid:
    def __init__(self, grid_size, tile_size, asset_store):
        self.grid_size = grid_size
        self.tile_size = tile_size
        config = asset_store["static"][Assets.MAPS][Maps.DEFAULT].config
        self.tile_is_obstacle_list = config.get("obstacles")
        self.explosion_group = []
        self.bubble_groups = []
        self.__tiles = [
            [
                Tile(row, col, self.tile_size)
                if (row + col) % 2 == 0
                else Tile(row, col, self.tile_size)
                for col in range(self.grid_size)
            ]
            for row in range(self.grid_size)
        ]

        for coord in self.tile_is_obstacle_list:
            self.__tiles[coord[0]][coord[1]].has_obstacle = True


    def toggle_bubble(self, row, col):
        self.__tiles[row][col].has_bubble = not self.__tiles[row][col].has_bubble

    def has_bubble(self, row, col):
        return self.__tiles[row][col].has_bubble

    def has_obstacle(self, row, col):
        return self.__tiles[row][col].has_obstacle

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

    def explode_tiles(self, group_idx, asset_store):
        group = pygame.sprite.Group()
        for bubble in self.bubble_groups[group_idx][0]:
            explosion = Explosion(
                asset_store,
                bubble.row,
                bubble.col,
                Explosion.EXPLODE_DIR.CENTER,
                self.tile_size,
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
                            asset_store,
                            row,
                            col,
                            Explosion.EXPLODE_DIR(j + 1),
                            self.tile_size,
                        )
                        group.add(explosion)

        self.explosion_group.append([group, pygame.time.get_ticks()])

    def get_tile(self, row, col):
        return self.__tiles[row][col]

    def get_coord(self, x, y):
        row = int((y + math.ceil(self.tile_size / 2)) / self.tile_size)
        col = int((x + math.ceil(self.tile_size / 2)) / self.tile_size)
        return (row, col)

    def update(self, asset_store):
        delete_bubble_groups = []
        delete_tile_exploded_groups = []

        for idx, bubble_group in enumerate(self.bubble_groups):
            bubble_group[0].update()
            if pygame.time.get_ticks() - bubble_group[1] >= 3000:
                for bubble in bubble_group[0].sprites():
                    self.toggle_bubble(bubble.row, bubble.col)
                self.explode_tiles(idx, asset_store)
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
