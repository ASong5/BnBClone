from utils.types import Assets
import entities
import pygame


class AnimationComponent:
    def __init__(self, frames, asset_type, time_per_frame, animation_mappings):
        self.frames = frames
        self.animation_mappings = animation_mappings
        self.animation_type_idx = 0
        self.frame_idx = 0
        self.asset_type = asset_type
        self.time_per_frame = time_per_frame
        self.timer = pygame.time.get_ticks()
        self.prev_animiation_idx = None

    def update_frame(self):
        self.frame_idx = self.frame_idx % len(self.frames[self.animation_type_idx])
        offset = 1 if self.asset_type == Assets.BUBBLE else 0
        if isinstance(self.time_per_frame, dict):
            animation_duration_dict = self.time_per_frame.get(self.animation_type_idx)
            if isinstance(animation_duration_dict, dict):
                for idx, time in animation_duration_dict.items():
                    time_elapsed = pygame.time.get_ticks() - self.timer
                    if time_elapsed <= time:
                        self.frame_idx = idx
                        break

        elif isinstance(self.time_per_frame, int):
            if pygame.time.get_ticks() - self.timer >= self.time_per_frame:
                self.timer = pygame.time.get_ticks()
                self.frame_idx = (self.frame_idx + 1) % (
                    len(self.frames[self.animation_type_idx]) - offset
                )

    def get_frame(self, entity=None, idx=None, flip_x=False):
        if idx is not None:
            if (
                idx != self.animation_mappings["idle"]
                and idx != self.animation_mappings["trapped"]
            ):
                self.animation_type_idx = idx
            elif idx == self.animation_mappings["trapped"]:
                if self.animation_type_idx != self.animation_mappings["trapped"]:
                    self.prev_animiation_idx = self.animation_type_idx
                    self.animation_type_idx = idx
            else:
                if self.animation_type_idx == self.animation_mappings["trapped"]:
                    self.animation_type_idx = self.prev_animiation_idx
                self.frame_idx = 0
            if isinstance(self.frames[self.animation_type_idx][self.frame_idx], list):
                if flip_x:
                    return self.frames[self.animation_type_idx][self.frame_idx][1]
                else:
                    return self.frames[self.animation_type_idx][self.frame_idx][0]
            else:
                return self.frames[self.animation_type_idx][self.frame_idx]

        elif isinstance(entity, entities.Explosion):
            if entity.explosion_dir == entities.Explosion.EXPLODE_DIR.DOWN:
                return self.frames[0][self.frame_idx][0]
            elif entity.explosion_dir == entities.Explosion.EXPLODE_DIR.RIGHT:
                return self.frames[0][self.frame_idx][1]
            elif entity.explosion_dir == entities.Explosion.EXPLODE_DIR.UP:
                return self.frames[0][self.frame_idx][2]
            elif entity.explosion_dir == entities.Explosion.EXPLODE_DIR.LEFT:
                return self.frames[0][self.frame_idx][3]
            elif entity.explosion_dir == entities.Explosion.EXPLODE_DIR.CENTER:
                return self.frames[0][self.frame_idx][0]

        else:
            return self.frames[self.animation_type_idx][self.frame_idx]
