import time
import logging
import logging.handlers
import datetime
import multiprocessing
import numpy as np
import socket
from typing import *
import os

Couple = Union[Tuple[int], List[int]]

def get_color(color: str) -> List[int]:
    '''
    Get a string color and return the 3-dimensional array that represents it.

        Parameters:
            color (str): The color to return.

        Returns:
            color (list): 3-dimensional array.
    '''
    colors_dict = {
        'BLACK':    [0, 0, 0],
        'BLUE':     [0, 0, 255],
        'RED':      [255, 0, 0],
        'YELLOW':   [255, 255, 0],
        'GREEN':    [0, 127, 0],
        'ORANGE':   [255, 165, 0],
        'GRAY':     [127, 127, 127],
        'WHITE':    [255, 255, 255],
    }
    color = color.upper()
    if color not in colors_dict:
        color = 'BLACK'

    return colors_dict[color]


def filter_color(colors_list: List[str], color: str):
    '''
    Get a list of colors and filter one color out.

        Parameters:
            colors_list (list): List of color names.
            color (str):        A color name to filter out.

        Return:
            colors_list (list): List with the colors but the one to filter.
    '''

    return [ c for c in colors_list if c != color ]


def is_won(board: np.ndarray, target: int, n: Optional[int] = 4) -> bool:
    '''
    Check if the target user has n-in-a-row.

        Parameters:
            target  (int): The user to check whether won or not.
            n       (int): The length to check, default 4.

        Returns:
            won (bool): True if there is n-in-a-row, False otherwise.
    '''
    #   force to numpy
    board = np.array(board)
    if board.ndim != 2:
        return False

    def check_row(row: int) -> bool:
        '''
        Check if a row has n-in-a-row

            Parameters:
                row (int): The row to check.

            Returns:
                won (bool): True if there are n-in-a-row in the specific row.
        '''
        count = 0
        #   iterate over the column but the last index
        for c in range( len(row)-1 ):
            #   if current equals to the next one and to the target, count it, otherwise reset the count
            if row[c] == target and row[c] == row[c+1]:
                count += 1
            else:
                count = 0

            #   if matched 'n' values in a row (3 matches means there are 4 values in a row)
            if count == n - 1:
                return True
        return False

    def check_rows(board: np.ndarray) -> bool:
        '''
        Check all rows in the board.

            Parameters:
                board (list of list): The board to check.

            Returns:
                won (bool): True if the user has n-in-a-row in one of the rows in the board, False otherwise.
        '''
        for row in board:               #   iterate over the rows
            if check_row(row):          #   if found a row with n-in-a-row, return true
                return True
        return False
    
    def check_cols(board: np.ndarray) -> bool:
        '''
        Check all columns in the board.

            Parameters:
                board (list of list): The board to check.

            Returns:
                won (bool): True if the user has n-in-a-row in one of the columns in the board, False otherwise.
        '''
        #   transpose the matrix so the columns become rows
        return check_rows(board.T)

    def check_diags(board: np.ndarray) -> bool:
        '''
        Check all diagonals in the board.

            Parameters:
                board (list of list): The board to check.

            Returns:
                won (bool): True if the user has n-in-a-row in one of the diagonals in the board, False otherwise.
        '''
        #   gets the diagonals as lists so each can be checked as a row, only diagonals with 'n' or more elements will be checked
        #   i.e. for n=4, rows=6   -> need to search from diagonal (-2) up to diagonal (6) so each will include at least 4 values

        #   calculate the min and max diagonal to check
        rows, cols = board.shape
        min_diag = n - rows
        max_diag = cols - n

        #   in order to check diagonals in both direction, iterate the original board and the vertically flipped board
        for b in [board, np.flip(board, axis=1)]:
            for offset in range(min_diag, max_diag+1):
                diag = np.diagonal(b, offset=offset)
                if check_row(diag):
                    return True
        return False

    return check_rows(board) or check_cols(board) or check_diags(board)


def is_board_full(board: np.ndarray) -> bool:
    '''
    Checks if the board is full, meaning there is no more space to add pieces.

        Parameters:
            board (list of list): The board to check.
        
        Returns:
            is_full (bool): True if the board is full, False otherwise.
    '''
    return not np.any(board == 0)


def add_piece(board: np.ndarray, col: int, turn: int) -> np.ndarray:
    '''
    Adds a piece in a given column if not column is not full and return the new board.

        Parameters:
            board (list of list):   The board to add the piece on.
            col (int):              The column index to add.
            turn (int):             The player id to add.

        Returns:
            board (list of list):   The new board if piece added or not, None if illegal location.
    '''
    rows, cols = board.shape
    if not cols > col >= 0:
        return None
    
    #   flip the board so it will be checked from top to bottom
    fliped_board = np.flip(board, 0)
    for r in range(rows):
        if fliped_board[r, col] == 0:
            fliped_board[r, col] = turn
            break
    
    #   flip the board back to suit fot the game
    board = np.flip(fliped_board, 0)
    return board


def is_valid_location(loc: int, board: np.ndarray) -> bool:
    '''
    Checks if a given column is valid and has space to add a piece.

        Parameters:
            loc (int):              The column index to check.
            board (list of list):   The board to check.

        Returns:
            valid (bool): True if column is not full, False otherwise.
    '''
    cols = board.shape[1]

    #   if the top row at this column is not taken
    if cols > loc >= 0:
        return board[0, loc] == 0
    return False


def wait_for_data(conn: socket, timeout: Optional[float] = None) -> bytes:
    '''
    Wait to receive data on a given socket.

        Parameters:
            conn (socket):      The sockets to receive data on.
            timeout: (float):   Amount of time to wait for a timeout, default None.
        
        Returns:
            data (object):  The data that was received from the socket.
    '''
    try:
        conn.settimeout(timeout)
        data = conn.recv(1024)
        if not data:
            return None
    except Exception as e:
        return None
    return data


def logger_listener(queue: multiprocessing.Queue, log_level: int):
    '''
    Function that will run the logger listener for multiprocess logging.

        Parameters:
            queue (Queue):  The queue to read the messages from, and log them to the file.
            log_level(int): The level of log, i.e.: debug, info.
    '''
    log_folder = 'logs'
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    date_time_str = datetime.datetime.now().strftime('%m-%d-%Y_%H-%M-%S')
    log_file_name = os.path.join(log_folder, '{}.log'.format(date_time_str))

    root = logging.getLogger()
    file_handler = logging.handlers.RotatingFileHandler(log_file_name, 'a')
    formatter = logging.Formatter('%(asctime)s %(name)-10s %(levelname)-8s; %(message)s;')
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    root.setLevel(log_level)

    #   run listener forever
    while True:
        while not queue.empty():
            record = queue.get()
            logger = logging.getLogger(record.name)
            logger.handle(record)
        time.sleep(1)


def root_logger_configurer(queue: multiprocessing.Queue, log_level: int):
    '''
    Defines the root logger to used by the server and clients processes.

        Parameters:
            queue (Queue):  The queue to read the messages from, and log them to the file.
            log_level(int): The level of log, i.e.: debug, info.
    '''
    h = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(log_level)


if __name__ == '__main__':

    def test() -> None:
        board = np.zeros( (6, 10) )

        # assert rows
        a = board.copy()
        a[5, 0] = 1
        a[5, 1] = 1
        a[5, 2] = 1
        a[5, 3] = 1

        assert(is_won(a, target=1, n=4))
        assert(not is_won(a, target=1, n=5))
        assert(not is_won(a, target=2, n=4))


        # assert columns
        b = board.copy()
        b[2, 4] = 1
        b[3, 4] = 1
        b[4, 4] = 1
        b[5, 4] = 1

        assert(is_won(b, target=1, n=4))
        assert(not is_won(b, target=1, n=5))
        assert(not is_won(b, target=2, n=4))


        # assert diagonals
        c = board.copy()
        c[2, 4] = 1
        c[3, 5] = 1
        c[4, 6] = 1
        c[5, 7] = 1

        assert(is_won(c, target=1, n=4))
        assert(not is_won(c, target=1, n=5))
        assert(not is_won(c, target=2, n=4))


        # assert flipped diagonals
        d = board.copy()
        d[2, 4] = 1
        d[3, 3] = 1
        d[4, 2] = 1
        d[5, 1] = 1

        assert(is_won(d, target=1, n=4))
        assert(not is_won(d, target=1, n=5))
        assert(not is_won(d, target=2, n=4))

    test()