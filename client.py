import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import time
import pygame
import tkinter as tk
import multiprocessing
import logging
import numpy as np
import sys
import math
import utils
import socket
from actions import Actions
from typing import *
from option_box import OptionBox
from memento import Originator, CareTaker
from win32gui import SetWindowPos


player_colors_list = ['red', 'yellow', 'green', 'orange']

class ClientGUI:

    def __init__(self, id: int, queue: multiprocessing.Queue, log_level: int, size: Union[Tuple, List] = (6, 10)) -> None:
        '''
        Create a new client, define it's gui, board, and create a socket.

            Parameters:
                id (int):                       The id of the client.
                queue (multiprocessing.Queue):  The queue to push the logs in.
                log_level (int):                The log level to use.
                size (tuple):                   Size of board to use.
        '''
        self.id = id

        #   if given size is not a tupple, a list or have not 2 dims
        if not ( isinstance(size, tuple) or isinstance(size, list) ) or len(size) != 2:
            size = (6, 10)

        #   define the board size
        self.rows = size[0]
        self.cols = size[1]

        self.queue = queue
        utils.root_logger_configurer(self.queue, log_level)
        self.logger = logging.getLogger('Client({})'.format(self.id))

        self.font_style = pygame.font.match_font('segoeuisymbol')
        self.wins = [0, 0]
        self.player1_color = 'yellow'
        self.player2_color = 'red'
        self.max_undo = 3

        #   calculate the clients gui size based on the amount of rows and cols
        self.calc_window_size()
        
        #   create the socket and the gui
        self.create_socket()
        
        self.reset_game_state()
        self.create_gui()

        #   run the main game loop
        self.run_game()


    def reset_game_state(self, winner: Optional[int] = None) -> None:
        '''
        Reset the state of the game

            Parameters:
                winner (int): The ID of the winner, default 1.
        '''
        if not winner:
            self.turn = 1

        self.state = Actions.READY
        self.board = np.zeros( (self.rows, self.cols), dtype=np.int8 )               #   define the main board state object

        self.reset_button = None
        self.undo_counts = [0, 0]

        self.origin = Originator()
        self.caretaker = CareTaker(self.origin)

        self.origin.set_state(self.board)
        self.caretaker.do()


    def get_turn_color(self) -> None:
        '''
        Returns the color to use based on the current player.

            Returns:
                color (str): Capitalized color string.
        '''
        return self.player1_color if self.turn == 1 else self.player2_color

    
    def get_other_turn_color(self) -> None:
        '''
        Returns the color to use based on the other player.

            Returns:
                color (str): Capitalized color string.
        '''
        return self.player2_color if self.turn == 1 else self.player1_color

    
    def get_player_color(self, row: int, col: int) -> str:
        '''
        Get a cell in the board and return it's color.

            Parameters:
                row (int): The row in the board.
                col (int): The column in the board.

            Returns:
                color (str): Color name string.
        '''
        if self.board[row][col] == 1:
            return self.player1_color
        elif self.board[row][col] == 2:
            return self.player2_color
        return 'black'

    
    def calc_col_by_mouse(self, x_cord: int) -> int:
        '''
        Calculate the column index based on the position of the mouse on the board.

            Parameters:
                x_cord (int): The X coordination of the mouse on the board.

            Returns:
                column (int): The index of the column in the board.
        '''
        return int(math.floor(x_cord / self.square_size))


    def create_socket(self) -> None:
        '''
        Creates the client's socket.
        '''
        self.client_socket = socket.socket()
        self.port = 1234
        self.host = '127.0.0.1'

        try:
            self.client_socket.connect( (self.host, self.port) )
        except socket.error as e:
            self.logger.error(str(e))
            self.client_socket.close()
        self.logger.info('created conn {}:{}'.format(self.host, self.port))


    def calc_window_size(self) -> None:
        '''
        Calculate the size of the window, and adjust the circles size based on the users screen size.
        '''
        self.options_rows = 2

        #   define the default size
        self.square_size = 80
        self.font_size = 32

        #   get the screen size
        win = tk.Tk()
        width, height = win.winfo_screenwidth(), win.winfo_screenheight()

        while True:
            #    calculate the total width and height based on the squares size
            self.width = self.cols * self.square_size
            self.height = (self.rows + self.options_rows) * self.square_size

            #   size of circle radius based on the squares
            self.radius = int(self.square_size/2 - 5)

            #   if the client's size is not bigger than the users screen, exit
            if not (self.width > width or self.height > height - 80):
                break
            
            #   client's size is bigger than the user's screen, reduce the size
            self.square_size -= 10
            self.font_size -= 2
        
        self.logger.debug('window size (width={}, height={}), radius={}, square_size={}, font_size={}'.format(self.width, self.height, self.radius, self.square_size, self.font_size))

    
    def create_gui(self) -> None:
        '''
        Creates the client's gui.
        '''

        #   set an icon and initiate the gui
        icon = pygame.image.load('assets/icon.png')
        pygame.display.set_icon(icon)
        pygame.init()   # initiate the pyGame module

        #   create the main display with black background
        self.main_display = pygame.display.set_mode((self.width, self.height), 0, 32)
        self.main_display.fill(utils.get_color('black'))

        options_box_width = 120

        self.options_player1 = OptionBox(
                0, 0, options_box_width, 40, pygame.font.Font(self.font_style, self.font_size), 
                [ clr for clr in utils.filter_color(player_colors_list, self.player2_color) ],
                self.player1_color)

        self.options_player2 = OptionBox(
                self.main_display.get_rect().right - options_box_width, 0, 120, 40, pygame.font.Font(self.font_style, self.font_size), 
                [ clr for clr in utils.filter_color(player_colors_list, self.player1_color) ],
                self.player2_color)

        self.reset_button = None
        self.undo_button = None

        pygame.display.update()
        pygame.display.set_caption('Client {}'.format(self.id))

        #   pyGame module does not support topmost attribute as Tkinter does
        #   in the following the -1 variable used as topmost
        SetWindowPos(pygame.display.get_wm_info()['window'], -1, 0, 0, 0, 0, 1)

        #   draw the board itself and the top bar
        self.draw_board()
        self.draw_options()


    def draw_board(self) -> None:
        '''
        Draws the board with its current state.
        '''
        board_top_offset = self.options_rows * self.square_size

        #   iterates over the rows and cols
        for r in range(self.rows):
            for c in range(self.cols):

                #   first, draw a blue rectangle
                pygame.draw.rect(
                    self.main_display,
                    utils.get_color('blue'),
                    (
                        c * self.square_size,
                        r * self.square_size + board_top_offset,
                        self.square_size,
                        self.square_size
                    )
                )

                width = int( c * self.square_size + self.square_size / 2)
                height = int( r * self.square_size + board_top_offset + self.square_size / 2)

                #   second, add a circle with the player's color, or black if empty cell
                color_name = self.get_player_color(r, c)
                color_rgb = utils.get_color(color_name)
                pygame.draw.circle(
                    self.main_display,
                    color_rgb,
                    (width, height),
                    self.radius)
                
                #   add a black ring around the coloed circle
                pygame.draw.circle(
                    self.main_display,
                    utils.get_color('black'),
                    (width, height),
                    self.radius, 1)

        pygame.display.update()
        self.logger.debug('board={}'.format(self.board))


    def clear_top(self, all=True) -> None:
        '''
        Clears the top row above the main board with a black rectangle.

            Parameters:
                all (bool): Whether to clear the entire top row or just the part when the circle is moving.
        '''
        num_rows = self.options_rows if all else 1
        y = 0 if all else self.square_size * (self.options_rows - 1)
        pygame.draw.rect(self.main_display, utils.get_color('black'), (0, y, self.width, self.square_size * num_rows))
        self.draw_scores()

    
    def draw_options(self):
        '''
        Update the color options menus and draw them.
        '''
        self.options_player1.set_options(
            [ clr for clr in utils.filter_color(player_colors_list, self.player2_color) ]
        )
        self.options_player2.set_options(
            [ clr for clr in utils.filter_color(player_colors_list, self.player1_color) ]
        )

        self.options_player1.draw(self.main_display)
        self.options_player2.draw(self.main_display)


    def add_text(self, txt: str) -> None:
        '''
        Adds text in the top black rectangle.

            Parameters:
                txt (str): Text to add.
        '''
        #   if the state of the game is win, define the color of the text as the color of the winner
        color_to_use = self.get_turn_color() if self.state == Actions.WIN else 'GRAY'
        font = pygame.font.Font(self.font_style, self.font_size)
        text = font.render(txt, True, utils.get_color(color_to_use), utils.get_color('black'))

        #   calculate the center of the text to place it in the center of the window
        text_rect = text.get_rect()
        text_rect.center = (self.width // 2, (self.square_size * self.options_rows) - (self.square_size // 3))
        self.main_display.blit(text, text_rect)
        self.logger.debug('draw text={}, color={}'.format(txt, color_to_use))

    
    def draw_scores(self) -> None:
        '''
        Draw the players scores at the top of the screen.
        '''
        player1_score, player2_score = str(self.wins[0]), str(self.wins[1])

        font = pygame.font.Font(self.font_style, self.font_size)
        text_1 = font.render(player1_score, True, utils.get_color(self.player1_color),      utils.get_color('black'))
        text_2 = font.render(player2_score, True, utils.get_color(self.player2_color),      utils.get_color('black'))
        text_c = font.render(':',           True, utils.get_color('gray'),                  utils.get_color('black'))

        text_rect_1 = text_1.get_rect()
        text_rect_2 = text_2.get_rect()
        text_rect_c = text_c.get_rect()

        offset = 20

        text_rect_1.right =     (self.width // 2 - offset)
        text_rect_2.left =      (self.width // 2 + offset)
        text_rect_c.centerx =   (self.width // 2)

        self.main_display.blit(text_1, text_rect_1)
        self.main_display.blit(text_2, text_rect_2)
        self.main_display.blit(text_c, text_rect_c)


    def exit(self, should_send: bool = False) -> None:
        '''
        Teardown function to close the socket and the gui.

            Parameters:
                should_send (bool): Whether to send an exit event to the server or not, default False.
        '''
        if should_send:
            self.client_socket.send(bytes(str(Actions.EXIT.value), 'utf8'))
            self.logger.debug('send exit event to server')
        host, port = self.client_socket.getsockname()
        self.client_socket.close()
        self.logger.info('conn closed {}:{}'.format(host, port))
        pygame.quit()
        sys.exit()


    def game_over_gui(self, is_win: bool = True) -> None:
        '''
        Add a title to the top of the screen based on the winner, or tie, and draw the reset button.

            Parameters:
                is_win (bool): Whether it's a win or a tie, default True.
        '''
        if is_win:
            self.wins[self.turn - 1] += 1
            pygame.mixer.music.load(os.path.join('assets/win.wav'))
        else:
            pygame.mixer.music.load(os.path.join('assets/tie.wav'))
        pygame.mixer.music.play()

        self.clear_top()

        self.state = Actions.WIN if is_win else Actions.TIE

        if self.state == Actions.WIN:
            self.add_text('Client({}) {} won!'.format(self.id, self.get_turn_color()))
        else:
            self.add_text("It's a tie!")

        player1_score, player2_score = self.wins[0], self.wins[1]
        num_format = '{:' + str(max(len(str(player1_score)), len(str(player2_score)))) + 'd}'
        score_format = num_format.format(player1_score) + ':' + num_format.format(player2_score)
        self.logger.debug('game over, state={}, scores(yellow:red)=({})'.format(self.state.value, score_format))


    def draw_undo_button(self) -> None:
        '''
        Draws the undo button on the options section.
        '''
        if self.undo_counts[self.turn - 1] >= self.max_undo:
            return

        #   define the span in each axis
        x_num_squares = 0.5
        y_num_squares = 0.5

        #   calculates the X and Y coordinates based on the size of the rectangles of the board
        x = ((self.cols / 2) - x_num_squares / 2) * self.square_size
        y = self.square_size * (self.options_rows - 1) * y_num_squares + 5

        color_to_use = self.get_other_turn_color()
        font = pygame.font.Font(self.font_style, self.font_size)
        text = font.render('⮌', True, utils.get_color(color_to_use), None)

        self.undo_button = pygame.draw.rect(
                    self.main_display,
                    utils.get_color('gray'),
                    (
                        x,
                        y,
                        self.square_size*x_num_squares,
                        self.square_size*y_num_squares
                    )
                )

        pygame.draw.rect(
                self.main_display,
                utils.get_color('black'),
                (
                    x,
                    y,
                    self.square_size*x_num_squares,
                    self.square_size*y_num_squares
                ), 1
            )

        #   add the undo text in the center of the button
        text_rect = text.get_rect()
        text_rect.center = self.undo_button.center
        self.main_display.blit(text, text_rect)

    
    def draw_reset_button(self) -> None:
        '''
        Draws the reset button on the center of the board.
        '''
        #   define the span in each axis
        x_num_squares = 1.5
        y_num_squares = 0.75

        #   calculates the X and Y coordinates based on the size of the rectangles of the board
        x = ((self.cols / 2) - x_num_squares / 2) * self.square_size
        y = (((self.rows / 2) - y_num_squares / 2) * self.square_size) + self.square_size * self.options_rows

        font = pygame.font.Font(self.font_style, self.font_size)
        text = font.render('Reset' , True , utils.get_color('black'))

        self.reset_button = pygame.draw.rect(
                    self.main_display,
                    utils.get_color('gray'),
                    (
                        x,
                        y,
                        self.square_size*x_num_squares,
                        self.square_size*y_num_squares
                    )
                )

        pygame.draw.rect(
                self.main_display,
                utils.get_color('black'),
                (
                    x,
                    y,
                    self.square_size*x_num_squares,
                    self.square_size*y_num_squares
                ), 1
            )

        #   add the reset text in the center of the button
        text_rect = text.get_rect()
        text_rect.center = self.reset_button.center
        self.main_display.blit(text, text_rect)


    def undo(self) -> None:
        '''
        Undo the last move.

            Returns:
                did_undo (bool): True if performed undo, False otherwise.
        '''
        if self.undo_counts[self.turn - 1] < self.max_undo:
            self.client_socket.send(bytes(str(Actions.UNDO.value), 'utf8'))
            if self.caretaker.undo():
                self.board = self.origin.get_state()
                self.undo_counts[self.turn - 1] += 1
                self.change_turn()
                self.undo_button = None
                self.clear_top()
                self.draw_options()
                self.draw_board()
                return True
        return False

    
    def change_turn(self):
        '''
        Change the turn between the players
        '''
        self.turn = 1 if self.turn == 2 else 2


    def draw_moving_piece(self, mouse_x: int) -> None:
        '''
        Drawing the moving piece on top of the board.

            Parameters:
                mouse_x (int): The X coordinate of the mouse.
        '''
        self.clear_top(all=False)
        #   get the column index of the mouse
        col = self.calc_col_by_mouse(mouse_x)
        #   get the current user color
        curr_color = self.get_turn_color()
        #   select the user color or an invalid location color based on the board state
        color_to_use = utils.get_color(curr_color) if utils.is_valid_location(col, self.board) else utils.get_color('gray')
        # calculate the x axis of the circle and draw
        circle_x = col * self.square_size + self.square_size / 2
        pygame.draw.circle(self.main_display, color_to_use, (circle_x, int(self.square_size * self.options_rows - self.radius)), self.radius)


    def run_game(self) -> None:
        '''
        The main function to communicate with the server and maintain the state of the game.
        '''

        #   send an ready event to the server to notify the client done its setup
        self.client_socket.send(bytes(str(Actions.READY.value), 'utf8'))
        self.logger.debug('sent ready event')

        self.draw_scores()
        action = Actions.UNKNOWN
        time.sleep(1)
        while True:
            #   if received an exit event
            is_exit =  utils.wait_for_data(self.client_socket, 0.01)
            if is_exit and Actions.EXIT.is_equals(is_exit):
                self.logger.debug('received exit event from server')
                self.exit()

            #   iterate over the pygame events
            for event in pygame.event.get():
                #   if exit event
                if event.type == pygame.QUIT:
                    self.logger.debug('pygame exit event')
                    self.exit(should_send=True)            

                #   if a mouse click event
                if event.type == pygame.MOUSEBUTTONUP:

                    selected_option1 = self.options_player1.update(event)
                    if selected_option1 >= 0:
                        self.player1_color = self.options_player1.get_selected_text()

                    selected_option2 = self.options_player2.update(event)
                    if selected_option2 >= 0:
                        self.player2_color = self.options_player2.get_selected_text()
                    
                    if selected_option1 >= -1 or selected_option2 >= -1:
                        self.clear_top()
                        self.draw_board()
                        self.draw_options()
                        break

                    if self.state == Actions.WIN or self.state == Actions.TIE:
                        if self.reset_button and self.reset_button.collidepoint(event.pos[0], event.pos[1]):
                            self.logger.debug('reset button pressed')
                            self.reset_game_state(self.turn if self.state == Actions.WIN else None)
                            self.client_socket.send(bytes(str(Actions.RESET.value), 'utf8'))
                            self.draw_board()
                            self.clear_top()

                    elif self.state == Actions.READY:
                        self.logger.debug('mouse button up event')

                        if self.undo_button and self.undo_button.collidepoint(event.pos[0], event.pos[1]):
                            self.logger.debug('undo button pressed')
                            if self.undo():
                                continue

                        #   get x coordinate of the mouse to calculate the board col
                        col = self.calc_col_by_mouse(event.pos[0])

                        #   send player id and col to add
                        self.client_socket.send(bytes(str(self.turn), 'utf8'))
                        self.client_socket.send(bytes(str(col), 'utf8'))
                        self.logger.debug('sent turn={}, col={}'.format(self.turn, col))

                        action = utils.wait_for_data(self.client_socket)
                        self.logger.debug('received action={}'.format(self.id, Actions(int(action))))

                        if Actions.EXIT.is_equals(action):
                            self.logger.debug('got exit event from server')
                            self.exit()

                        #   if action is to add a piece
                        if Actions.ADD_PIECE.is_equals(action):
                            utils.add_piece(self.board, col, self.turn)
                            self.draw_board()

                            self.origin.set_state(self.board)
                            self.caretaker.do()

                            #   get an win, tie or continue action
                            action = utils.wait_for_data(self.client_socket)
                            self.logger.debug('received action={}'.format(Actions(int(action))))

                            if Actions.EXIT.is_equals(action):
                                self.logger.debug('got exit event from server')
                                self.exit()             
                            elif Actions.WIN.is_equals(action) or Actions.TIE.is_equals(action):
                                self.game_over_gui(is_win=Actions.WIN.is_equals(action))
                            elif Actions.CONTINUE.is_equals(action):
                                self.change_turn()
                                self.logger.debug('current turn({})'.format(self.turn))
                                self.draw_undo_button()


                #   if the mouse hovering over the board, draw the top moving circle
                if (event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONUP):
                    if self.state == Actions.READY:
                        self.draw_moving_piece(event.pos[0])

                        if self.undo_button and self.undo_button.collidepoint(event.pos[0], event.pos[1]):
                            pygame.mouse.set_cursor(pygame.cursors.broken_x)
                        else:
                            pygame.mouse.set_cursor(pygame.cursors.tri_left)

                    elif self.state == Actions.WIN or self.state == Actions.TIE:
                        if self.reset_button and self.reset_button.collidepoint(event.pos[0], event.pos[1]):
                            pygame.mouse.set_cursor(pygame.cursors.broken_x)
                        else:
                            pygame.mouse.set_cursor(pygame.cursors.tri_left)    

                #   if the mouse is out of the window, clear the top row with black rectangle
                if event.type == pygame.WINDOWLEAVE and self.state == Actions.READY:
                    self.clear_top(all=False)
            
            if self.state == Actions.READY:
                self.draw_board()
            else:
                self.draw_reset_button()
            self.draw_options()
            
                # if self.state == Actions.WIN or self.state == Actions.TIE:
                #     print('fff')
                #     self.game_over_gui(is_win=(self.state == Actions.WIN))
                    
                
                # update the main display
            pygame.display.update()