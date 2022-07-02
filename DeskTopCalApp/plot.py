import tkinter as tk

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
import collections


class Data_Plot:
    def __init__(self, parent, x_container, y1_container, y2_container, title, x_label, y1_label, y2_label, is_static = True) :
        self.parent = parent

        self.figure = Figure(figsize = (9, 6), dpi = 100)
        self.sub_plot_1 = self.figure.add_subplot(111)
        self.sub_plot_2 = self.sub_plot_1.twinx()

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.parent)
        self.canvas.get_tk_widget().grid(row=0,column=1, sticky=tk.NW, padx = (10, 10), pady = (0, 0))
        self.canvas.draw()

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.parent, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(row=1,column=1, sticky=tk.N, padx = (0, 0), pady = (0, 0))
        self.figure.tight_layout()

        self.x_container = x_container
        self.y1_container = y1_container
        self.y2_container = y2_container

        self.title = title
        self.x_label = x_label
        self.y1_label = y1_label
        self.y2_label = y2_label
        self.is_static = is_static

        self.x_min = 0
        self.x_max = 0
        self.y1_min = 0
        self.y1_max = 0
        self.y2_min = 0
        self.y2_max = 0

        #self.update_plot()


    def append_values(self, x, y1, y2) :
        self.x_container.append(x)
        self.y1_container.append(y1)
        self.y2_container.append(y2)


    def decorate_plot(self) : 
        self.sub_plot_1.grid()
        self.sub_plot_1.set_title (self.title, fontsize=20)
        self.sub_plot_1.set_ylabel(self.y1_label, fontsize=14)
        self.sub_plot_1.set_xlabel(self.x_label, fontsize=14)
        self.sub_plot_2.set_ylabel(self.y2_label, fontsize=14)
        self.sub_plot_2.yaxis.set_label_coords(1.1, 0.5)
        self.figure.tight_layout()
    

    def resize_plot_axes_limits(self) :
        self.sub_plot_1.set_ylim(self.y1_min, self.y1_max)
        self.sub_plot_2.set_ylim(self.y2_min, self.y2_max)

        if self.is_static == True :
            self.sub_plot_1.set_xlim(self.x_min, self.x_max)


    def set_axes_limits(self, x_min, x_max, y1_min, y1_max, y2_min, y2_max) :
        self.x_min = x_min
        self.x_max = x_max
        self.y1_min = y1_min
        self.y1_max = y1_max
        self.y2_min = y2_min
        self.y2_max = y2_max


    def update_plot(self) :
        self.sub_plot_1.clear()
        self.sub_plot_2.clear()

        self.resize_plot_axes_limits()
        self.decorate_plot()
        
        self.sub_plot_1.plot(self.x_container, self.y1_container, color = 'red')
        self.sub_plot_2.plot(self.x_container, self.y2_container, color = 'blue')

        self.canvas.draw()


class Data_Plot3:
    def __init__(self, parent, x_container, y1_container, y2_container, y3_container, title, x_label, y1_label, y2_label,
                 is_static=True):
        self.parent = parent

        self.figure = Figure(figsize=(9, 6), dpi=100)
        self.sub_plot_1 = self.figure.add_subplot(111)
        self.sub_plot_2 = self.sub_plot_1.twinx()
        self.sub_plot_3 = self.sub_plot_1.twinx()

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.parent)
        self.canvas.get_tk_widget().grid(row=0, column=1, sticky=tk.NW, padx=(10, 10), pady=(0, 0))
        self.canvas.draw()

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.parent, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(row=1, column=1, sticky=tk.N, padx=(0, 0), pady=(0, 0))
        self.figure.tight_layout()

        self.x_container = x_container
        self.y1_container = y1_container
        self.y2_container = y2_container
        self.y3_container = y3_container

        self.title = title
        self.x_label = x_label
        self.y1_label = y1_label
        self.y2_label = y2_label
        self.is_static = is_static

        self.x_min = 0
        self.x_max = 0
        self.y1_min = 0
        self.y1_max = 0
        self.y2_min = 0
        self.y2_max = 0

        # self.update_plot()

    def append_values(self, x, y1, y2, y3):
        self.x_container.append(x)
        self.y1_container.append(y1)
        self.y2_container.append(y2)
        self.y3_container.append(y3)

    def decorate_plot(self):
#        self.sub_plot_1.grid()
        self.sub_plot_2.grid()
        self.sub_plot_1.set_title(self.title, fontsize=20)
        self.sub_plot_1.set_ylabel(self.y1_label, fontsize=14)
        self.sub_plot_1.set_xlabel(self.x_label, fontsize=14)
        self.sub_plot_2.set_ylabel(self.y2_label, fontsize=14)
        self.sub_plot_2.yaxis.set_label_coords(1.1, 0.5)
        self.figure.tight_layout()

    def resize_plot_axes_limits(self):
        self.sub_plot_1.set_ylim(self.y1_min, self.y1_max)
        self.sub_plot_2.set_ylim(self.y2_min, self.y2_max)
        self.sub_plot_3.set_ylim(self.y2_min, self.y2_max)

        if self.is_static == True:
            self.sub_plot_1.set_xlim(self.x_min, self.x_max)

    def set_axes_limits(self, x_min, x_max, y1_min, y1_max, y2_min, y2_max):
        self.x_min = x_min
        self.x_max = x_max
        self.y1_min = y1_min
        self.y1_max = y1_max
        self.y2_min = y2_min
        self.y2_max = y2_max

    def update_plot(self):
        self.sub_plot_1.clear()
        self.sub_plot_2.clear()
        self.sub_plot_3.clear()

        self.resize_plot_axes_limits()
        self.decorate_plot()

        self.sub_plot_1.plot(self.x_container, self.y1_container, color='red')
        self.sub_plot_2.plot(self.x_container, self.y2_container, color='blue')
        self.sub_plot_3.plot(self.x_container, self.y3_container, color='green')

        self.canvas.draw()

class Data_Plot_Smoothing(Data_Plot3):
    def __init__(self, parent, x_container, y1_container, y2_container, y3_container, title, x_label, y_label,
                 is_static=True):
        self.parent = parent

        self.figure = Figure(figsize=(9, 6), dpi=100)
        self.sub_plot_1 = self.figure.add_subplot(111)
        self.sub_plot_2 = self.sub_plot_1.twinx()
        self.sub_plot_3 = self.sub_plot_1.twinx()

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.parent)
        self.canvas.get_tk_widget().grid(row=0, column=1, sticky=tk.NW, padx=(10, 10), pady=(0, 0))
        self.canvas.draw()

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.parent, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(row=1, column=1, sticky=tk.N, padx=(0, 0), pady=(0, 0))
        self.figure.tight_layout()

        self.x_container = x_container
        self.y1_container = y1_container
        self.y2_container = y2_container
        self.y3_container = y3_container

        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.is_static = is_static

        self.x_min = 0
        self.x_max = 0
        self.y_min = 0
        self.y_max = 0

    def decorate_plot(self):
        self.sub_plot_1.grid()
        self.sub_plot_1.set_title(self.title, fontsize=20)
        self.sub_plot_1.set_ylabel(self.y_label, fontsize=14)
        self.sub_plot_1.set_xlabel(self.x_label, fontsize=14)
        self.figure.tight_layout()

    def resize_plot_axes_limits(self):
        self.sub_plot_1.set_ylim(self.y_min, self.y_max)
        self.sub_plot_2.set_ylim(self.y_min, self.y_max)
        self.sub_plot_3.set_ylim(self.y_min, self.y_max)

        if self.is_static == True:
            self.sub_plot_1.set_xlim(self.x_min, self.x_max)

    def set_axes_limits(self, x_min, x_max, y_min, y_max):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

    def update_plot(self, settings):
        self.sub_plot_1.clear()
        self.sub_plot_2.clear()
        self.sub_plot_3.clear()

        self.resize_plot_axes_limits()
        self.decorate_plot()

        if(settings['reg_active']):
            self.sub_plot_1.plot(self.x_container, self.y1_container, color='red')
        if(settings['sma_active']):
            self.sub_plot_2.plot(self.x_container, self.y2_container, color='blue')
        if(settings['ema_active']):
            self.sub_plot_3.plot(self.x_container, self.y3_container, color='green')

        self.canvas.draw()