from tkinter import *
from tkinter.ttk import *

class Application(LabelFrame):
    
    def __init__(self, master):
        """ Inicjalizuj ramkę. """
        super(Application, self).__init__(master)
        self.config(text = "fasds")
        self.grid()
        self.create_widgets()




    def create_widgets(self):

        self.blb = Label(self, text = "label")
        self.blb.grid(row = 0, column = 0 , columnspan = 1 , sticky = W)

        self.blb2 = Label(self, text = "label")
        self.blb2.grid(row = 1, column = 1 , columnspan = 1, sticky = W)

        self.blb3 = Label(self, text = "label")
        self.blb3.grid(row = 2, column = 2 , columnspan = 1, sticky = W) 
#        self.btn1 = Button(self, command = self.update_count)
#        self.btn1.grid()
#        self.click = 0
#        self.btn2 = Button(self)
#        self.btn2.grid()

        self.txt = Text(self, width = 35, height = 5, wrap = WORD)
        self.txt.grid(row = 3, column = 0, columnspan = 2, sticky = W)

        self.lista = [1,2,3]
        self.combo = Combobox(self, values = self.lista)
        self.combo.grid(column = 2, row = 0)


    def update_count(self):
        self.click +=1
        self.btn1.config(text = str(self.click))
        print("dsfsdfs")
        
root = Tk()
root.title("csdcsd")
Application(root)
root.mainloop()
