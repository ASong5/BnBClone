import faulthandler
import os
import pickle
import pygame
import socketio
from room_manager import RoomManager
import entities
import utils.config as config
from grid import Grid
from utils.assets import Asset, AssetStore

faulthandler.enable()


class GameObject:
    def __init__(self):
        pygame.init()
        self.user_id = None
        self.sio = socketio.Client()

        # Event handlers for Socket.IO
        @self.sio.event
        def connect():
            print("Connected to server")
            self.user_id = (
                self.sio.get_sid()
            )  # Use the Socket.IO session ID as the user ID

        @self.sio.event
        def disconnect():
            print("Disconnected from server")
            self.running = False  # Ensure the game loop stops if disconnected

        @self.sio.event
        def update_game_state(data):
            players = data["players"]
            # Iterate over the list of players received from the server
            for player_data in players:
                player_id = player_data["player_id"]
                x = player_data["x"]
                y = player_data["y"]
                
                # Store remote player actions instead of directly updating positions
                self.player_actions[player_id] = player_data["pressed_keys"]

                # Check if the player already exists locally
                player_found = False
                for player in self.grid.player_group.sprites():
                    if player.id == player_id:
                        player_found = True
                        break

                # If player does not exist locally, add them
                if not player_found:
                    print(f"Adding player {player_id}")
                    new_player = entities.Player(
                        self.asset_store, player_id, self.max_speed, x, y
                    )
                    self.grid.player_group.add(new_player)

        self.room_manager = RoomManager(self.sio)
        self.sio.connect("http://localhost:5000")

        self.screen = pygame.display.set_mode(config.RESOLUTION)
        self.sprite_size = config.GRID_SIZE / config.NUM_TILES
        self.asset_store = AssetStore(self.sprite_size, config.GRID_SIZE)
        self.max_speed = 3
        self.map_name = config.MAP_NAME
        self.clock = pygame.time.Clock()
        self.running = True
        self.x = 0
        self.y = 0
        self.pressed_keys = []
        self.player_actions = {}

    def fetch_tile_map(self):
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(curr_dir, "../tilemaps/", self.map_name)
        with open(path, "rb") as file:
            tile_map = pickle.load(file)
        return tile_map if tile_map else None

    def update(self):
        # update animations
        for _, asset_dict in self.asset_store["spritesheets"].items():
            for _, asset in asset_dict.items():
                if isinstance(asset, Asset) and asset.animation is not None:
                    asset.animation.update_frame()
        self.grid.update(self.asset_store)

        players = self.grid.player_group.sprites()
        for player in players:
            if player.id == self.user_id:
                player.update(
                    self.grid, config.GRID_SIZE, self.pressed_keys, self.user_id
                )
                self.x = player.rect.x
                self.y = player.rect.y
            elif player.id in self.player_actions:
                player.update(
                    self.grid,
                    config.GRID_SIZE,
                    self.player_actions[player.id],
                    player.id,
                )

    def draw(self):
        self.screen.fill("black")
        self.screen.blit(self.asset_store["static"]["maps"]["default"].image, (0, 0))
        self.grid.item_group.draw(self.screen)
        self.grid.block_group.draw(self.screen)
        for tile_group in self.grid.explosion_groups:
            tile_group[0].draw(self.screen)
        for bubble_group in self.grid.bubble_groups:
            bubble_group[0].draw(self.screen)
        self.grid.player_group.draw(self.screen)
        self.grid.trapped_bubble_group.draw(self.screen)
        self.grid.obstacle_group.draw(self.screen)
        pygame.display.flip()

    def start(self):
        self.room_manager.prompt_for_room()

        player_list = [entities.Player(self.asset_store, self.user_id, self.max_speed)]
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

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key in [
                        pygame.K_UP,
                        pygame.K_DOWN,
                        pygame.K_RIGHT,
                        pygame.K_LEFT,
                    ]:
                        self.pressed_keys.append(event.key)
                        self.send_player_action()
                    if event.key == pygame.K_SPACE:
                        for player in self.grid.player_group.sprites():
                            if player.id == self.user_id:
                                player.drop_bubble(self.grid, self.asset_store)
                    if event.key == pygame.K_1:
                        for player in self.grid.player_group.sprites():
                            if player.id == self.user_id:
                                player.use_item(0)
                    if event.key == pygame.K_2:
                        for player in self.grid.player_group.sprites():
                            if player.id == self.user_id:
                                player.use_item(1)
                    if event.key == pygame.K_3:
                        for player in self.grid.player_group.sprites():
                            if player.id == self.user_id:
                                player.use_item(2)
                    if event.key == pygame.K_4:
                        for player in self.grid.player_group.sprites():
                            if player.id == self.user_id:
                                player.use_item(3)
                elif event.type == pygame.KEYUP:
                    if event.key in [
                        pygame.K_UP,
                        pygame.K_DOWN,
                        pygame.K_RIGHT,
                        pygame.K_LEFT,
                    ]:
                        self.pressed_keys.remove(event.key)
                        self.send_player_action()
            self.update()
            self.draw()
            self.clock.tick(config.FPS)
        self.terminate()
        self.sio.disconnect()

    def send_player_action(self):
        self.sio.emit(
            "player_action",
            {
                "room_id": self.room_manager.current_room,
                "pressed_keys": self.pressed_keys,
                "x": self.x,
                "y": self.y,
            },
        )

    def terminate(self):
        pygame.quit()


game = GameObject()
game.start()
