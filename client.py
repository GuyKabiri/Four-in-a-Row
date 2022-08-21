import os
import time
import multiprocessing
import logging
import sys
import math
import utils
import socket

import tkinter as tk
import numpy as np
from typing import *
from actions import Actions
from memento import Originator, CareTaker

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
from button import Button

player_colors_list = ['red', 'yellow', 'green', 'orange', 'pink', 'cyan']


def get_next_color(my_color: str, other_color: str) -> str:
    """
    Get the next available color from the color list based on the current player and opponent colors.

        Parameters:
            my_color (str):     The color of the current player.
            other_color (str):  The color of the opponent.

        Returns:
            color (str):        The next color that can be used.
    """
    #   get list of all colors but the opponent
    available_colors = [c for c in player_colors_list if c != other_color]
    #   get current color based on the new list
    index = available_colors.index(my_color)
    #   iterate over the colors until find an unused one
    while my_color == available_colors[index]:
        index += 1
        if index >= len(available_colors):
            index = 0
    return available_colors[index]


class ClientGUI:

    def __init__(self, client_id: int, queue: multiprocessing.Queue, log_level: int,
                 size: utils.Couple = (6, 10)) -> None:
        """
        Create a new client, define it's gui, board, and create a socket.

            Parameters:
                client_id (int):                The id of the client.
                queue (multiprocessing.Queue):  The queue to push the logs in.
                log_level (int):                The log level to use.
                size (tuple):                   Size of board to use.
        """
        self.square_size = 80
        self.options_rows = 2
        self.width = 0
        self.height = 0
        self.radius = 0
        self.client_socket = None
        self.port = 0
        self.host = ''
        self.main_display = None
        self.font_size = 32
        self.font_style = None
        self.font = None
        self.undo_button = None
        self.reset_button = None
        self.start_button = None
        self.main_menu = None
        self.player1_text = None
        self.player2_text = None
        self.player1_circle = None
        self.player2_circle = None
        self.board = None
        self.origin = None
        self.caretaker = None

        self.id = client_id

        #   if given size is not a tuple, a list or have not 2 dims
        if not (isinstance(size, tuple) or isinstance(size, list)) or len(size) != 2:
            size = (6, 10)

        #   define the board size
        self.rows = size[0]
        self.cols = size[1]

        self.queue = queue
        utils.root_logger_configurer(self.queue, log_level)
        self.logger = logging.getLogger('Client({})'.format(self.id))

        self.undo_counts = [0, 0]
        self.wins = [0, 0]
        self.max_undo = 3
        self.player1_color = 'yellow'
        self.player2_color = 'red'
        self.turn = 1
        self.state = Actions.UNKNOWN

        #   calculate the clients gui size based on the amount of rows and cols
        self.calc_window_size()

        #   create the socket and the gui
        self.create_socket()

        self.handle_reset()
        self.create_gui()

        #   run the main game loop
        self.run_game()

    def get_turn_color(self) -> str:
        """
        Returns the color to use based on the current player.

            Returns:
                color (str): Capitalized color string.
        """
        return self.player1_color if self.turn == 1 else self.player2_color

    def get_other_turn_color(self) -> str:
        """
        Returns the color to use based on the other player.

            Returns:
                color (str): Capitalized color string.
        """
        return self.player2_color if self.turn == 1 else self.player1_color

    def get_player_color(self, row: int, col: int) -> str:
        """
        Get a cell in the board and return it's color.

            Parameters:
                row (int): The row in the board.
                col (int): The column in the board.

            Returns:
                color (str): Color name string.
        """
        if self.board[row][col] == 1:
            return self.player1_color
        elif self.board[row][col] == 2:
            return self.player2_color
        return 'black'

    def calc_col_by_mouse(self, x_cord: int) -> int:
        """
        Calculate the column index based on the position of the mouse on the board.

            Parameters:
                x_cord (int): The X coordination of the mouse on the board.

            Returns:
                column (int): The index of the column in the board.
        """
        return int(math.floor(x_cord / self.square_size))

    def calc_window_size(self) -> None:
        """
        Calculate the size of the window, and adjust the circles size based on the users screen size.
        """
        #   get the screen size
        win = tk.Tk()
        width, height = win.winfo_screenwidth(), win.winfo_screenheight()

        while True:
            #    calculate the total width and height based on the squares size
            self.width = self.cols * self.square_size
            self.height = (self.rows + self.options_rows) * self.square_size

            #   size of circle radius based on the squares
            self.radius = int(self.square_size / 2 - 5)

            #   if the client's size is not bigger than the users screen, exit
            if not (self.width > width or self.height > height - 80):
                break

            #   client's size is bigger than the user's screen, reduce the size
            self.square_size -= 10
            self.font_size -= 2

        self.logger.debug(
            'window size (width={}, height={}), radius={}, square_size={}, font_size={}'.format(self.width, self.height,
                                                                                                self.radius,
                                                                                                self.square_size,
                                                                                                self.font_size))

    def create_socket(self) -> None:
        """
        Creates the client's socket.
        """
        self.client_socket = socket.socket()
        self.port = 1234
        self.host = '127.0.0.1'

        try:
            self.client_socket.connect((self.host, self.port))
        except Exception as e:
            self.logger.error(str(e))
            self.client_socket.close()
        self.logger.info('created conn {}:{}'.format(self.host, self.port))

    def exit(self, should_send: bool = False) -> None:
        """
        Teardown function to close the socket and the gui.

            Parameters:
                should_send (bool): Whether to send an exit event to the server or not, default False.
        """
        if should_send:
            self.client_socket.send(bytes(str(Actions.EXIT.value), 'utf8'))
            self.logger.debug('send exit event to server')
        host, port = self.client_socket.getsockname()
        self.client_socket.close()
        self.logger.info('conn closed {}:{}'.format(host, port))
        pygame.quit()
        sys.exit()

    def create_gui(self) -> None:
        """
        Creates the client's gui.
        """

        #   set an icon and initiate the gui
        icon = pygame.image.load('assets/icon.png')
        pygame.display.set_icon(icon)
        pygame.init()  # initiate the pyGame module
        pygame.mouse.set_cursor(pygame.cursors.tri_left)

        #   create the main display with black background, pygame.SHOWN flags is used as a topmost
        self.main_display = pygame.display.set_mode((self.width, self.height), pygame.SHOWN)
        self.main_display.fill(utils.get_color('black'))

        self.font_style = pygame.font.match_font('segoeuisymbol')
        self.font = pygame.font.Font(self.font_style, self.font_size)

        self.create_undo_button()
        self.create_reset_button()
        self.start_button = None

        pygame.display.update()
        pygame.display.set_caption('Client {}'.format(self.id))

        #   draw the board itself and the top bar
        self.draw_board()

    def draw_board(self) -> None:
        """
        Draws the board with its current state.
        """
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

                center_x = int(c * self.square_size + self.square_size / 2)
                center_y = int(r * self.square_size + board_top_offset + self.square_size / 2)

                #   second, add a circle with the player's color, or black if empty cell
                color_name = self.get_player_color(r, c)
                self.draw_circle(color_name, (center_x, center_y))

        pygame.display.update()
        self.logger.debug('board=\n{}'.format(self.board))

    def draw_text_top(self, txt: str) -> None:
        """
        Adds text in the top black rectangle.

            Parameters:
                txt (str): Text to add.
        """
        #   if the state of the game is win, define the color of the text as the color of the winner
        color_to_use = self.get_turn_color() if self.state == Actions.WIN else 'GRAY'
        text = self.font.render(txt, True, utils.get_color(color_to_use), utils.get_color('black'))

        #   calculate the center of the text to place it in the center of the window
        text_rect = text.get_rect()
        text_rect.center = (self.width // 2, (self.square_size * self.options_rows) - (self.square_size // 3))
        self.main_display.blit(text, text_rect)
        self.logger.debug('draw text={}, color={}'.format(txt, color_to_use))

    def draw_scores(self) -> None:
        """
        Draw the players scores at the top of the screen.
        """
        player1_score, player2_score = str(self.wins[0]), str(self.wins[1])

        self.font.set_bold(True)
        text_1 = self.font.render(player1_score, True, utils.get_color(self.player1_color), utils.get_color('black'))
        text_2 = self.font.render(player2_score, True, utils.get_color(self.player2_color), utils.get_color('black'))
        text_c = self.font.render(':', True, utils.get_color('gray'), utils.get_color('black'))

        text_rect_1 = text_1.get_rect()
        text_rect_2 = text_2.get_rect()
        text_rect_c = text_c.get_rect()

        offset = 20

        text_rect_1.right = (self.width // 2 - offset)
        text_rect_2.left = (self.width // 2 + offset)
        text_rect_c.centerx = (self.width // 2)

        self.main_display.blit(text_1, text_rect_1)
        self.main_display.blit(text_2, text_rect_2)
        self.main_display.blit(text_c, text_rect_c)

    def draw_main_menu(self) -> None:
        """
        Draws a menu where each player can choose its color and who will play first.
        """
        #   define the span in each axis
        x_num_squares = 4
        y_num_squares = 3

        #   calculates the X and Y coordinates based on the size of the rectangles of the board
        x = int(((self.cols / 2) - x_num_squares / 2) * self.square_size)
        y = int((((self.rows / 2) - y_num_squares / 2) * self.square_size) + self.square_size * self.options_rows)

        #   draw the main rectangle of the menu
        self.main_menu = pygame.draw.rect(
            self.main_display,
            utils.get_color('gray'),
            (
                x,
                y,
                self.square_size * x_num_squares,
                self.square_size * y_num_squares
            )
        )

        row_offset = 20

        #   draw player 1 title
        self.font.set_bold(self.turn == 1)
        text = self.font.render('{} Player 1:'.format('🠖' if self.turn == 1 else '    '), True,
                                utils.get_color('black'))
        self.player1_text = text.get_rect()
        self.player1_text.midleft = (x, y + row_offset * 2)
        self.main_display.blit(text, self.player1_text)

        #   draw player 2 title
        self.font.set_bold(self.turn == 2)
        text = self.font.render('{} Player 2:'.format('🠖' if self.turn == 2 else '    '), True,
                                utils.get_color('black'))
        self.player2_text = text.get_rect()
        self.player2_text.midleft = (x, y + row_offset * 4)
        self.main_display.blit(text, self.player2_text)

        #   draw players colors
        right_most = max(self.player1_text.right, self.player2_text.right)

        self.player1_circle = self.draw_circle(self.player1_color, (right_most + 40, y + row_offset * 2),
                                               radius=self.radius // 2)

        self.player2_circle = self.draw_circle(self.player2_color, (right_most + 40, y + row_offset * 4),
                                               radius=self.radius // 2)

        #   define and draw start button
        if not self.start_button:
            x_num_squares = 3
            y_num_squares = 0.75

            x = int(((self.cols / 2) - x_num_squares / 2) * self.square_size)
            width = int(self.square_size * x_num_squares)
            height = int(self.square_size * y_num_squares)
            y = int(self.main_menu.bottom - height - 20)

            self.start_button = Button(position=(x, y), size=(width, height), btn_color='blue',
                                       callback=self.handle_start, is_active=True, text='Start Game', txt_color='black',
                                       font=self.font)

        self.start_button.draw(self.main_display)

    def draw_circle(self, color: str, center: utils.Couple, radius: Optional[int] = None):
        """
        Draw a single circle on the screen and returns it.

            Parameters:
                color (str):    The name of the color to use.
                center (list):  The X and Y coordinates of the center of the circle.
                radius (int):   The radius to use, default None will use the default radius.

            Returns:
                circle (pygame.Rect): The rectangle boundaries of the circle that was drawn.
        """
        if not isinstance(center, (tuple, list)):
            return

        if not radius:
            radius = self.radius

        color_rgb = utils.get_color(color)
        circle = pygame.draw.circle(self.main_display, color_rgb, center, radius)

        pygame.draw.circle(self.main_display, utils.get_color('black'), center, radius, 1)

        return circle

    def draw_moving_piece(self, mouse_x: int) -> None:
        """
        Drawing the moving piece on top of the board.

            Parameters:
                mouse_x (int): The X coordinate of the mouse.
        """
        self.clear_top(entire=False)
        #   get the column index of the mouse
        col = self.calc_col_by_mouse(mouse_x)
        #   select the user color or an invalid location color based on the board state
        color_to_use = self.get_turn_color() if utils.is_valid_location(col, self.board) else 'gray'
        # calculate the x axis of the circle and draw
        circle_x = int(col * self.square_size + self.square_size / 2)
        self.draw_circle(color_to_use, (circle_x, int(self.square_size * self.options_rows - self.radius)))

    def clear_top(self, entire=True) -> None:
        """
        Clears the top row above the main board with a black rectangle.

            Parameters:
                entire (bool): Whether to clear the entire top row or just the part when the circle is moving.
        """
        num_rows = self.options_rows if entire else 1
        y = 0 if entire else self.square_size * (self.options_rows - 1)
        pygame.draw.rect(self.main_display, utils.get_color('black'), (0, y, self.width, self.square_size * num_rows))
        self.draw_scores()

    def draw_game_over(self, is_win: bool = True) -> None:
        """
        Add a title to the top of the screen based on the winner, or tie, and draw the reset button.

            Parameters:
                is_win (bool): Whether it's a win or a tie, default True.
        """
        try:
            if is_win:
                self.wins[self.turn - 1] += 1
                pygame.mixer.music.load(os.path.join('assets/win.wav'))
            else:
                pygame.mixer.music.load(os.path.join('assets/tie.wav'))
            pygame.mixer.music.play()
        except Exception as e:
            self.logger.error('error playing sound: {}'.format(str(e)))

        self.clear_top()

        self.state = Actions.WIN if is_win else Actions.TIE

        if self.state == Actions.WIN:
            self.draw_text_top('Client({}) {} won!'.format(self.id, self.get_turn_color()))
        else:
            self.draw_text_top("It's a tie!")

        player1_score, player2_score = self.wins[0], self.wins[1]
        num_format = '{:' + str(max(len(str(player1_score)), len(str(player2_score)))) + 'd}'
        score_format = num_format.format(player1_score) + ':' + num_format.format(player2_score)
        self.logger.debug('game over, state={}, scores(yellow:red)=({})'.format(self.state.value, score_format))

    def create_undo_button(self) -> None:
        """
        Create the undo button with its position, size and callback.
        """
        if self.undo_counts[self.turn - 1] >= self.max_undo:
            return

        #   define the span in each axis
        x_num_squares = 0.5
        y_num_squares = 0.5

        #   calculates the X and Y coordinates based on the size of the rectangles of the board
        x = 0
        y = 0
        width = int(self.square_size * x_num_squares)
        height = int(self.square_size * y_num_squares)
        color_to_use = self.get_other_turn_color()

        self.undo_button = Button(position=(x, y), size=(width, height), btn_color=color_to_use,
                                  callback=self.handle_undo, is_active=False, img_path='assets/undo.png')

    def create_reset_button(self) -> None:
        """
        Create the reset button with its position, size and callback.
        """
        #   define the span in each axis
        x_num_squares = 1.5
        y_num_squares = 0.75

        #   calculates the X and Y coordinates based on the size of the rectangles of the board
        x = int(((self.cols / 2) - x_num_squares / 2) * self.square_size)
        y = int((((self.rows / 2) - y_num_squares / 2) * self.square_size) + self.square_size * self.options_rows)
        width = int(self.square_size * x_num_squares)
        height = int(self.square_size * y_num_squares)

        self.reset_button = Button(position=(x, y), size=(width, height), btn_color='gray', callback=self.handle_reset,
                                   is_active=False,
                                   text='Reset', txt_color='black', font=self.font)

    def handle_reset(self) -> None:
        """
        Reset the state of the game.
        """
        if self.state == Actions.WIN or self.state == Actions.TIE or self.state == Actions.UNKNOWN:
            #   define the main board state object
            self.board = np.zeros((self.rows, self.cols), dtype=np.int8)

            self.undo_counts = [0, 0]

            self.origin = Originator()
            self.caretaker = CareTaker(self.origin)

            self.origin.set_state(self.board)
            self.caretaker.do()

            self.client_socket.send(bytes(str(Actions.RESET.value), 'utf8'))

        if self.state == Actions.WIN or self.state == Actions.TIE:
            self.logger.debug('reset button pressed')
            self.state = Actions.READY

        if self.state == Actions.UNKNOWN:
            self.state = Actions.PRE_GAME

    def handle_start(self) -> None:
        """
        Handle the start button.
        """
        #   send an ready event to the server to notify the client done its setup
        self.state = Actions.READY
        self.client_socket.send(bytes(str(Actions.READY.value), 'utf8'))
        self.logger.debug('sent ready event')
        self.start_button = None

    def handle_main_menu(self, event: pygame.event) -> bool:
        """
        Handle the main menu functionality when it has been pressed.

            Parameters:
                event (pygame.Event): The event that occurred.

            Returns:
                pressed (bool): True if the button was pressed, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.player1_circle.collidepoint(event.pos):
                self.player1_color = get_next_color(self.player1_color, self.player2_color)
                return True

            elif self.player2_circle.collidepoint(event.pos):
                self.player2_color = get_next_color(self.player2_color, self.player1_color)
                return True

            elif self.player1_text.collidepoint(event.pos) or self.player2_text.collidepoint(event.pos):
                self.change_turn()
                return True

        return False

    def handle_undo(self) -> None:
        """
        Undo the last move.
        """
        self.logger.debug('undo button pressed')
        if self.undo_counts[self.turn - 1] < self.max_undo:
            self.client_socket.send(bytes(str(Actions.UNDO.value), 'utf8'))
            if self.caretaker.undo():
                self.board = self.origin.get_state()
                self.undo_counts[self.turn - 1] += 1
                self.change_turn()

    def change_turn(self) -> None:
        """
        Change the turn between the players
        """
        self.turn = 1 if self.turn == 2 else 2

    def run_game(self) -> None:
        """
        The main function to communicate with the server and maintain the state of the game.
        """
        action = Actions.UNKNOWN
        self.state = Actions.PRE_GAME
        time.sleep(1)

        should_draw_board = False
        self.reset_button.set_active(False)
        self.undo_button.set_active(False)

        while True:
            #   if received an exit event
            is_exit = utils.wait_for_data(self.client_socket, 0.01)
            if is_exit and Actions.EXIT.is_equals(is_exit):
                self.logger.debug('received exit event from server')
                self.exit()

            #   iterate over the pygame events
            for event in pygame.event.get():
                #   if exit event
                if event.type == pygame.QUIT:
                    self.logger.debug('pygame exit event')
                    self.exit(should_send=True)

                if self.state == Actions.PRE_GAME:
                    self.draw_main_menu()
                    if self.start_button.handle_event(event):
                        should_draw_board = True
                        self.draw_scores()
                        self.draw_moving_piece(event.pos[0])
                        continue
                    if self.handle_main_menu(event):
                        continue

                if self.state == Actions.READY:
                    if self.undo_button.handle_event(event):
                        should_draw_board = True
                        self.undo_button.set_active(False)
                        self.clear_top()
                        self.draw_moving_piece(event.pos[0])
                        continue

                if self.state == Actions.WIN or self.state == Actions.TIE:
                    if self.reset_button.handle_event(event):
                        should_draw_board = True
                        self.clear_top()
                        self.reset_button.set_active(False)
                        continue

                #   if a mouse click event
                if event.type == pygame.MOUSEBUTTONUP:
                    self.undo_button.set_active(False)
                    self.undo_button.button_color = self.get_turn_color()
                    if self.state == Actions.READY:
                        self.logger.debug('mouse button up event')

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
                            self.board = utils.add_piece(self.board, col, self.turn)
                            should_draw_board = True

                            self.origin.set_state(self.board)
                            self.caretaker.do()

                            #   get an win, tie or continue action
                            action = utils.wait_for_data(self.client_socket)
                            self.logger.debug('received action={}'.format(Actions(int(action))))

                            if Actions.EXIT.is_equals(action):
                                self.logger.debug('got exit event from server')
                                self.exit()
                            elif Actions.WIN.is_equals(action) or Actions.TIE.is_equals(action):
                                self.draw_game_over(is_win=Actions.WIN.is_equals(action))
                            elif Actions.CONTINUE.is_equals(action):
                                self.change_turn()
                                self.logger.debug('current turn({})'.format(self.turn))
                                if self.undo_counts[self.turn - 1] < self.max_undo:
                                    self.undo_button.text_color = self.get_other_turn_color()
                                    self.undo_button.set_active(True)

                #   if the mouse hovering over the board, draw the top moving circle
                if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONUP:
                    if self.state == Actions.READY:
                        self.draw_moving_piece(event.pos[0])

                #   if the mouse is out of the window, clear the top row with black rectangle
                if event.type == pygame.WINDOWLEAVE and self.state == Actions.READY:
                    self.clear_top(entire=False)

            if should_draw_board:
                self.draw_board()
                should_draw_board = False

            if self.state == Actions.WIN or self.state == Actions.TIE:
                self.reset_button.set_active(True)

            self.undo_button.draw(self.main_display)
            self.reset_button.draw(self.main_display)

            # update the main display
            pygame.display.update()
