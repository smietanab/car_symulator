from tkinter import *
from tkinter.ttk import *

class EntryPopup(Entry):

    def __init__(self, parent, text,frame_item, signal_index, **kw):
        ''' If relwidth is set, then width is ignored '''
        super().__init__(parent, **kw)
        self.tv = parent
        self.frame = frame_item
        self.signal_nr = signal_index
        self.insert(0, text) 
        self['exportselection'] = False

        self.focus_force()
        self.bind("<Return>", self.on_return)
        self.bind("<Control-a>", self.select_all)
        self.bind("<Escape>", lambda *ignore: self.destroy())

    def on_return(self, event):

        self.frame.signall_list[self.signal_nr].default_value = int(self.get(),0)
        self.frame.SetSignall(self.frame.signall_list[self.signal_nr].name, self.frame.signall_list[self.signal_nr].default_value)
        
        
        item = self.tv.focus()
        self.tv.delete(item)
        self.tv.insert('', self.signal_nr, values = (self.frame.signall_list[self.signal_nr].get()))
        self.destroy()

    def select_all(self, *ignore):
        ''' Set selection on the whole text '''
        self.selection_range(0, 'end')
        return 'break'
