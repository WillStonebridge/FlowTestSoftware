import tkinter as tk
from GUI import Main_Application


def main():
    root = tk.Tk()
    app = Main_Application(root, 'Honeywell Liquid Flow Char Application')
    # app.set_window_size(530, 800)
    app.set_window_size(830, 1375)
    app.set_style('vista')
    app.create_frames()
    app.pack(side="top", fill="both", expand=True)
    #app.place(x = 0, y = 0)
    #app.grid(row = 0, column = 0, sticky = tk.W)
    root.mainloop()


if __name__ == '__main__':
    main()