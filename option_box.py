import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
import utils

class OptionBox():

    def __init__(self, x, y, w, h, font, option_list, selected = 0):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.option_list = option_list
        if isinstance(selected, str):
            self.selected = option_list.index(selected)
        else:
            self.selected = selected
        self.draw_menu = False
        self.menu_active = False
        self.active_option = -1

    def get_selected_text(self):
        return self.option_list[ self.selected ].lower()

    def set_options(self, options):
        prev_selected = self.get_selected_text()
        self.option_list = options
        self.selected = self.option_list.index(prev_selected)

    def draw(self, surf):
        pygame.draw.rect(surf, utils.get_color(self.get_selected_text()), self.rect)
        pygame.draw.rect(surf, (0, 0, 0), self.rect, 2)
        msg = self.font.render(self.option_list[ self.selected ].capitalize(), 1, (0, 0, 0))
        surf.blit(msg, msg.get_rect(center = self.rect.center))

        if self.draw_menu:
            for i, text in enumerate(self.option_list):
                rect = self.rect.copy()
                rect.y += (i+1) * self.rect.height
                pygame.draw.rect(surf, utils.get_color(text), rect)
                msg = self.font.render(text.capitalize(), 1, (0, 0, 0))
                surf.blit(msg, msg.get_rect(center = rect.center))
            outer_rect = (self.rect.x, self.rect.y + self.rect.height, self.rect.width, self.rect.height * len(self.option_list))
            pygame.draw.rect(surf, (0, 0, 0), outer_rect, 2)

    def update(self, event):
        menu_was_open = self.menu_active
        mpos = pygame.mouse.get_pos()
        self.menu_active = self.rect.collidepoint(mpos)
        
        self.active_option = -1
        for i in range(len(self.option_list)):
            rect = self.rect.copy()
            rect.y += (i+1) * self.rect.height
            if rect.collidepoint(mpos):
                self.active_option = i
                break

        if not self.menu_active and self.active_option == -1:
            self.draw_menu = False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.menu_active:
                self.draw_menu = not self.draw_menu
            elif self.draw_menu and self.active_option >= 0:
                self.selected = self.active_option
                self.draw_menu = False
                return self.active_option
        return -1 if menu_was_open or self.draw_menu else -2