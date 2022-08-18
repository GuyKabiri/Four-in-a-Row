from msilib.schema import Error
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
import utils
from typing import *

class OptionBox():

    def __init__(self, x: int, y: int, w: int, h: int, font: pygame.font.Font, option_list: List, selected: Optional[Union[int, str]] = 0) -> None:
        '''
        Create a new option box.

            Parameters:
                x (int):            The X axis of the box.
                y (int):            The Y axis of the box.
                w (int):            The width of the box.
                h (int):            The height of the box.
                font (pygame.font): The font object with the style and size to use.
                option_list (list): List with the options to show.
                selected (int):     The index or the string value of the default option, default 0.
        '''
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.option_list = option_list

        #   if selected is str find its index value
        if isinstance(selected, str):
            self.selected = option_list.index(selected)
        else:
            self.selected = selected

        self.draw_menu = False      #   whether to show the menu or not
        self.menu_active = False    #   whether the menu was pressed or not
        self.active_option = -1     #   the current active option

    def get_selected_text(self) -> str:
        '''
        Get the selected option string value

            Returns:
                value (str): The text of the selected option.
        '''
        return self.option_list[ self.selected ].lower()


    def set_options(self, options: List) -> None:
        '''
        Set a new options list, and set the previous selected options as selected again (order may be different).
        '''
        prev_selected = self.get_selected_text()
        self.option_list = options
        try:
            self.selected = self.option_list.index(prev_selected)
        except Error:
            self.selected = 0


    def draw(self, surf: pygame.Surface) -> None:
        '''
        Draws the options box, with or without the options, depend if was pressed or not.
        '''
        #   draw the current option with the box
        pygame.draw.rect(surf, utils.get_color(self.get_selected_text()), self.rect)
        pygame.draw.rect(surf, (0, 0, 0), self.rect, 2)
        msg = self.font.render(self.option_list[ self.selected ].capitalize(), 1, (0, 0, 0))
        surf.blit(msg, msg.get_rect(center = self.rect.center))

        #   if needs to draw the options, iterate over the list and draw each rectangle
        if self.draw_menu:
            for i, text in enumerate(self.option_list):
                rect = self.rect.copy()
                rect.y += (i + 1) * self.rect.height
                pygame.draw.rect(surf, utils.get_color(text), rect)
                msg = self.font.render(text.capitalize(), 1, (0, 0, 0))
                surf.blit(msg, msg.get_rect(center = rect.center))
            outer_rect = (self.rect.x, self.rect.y + self.rect.height, self.rect.width, self.rect.height * len(self.option_list))
            pygame.draw.rect(surf, (0, 0, 0), outer_rect, 2)


    def update(self, event: pygame.event) -> int:
        '''
        Update the options box uppon an event, whether the menu or an option were pressed and return the selected value.

            Returns:
                selected (int): If option selected, return its index, otherwise returns -1 if the menu was open and -2 if was not.
        '''
        menu_was_open = self.menu_active
        mpos = pygame.mouse.get_pos()

        #   true if the main box was pressed (to open/close it)
        self.menu_active = self.rect.collidepoint(mpos)
        
        #   iterate over the options and check if was pressed,
        #   if no option was pressed, active_option will remain with -1
        self.active_option = -1
        for i in range(len(self.option_list)):
            rect = self.rect.copy()
            rect.y += (i+1) * self.rect.height
            if rect.collidepoint(mpos):
                self.active_option = i
                break
        
        #   if nor the menu, neither an option was pressed, close the menu
        # if not self.menu_active and self.active_option == -1:
        #     self.draw_menu = False

        #   if the main box pressed, toggle the menu
        if self.menu_active:
            self.draw_menu = not self.draw_menu
        
        #   if the menu was open and an was option selected, close the menu and set the selected option
        elif self.draw_menu and self.active_option >= 0:
            self.selected = self.active_option
            self.draw_menu = False
            return self.active_option
        
        #   not the menu was pressed, close it
        else:
            self.draw_menu = False
        
        return -1 if menu_was_open or self.draw_menu else -2