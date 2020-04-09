from tkinter import *
from template import *
from application import *

def start():
    root = Tk()
    conn = Connection(root)
    mess = Messages(root)
    log = Log(root)
    root.title("Car emulator v1.0")
#print(conn.label_port["text"])
    Application(conn, mess, log)
    root.mainloop()

if __name__ == "__main__":
    start()
