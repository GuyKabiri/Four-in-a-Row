import os
import tkinter as tk
from tkinter.font import Font
import threading, multiprocessing, threading
from _thread import *
import socket
import numpy as np
from typing import *
from client import ClientGUI
from actions import Actions
import utils
import logging
import datetime
import argparse

# end of imports



class ServerGUI(tk.Tk):
    HEIGHT, WIDTH = 300, 200

    def __init__(self) -> None:
        '''
        Create a new server, define it's gui and create a server socket.
        '''
        super().__init__()

        parser = argparse.ArgumentParser()
        parser.add_argument('--log_level', default='info', type=str, choices=['info', 'debug', 'warning', 'error', 'critical'])
        parser.add_argument('--n', default=4, type=int, choices=[4, 5, 6])
        args = vars(parser.parse_args())
        
        self.n = int(args['n'])
        self.log_level = getattr(logging, args['log_level'].upper())

        if not os.path.exists('logs'):
            os.mkdir('logs')

        date_time_str = datetime.datetime.now().strftime('%m-%d-%Y_%H-%M-%S')
        log_file_name = 'logs/{}.log'.format(date_time_str)
        print('Logging into', log_file_name)
        logging.basicConfig(filename=log_file_name, level=self.log_level, format='%(asctime)s %(levelname)-8s; %(message)s;')
        logging.info('n={}, log_level={}'.format(self.n, logging.getLevelName(self.log_level)))

        self.clients = []
        self.client_id = 0

        #   define server's gui window
        self.title('Four in a Row Server')
        self.iconphoto(False, tk.PhotoImage(file='icon.png'))
        self.geometry('{}x{}'.format(ServerGUI.HEIGHT, ServerGUI.WIDTH))
        self.minsize(ServerGUI.HEIGHT, ServerGUI.WIDTH)
        self.maxsize(ServerGUI.HEIGHT, ServerGUI.WIDTH)
        self.resizable(False, False)
        # on exit event, run the close_all functions
        self.protocol("WM_DELETE_WINDOW", self.close_all)

        self.main_frame = tk.Frame()

        #   define rows and cols spinboxes
        self.spin_frame = tk.Frame(self.main_frame)
        rows = tk.StringVar(value='8')
        cols = tk.StringVar(value='8')
        self.rowsBox = tk.Spinbox(self.spin_frame, textvariable=rows, from_=5, to=10, width=2, font=Font(family='Helvetica', size=20, weight='bold'), state='readonly')
        self.colsBox = tk.Spinbox(self.spin_frame, textvariable=cols, from_=5, to=10, width=2, font=Font(family='Helvetica', size=20, weight='bold'), state='readonly')
        self.rowsBox.grid(row=0, column=0, sticky=tk.W,)
        self.colsBox.grid(row=0, column=2, sticky=tk.W,)
        tk.Label(self.spin_frame, text="X", font=Font(family='Helvetica', size=20, weight='bold')).grid(row=0, column=1)
        self.spin_frame.pack()

        #   define start button
        self.generate_game_button = tk.Button(self.main_frame, text='Start Play', font=Font(family='Helvetica', size=18, weight='bold'), command=self.create_game)
        self.generate_game_button.pack()
        
        self.main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.create_server_socket()

    
    def create_game(self) -> None:
        '''
        Callback function for the start game button.
        Reads the number of rows and columns, create a new client gui and open a socket.
        '''
        rows, cols = int(self.rowsBox.get()), int(self.colsBox.get())

        self.client_id += 1
        #   creates new process to start the client's gui on
        client_process = multiprocessing.Process(target=ClientGUI, args=(self.client_id, (rows, cols)))
        client_process.start()
        logging.info('created Client({}) with board size (rows={}, cols={})'.format(self.client_id, rows, cols))

        client, address = self.server_socket.accept()

        #   creates new thread to maintain the client's state
        thread = threading.Thread(target=self.run_client, daemon=True, args=(client, self.client_id, (rows, cols), ))
        thread.start()

        self.clients.append(client)
        logging.info('connected to={}:{}'.format(address[0], str(address[1])))

    
    def close_all(self) -> None:
        '''
        Callback function for server exit event.
        Sends an exit event to all clients to close their sockets,
        close the server's socket and teardown the gui.
        '''
        for conn in self.clients:
            host, port = conn.getpeername()
            logging.debug('closing {}:{}'.format(host, port))
            # send an exit to the client, so it will close its conn
            conn.send(bytes(str(Actions.EXIT.value), 'utf8'))
            logging.debug('conn {}:{} closed'.format(host, port))
        
        logging.info('Server: closing server conn')
        self.server_socket.close()
        self.destroy()


    def create_server_socket(self) -> None:
        '''
        Creates the server socket.
        '''
        self.server_socket = socket.socket()
        self.host = '127.0.0.1'
        self.port = 1234
        
        try:
            self.server_socket.bind( (self.host, self.port) )
            self.server_socket.listen()
        except socket.error as e:
            self.server_socket.close()
            logging.error(e)
        host, port = self.server_socket.getsockname()
        logging.info('socket created {}:{}'.format(host, port))


    def run_client(self, conn: socket, id: int, size: Union[Tuple, List]) -> None:
        '''
        Maintains the client's state, receive steps and send responses.

            Parameters:
                conn (socket):      The socket to communicate with the client.
                id (int):           The ID of the client.
                size (tuple):       The size of the board.     
        '''

        #   initiate the board
        state = np.zeros( size, dtype=np.int8 )

        #   wait for the client to finish it's setup
        while True:
            wait_to_ready = utils.wait_for_data(conn, 0.1)
            if wait_to_ready and Actions.READY.is_equals(wait_to_ready):
                host, port = conn.getpeername()
                logging.debug('Client({}) is ready {}:{}'.format(id, host, port))
                break

        #   run the main clients loop
        while True:
            #   receive the player id from the client
            turn_to_add = utils.wait_for_data(conn)

            #   if client sent an exit event, break the main loop
            if turn_to_add and Actions.EXIT.is_equals(turn_to_add):
                logging.debug('received exit event from Client({})'.format(id))
                break

            elif turn_to_add and Actions.RESET.is_equals(turn_to_add):
                logging.debug('received reset event from Client({})'.format(id))
                state = np.zeros( size, dtype=np.int8 )
                continue
            
            #   receive the step from the client
            col_to_add = utils.wait_for_data(conn)

            #   if none, error occurred
            if not turn_to_add or not col_to_add:
                break
            
            turn_to_add, col_to_add = int(turn_to_add), int(col_to_add)
            logging.debug('got turn({}), col({}) from Client({})'.format(turn_to_add, col_to_add, id))

            #   validate the step, if illegal, send event to notify the client
            if not utils.is_valid_location(col_to_add, state):
                logging.error('send illegal_location to Client({})'.format(id))
                conn.send(bytes(str(Actions.ILLEGAL_LOCATION.value), 'utf8'))
                continue

            logging.debug('legal location')
            
            #   add the piece in the requested place and send event to update the client
            state = utils.add_piece(state, col_to_add, turn_to_add)
            conn.send(bytes(str(Actions.ADD_PIECE.value), 'utf8'))
            logging.debug('piece added')

            #   if the user that added the piece won, send win event
            if utils.is_won(state, turn_to_add, self.n):
                logging.debug('send win to Client({})'.format(id))
                conn.send(bytes(str(Actions.WIN.value), 'utf8'))
            #   if the board is full, send tie event
            elif utils.is_board_full(state):
                logging.debug('send tie to Client({})'.format(id))
                conn.send(bytes(str(Actions.TIE.value), 'utf8'))
            #   if not win and board is not full, send continue event to continue the game
            else:
                logging.debug('send continue to Client({})'.format(id))
                conn.send(bytes(str(Actions.CONTINUE.value), 'utf8'))




if __name__ == '__main__':
    server = ServerGUI()
    server.mainloop()