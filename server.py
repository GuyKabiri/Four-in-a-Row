from argparse import Action
from http import client
import tkinter as tk
from tkinter.font import Font
import os
import time
from typing import Tuple

from client import ClientGUI
import threading, multiprocessing, threading
from _thread import *
import socket
import numpy as np
from actions import Actions

import utils

# end of imports



class ServerGUI(tk.Tk):
    HEIGHT, WIDTH = 300, 200

    def __init__(self) -> None:
        '''
        Create a new server, define it's gui and create a server socket.
        '''
        super().__init__()

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

        #   define start button
        self.generate_game_button = tk.Button(text='Start Play', font=Font(family='Helvetica', size=18, weight='bold'), command=self.create_game)
        self.generate_game_button.grid(row=0, column=0, sticky=tk.W, columnspan=3)

        #   define rows and cols spinboxes
        self.rowsBox = tk.Spinbox(from_=2, to=10, width=2, font=Font(family='Helvetica', size=20, weight='bold'))
        self.colsBox = tk.Spinbox(from_=2, to=10, width=2, font=Font(family='Helvetica', size=20, weight='bold'))
        self.rowsBox.grid(row=1, column=0, sticky=tk.W,)
        self.colsBox.grid(row=1, column=2, sticky=tk.W,)
        tk.Label(text="X", font=Font(family='Helvetica', size=20, weight='bold')).grid(row=1, column=1)

        self.create_server_socket()

    
    def create_game(self):
        '''
        Callback function for the start game button.
        Reads the number of rows and columns, create a new client gui and open a socket.
        '''
        rows, cols = int(self.rowsBox.get()), int(self.colsBox.get())

        self.client_id += 1
        #   creates new process to start the client's gui on
        client_process = multiprocessing.Process(target=ClientGUI, args=(self.client_id, (rows, cols)))
        client_process.start()
        print('Server: created Client({})'.format(self.client_id))

        client, address = self.server_socket.accept()

        #   creates new thread to maintain the client's state
        thread = threading.Thread(target=self.run_client, daemon=True, args=(client, (rows, cols), ))
        thread.start()

        # self.clients.append(( client, thread ))
        self.clients.append(client)
        print('Server: connected to={}:{}'.format(address[0], str(address[1])))

    
    def close_all(self):
        '''
        Callback function for server exit event.
        Sends an exit event to all clients to close their sockets,
        close the server's socket and teardown the gui.
        '''
        for conn in self.clients:
            print('Server: closing', conn)
            addr = ''
            # send an exit to the client, so it will close its conn
            conn.send(bytes(str(Actions.EXIT.value), 'utf8'))
            print('Server: {} closed'.format(addr))
        
        print('Server: closing server conn')
        self.server_socket.close()
        self.destroy()


    def create_server_socket(self):
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
            print('Server: ERROR=', e)


    def run_client(self, conn, size):
        '''
        Maintains the client's state, receive steps and send responses.
        '''

        #   initiate the board
        state = np.zeros( size, dtype=np.int8 )

        #   wait for the client to finish it's setup
        while True:
            wait_to_ready = utils.wait_for_data(conn, 0.1)
            if wait_to_ready and Actions.READY.is_equals(wait_to_ready):
                print('Server: client is ready {}'.format(conn))
                break

        #   run the main clients loop
        while True:
            #   receive the player id from the client
            turn_to_add = utils.wait_for_data(conn)

            #   if client sent an exit event, break the main loop
            if turn_to_add and Actions.EXIT.is_equals(turn_to_add):
                print('Server: received exit event from client')
                break
            
            #   receive the step from the client
            col_to_add = utils.wait_for_data(conn)

            #   if none, error occurred
            if not turn_to_add or not col_to_add:
                break
            
            print('Server: got turn({}), col({})'.format(turn_to_add, col_to_add))
            turn_to_add, col_to_add = int(turn_to_add), int(col_to_add)

            #   validate the step, if illegal, send event to notify the client
            if not utils.is_valid_location(col_to_add, state):
                print('Server: send illegal_location')
                conn.send(bytes(str(Actions.ILLEGAL_LOCATION.value), 'utf8'))
                continue

            print('Server: legal location')
            
            #   add the piece in the requested place and send event to update the client
            state = utils.add_piece(state, col_to_add, turn_to_add)
            conn.send(bytes(str(Actions.ADD_PIECE.value), 'utf8'))
            print('Server: piece added')

            #   if the user that added the piece won, send win event
            if utils.is_won(state, turn_to_add):
                print('Server: send win')
                conn.send(bytes(str(Actions.WIN.value), 'utf8'))
            #   if the board is full, send tie event
            elif utils.is_board_full(state):
                print('Server: send tie')
                conn.send(bytes(str(Actions.TIE.value), 'utf8'))
            #   if not win and board is not full, send continue event to continue the game
            else:
                print('Server: send continue')
                conn.send(bytes(str(Actions.CONTINUE.value), 'utf8'))




if __name__ == '__main__':
    server = ServerGUI()
    server.mainloop()