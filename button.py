import pygame
from typing import *
import utils

class Button:

    def __init__(self, position: utils.Couple, size: utils.Couple, btn_color: str, callback: Callable = None, is_active: bool = True,
        img_path: Optional[str] = '', text: Optional[str] = '', txt_color: Optional[str] = 'black', font: Optional[pygame.font.Font] = None) -> None:
        '''
        Create a new button.

            Parameters:
                position (tuple):       The top left X and Y coordinates to draw the button.
                size (tuple):           The width and height of the button.
                btn_color (str):        The color name of the button.
                callback (Callable):    A callback function to run.
                is_active (bool):       Whether the button is active or not, default True.
                img_path (str):         Path to an image, default empty string,
                text (str):             Text of the button, default empty string.
                txt_color (str):        The color name of the text, default black.
                font (pygame.font):     Font to draw the text, default None.
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
        self.is_active = is_active

        self.image = None
        if img_path != '':
            img_offset = 2
            self.image = pygame.image.load(img_path)
            self.image = pygame.transform.scale(self.image, (self.width - img_offset, self.height - img_offset))

        self.collide = False
        self.rect = None

        self.callback = callback
    

    def draw(self, surf):
        '''
        Draw the button on top of the surface.

            Parameters:
                surf: (pygame.Surface): The surface to draw on.
        '''
        if not self.is_active:
            return

        #   if mouse collide with the button, set the text to bold
        if self.font:
            self.font.set_bold(self.collide)
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
        if self.font:
            text_rect = text.get_rect()
            text_rect.center = self.rect.center
            surf.blit(text, text_rect)
        
        if self.image:
            image_rect = self.image.get_rect()
            image_rect.center = self.rect.center
            surf.blit(self.image, image_rect)

    
    def handle_event(self, event):
        '''
        Hnadle a pyGame event, change text and cursor if the mouse is in the button boundaries and return True if the button was pressed.

            Parameters:
                event (pygame.event): A pyGame event to handle.

            Returns:
                is_clicked (bool): True if the button was clicked, False if not.
        '''
        #   if button is not defined or set to inactive
        if not self.rect or not self.is_active:
            return False

        #   if it's a mouse event, check if it's in the button boundaries
        if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONUP:
            self.collide = self.rect.collidepoint(event.pos)
        else:
            self.collide = False

        #   if mouse in boundaries, draw a different cursor and check if mouse was clicked
        if self.collide:
            pygame.mouse.set_cursor(pygame.cursors.broken_x)
            if event.type == pygame.MOUSEBUTTONUP:
                self.callback()
                pygame.mouse.set_cursor(pygame.cursors.tri_left)
                return True 
        else:
            pygame.mouse.set_cursor(pygame.cursors.tri_left)

        return False
        

    def set_active(self, active):
        '''
        Change the active state of the button.

            Parameters:
                active (bool): True to set it active and False to set it as inactive.
        '''
        self.is_active = active
        if not active:
            self.collide = False