import pygame
from utils.types import Assets


class Item(pygame.sprite.Sprite):
    items = {}

    def __init__(self, asset_store, row, col, item_type):  # type: ignore
        super(Item, self).__init__()
        self.asset = asset_store["spritesheets"][Assets.ITEMS][item_type]
        self.row = row
        self.col = col

        self.image = self.asset.get_current_frame()
        self.rect = self.image.get_rect()
        self.size = self.rect.width
        self.rect.topleft = (self.col * self.size, self.row * self.size)

        Item.items[(self.row, self.col)] = self

    def update(self):  # type: ignore
        self.image = self.asset.get_current_frame()

    def acquire(self, player):
        self.kill()
        Item.items.pop((self.row, self.col))

    @classmethod
    def get_item(cls, row, col):
        return cls.items.get((row, col), None)


class BubbleItem(Item):
    def __init__(self, asset_store, row, col, item_type):
        super(BubbleItem, self).__init__(asset_store, row, col, item_type)

    def acquire(self, player):
        super().acquire(player)
        player.num_bubbles += 1


class SpeedShoeItem(Item):
    def __init__(self, asset_store, row, col, item_type):
        super(SpeedShoeItem, self).__init__(asset_store, row, col, item_type)

    def acquire(self, player):
        super().acquire(player)
        player.max_speed += 0.3


class NeedleItem(Item):
    def __init__(self, asset_store, row, col, item_type):
        super(NeedleItem, self).__init__(asset_store, row, col, item_type)

    def acquire(self, player):
        super().acquire(player)
        if len(player.inventory) > 4:
            player.inventory.pop()
        player.inventory.insert(0, self)

    def activate(self, player):
        if player.is_trapped:
            player.is_trapped = False
            return True
        return False
