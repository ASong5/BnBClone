import pygame
import os
import json
from utils.config import convert_indices_to_int


class Spritesheet:
    def __init__(self, path, config_path):
        self.path = path
        self.config = self.__read_config(config_path)
        self.time_per_frame = self.config.get("time_per_frame")
        self.sheet = pygame.image.load(path).convert_alpha()
        self.width, self.height = self.sheet.get_size()
        self.animation_mappings = self.config.get("animation_mappings")

    def __read_config(self, path):
        file = open(path)
        return convert_indices_to_int(json.load(file))

    def get_sprites(
        self,
        output_width,
        output_height,
    ):
        if "colorkey" in self.config:
            self.sheet.set_colorkey(self.config["colorkey"])
            if "ignore_colors" in self.config:
                width = self.sheet.get_size()[0]
                height = self.sheet.get_size()[1]
                for x in range(width):
                    for y in range(height):
                        for color in self.config["ignore_colors"]:
                            if tuple(self.sheet.get_at((x, y))) == pygame.Color(color):
                                self.sheet.set_at((x, y), self.config["colorkey"])
                                break

        sprite_list = []
        sprite_width = self.width / self.config["cols"]
        sprite_height = self.height / self.config["rows"]

        for i in range(self.config["rows"]):
            only = self.config.get("only")
            if only:
                if i not in only:
                    continue
            sprites = []
            for j in range(self.config["cols"]):
                image = pygame.Surface(
                    (sprite_width, sprite_height), pygame.SRCALPHA
                ).convert_alpha()
                image.blit(
                    self.sheet,
                    (0, 0),
                    (sprite_width * j, sprite_height * i, sprite_width, sprite_height),
                )

                ignore_bounding_rect = self.config.get("ignore_bounding_rect")

                if isinstance(ignore_bounding_rect, list) and i in ignore_bounding_rect:
                    bounding_box = image.get_rect()
                elif isinstance(ignore_bounding_rect, bool) and ignore_bounding_rect is True:
                    bounding_box = image.get_rect()
                else:
                    bounding_box = image.get_bounding_rect()

                box_width = bounding_box.width
                box_height = bounding_box.height

                if box_width != 0 or box_height != 0:
                    scale_x = output_width / box_width
                    scale_y = output_height / box_height
                    scaled_image = pygame.transform.scale(
                        image.subsurface(bounding_box),
                        (
                            int(box_width * scale_x),
                            int(box_height * scale_y),
                        ),
                    )

                    if "transform" in self.config:
                        if (
                            not self.config["transform"].get("flip_x")
                            and not self.config["transform"].get("flip_y")
                            and not self.config["transform"].get("flip_xy")
                            and not self.config["transform"].get("rotate_cardinal")
                        ):
                            sprites.append(scaled_image)
                        else:
                            transformed_sprites = []
                            transform_idx = self.config["transform"].get("idx")
                            if self.config["transform"].get("flip_x"):
                                if not transform_idx or transform_idx == i:
                                    transformed_sprites.append(
                                        pygame.transform.flip(scaled_image, True, False)
                                    )
                            if self.config["transform"].get("flip_y"):
                                if not transform_idx or transform_idx == i:
                                    transformed_sprites.append(
                                        pygame.transform.flip(scaled_image, False, True)
                                    )
                            if self.config["transform"].get("flip_xy"):
                                if not transform_idx or transform_idx == i:
                                    transformed_sprites.append(
                                        pygame.transform.flip(scaled_image, True, True)
                                    )
                            if self.config["transform"].get("rotate_cardinal"):
                                if not transform_idx or transform_idx == i:
                                    transformed_sprites.append(
                                        pygame.transform.rotate(scaled_image, 90)
                                    )
                                    transformed_sprites.append(
                                        pygame.transform.rotate(scaled_image, 180)
                                    )
                                    transformed_sprites.append(
                                        pygame.transform.rotate(scaled_image, 270)
                                    )

                            sprites.append([scaled_image] + transformed_sprites)
                    else:
                        sprites.append(scaled_image)
            sprite_list.append(sprites)
        return sprite_list


class Spritesheets:
    def __init__(self, path):
        self.path = path
        self.sheets = self.__load()

    def __load(self):
        config_path = ""
        spritesheets = {}
        for root, _, files in os.walk(self.path):
            path_tokens = root.split(os.sep)
            for file in files:
                if file == "config.json":
                    config_path = os.path.join(root, file)
                if file.split(".")[-1] == "png" and config_path:
                    curr_dict = spritesheets
                    for token in path_tokens[2:]:
                        if token not in curr_dict:
                            curr_dict[token] = {}
                        curr_dict = curr_dict[token]
                    curr_dict["spritesheet"] = Spritesheet(
                        os.path.join(root, file), config_path
                    )
        return spritesheets

