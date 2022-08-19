import pygame
from typing import *
import utils

class Button:

    def __init__(self, position: utils.Couple, size: utils.Couple, text: str, btn_color: str, txt_color: str, font: pygame.font, callback: Callable = None) -> None:
        '''
        Create a new button.

            Parameters:
                position (tuple):       The top left X and Y coordinates to draw the button.
                size (tuple):           The width and height of the button.
                text (str):             Text of the button.
                btn_color (str):        The color name of the button.
                txt_color (str):        The color name of the text.
                font (pygame.font):     Font to draw the text.
                callback (Callable):    A callback function to run.
        '''
        if not isinstance(position, (list, tuple)) or not isinstance(size, (list, tuple)):
            return

        self.x = position[0]
        self.y = position[1]
        self.width = size[0]
        self.height = size[1]

        self.text = text
        self.button_color = btn_color
        self.text_color = txt_color
        self.font = font

        self.bold = False
        self.rect = None

        self.callback = callback
    

    def draw(self, surf):
        self.font.set_bold(self.bold)
        text = self.font.render(self.text, True, utils.get_color(self.text_color), None)

        position_and_size = (
            self.x,
            self.y,
            self.width,
            self.height
        )

        self.rect = pygame.draw.rect(
            surf,
            utils.get_color(self.button_color),
            position_and_size
        )

        pygame.draw.rect(
            surf,
            utils.get_color('black'),
            position_and_size,
            1
        )

        #   add the undo text in the center of the button
        text_rect = text.get_rect()
        text_rect.center = self.rect.center
        surf.blit(text, text_rect)

    
    def handle_event(self, event):
        if not self.rect:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.bold = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True

        return False
        