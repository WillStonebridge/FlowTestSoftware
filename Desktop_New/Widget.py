import tkinter as tk
from tkinter import ttk
from tkinter import font
from typing_extensions import IntVar



def def_callback(*argc) :
    x = 10



class User_Fonts :
    def __init__(self) -> None:
        self.helv18 = font.Font(family='Helvetica',size=18, weight='bold')
        self.helv14 = font.Font(family='Helvetica',size=14, weight='bold')
        self.helv12 = font.Font(family='Helvetica',size=12, weight='bold')
        self.helv10 = font.Font(family='Helvetica',size=10, weight='bold')
        self.cal32 = font.Font(family='Calibri',size=32, weight='bold')



class Module(tk.LabelFrame) :
    def __init__(self, parent, title, t_width, t_height, bg = 'black') :
        self.fonts = User_Fonts()  
        self.label = tk.Label(text = title, anchor=tk.W, font = self.fonts.helv12, height = 1, width = t_width + 20, fg = 'white', bg = bg)        
        super().__init__(parent, labelanchor = 'n', labelwidget = self.label, width = t_width, height = t_height, background= 'white')



class Combo_Box :
        def __init__(self, module, title, values, callback = def_callback) :
            self.fonts = User_Fonts()
            self.value = tk.StringVar()
            self.title = tk.Label(module, text = title, anchor=tk.W, font = self.fonts.helv10, height = 1, width = 20, fg = 'black', bg = 'white', bd = 2)
            self.list = ttk.Combobox(module, textvariable = self.value, value = values, width = 30)
            self.list.bind("<<ComboboxSelected>>", callback)


        def place(self, X, Y) :
            self.title.place(x = X - 3, y = Y)
            self.list.current()		# self.list.current(0) causes error
            self.list.place(x=X, y = Y + 20)


        def get_value(self) :
            return self.list.get()

        
        def get_index(self) :
            return self.list.current()


        def set_index(self, index) :
            self.list.current(index)


    
class Push_Button :
    def __init__(self, module, title, fun) :
        self.button = tk.Button(module, text = title, command = fun, width = 10, height = 1, fg = 'black', activebackground = 'grey')

    def place(self, X, Y) :
        self.button.place(x=X, y=Y)

    def set_title(self, title) :
        self.button["text"] = title



class Indicator :
    def __init__(self, module, title, true_val, false_val, bgc = 'red', t_width = 20, t_height = 1, t_alignment = tk.N) :
        self.fonts = User_Fonts()
        self.title = tk.Label(module, text = title, anchor=tk.W, font = self.fonts.helv10, height = 1, width = 20, fg = 'black', bg = 'white', bd = 2)
        self.value = tk.StringVar()
        self.value = false_val
		# Easier to read
        self.indicator = tk.Label(module, text = self.value, width = t_width, height = t_height, fg = 'white', bg = bgc, anchor= t_alignment)
        self.true = true_val
        self.false = false_val


    def place(self, X, Y) :
        self.title.place(x=X - 3, y=Y)
        self.indicator.place(x=X+2, y = Y + 20)


    def make_true(self) :
        self.value = self.true
        self.indicator["text"] = self.value
        self.indicator["bg"] = 'green'


    def make_false(self) :
        self.value = self.false
        self.indicator["text"] = self.value
        self.indicator["bg"] = 'red'


    def write_value_bg(self, text, bg_color) :
        self.value = self.false
        self.indicator["text"] = text
        self.indicator["bg"] = bg_color

    
    def write_value(self, str) :
        #self.value = str
        self.indicator["text"] = str



class Text_Input :
    def __init__(self, module, title, t_width = 40, t_title_width = 18) :
        self.module = module
        self.fonts = User_Fonts()
        self.input = tk.Entry(self.module, fg = 'black', bg = 'white', width= t_width)
        self.title = tk.Label(module, text = title, anchor=tk.W, font = self.fonts.helv10, height = 1, width = t_title_width, fg = 'black', bg = 'white', bd = 2)
        

    def place(self, X, Y) :
        self.title.place(x=X - 3, y=Y)
        self.input.place(x=X+2, y = Y + 22)


    def get(self) :
        return self.input.get()

    
    def set(self, str) :
        self.input.insert(0, str)



class Check_Button :
    def __init__(self, module, title) :
        self.module = module
        self.value = tk.IntVar()
        self.check_button = tk.Checkbutton(self.module, text=title, variable=self.value, fg = 'black', bg = 'white')

    
    def get_value(self) :
        return self.value.get()


    def place(self, t_x, t_y) :
        self.check_button.place(x = t_x, y = t_y)
