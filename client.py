import pygame
import tkinter as tk
import numpy as np
import sys
import math
import utils
import socket
import threading
from actions import Actions

COLORS = {
    'BLACK':    [0, 0, 0],
    'BLUE':     [0, 0, 255],
    'RED':      [255, 0, 0],
    'YELLOW':   [255, 255, 0],
    'GRAY':     [127, 127, 127], 
}


class ClientGUI:

    # myfont = pygame.font.SysFont("monospace", 75)

    def __init__(self, id, size=(6, 10)):
        self.id = id

        # if given size is not a tupple, a list or have not 2 dims
        if not ( isinstance(size, tuple) or isinstance(size, list) ) or len(size) != 2:
            size = (6, 10)
        self.rows = size[0]
        self.cols = size[1]
        self.board = np.zeros( size, dtype=np.int8 )               #   define the main board state object
        self.turn = 1
        self.state = Actions.READY

        self.square_size = 80                       #   size of squares
        # # if self.rows > 8 or self.cols > 10:
        # #     self.square_size = 50
        # self.radius = int(self.square_size/2 - 5)   #   size of circle radius based on the squares

        # #    calc the total width and height based on the squares size
        # self.width = self.cols * self.square_size
        # self.height = (self.rows + 1) * self.square_size

        self.calc_window_size()
        
        self.create_socket()
        self.create_gui()   #   create the gui

        # threadEl = threading.Thread(target=self.wait_for_other_player, args=( ))
        # threadEl.daemon = True # without the daemon parameter, the function in parallel will continue even your main program ends
        # threadEl.start()

        self.run_game()     #   run the main game loop

    def get_turn_color(self):
        return 'YELLOW' if self.turn == 1 else 'RED'


    def create_socket(self):
        self.client_socket = socket.socket()
        self.port = 1234
        self.host = '127.0.0.1'
    # self.host = socket.gethostname()

        try:
            self.client_socket.connect( (self.host, self.port) )
        except socket.error as e:
            print('cli-error',e)
            self.client_socket.close()


    '''
        calculate the size of the window, and adjust the circles size based on the users screen size
    '''
    def calc_window_size(self):
        win = tk.Tk()
        width, height = win.winfo_screenwidth(), win.winfo_screenheight()

        while True:
            #    calc the total width and height based on the squares size
            self.width = self.cols * self.square_size
            self.height = (self.rows + 1) * self.square_size

            self.radius = int(self.square_size/2 - 5)   #   size of circle radius based on the squares

            if not (self.width > width or self.height > height - 80):
                break

            self.square_size -= 10

    
    '''
        creates the client gui
    '''
    def create_gui(self):
        pygame.init()   # initiate the pyGame module

        #   create the main display with black background
        self.main_display = pygame.display.set_mode((self.width, self.height), 0, 32)
        self.main_display.fill(COLORS['BLACK'])
        pygame.display.update()
        pygame.display.set_caption('Client {}'.format(self.id))

        self.draw_board()   #   draw the board itself


    '''
        draws the board with its current state
    '''    
    def draw_board(self):
        for r in range(self.rows):
            for c in range(self.cols):

                # first, draw a blue rectangle around each circle
                pygame.draw.rect(
                    self.main_display,
                    COLORS['BLUE'],
                    (
                        c * self.square_size,
                        r * self.square_size + self.square_size,
                        self.square_size,
                        self.square_size
                    )
                )

                # if cell of player1
                if self.board[r][c] == 1:
                    color_to_use = 'YELLOW'
                elif self.board[r][c] == 2:
                    color_to_use = 'RED'
                else:
                    color_to_use = COLORS['BLACK']

                pygame.draw.circle(
                    self.main_display,
                    color_to_use,
                    (
                        int( c * self.square_size + self.square_size / 2),
                        int( r * self.square_size + self.square_size + self.square_size / 2)
                    ),
                    self.radius)

        pygame.display.update()


    def clear_top(self):
        pygame.draw.rect(self.main_display, COLORS['BLACK'], (0, 0, self.width, self.square_size))

    def add_text(self, txt):
        font = pygame.font.Font('freesansbold.ttf', 32)
        color_to_use = self.get_turn_color() if self.state == Actions.WIN else 'GRAY'
        text = font.render(txt, True, COLORS[color_to_use], COLORS['BLACK'])
        textRect = text.get_rect()
        textRect.center = (self.width // 2, self.square_size - (self.square_size // 3))
        self.main_display.blit(text, textRect)
        # pygame.draw.rect(self.main_display, COLORS['BLACK'], (0, 0, self.width, self.square_size))



    
    # def wait_for_other_player(self):
    #     while True:
    #         try:
    #             self.client_socket.settimeout(0.2)
    #             data = self.client_socket.recv(1024)
    #             if not data:
    #                 continue

    #             if int(data.decode('utf-8')) == -1:
    #                 print('client', self.id, 'closing')
    #                 self.client_socket.close()
    #                 pygame.quit()
    #                 sys.exit()

    #             elif not self.is_my_turn():
    #                 print('client', self.id, 'recv on wait',  data.decode('utf-8'))
    #                 self.add_piece(int(data))
    #                 self.draw_board()
    #                 self.turn = not self.turn
    #         except socket.error as e:
    #             pass

    def exit(self, should_send=False):
        if should_send:
            self.client_socket.send(bytes(str(Actions.EXIT.value), 'utf8'))
        self.client_socket.close()
        pygame.quit()
        sys.exit()


    
    def run_game(self):
        self.client_socket.send(bytes(str(Actions.READY.value), 'utf8'))

        action = Actions.UNKNOWN
        while True:

            is_exit =  utils.wait_for_data(self.client_socket, 0.01)
            if is_exit and Actions.EXIT.is_equals(is_exit):
                print('client({}) got exit'.format(self.id))
                self.exit()


            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print('pygame exit')
                    self.exit(should_send=True)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print('esc exit')
                        self.exit(should_send=True)


                if event.type == pygame.MOUSEBUTTONUP and self.state == Actions.READY:
                    print('client({}) mouse button up event'.format(self.id))
                    #print(event.pos)

                    posx = event.pos[0]     #   get x coordinate of the mouse
                    col = int(math.floor(posx / self.square_size))
    
                    self.client_socket.send(bytes(str(self.turn), 'utf8'))
                    self.client_socket.send(bytes(str(col), 'utf8'))

                    print('client({}) sent turn={}, col={}'.format(self.id, self.turn, col))
                    
                    action = utils.wait_for_data(self.client_socket)

                    print('client({}) recv action={}'.format(self.id, Actions(int(action))))
                    if Actions.EXIT.is_equals(action):
                        print('client({}) got exit'.format(self.id))
                        self.exit()
                    if Actions.ADD_PIECE.is_equals(action):
                        utils.add_piece(self.board, col, self.turn)
                        self.draw_board()

                        continue_or_win = utils.wait_for_data(self.client_socket)
                        print('client({}) recv action={}'.format(self.id, Actions(int(continue_or_win))))
                        if Actions.EXIT.is_equals(action):
                            print('client({}) got exit'.format(self.id))
                            self.exit()                   
                        elif Actions.WIN.is_equals(continue_or_win):
                            self.clear_top()
                            self.state = Actions.WIN
                            self.add_text('{} won!'.format(self.get_turn_color()))
                        elif Actions.TIE.is_equals(continue_or_win):
                            self.clear_top()
                            self.state = Actions.TIE
                            self.add_text("It's a tie!")
                        elif Actions.CONTINUE.is_equals(continue_or_win):
                            self.turn = 2 if self.turn == 1 else 1
                            print('client({}) current turn({})'.format(self.id, self.turn))

                if self.state == Actions.READY:

                    if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONUP:
                        self.clear_top()
                        posx = event.pos[0] #   get x coordinate of the mouse
                        col = int(math.floor(posx / self.square_size))
                        curr_color = self.get_turn_color()
                        color_to_use = COLORS[curr_color] if utils.is_valid_location(col, self.board) else COLORS['GRAY']
                        circlex = col * self.square_size + self.square_size / 2
                        pygame.draw.circle(self.main_display, color_to_use, (circlex, int(self.square_size/2)), self.radius)  #   draw circle on top of the board

                    if event.type == pygame.WINDOWLEAVE:
                        #   clears the top row with black rectangle when the mouse leaves the window
                        self.clear_top()
                
                
                pygame.display.update()     # update the main display for mouse events
                    
                    # pygame.draw.circle(self.main_display, COLORS[self.my_color], (posx, int(self.square_size/2)), self.radius)  #   draw circle on top of the board

            # manager.keyevent(pygame.key.get_pressed())
            # manager.update()


    # '''
    #     checks whether the given row and column are legal to use
    # '''            
    # def is_valid_location(self, col):
    #     if self.cols > col >= 0:
    #         return self.board[0, col] == 0  # if the top row at this column is not taken
        
    #     return False


