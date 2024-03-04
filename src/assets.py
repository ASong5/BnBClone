from entities import AnimationComponent

class Asset:
    def __init__(self, frames, asset_type, asset_name):
        self.frames = frames
        self.asset_type = asset_type
        self.asset_name = asset_name
        self.animation = AnimationComponent(frames, asset_type)
        self.current_frame = self.get_current_frame()

    def get_current_frame(self, entity=None):
        return self.animation.get_frame(entity)
