import pygame
import faulthandler
from utils import spritesheets
from utils.types import Assets, Bubbles, Characters, Explosions
from grid import Grid
from entities import Player, AnimationComponent
from assets import Asset

faulthandler.enable()
pygame.init()

NUM_TILES = 15

class GameObject:
    def __init__(self, screen_size):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_size, screen_size))
        self.sprite_size = screen_size / NUM_TILES
        self.user_id = 0
        self.assets = self.load_assets()
        self.grid = Grid(
            NUM_TILES,
            screen_size,
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


game = GameObject(1200)
game.start()
