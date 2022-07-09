import tkinter as tk
import os
import time
from client2 import ClientGUI2
from client import ClientGUI
import threading, multiprocessing

# end of imports



class ServerGUI(tk.Tk):
    HEIGHT, WIDTH = 300, 200

    def __init__(self) -> None:
        super().__init__()

        self.client_list = []

        self.title('Four in a Row Server')
        self.geometry('{}x{}'.format(ServerGUI.HEIGHT, ServerGUI.WIDTH))
        self.minsize(ServerGUI.HEIGHT, ServerGUI.WIDTH)
        self.maxsize(ServerGUI.HEIGHT, ServerGUI.WIDTH)
        self.resizable(False, False) 

        self.protocol("WM_DELETE_WINDOW", self.close_all)

        self.create_game_button = tk.Button(text='Start Play', command=self.create_game).pack()

    
    def create_game(self):
        # self.client_list.append(ClientGUI(0))
        
        client_id = 1
        client_process = multiprocessing.Process(target=ClientGUI, args=(client_id, ))
        client_process.start()
        # tmp_client = ClientGUI2(0)

        # client_1.mainloop()
        print('client opened 1')

        # client_2 = ClientGUI()
        # # client_2.mainloop()
        # print('client opened 2')

    
    def close_all(self):
        
        print("send 'close' message to ALL clients, close the connection and exit")

        self.destroy()



if __name__ == '__main__':
    server = ServerGUI()
    server.mainloop()



# # start of GUI defenition

# root = tk.Tk()
# root.title('Four in a Row Server')

# client_button = tk.Button(text='Client', command=open_client)
# client_button.pack()

# root.mainloop()