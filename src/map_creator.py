import pygame
import os
import pickle
from utils.assets import AssetStore, Asset
import utils.config as config


class Image(pygame.sprite.Sprite):
    def __init__(self, row, col, asset_size, asset=None):
        super(Image, self).__init__()
        self.row = row
        self.col = col
        self.empty_image = pygame.Surface((asset_size, asset_size), pygame.SRCALPHA)
        self.image = self.empty_image if asset is None else asset.image
        self.rect = self.image.get_rect(topleft=(col * asset_size, row * asset_size))
        self.original_pos = [self.rect.x, self.rect.y]

        if asset:
             x_offset = asset.config.get("x_pos_offset")
             y_offset = asset.config.get("y_pos_offset")
             self.rect.x += x_offset if x_offset is not None else 0
             self.rect.y += y_offset if y_offset is not None else 0

    def update(self):  # type: ignore
        pass

    def set_image(self, coord, asset, tile_map, last_edited_image):
        if last_edited_image != self:
            if self.rect and self.rect.collidepoint(coord):
                self.rect.x = self.original_pos[0]
                self.rect.y = self.original_pos[1]

                if self.image == asset.image:
                    self.image = self.empty_image
                    tile_map[self.row][self.col] = None
                else:
                    x_offset = asset.config.get("x_pos_offset")
                    y_offset = asset.config.get("y_pos_offset")
                    self.image = asset.image
                    self.rect.x += x_offset if x_offset is not None else 0
                    self.rect.y += y_offset if y_offset is not None else 0
                    tile_map[self.row][self.col] = [asset.asset_type, asset.asset_name]
                return self
        return last_edited_image


class Canvas:
    def __init__(self, num_tiles, tile_size, asset_store, tile_map=None):
        self.num_tiles = num_tiles
        self.tile_size = tile_size
        self.asset_store = asset_store
        self.image_group = pygame.sprite.Group()

        if tile_map:
            self.tile_map = tile_map
            for row in range(self.num_tiles):
                for col in range(self.num_tiles):
                    if self.tile_map[row][col]:
                        self.image_group.add(
                            Image(
                                row,
                                col,
                                self.tile_size,
                                self.asset_store["static"][self.tile_map[row][col][0]][
                                    self.tile_map[row][col][1]
                                ],
                            )
                        )
                    else:
                        self.image_group.add(Image(row, col, self.tile_size))

        else:
            self.tile_map = [
                [None for _ in range(self.num_tiles)] for _ in range(self.num_tiles)
            ]

            for row in range(self.num_tiles):
                for col in range(self.num_tiles):
                    self.tile_map[row][col] = None
                    self.image_group.add(Image(row, col, self.tile_size))


class AssetPanel(pygame.sprite.Sprite):
    def __init__(self, grid_size, screen_width, asset_store):
        super(AssetPanel, self).__init__()
        self.grid_size = grid_size
        self.x = grid_size
        self.y = 0
        self.panel_width = screen_width - grid_size
        self.panel_height = grid_size
        self.image = pygame.Surface((self.panel_width, self.panel_height))
        self.rect = self.image.get_rect()
        pygame.draw.rect(
            self.image,
            pygame.Color((128, 128, 128)),
            (0, 0, self.panel_width, self.panel_height),
        )

        self.assets = []
        self.asset_at_pos = {}
        self.asset_store = asset_store
        self.load_assets(self.asset_store["static"]["blocks"])
        self.load_assets(self.asset_store["static"]["obstacles"])

    def update(self):  # type: ignore
        x = y = 0
        if self.image:
            for asset in self.assets:
                if x + asset.image.get_width() >= self.panel_width:
                    y += asset.image.get_height() + 10
                    x += 0
                self.image.blit(
                    asset.image,
                    (x, y),
                )
                self.asset_at_pos[(x + self.grid_size, y)] = asset
                x += asset.image.get_width() + 10

    def load_assets(self, start_dict):
        for key, val in start_dict.items():
            if not isinstance(val, Asset):
                self.load_assets(start_dict[key])
            else:
                self.assets.append(val)

    def get_clicked_asset(self, coord):
        for pos, asset in self.asset_at_pos.items():
            if (
                pos[0] <= coord[0] <= pos[0] + asset.image.get_width()
                and pos[1] <= coord[1] <= pos[1] + asset.image.get_height()
            ):
                return asset
        return None


class MapCreator:
    def __init__(self, map_name, mode):
        pygame.init()
        self.screen = pygame.display.set_mode(config.RESOLUTION)

        self.mode = mode
        self.map_name = map_name
        self.sprite_size = config.GRID_SIZE / config.NUM_TILES
        self.asset_store = AssetStore(self.sprite_size, config.GRID_SIZE)

        if mode == 1:
            tile_map = self.fetch_tile_map()
            if tile_map:
                self.canvas = Canvas(
                    config.NUM_TILES, config.SPRITE_SIZE, self.asset_store, tile_map
                )
            else:
                raise Exception(f"tile_map {self.map_name} does not exist")
        else:
            self.canvas = Canvas(config.NUM_TILES, config.SPRITE_SIZE, self.asset_store)

        self.asset_panel = AssetPanel(
            config.GRID_SIZE, self.screen.get_width(), self.asset_store
        )
        self.clock = pygame.time.Clock()
        self.running = True
        self.selected_asset = self.asset_panel.assets[0]
        self.last_edited_canvas_image = None

    def fetch_tile_map(self):
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(curr_dir, "../tilemaps/", self.map_name)
        file = open(path, "rb")
        tile_map = pickle.load(file)

        return tile_map if tile_map else None

    def handle_click(self, coord):
        for image in self.canvas.image_group:
            image = image.set_image(
                coord,
                self.selected_asset,
                self.canvas.tile_map,
                self.last_edited_canvas_image,
            )
            if image != self.last_edited_canvas_image:
                self.last_edited_canvas_image = image
                break

    def set_mouse_cursor(self):
        pygame.mouse.set_cursor(
            (
                int(self.selected_asset.image.get_width() / 2),
                int(self.selected_asset.image.get_height() / 2),
            ),
            self.selected_asset.image,
        )

    def update(self):
        self.asset_panel.update()

    def draw(self):
        self.screen.fill("black")
        self.screen.blit(self.asset_store["static"]["maps"]["default"].image, (0, 0))
        self.canvas.image_group.draw(self.screen)
        if self.asset_panel.image:
            self.screen.blit(
                self.asset_panel.image, (self.asset_panel.x, self.asset_panel.y)
            )

        pygame.display.flip()

    def start(self):
        self.set_mouse_cursor()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_coord = pygame.mouse.get_pos()
                    asset = self.asset_panel.get_clicked_asset(mouse_coord)
                    if asset:
                        self.selected_asset = asset
                        self.set_mouse_cursor()

            mouse_coord = pygame.mouse.get_pos()
            if pygame.mouse.get_pressed()[0]:
                self.handle_click(mouse_coord)

            self.update()
            self.draw()
            self.clock.tick(config.FPS)
        self.terminate()

    def terminate(self):
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(curr_dir, "../tilemaps/", self.map_name)
        file = open(path, "w+b")
        pickle.dump(self.canvas.tile_map, file)
        pygame.quit()


option = None
while option not in [1, 2]:
    print(
        "Would you like to update an existing map or create a new map?\n1) Update\n2) New"
    )
    option = int(input("Enter selection: "))

map_name = input("Enter the map name: ")

game = MapCreator(map_name, option)
game.start()
