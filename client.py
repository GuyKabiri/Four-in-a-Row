import pygame
import numpy as np
import sys
import math
import utils

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
        if not isinstance(size, tuple) or not isinstance(size, list) or len(size) != 2:
            size = (6, 10)
        self.rows = size[0]
        self.cols = size[1]
        self.board = np.zeros( size, dtype=np.int8 )               #   define the main board state object

        self.square_size = 80                       #   size of squares
        self.radius = int(self.square_size/2 - 5)   #   size of circle radius based on the squares

        #    calc the total width and height based on the squares size
        self.width = self.cols * self.square_size
        self.height = (self.rows + 1) * self.square_size

        self.my_color = 'YELLOW'
        
        self.create_gui()   #   create the gui
        self.run_game()     #   run the main game loop

    
    '''
        creates the client gui
    '''
    def create_gui(self):
        pygame.init()   # initiate the pyGame module

        #   create the main display with black background
        self.main_display = pygame.display.set_mode((self.width, self.height), 0, 32)
        self.main_display.fill(COLORS['BLACK'])
        pygame.display.update()
        pygame.display.set_caption('Client XXX___XXX')

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
                    color_to_use = COLORS['RED']
                elif self.board[r][c] == 2:
                    color_to_use = COLORS['YELLOW']
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

    
    def run_game(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                if event.type == pygame.MOUSEBUTTONUP:
                    #print(event.pos)

                    posx = event.pos[0]     #   get x coordinate of the mouse
                    col = int(math.floor(posx / self.square_size))
    
                    if self.is_valid_location(col):
                        self.add_piece(col)
                        self.draw_board()
                        check = utils.check_board(self.board, self.id)
                        print('send data to server, check if win', col, 'checked=', check)



                        self.id = 1 if self.id == 2 else 2

                        

                if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONUP:
                    self.clear_top()
                    posx = event.pos[0] #   get x coordinate of the mouse
                    col = int(math.floor(posx / self.square_size))
                    color_to_use = COLORS[self.my_color] if self.is_valid_location(col) else COLORS['GRAY']
                    posx = col * self.square_size + self.radius
                    pygame.draw.circle(self.main_display, color_to_use, (posx, int(self.square_size/2)), self.radius)  #   draw circle on top of the board

                if event.type == pygame.WINDOWLEAVE:
                    #   clears the top row with black rectangle when the mouse leaves the window
                    self.clear_top()
                
                
                pygame.display.update()     # update the main display for mouse events
                    
                    # pygame.draw.circle(self.main_display, COLORS[self.my_color], (posx, int(self.square_size/2)), self.radius)  #   draw circle on top of the board

            # manager.keyevent(pygame.key.get_pressed())
            # manager.update()


    '''
        checks whether the given row and column are legal to use
    '''            
    def is_valid_location(self, col):
        if self.cols > col >= 0:
            return self.board[0, col] == 0  # if the top row at this column is not taken
        
        return False


    '''
        adds a piece in a given column if not full
    '''
    def add_piece(self, col):
        if not self.cols > col >= 0:
            return
        
        fliped_board = np.flip(self.board, 0)       #   flip the board so it will be checked from top to bottom
        for r in range(self.rows):
            if fliped_board[r, col] == 0:
                fliped_board[r, col] = self.id
                break
        
        self.board = np.flip(fliped_board, 0)         #   flip the board back to suit fot the game

        print(self.board)