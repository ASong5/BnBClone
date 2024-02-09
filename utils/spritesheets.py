import pygame


class Spritesheet:
    def __init__(self, path):
        self.sheet = pygame.image.load(path).convert_alpha()
        self.width, self.height = self.sheet.get_size()

    def get_sprites(
        self,
        idx,
        num_sprites,
        num_animations,
        output_width,
        output_height,
        colour_key=None,
        colours_to_ignore=[],
    ):
        if colour_key:
            self.sheet.set_colorkey(colour_key)
            if len(colours_to_ignore) > 0:
                width = self.sheet.get_size()[0]
                height = self.sheet.get_size()[1]
                for x in range(width):
                    for y in range(height):
                        for colour in colours_to_ignore:
                            if tuple(self.sheet.get_at((x, y))) == colour:
                                self.sheet.set_at((x, y), colour_key)
                                break

        sprite_list = []
        sprite_width = self.width / num_sprites
        sprite_height = self.height / num_animations
        for i in range(num_sprites):
            image = pygame.Surface(
                (sprite_width, sprite_height), pygame.SRCALPHA
            ).convert_alpha()
            image.blit(
                self.sheet,
                (0, 0),
                (sprite_width * i, sprite_height * idx, sprite_width, sprite_height),
            )
            bounding_box = image.get_bounding_rect()
            scale_x = output_width / bounding_box.width
            scale_y = output_height / bounding_box.height
            scaled_image = pygame.transform.scale(
                image.subsurface(bounding_box),
                (int(bounding_box.width * scale_x), int(bounding_box.height * scale_y)),
            )
            sprite_list.append(scaled_image)
        return sprite_list
