from tkinter import *
from tkinter.ttk import *
from tkinter import scrolledtext
import serial
import os

class Connection(LabelFrame):
#    COM = ()  
    def __init__(self, master):
        super(Connection, self).__init__(master)
        self.config(text = "Connection")
        self.grid(column = 0, row = 0, sticky = "we")
        self.create_widgets()

    def  get_com(self):
        if os.name == 'nt':  # sys.platform == 'win32':
            from serial.tools.list_ports_windows import comports
        elif os.name == 'posix':
            from serial.tools.list_ports_posix import comports
        else:
            raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))
        ports = comports()
        return list(map(lambda p: p.device, ports))

    def create_widgets(self):
        
        self.label_port = Label(self, text = "Port:")
        self.label_port.grid(row = 0, column = 0)
        self.COM = self.get_com()
        self.comboBox_comlist = Combobox(self,values = self.COM)
        self.comboBox_comlist.grid(column = 1, row = 0, sticky = "nsew")     

        self.btn_refsresh = Button(self,text = "Refresh")
        self.btn_refsresh.grid(column = 2, row = 0, sticky = "nsew")   

        self.btn_connect = Button(self,text = "Connect")
        self.btn_connect.grid(column = 0, row = 1, columnspan = 2, sticky = "nsew")  
        self.btn_disconnect = Button(self,text = "Disconnect", state=DISABLED)
        self.btn_disconnect.grid(column = 2, row = 1, sticky = "nsew")  

        self.txt_connect = scrolledtext.ScrolledText(self, wrap = WORD, width = 50, height = 10)
        self.txt_connect.grid(row = 3, column = 0, columnspan = 3, rowspan = 3, sticky = "nsew")



class Messages(LabelFrame):
    def __init__(self, master):
        super(Messages, self).__init__(master)
        self.config(text = "Messages")
        self.grid(column = 0, row = 1)
        self.create_widgets()

    def create_widgets(self):
        
        self.txt_messages = Listbox(self, width = 70, height = 10)
        self.txt_messages.grid(row = 0, column = 0, columnspan = 3, sticky = "nsew")

        self.btn_send = Button(self,text = "Send")
        self.btn_send.grid(column = 0, row = 4, columnspan = 3, sticky = "nsew")

        self.cols = ('Name', 'Pos', 'Len', 'Value')
        self.listBox = Treeview(self, columns=self.cols, show='headings')

        for col in self.cols:
            self.listBox.heading(col, text=col)
            self.listBox.column(col,stretch=30, minwidth=5, width = 30)
        self.listBox.grid(row=5, column=0,columnspan = 3, sticky = "nsew")

class Log(LabelFrame):
    def __init__(self, master):
        super(Log, self).__init__(master)
        self.config(text = "Log")
        self.grid(column = 1, row = 0,rowspan = 3, columnspan = 3, sticky = "nsew")
        self.create_widgets()

    def create_widgets(self):

        #self.txt_messages = Text(self, wrap = WORD, height = 50)
        #self.txt_messages.grid(row = 0, column = 0, columnspan = 3, rowspan = 3, sticky = "nsew")
        self.cols = ('Name','Time', 'Type', 'ID', 'DLC', 'Payload')
        self.listBox = Treeview(self, height = 31, columns=self.cols, show='headings')
        
        for col in self.cols:
            self.listBox.heading(col, text=col)
            self.listBox.column(col, minwidth=50, width = 100)
        self.listBox.grid(row=0, column=0, columnspan = 3, sticky = "nsew")


