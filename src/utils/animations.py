from utils.types import Assets
import entities
import pygame

class AnimationComponent:
    mappings = {
        Assets.CHARACTER: {
            "animation_type": {
                "idle": -1,
                "move_down": 0,
                "move_up": 1,
                "move_side": 2,
            },
        },
        Assets.BUBBLE: {"idle": 0,},
        Assets.EXPLOSION: {
            "animation_type": {"explode": 2, "fizzle_one": 1, "fizzle_two": 0},
        },
    }

    def __init__(self, frames, asset_type, time_per_frame):
        self.frames = frames
        self.animation_type_idx = 0
        self.frame_idx = 0
        self.asset_type = asset_type
        self.time_per_frame = time_per_frame
        self.timer = pygame.time.get_ticks()

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

    def get_frame(self, entity=None):
        if isinstance(entity, entities.Player):
            if (
                entity.animation_state
                != self.mappings[Assets.CHARACTER]["animation_type"]["idle"]
            ):
                self.animation_type_idx = entity.animation_state
            if (
                entity.animation_state
                == self.mappings[Assets.CHARACTER]["animation_type"]["move_side"]
            ):
                return self.frames[self.animation_type_idx][self.frame_idx][
                    entity.sprite_flip_x
                ]
            elif (
                entity.animation_state
                == self.mappings[Assets.CHARACTER]["animation_type"]["idle"]
            ):
                return self.frames[self.animation_type_idx][0][entity.sprite_flip_x]
            else:
                return self.frames[self.animation_type_idx][self.frame_idx][
                    entity.sprite_flip_x
                ]

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



