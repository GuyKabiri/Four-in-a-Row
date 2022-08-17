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
import argparse
import multiprocessing
import time
from memento import Originator, CareTaker

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
        args = vars(parser.parse_args())
        
        self.log_level = getattr(logging, args['log_level'].upper())
        self.n = 4

        self.queue = multiprocessing.Queue(-1)  #   -1=unlimited
        self.logger_listener = multiprocessing.Process(target=utils.logger_listener, args=(self.queue, self.log_level, ))
        self.logger_listener.start()

        utils.root_logger_configurer(self.queue, self.log_level)
        self.logger = logging.getLogger('Server')
        self.logger.info('n={}, log_level={}'.format(self.n, logging.getLevelName(self.log_level)))

        self.clients = []
        self.client_id = 0

        self.origin = Originator()
        self.caretacker = CareTaker(self.origin)

        #   define server's gui window
        self.title('Four in a Row Server')
        self.iconphoto(False, tk.PhotoImage(file='assets/icon.png'))
        self.geometry('{}x{}'.format(ServerGUI.HEIGHT, ServerGUI.WIDTH))
        self.minsize(ServerGUI.HEIGHT, ServerGUI.WIDTH)
        self.maxsize(ServerGUI.HEIGHT, ServerGUI.WIDTH)
        self.resizable(False, False)
        # on exit event, run the close_all functions
        self.protocol("WM_DELETE_WINDOW", self.close_all)

        self.main_frame = tk.Frame()

        #   define n-in-a-row frame
        self.n_frame = tk.Frame(self.main_frame)
        tk.Label(self.n_frame, text="n=", font=Font(family='Helvetica', size=20, weight='bold')).grid(row=0, column=0)
        n = tk.StringVar(value='4')
        self.n_value = tk.Spinbox(self.n_frame, textvariable=n, from_=4, to=6, width=2, font=Font(family='Helvetica', size=20, weight='bold'), state='readonly', command=self.validate_n)
        self.n_value.grid(row=0, column=1)
        self.n_frame.pack()

        #   define rows and cols spinboxes
        self.spin_frame = tk.Frame(self.main_frame)
        rows = tk.StringVar(value='8')
        cols = tk.StringVar(value='8')
        self.rowsBox = tk.Spinbox(self.spin_frame, textvariable=rows, from_=5, to=10, width=2, font=Font(family='Helvetica', size=20, weight='bold'), state='readonly', command=self.validate_n)
        self.colsBox = tk.Spinbox(self.spin_frame, textvariable=cols, from_=5, to=10, width=2, font=Font(family='Helvetica', size=20, weight='bold'), state='readonly', command=self.validate_n)
        self.rowsBox.grid(row=0, column=0, sticky=tk.W,)
        self.colsBox.grid(row=0, column=2, sticky=tk.W,)
        tk.Label(self.spin_frame, text="X", font=Font(family='Helvetica', size=20, weight='bold')).grid(row=0, column=1)
        self.spin_frame.pack()

        #   define start button
        self.generate_game_button = tk.Button(self.main_frame, text='Start Play', font=Font(family='Helvetica', size=18, weight='bold'), command=self.create_game)
        self.generate_game_button.pack()
        
        self.main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.create_server_socket()

    
    def validate_n(self):
        '''
        Callback function which validates the selected n value with the selected rows or columns.
        And disabled the start game button if illegal values selected.
        '''
        n_val = int(self.n_value.get())
        rows, cols = int(self.rowsBox.get()), int(self.colsBox.get())

        if n_val > cols and n_val > rows:
            self.generate_game_button['state'] = tk.DISABLED
        else:
            self.generate_game_button['state'] = tk.ACTIVE


    def create_game(self) -> None:
        '''
        Callback function for the start game button.
        Reads the number of rows and columns, create a new client gui and open a socket.
        '''
        rows, cols = int(self.rowsBox.get()), int(self.colsBox.get())
        n = int(self.n_value.get())
        if n > cols and n > rows:
            return

        self.client_id += 1
        #   creates new process to start the client's gui on
        client_process = multiprocessing.Process(target=ClientGUI, args=(self.client_id, self.queue, self.log_level, (rows, cols)))
        client_process.start()
        self.logger.info('created Client({}) with board size (rows={}, cols={})'.format(self.client_id, rows, cols))

        client, address = self.server_socket.accept()

        #   creates new thread to maintain the client's state
        thread = threading.Thread(target=self.run_client, daemon=True, args=(client, self.client_id, (rows, cols), n, ))
        thread.start()

        self.clients.append(client)
        self.logger.info('connected to={}:{}'.format(address[0], str(address[1])))

    
    def close_all(self) -> None:
        '''
        Callback function for server exit event.
        Sends an exit event to all clients to close their sockets,
        close the server's socket and teardown the gui.
        '''
        for conn in self.clients:
            host, port = conn.getpeername()
            self.logger.debug('closing {}:{}'.format(host, port))
            # send an exit to the client, so it will close its conn
            conn.send(bytes(str(Actions.EXIT.value), 'utf8'))
            self.logger.debug('conn {}:{} closed'.format(host, port))
        
        self.logger.info('closing server conn')
        self.server_socket.close()

        #   sleep before terminate the logger listener so it will finish to log
        time.sleep(1)
        self.logger_listener.terminate()

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
            self.logger.error(str(e))
        host, port = self.server_socket.getsockname()
        self.logger.info('socket created {}:{}'.format(host, port))


    def run_client(self, conn: socket, client_id: int, size: Union[Tuple, List], n: int) -> None:
        '''
        Maintains the client's state, receive steps and send responses.

            Parameters:
                conn (socket):      The socket to communicate with the client.
                client_id (int):    The ID of the client.
                size (tuple):       The size of the board.
                n (int):            Value for n-in-a-row.    
        '''

        #   initiate the board
        state = np.zeros( size, dtype=np.int8 )
        self.origin.set_state(state)
        self.caretacker.do()

        #   wait for the client to finish it's setup
        while True:
            wait_to_ready = utils.wait_for_data(conn, 0.1)
            if wait_to_ready and Actions.READY.is_equals(wait_to_ready):
                host, port = conn.getpeername()
                self.logger.debug('Client({}) is ready {}:{}'.format(client_id, host, port))
                break

        #   run the main clients loop
        while True:
            #   receive the player id from the client
            action1 = utils.wait_for_data(conn)

            #   if client sent an exit event, break the main loop
            if action1 and Actions.EXIT.is_equals(action1):
                self.logger.debug('received exit event from Client({})'.format(client_id))
                break

            elif action1 and Actions.RESET.is_equals(action1):
                self.logger.info('received reset event from Client({})'.format(client_id))
                state = np.zeros( size, dtype=np.int8 )
                continue
            
            elif action1 and Actions.UNDO.is_equals(action1):
                self.logger.info('received undo event from Client({})'.format(client_id))
                if self.caretacker.undo():
                    state = self.origin.get_state()
                continue
            
            #   receive the step from the client
            action2 = utils.wait_for_data(conn)

            #   if none, error occurred
            if not action1 or not action2:
                break

            player, column = int(action1), int(action2)
            
            self.logger.info('Client({}) got column={} from player={}'.format(client_id, column, player))

            #   validate the step, if illegal, send event to notify the client
            if not utils.is_valid_location(column, state):
                self.logger.warning('send illegal_location to Client({})'.format(client_id))
                conn.send(bytes(str(Actions.ILLEGAL_LOCATION.value), 'utf8'))
                continue

            self.logger.debug('legal location')
            
            #   add the piece in the requested place and send event to update the client
            state = utils.add_piece(state, column, player)
            conn.send(bytes(str(Actions.ADD_PIECE.value), 'utf8'))
            self.logger.debug('piece added')

            self.origin.set_state(state)
            self.caretacker.do()

            #   if the user that added the piece won, send win event
            if utils.is_won(state, player, n):
                self.logger.info('player {} won on Client({})'.format(player, client_id))
                conn.send(bytes(str(Actions.WIN.value), 'utf8'))
            #   if the board is full, send tie event
            elif utils.is_board_full(state):
                self.logger.debug('send tie to Client({})'.format(client_id))
                conn.send(bytes(str(Actions.TIE.value), 'utf8'))
            #   if not win and board is not full, send continue event to continue the game
            else:
                self.logger.debug('send continue to Client({})'.format(client_id))
                conn.send(bytes(str(Actions.CONTINUE.value), 'utf8'))




if __name__ == '__main__':
    server = ServerGUI()
    server.mainloop()