from enum import Enum

class Assets(str, Enum):
    CHARACTER = "characters"
    BUBBLE = "bubbles"
    TILE = "tiles"
    EXPLOSION = "explosions"
    OBSTACLE = "obstacles"

class Bubbles(str, Enum):
    DEFAULT = "default"

class Characters(str, Enum):
    DEFAULT = "default" 

class Explosions(str, Enum):
    DEFAULT = "default" 
