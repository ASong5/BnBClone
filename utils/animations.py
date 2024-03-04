from utils import spritesheets
from utils.types import Assets
import pygame

class AnimationComponent:
    mappings = {
        Assets.CHARACTER: {"move_down": 0, "move_up": 1, "move_side": 2},
        Assets.BUBBLE: {"idle": 0}
    }

    spritesheets = spritesheets.Spritesheets("assets/spritesheets").sheets
    def __init__(self, asset_type, variation, time_per_frame):
        self.image_idx = 0
        self.animation_idx = 0
        self.time_per_frame = time_per_frame
        self.timer = pygame.time.get_ticks()
        self.images = AnimationComponent.spritesheets[asset_type][variation]["spritesheets"].get_sprites()[asset_type][variation]

    def update_frame(self):
        if pygame.time.get_ticks() - self.timer >= self.time_per_frame:
            self.timer = pygame.time.get_ticks()
            self.animation_idx = (
                self.animation_idx + 1
                if self.animation_idx < len(self.images[self.image_idx]) else 0
            )
    
    def get_frame(self):
        return self.images[self.image_idx][self.animation_idx]
