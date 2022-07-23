import numpy as np
import socket


def is_won(board, target, n=4):
    board = np.array(board)     #   force to numpy
    if board.ndim != 2:
        return False

    def check_row(row):
        count = 0
        #   iterate over the column but the last
        for c in range( len(row)-1 ):
            #   if current equals to the next one and to the target, count it, otherwise reset the count
            if row[c] == target and row[c] == row[c+1]:
                count += 1
            else:
                count = 0

            #   if matched 'n' values in a row (3 matches means there are 4 values in a row)
            if count == n - 1:
                return True

    def check_rows(board):
        for row in board:               #   iterate over the rows
            if check_row(row):          #   if found a row with 'n' in a row, return true
                return True
        return False
    
    def check_cols(board):
        return check_rows(board.T)      #   transpose the matrix so the columns become rows

    def check_diags(board):          #   gets the diagonals as lists so each can be checked as a row, only diagonals with 'n' or more elements will be checked
        # i.e. for n=4, rows=6   -> need to search from diagonal (-2) up to diagonal (6) so each will include at least 4 values

        rows, cols = board.shape
        min_diag = n - rows
        max_diag = cols - n

        #   in order to check diagonals in both direction, iterate over the board and the vertically flipped board
        for b in [board, np.flip(board, axis=1)]:
            for offset in range(min_diag, max_diag+1):
                diag = np.diagonal(b, offset=offset)    # if found diagonal with 'n' in a row, return true
                if check_row(diag):
                    return True

        return False

    return check_rows(board) or check_cols(board) or check_diags(board)


'''
    check if the board is full, meaning there is no more space to add pieces
'''
def is_board_full(board):
    return not np.any(board == 0)

def is_even(num):
    return num % 2 == 0


'''
    adds a piece in a given column if not full
'''
def add_piece(board, col, turn):
    rows, cols = board.shape
    if not cols > col >= 0:
        return
    
    fliped_board = np.flip(board, 0)       #   flip the board so it will be checked from top to bottom
    for r in range(rows):
        if fliped_board[r, col] == 0:
            fliped_board[r, col] = turn
            break
    
    board = np.flip(fliped_board, 0)         #   flip the board back to suit fot the game
    # print(self.board)

    return board


'''
    checks if a column is valid location and has space to add an circle 
'''
def is_valid_location(loc, board):
    cols = board.shape[1]
    
    if cols > loc >= 0:
        return board[0, loc] == 0  # if the top row at this column is not taken
    
    return False


def wait_for_data(conn, timeout=None):
    try:
        conn.settimeout(timeout)
        data = conn.recv(1024)
        print('wait_for_data: received=', data.decode('utf-8'), 'from', conn)
        if not data:
            return None
    except socket.error as e:
        return None
    print('wait_for_data: return', data)
    return data


# def is_socket_closed(sock: socket.socket) -> bool:
#     try:
#         # this will try to read bytes without blocking and also without removing them from buffer (peek only)
#         data = sock.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
#         if len(data) == 0:
#             return True
#     except BlockingIOError:
#         return False  # socket is open and reading from it would block
#     except ConnectionResetError:
#         return True  # socket was closed for some other reason
#     except Exception as e:
#         # logger.exception("unexpected exception when checking if a socket is closed")
#         return False
#     return False



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