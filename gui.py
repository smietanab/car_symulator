from tkinter import *







root = Tk()
root.title("Car Symulator")
root.geometry("800x600")

app= Frame(root, borderwidth = 10, bg="red")
app.grid(row=0, column=0, sticky="nsew")
lbl = Label(app, text = "Jestem etykietą")
lbl.grid()
btn =Button(app, text = "klik")
btn.grid()

btn2 =Button(app, text = "klik2")
btn2.grid()


app2= Frame(root, borderwidth = 10, bg="blue")
app2.grid(row=0, column=1, sticky="nsew")
lbl2 = Label(app2, text = "Jestem etykietą")
lbl2.grid()

#root.grid_rowconfigure(0, minsize=200, weight=1)
#root.grid_columnconfigure(0, minsize=200, weight=1)
#root.grid_columnconfigure(1, weight=1)

root.mainloop()
