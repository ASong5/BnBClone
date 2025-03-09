import json

file = open("game_config.json")
config = json.load(file)

RESOLUTION = tuple(config["screen_resolution"])
GRID_SIZE = config["grid_size"]
NUM_TILES = config["num_tiles"]
SPRITE_SIZE = GRID_SIZE / NUM_TILES
FPS = config["fps"]
MAP_NAME = "test123"

def convert_indices_to_int(data) -> dict:
    if isinstance(data, dict):
        converted_data = {}
        for key, value in data.items():
            if isinstance(key, str) and key.isdigit():
                key = int(key)
            converted_data[key] = convert_indices_to_int(value)
        return converted_data
    elif isinstance(data, list):
        return [convert_indices_to_int(item) for item in data] # type: ignore
    else:
        return data
