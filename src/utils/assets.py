from utils.animations import AnimationComponent
from utils import spritesheets
import pygame
import os
import json


class Asset:
    def __init__(self, asset_type, asset_name, animation=None, image=None, config=None):
        self.asset_type = asset_type
        self.asset_name = asset_name
        self.config = config
        if animation is None and image is None:
            raise ValueError("Asset must have an animation or an image")
        elif animation is not None and image is not None:
            raise ValueError("Asset can not have both an animation and an image")
        elif animation:
            if not isinstance(animation, AnimationComponent):
                raise ValueError("Animation must be an instance of AnimationComponent")
            self.animation = animation
            self.current_frame = self.get_current_frame()
        else:
            if not isinstance(image, pygame.Surface):
                raise ValueError("image must be an instance of pygame.Surface")
            self.image = image

    def get_current_frame(self, entity=None, idx=None, flip_x=None):
        return self.animation.get_frame(entity, idx, flip_x)

    def get_animation_mapping(self, animation_type):
        if self.animation:
            return self.animation.animation_mappings[animation_type]


class AssetStore(dict):
    def __init__(self, asset_size, grid_size):
        super().__init__()
        self.asset_size = asset_size
        self.grid_size = grid_size
        self.load_assets()

    def load_assets(self):
        self["spritesheets"] = {}
        spritesheet_list = spritesheets.Spritesheets("assets/spritesheets")
        for asset_type, asset_dict in spritesheet_list.sheets.items():
            for asset_name, asset_data in asset_dict.items():
                asset_spritesheet = asset_data.get("spritesheet")
                if asset_spritesheet:
                    if asset_type not in self:
                        self["spritesheets"][asset_type] = {}
                    new_asset = Asset(
                        asset_type,
                        asset_name,
                        animation=AnimationComponent(
                            asset_spritesheet.get_sprites(
                                self.asset_size, self.asset_size
                            ),
                            asset_type,
                            asset_spritesheet.time_per_frame,
                            asset_spritesheet.animation_mappings
                        ),
                    )
                    self["spritesheets"][asset_type][asset_name] = new_asset

        self["static"] = {}
        for root, _, files in os.walk("assets/static"):
            for file in files:
                path_tokens = root.split("/")
                asset_type = path_tokens[-2]
                asset_name = path_tokens[-1]
                if file.split(".")[-1] == "png":
                    if asset_type not in self["static"]:
                        self["static"][asset_type] = {}
                    config_file = os.path.join(root, "config.json") 
                    config = json.load(open(config_file)) if os.path.exists(config_file) else None
                    width = height = self.asset_size
                    if config:
                        x_scale_offset = config.get("x_scale_offset")
                        y_scale_offset = config.get("y_scale_offset")
                        width += x_scale_offset if x_scale_offset is not None else 0
                        height += y_scale_offset if y_scale_offset is not None else 0
                    map = pygame.transform.scale(
                        pygame.image.load(os.path.join(root, file)).convert_alpha(),
                        (self.grid_size if asset_type == "maps" else width, self.grid_size if asset_type == "maps" else height),
                    )
                    new_asset = Asset(asset_type, asset_name, image=map, config=config)
                    self["static"][asset_type][asset_name] = new_asset

    def __getitem__(self, key):
        return super().__getitem__(key)
