import faulthandler
import os
import pickle

import pygame

import entities
import utils.config as config
from grid import Grid
from utils.assets import Asset, AssetStore

faulthandler.enable()


class GameObject:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(config.RESOLUTION)
        self.sprite_size = config.GRID_SIZE / config.NUM_TILES
        self.asset_store = AssetStore(self.sprite_size, config.GRID_SIZE)
        self.map_name = config.MAP_NAME
        self.user_id = 0
        player_list = []
        player_list.append(entities.Player(self.asset_store, self.user_id, 4))
        tile_map = self.fetch_tile_map()
        if tile_map:
            self.grid = Grid(
                config.NUM_TILES,
                config.SPRITE_SIZE,
                self.asset_store,
                player_list,
                tile_map,
            )
        else:
            raise Exception(f"tile_map {self.map_name} does not exist")

        self.clock = pygame.time.Clock()
        self.running = True
        self.pressed_keys = []

    def fetch_tile_map(self):
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(curr_dir, "../tilemaps/", self.map_name)
        file = open(path, "rb")
        tile_map = pickle.load(file)

        return tile_map if tile_map else None

    def update(self):
        for _, asset_dict in self.asset_store["spritesheets"].items():
            for _, asset in asset_dict.items():
                if isinstance(asset, Asset) and asset.animation is not None:
                    asset.animation.update_frame()
        self.grid.update(self.asset_store)
        self.grid.player_group.update(self.grid, config.GRID_SIZE, self.pressed_keys)

    def draw(self):
        self.screen.fill("black")

        self.screen.blit(self.asset_store["static"]["maps"]["default"].image, (0, 0))

        self.screen.blit(self.asset_store["spritesheets"]["bubble-trapped"]["default"].get_current_frame(), (0, 0))

        self.grid.item_group.draw(self.screen)

        self.grid.block_group.draw(self.screen)

        for tile_group in self.grid.explosion_groups:
            tile_group[0].draw(self.screen)

        for bubble_group in self.grid.bubble_groups:
            bubble_group[0].draw(self.screen)

        self.grid.player_group.draw(self.screen)

        self.grid.obstacle_group.draw(self.screen)

        # only for testing
        pygame.draw.rect(
            self.screen,
            pygame.Color(0, 255, 0),
            self.grid.player_group.sprites()[0].hitbox,
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
                        for player in self.grid.player_group.sprites():
                            if player.id == self.user_id:
                                player.drop_bubble(self.grid, self.asset_store)
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
            self.clock.tick(config.FPS)
        self.terminate()

    def terminate(self):
        # will probably do more stuff here in the future
        pygame.quit()


game = GameObject()
game.start()
