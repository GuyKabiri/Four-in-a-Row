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
        super().__init__()

        self.clients = []

        self.title('Four in a Row Server')
        self.iconphoto(False, tk.PhotoImage(file='icon.png'))
        self.geometry('{}x{}'.format(ServerGUI.HEIGHT, ServerGUI.WIDTH))
        self.minsize(ServerGUI.HEIGHT, ServerGUI.WIDTH)
        self.maxsize(ServerGUI.HEIGHT, ServerGUI.WIDTH)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close_all)

        self.generate_game_button = tk.Button(text='Start Play', font=Font(family='Helvetica', size=18, weight='bold'), command=self.create_game)
        self.generate_game_button.grid(row=0, column=0, sticky=tk.W, columnspan=3)

        # self.rowsBox = tk.Spinbox(from_=5, to=10, width=2)
        # self.colsBox = tk.Spinbox(from_=5, to=10, width=2)

        self.rowsBox = tk.Spinbox(from_=2, to=10, width=2, font=Font(family='Helvetica', size=20, weight='bold'))
        self.colsBox = tk.Spinbox(from_=2, to=10, width=2, font=Font(family='Helvetica', size=20, weight='bold'))

        self.rowsBox.grid(row=1, column=0, sticky=tk.W,)
        tk.Label(text="X", font=Font(family='Helvetica', size=20, weight='bold')).grid(row=1, column=1)
        self.colsBox.grid(row=1, column=2, sticky=tk.W,)

        # threadEl = threading.Thread(target=self.create_server_socket, args=( ))
        # threadEl.daemon = True # without the daemon parameter, the function in parallel will continue even your main program ends
        # threadEl.start()
        self.create_server_socket()

        self.client_id = 0


    
    def create_game(self):
        rows, cols = int(self.rowsBox.get()), int(self.colsBox.get())

        self.client_id += 1
        client_process = multiprocessing.Process(target=ClientGUI, args=(self.client_id, (rows, cols)))
        client_process.start()
        print('client({}) opened'.format(self.client_id))

        client, address = self.server_socket.accept()
    
        # thread = start_new_thread(self.run_client, (client, (rows, cols), ))
        thread = threading.Thread(target=self.run_client, daemon=True, args=(client, (rows, cols), ))
        thread.start()

        # self.clients.append(( client, thread ))
        self.clients.append(client)
        print('Connected to: ' + address[0] + ':' + str(address[1]))


    
    def close_all(self):
        count = 1
        # for (conn, thrd) in self.clients:
        index = 0
        print('server close_all: num of client=', len(self.clients))

        for conn in self.clients:
            print('server closing', count, conn)
            count += 1
            addr = ''
            try:
                # addr = conn.gethostname()
                conn.send(bytes(str(Actions.EXIT.value), 'utf8'))
                conn.close()
            except Exception as e:
                print('server: {} has already been closed, {}'.format(count, e))
                continue
            print(addr, 'closed')
        
        print('server closing server conn')
        self.server_socket.close()

        self.destroy()


    
    def create_server_socket(self):
        self.server_socket = socket.socket()
        self.host = '127.0.0.1'
        # self.host = socket.gethostname()
        self.port = 1234
        
        try:
            # server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind( (self.host, self.port) )
            self.server_socket.listen()
        except socket.error as e:
            self.server_socket.close()
            print('ERRORrrr:', e)
        # server_socket.close()


    def run_client(self, conn, size):
        state = np.zeros( size, dtype=np.int8 )
        while True:
            wait_to_ready = utils.wait_for_data(conn, 0.1)
            if wait_to_ready and Actions.READY.is_equals(wait_to_ready):
                print('client is ready', conn)
                break

        while True:
            turn_to_add = utils.wait_for_data(conn)

            if turn_to_add and Actions.EXIT.is_equals(turn_to_add):
                print('server recv exit')
                break

            col_to_add = utils.wait_for_data(conn)

            if not turn_to_add or not col_to_add:
                break
            
            print('server got turn({}), col({})'.format(turn_to_add, col_to_add))

            turn_to_add, col_to_add = int(turn_to_add), int(col_to_add)

            if not utils.is_valid_location(col_to_add, state):
                print('server send illegal_location')
                conn.send(bytes(str(Actions.ILLEGAL_LOCATION.value), 'utf8'))
                continue

            print('legal location')
            
            state = utils.add_piece(state, col_to_add, turn_to_add)
            print('piece added')
            conn.send(bytes(str(Actions.ADD_PIECE.value), 'utf8'))

            if utils.is_won(state, turn_to_add):
                print('server send win')
                conn.send(bytes(str(Actions.WIN.value), 'utf8'))
            elif utils.is_board_full(state):
                print('server send tie')
                conn.send(bytes(str(Actions.TIE.value), 'utf8'))
            else:
                print('server send continue')
                conn.send(bytes(str(Actions.CONTINUE.value), 'utf8'))


        # try:
        #     print('closing client conn from server side', conn)
        #     self.clients.remove(conn)
        #     conn.close()
        # except Exception as e:
        #     print(e)
    






# def connect_socket(all_conns, conn):
#     while True:
#         try:
#             data = conn.recv(1024)
#             print('server received:=', data.decode('utf-8'), 'from', conn)
#             for i in range(len(all_conns)):
#                 if all_conns[i] == conn:
#                     if i % 2 == 0:
#                         other_conn = i + 1
#                     else:
#                         other_conn = i - 1
#                     print('from=', i, '| to=', other_conn)
#             all_conns[other_conn].send(data)
#             if not data:
#                 break
#         except socket.error as e:
#             conn.close()





if __name__ == '__main__':
    server = ServerGUI()
    server.mainloop()



# # start of GUI defenition

# root = tk.Tk()
# root.title('Four in a Row Server')

# client_button = tk.Button(text='Client', command=open_client)
# client_button.pack()

# root.mainloop()