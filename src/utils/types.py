from enum import Enum

class Assets(str, Enum):
    CHARACTER = "characters"
    BUBBLE = "bubbles"
    TILE = "tiles"
    EXPLOSION = "explosions"
    MAPS = "maps"
    ITEMS = "items"
    BLOCKS = "blocks"
    OBSTACLES = "obstacles"
    BUBBLE_TRAPPED = "bubble_trapped"

class Bubbles(str, Enum):
    DEFAULT = "default"

class Bubble_Trapped(str, Enum):
    DEFAULT = "default"

class Characters(str, Enum):
    DEFAULT = "default" 

class Explosions(str, Enum):
    DEFAULT = "default" 

class Maps(str, Enum):
    DEFAULT = "default" 

class Items(str, Enum):
    BUBBLE = "bubble"
    SPEED_SHOE = "speed_shoe"
    NEEDLE = "needle"

class Obstacles(str, Enum):
    POST = "post"

class Blocks(str, Enum):
    DEFAULT = "default"
    DEFAULT_1 = "default1"
    DEFAULT_2 = "default2"
