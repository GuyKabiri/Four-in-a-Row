import numpy as np
import socket


def get_color(color):
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
        'GRAY':     [127, 127, 127], 
    }
    color = color.upper()
    if color not in colors_dict:
        color = 'BLACK'

    return colors_dict[color]


def is_won(board, target, n=4):
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

    def check_row(row):
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

    def check_rows(board):
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
    
    def check_cols(board):
        '''
        Check all columns in the board.

            Parameters:
                board (list of list): The board to check.

            Returns:
                won (bool): True if the user has n-in-a-row in one of the columns in the board, False otherwise.
        '''
        #   transpose the matrix so the columns become rows
        return check_rows(board.T)

    def check_diags(board):
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


def is_board_full(board):
    '''
    Checks if the board is full, meaning there is no more space to add pieces.

        Parameters:
            board (list of list): The board to check.
        
        Returns:
            is_full (bool): True if the board is full, False otherwise.
    '''
    return not np.any(board == 0)


def add_piece(board, col, turn):
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


def is_valid_location(loc, board):
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


def wait_for_data(conn, timeout=None):
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
        print('wait_for_data: received=', data.decode('utf-8'), 'from', conn)
        if not data:
            return None
    except socket.error as e:
        return None
    return data


if __name__ == '__main__':

    def test():
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