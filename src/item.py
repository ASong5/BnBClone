import pygame
from utils.types import Assets

class Item(pygame.sprite.Sprite):
    def __init__(self, asset_store, row, col, item_type): # type: ignore
        super(Item, self).__init__()
        self.asset = asset_store["spritesheets"][Assets.ITEMS][item_type]
        self.row = row
        self.col = col
        
        self.image = self.asset.get_current_frame()
        self.rect = self.image.get_rect()
        self.size = self.rect.width
        self.rect.topleft = (self.col * self.size, self.row * self.size)

    def update(self): # type: ignore
        self.image = self.asset.get_current_frame()

class BubbleItem(Item):
    def __init__(self, asset_store, row, col, item_type):
        super(BubbleItem, self).__init__(asset_store, row, col, item_type)






















        

