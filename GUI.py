import tkinter.messagebox

from Widget import *
from flow_controller_one import Connection_one
from mavlink_interface import *
from Test import *
from scale_ohaus import scale
from flow_controllerPhd import *

import tkinter as tk
from tkinter import filedialog as fd
from tkinter.constants import BOTTOM, RIGHT
from transitions import Machine, State
import threading
from time import process_time
import shutil


class Main_Application(tk.Frame):
    def __init__(self, parent, title):
        tk.Frame.__init__(self, parent, background="#ffffff")
        self.pack(fill=tk.BOTH, expand=1)

        self.parent = parent
        self.parent.iconbitmap("images\Honeywell App Icon.ico")
        self.parent.title(title)
        self.parent.style = ttk.Style(self)

        self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")

        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.vsb.pack(side=RIGHT, fill=tk.Y)

        self.hsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.hsb.pack(side=BOTTOM, fill=tk.X)

        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        # self.canvas.bind("<Configure>", lambda e : self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.frame = tk.Frame(self.canvas, background="#ffffff")
        self.frame_id = self.canvas.create_window((0, 0), window=self.frame, anchor="nw", tags="self.frame")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def set_window_size(self, window_height, window_width):
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        self.parent.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
        self.parent.state('zoomed')

    def set_style(self, style_name):
        self.parent.style.theme_use(style_name)
        self.parent['bg'] = 'white'

    def create_frames(self):
        self.logo_frame = tk.Frame(self.frame, background="#ffffff")
        self.logo1 = tk.Label(master=self.logo_frame, text="Honeywell", font=('Helvetica', 32),
                              background="#ffffff", justify='center', fg='red')
        self.logo2 = tk.Label(master=self.logo_frame, text="| Test Automater", font=('Helvetica', 32),
                              background="#ffffff", justify='center')
        self.logo1.grid(row=0, column=0)
        self.logo2.grid(row=0, column=1)

        self.panel_frame = tk.Frame(self.frame, background="#ffffff")
        self.Automater_GUI = Automater_GUI(self.panel_frame, self)

        self.logo_frame.grid(row=0, column=0, sticky=tk.NW)
        self.panel_frame.grid(row=1, column=0, sticky=tk.NW)


class Automater_GUI:
    def __init__(self, parent, t_app):
        self.fonts = User_Fonts()
        self.parent = parent
        self.app = t_app
        self.monitor_message = None

        self.pump = None
        self.scale = None
        self.connected_scale = False
        self.connected_pump = False
        self.connected_sensor = False
        self.test_started = False
        self.starting_first_time = True
        self.timer_ticks = 0

        self.current_test = None
        self.test_list = []
        self.test_index = 0

        self.log_path = None
        self.portinfo = getOpenPorts()
        self.data_handler = None
        self.sensor_serial_handler = None
        self.mav_stream_type_dictionary = {
            'Raw Data': SENSOR_DATA_TYPE_RAW,
            'Corrected Data': SENSOR_DATA_TYPE_FLOW,
            'Both Data': SENSOR_DATA_TYPE_BOTH,
        }

        self.state_list = [
            State(name='idle', on_enter=[], on_exit=[]),
            State(name='testing', on_enter=[], on_exit=[]),
            State(name='paused', on_enter=[], on_exit=[]),
            State(name='preparing', on_enter=[], on_exit=[]),
            State(name='initialized', on_enter=[], on_exit=[])
        ]

        self.transition_list = [
            {'trigger': 'trig_prep_test', 'source': ['initialized', 'paused', 'testing'], 'dest': 'preparing',
             'after': 'prep_test'},
            {'trigger': 'trig_start_testing', 'source': 'preparing', 'dest': 'testing', 'after': 'start_testing'},
            {'trigger': 'trig_end_tests', 'source': '*', 'dest': 'idle', 'after': 'end_tests'},
            {'trigger': 'trig_initialize_tests', 'source': 'idle', 'dest': 'initialized', 'after': 'initialize_testing'}
        ]

        self.state_machine = Machine(model=self, states=self.state_list, transitions=self.transition_list,
                                     initial='idle')

        self.create()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pump:
            self.pump.ser.close()
        if self.scale:
            self.scale.ser.close()
        if self.sensor_serial_handler:
            self.sensor_serial_handler.close_connection()

    def create(self):

        # sets up and places the major modules
        self.setup_panel = Module(self.parent, 'Test Setup', 480, 690, 'red')
        self.monitor_panel = Module(self.parent, 'Test Monitor', 680, 690, 'red')
        self.connections_panel = Module(self.parent, 'Connections', 300, 690, 'red')

        self.setup_panel.grid(row=0, column=0, sticky=tk.NW, padx=(10, 10))
        self.monitor_panel.grid(row=0, column=1, sticky=tk.S, padx=(10, 10))
        self.connections_panel.grid(row=0, column=2, sticky=tk.NE, padx=(10, 10))

        # TEST SETUP MODULE

        # test add module
        self.test_add_panel = Module(self.setup_panel, 'Add tests', 450, 220)
        self.indv_test_label = Text_Box(self.test_add_panel, "Add a single test:", underline=True)
        self.indv_test_flow = Text_Input(self.test_add_panel, "Flow", t_width=20)
        self.indv_test_time = Text_Input(self.test_add_panel, "Time", t_width=20)
        self.pb_add_indv_test = Push_Button(self.test_add_panel, "Add", self.add_indv_test)
        self.series_test_label = Text_Box(self.test_add_panel, "Add a test series:", underline=True)
        self.series_start_flow = Text_Input(self.test_add_panel, "Initial Flow", t_width=10)
        self.series_end_flow = Text_Input(self.test_add_panel, "Final Flow", t_width=10)
        self.series_step_flow = Text_Input(self.test_add_panel, "Flow Step", t_width=10)
        self.series_test_time = Text_Input(self.test_add_panel, "Time", t_width=10)
        self.pb_add_test_series = Push_Button(self.test_add_panel, "Add", self.add_test_series)
        self.adding_info_label = Text_Box(self.test_add_panel,
                                          "All Flow inputs are in ml/hr and\nall Time inputs are in minutes")
        self.pb_clear_tests = Push_Button(self.test_add_panel, "Clear All", self.clear_tests)

        Y = 5
        self.indv_test_label.place(x=10, y=Y)
        Y += 20
        self.indv_test_flow.place(X=10, Y=Y)
        self.indv_test_time.place(X=150, Y=Y)
        self.pb_add_indv_test.place(X=340, Y=Y + 10)
        Y += 50
        self.series_test_label.place(x=10, y=Y)
        Y += 20
        self.series_start_flow.place(X=10, Y=Y)
        self.series_end_flow.place(X=90, Y=Y)
        self.series_step_flow.place(X=170, Y=Y)
        self.series_test_time.place(X=250, Y=Y)
        self.pb_add_test_series.place(X=340, Y=Y + 10)
        Y += 50
        self.adding_info_label.place(x=60, y=Y)
        self.pb_clear_tests.place(X=340, Y=Y + 10)

        # test queue module
        self.test_queue_panel = Module(self.setup_panel, 'Test Queue', 450, 410)
        self.queue_box = Text_Box(self.test_queue_panel, text="")
        self.update_queue()

        self.queue_box.place(x=10, y=10)

        # places modules in the test setup module
        self.test_add_panel.place(x=10, y=10)
        self.test_queue_panel.place(x=10, y=240)

        # TEST MONITOR MODULE
        self.overview_panel = Module(self.monitor_panel, 'Current Test Overview', 650, 150)
        self.save_fig_pb = Push_Button(self.overview_panel, "Save Plot", self.save_plot)
        self.autoscale_pb = Push_Button(self.overview_panel, "Autoscale", self.autoscale_plot)
        self.average_monitor = Text_Box(self.overview_panel, "functional")
        self.error_monitor = Text_Box(self.overview_panel, "")

        self.autoscale_pb.place(X=550, Y=20)
        self.save_fig_pb.place(X=550, Y=70)
        self.average_monitor.place(x=10, y=10)
        self.error_monitor.place(x=250, y=10)

        self.update_test_overview()

        self.overview_panel.place(x=10, y=510)

        # CONNECTIONS MODULE

        # connect flow sensor module
        self.sensor_connect_panel = Module(self.connections_panel, 'Flow Sensor', 280, 170)
        self.cb_sensor_com = Combo_Box(self.sensor_connect_panel, 'COM Port', self.portinfo)
        self.pb_connect_sensor = Push_Button(self.sensor_connect_panel, 'Connect', self.connect_sensor)
        self.ic_sensor_status = Indicator(self.sensor_connect_panel, 'Connection Status', 'Connected', 'Not Connected')

        self.cb_sensor_com.place(10, 10)
        self.pb_connect_sensor.place(10, 65)
        self.ic_sensor_status.place(10, 95)

        # connect pump module
        self.pump_connect_panel = Module(self.connections_panel, 'Syringe Pump', 280, 170)
        self.cb_fc_com = Combo_Box(self.pump_connect_panel, 'COM port/Serial Number', self.portinfo)
        self.pb_connect_pump = Push_Button(self.pump_connect_panel, 'Connect', self.connect_pump)
        self.ic_pump_status = Indicator(self.pump_connect_panel, 'Connection Status', 'Connected', 'Not Connected')

        self.cb_fc_com.place(10, 10)
        self.pb_connect_pump.place(10, 65)
        self.ic_pump_status.place(10, 95)

        # connect scale module
        self.scale_connect_panel = Module(self.connections_panel, 'Scale', 280, 170)
        self.cb_scale_com = Combo_Box(self.scale_connect_panel, 'COM port', self.portinfo)
        self.pb_connect_scale = Push_Button(self.scale_connect_panel, 'Connect', self.connect_scale)
        self.ic_scale_status = Indicator(self.scale_connect_panel, 'Connection Status', 'Connected', 'Not Connected')

        self.cb_scale_com.place(10, 10)
        self.pb_connect_scale.place(10, 65)
        self.ic_scale_status.place(10, 95)

        y = 10
        self.sensor_connect_panel.place(x=10, y=y)
        y += 180
        self.pump_connect_panel.place(x=10, y=y)
        y += 180
        self.scale_connect_panel.place(x=10, y=y)

        # test status buttons
        self.pb_start_tests = Push_Button(self.connections_panel, "Start Tests", self.trig_initialize_tests)
        self.pb_stop_tests = Push_Button(self.connections_panel, "Stop Tests", self.trig_end_tests)
        self.ti_log_dir = Text_Input(self.connections_panel, "Log Name", t_width=12)
        self.pb_pause_tests = Push_Button(self.connections_panel, "Pause", self.pause_resume_event)

        self.ti_log_dir.place(X=150, Y=545)
        self.pb_pause_tests.place(X=150, Y=600)
        self.pb_start_tests.place(X=50, Y=560)
        self.pb_stop_tests.place(X=50, Y=600)

        # TODO remove when done testing
        self.indv_test_time.set(".1")
        self.indv_test_flow.set("10")

        # TODO remove this at the end of testing
        self.cb_sensor_com.set_index(0)
        self.cb_fc_com.set_index(1)
        self.cb_scale_com.set_index(2)
        self.connect_pump()
        self.connect_sensor()
        self.connect_scale()
        for x in range(3):
            self.add_indv_test()
        self.ti_log_dir.set("LogTest")

        """
            \--------------\
        |===]      |||||||||}====
            /--------------/
        """

    def initialize_testing(self):
        if self.make_log_folders():
            assert (self.connected_pump and self.connected_sensor and self.connected_scale), "All devices must be connected before running!"
            self.scale.openConnection()
            self.pump.openConnection()
            self.pump.setScale(self.scale)

            cumulative_fields = ["pump flow rate (ml/hr)", "test time (min)", "% error on pump", "% error on scale"]
            self.cumulative_logger = CSV_Data_Logger(self.log_path + r"\cumulative_data", 100000, cumulative_fields)

            self.update_test_monitor_message("Preparing First Test")
            self.trig_prep_test()

    def prep_test(self):

        priming_time = 5 #the amount of time in seconds that the pump is primed for

        # prepares the test and gets the starting weight once the pump is prepared
        self.pump.prep_test(self.test_list[self.test_index].flow, self.test_list[self.test_index].time,
                            priming_time=priming_time)
        self.test_list[self.test_index].start_weight = self.scale.getWeight()


        self.app.after(priming_time * 1000, self.trig_start_testing)

    def start_testing(self):

        # clears the monitor message so that it does not interfere with the plot
        self.update_test_monitor_message()

        # starts the pump are error calculations in a separate thread to avoid stalling the main thread
        self.pump_thread = threading.Thread(target=self.pump.run_test,
                                            args=(
                                                self.test_list[self.test_index].flow,
                                                self.test_list[self.test_index].time),
                                            daemon=True)
        self.error_thread = threading.Thread(target=self.error_calculator, daemon=True)

        self.pump_thread.start()

        # MavLink and data handler stuff. This is what gets data from the sensor (very confusing, written by like 6
        # different people).
        self.sampling_freq = 1000  # the frequency at which flow data is collected
        log_location = r"../Result_Logs/" + self.ti_log_dir.get() + r"/individual_tests/" + self.test_list[
            self.test_index].getFileName()
        self.data_handler = Monitor_Test_Data_Handler(self.monitor_panel, log_location, self.sampling_freq, 5)
        self.mavlink_handler = MAVLink_Handler(self.sensor_serial_handler, 1, 2, self.data_handler)
        self.mavlink_handler.mavlink.configure_sensirion_data_stream_send(True)  # enables the request for Vrt
        self.mavlink_handler.mavlink.configure_data_stream_send(
            self.mav_stream_type_dictionary['Both Data'], self.sampling_freq)
        self.data_handler.capture_timestamp_for_data_logging_about_to_start()

        self.error_thread.start()

        # begins the process that updates the plot and records data
        self.timer_interrupt_handler()

    def end_tests(self):
        self.mavlink_handler.mavlink.configure_data_stream_send(self.mav_stream_type_dictionary['Both Data'], 0)
        time.sleep(1)
        self.mavlink_handler.parse_received_data()
        self.data_handler.close_files()
        self.cumulative_logger.close_csv()

        self.test_index = 0

    def record_results(self):

        # calculates and records data at the end of each individual test
        end_weight = self.scale.getWeight()
        sensor_flow_average = float(self.data_handler.test_packet['reg_avg'])
        pump_error = self.test_list[self.test_index].calculate_pump_error(sensor_flow_average)
        scale_error = self.test_list[self.test_index].calculate_scale_error(sensor_flow_average, end_weight,
                                                                            self.test_list[self.test_index].time)
        cumulative_data = [self.test_list[self.test_index].flow, self.test_list[self.test_index].time,
                           sensor_flow_average, pump_error, scale_error]
        self.cumulative_logger.write_row(cumulative_data)

        # marks the recorded test as complete
        self.test_list[self.test_index].mark_complete()
        self.update_queue()

        # Determines whether or not there are more tests to complete
        if self.test_index < len(self.test_list) - 1:
            self.test_index += 1
            self.update_test_monitor_message("Preparing Next Test...")
            self.trig_prep_test()
        else:
            self.update_test_monitor_message("Tests Complete!")
            self.trig_end_tests()

    def timer_interrupt_handler(self):
        if self.state == 'testing':
            if self.pump_thread.is_alive():  # if the pump is still running, keep the test running

                self.mavlink_handler.parse_received_data()
                self.data_handler.update_plot()
                self.update_test_overview()

                """
                weight = self.scale.getWeight()
                print(self.test_list[self.test_index].calculate_scale_flow(weight, float(self.data_handler.clock.get_elapsed_milli_sec()) / 1000 / 60))
                """

                self.app.after(100, self.timer_interrupt_handler)
            else:  # if the pump stops, end the current test

                # Stops the mavlink and data handler
                self.mavlink_handler.mavlink.configure_data_stream_send(self.mav_stream_type_dictionary['Both Data'], 0)
                time.sleep(1)
                self.mavlink_handler.parse_received_data()
                self.data_handler.close_files()

                # TODO raise wait time for recording weight
                # waits for the scale to settle before recording results
                self.update_test_monitor_message("Recording Test Data...")
                self.app.after(3000, self.record_results)

        if self.state == 'preparing':
            pass
        if self.state == 'paused':
            pass
        if self.state == 'idle':
            # clears the graph
            self.update_test_monitor_message()

    def error_calculator(self):
        if self.pump_thread.is_alive():
            sensed_flow = float(self.data_handler.test_packet['reg_avg'])
            weight = self.scale.getWeight()

            self.test_list[self.test_index].calculate_pump_error(sensed_flow)
            self.test_list[self.test_index].calculate_scale_error(sensed_flow, weight, self.data_handler.clock.get_elapsed_milli_sec() / 1000 / 60)

            self.app.after(2000, self.error_calculator)


    # TEST SETUP FUNCTIONS

    """Adds a test to the Queue. Flow is ml/hr and time is minutes"""

    def add_test(self, flow, time):
        test_to_add = Test(flow, time)
        count = 0

        for test in self.test_list:  # checks to see if the test is a repeat of any previously added tests
            if test == test_to_add:
                count += 1

        self.test_list.append(Test(flow, time, duplicate=count))
        self.update_queue()

    def add_indv_test(self):
        flow = float(self.indv_test_flow.get())
        time = float(self.indv_test_time.get())

        self.add_test(flow, time)

    def add_test_series(self):
        flow_step = float(self.series_step_flow.get())
        flow_start = float(self.series_start_flow.get())
        flow_end = float(self.series_end_flow.get())
        time = float(self.series_test_time.get())

        for flow in np.arange(flow_start, flow_end + 0.00001, flow_step):
            self.add_test(flow, time)

    def clear_tests(self):
        self.test_list = []
        self.update_queue()

    def update_queue(self):
        text = ""

        if len(self.test_list) > 0:
            num = 1
            for test in self.test_list:
                min = int(test.time)
                sec = int((test.time % 1) * 60)
                text += "Test {:d} - ".format(num) + str(test) + "\n"
                num += 1
        else:
            text = "No Tests"

        self.queue_box["text"] = text

    # TEST MONITOR FUNCTIONS

    def update_test_monitor_message(self, message=None):
        # clears the monitor panel
        for child in self.monitor_panel.children.keys():
            if child.__contains__('!canvas'): #checks if the child is a graph
                self.monitor_panel.children[child].destroy()
                break
        if self.monitor_message:
            self.monitor_message.destroy()
            self.monitor_message = None
            self.monitor_panel.update()

        # adds a message in the monitor panel
        if message:
            self.monitor_message = Text_Box(self.monitor_panel, message)
            self.monitor_message.place(x=225, y=225)

    def update_test_overview(self):
        if self.data_handler:  # TODO alter to a state machine conditional
            # Acquires various overall test statistics from the data handler
            packet = self.data_handler.test_packet

            # formats the data received from the packet
            average_monitor_text = "TIME: " + packet["time"] + "\n" + "Average: " + packet[
                "reg_avg"] + " ml/hr\n" + "Standard Deviation: " + packet[
                       "reg_stdev"] + " ml\n" + "Average (Past " + str(packet["x"]) + "s): " + packet[
                       "avg_x"] + " ml/hr\n" + "Standard Deviation (Past " + str(packet["x"]) + "s): " + packet[
                       "stdev_x"] + "ml"

            current_test = self.test_list[self.test_index]
            error_monitor_text = "Pump Error: {}%\n Scale Error: {}%\n".format(current_test.pump_error, current_test.scale_error)

            # updates the monitor
            self.average_monitor["text"] = average_monitor_text
            self.error_monitor["text"] = error_monitor_text

        else:
            self.average_monitor["text"] = "\n\n                                                     No Test is running"
            self.error_monitor["text"] = ""

    def autoscale_plot(self):
        if (len(self.data_handler.reg_pts) > 5000):
            pts = self.data_handler.reg_pts[-5000:]
        else:
            pts = self.data_handler.reg_pts

        y_min = min(pts)
        y_max = max(pts)
        y_delta = y_max - y_min
        y_min = y_min - 0.25 * y_delta
        y_max = y_max + 0.25 * y_delta
        self.data_handler.graph.set_axes_limits(0, 0, y_min, y_max)

    def save_plot(self):

        # Acquires the file location from the user
        filetypes = (
            ('png files', '*.png'),
            ('All files', '*.*'))

        file_location = fd.asksaveasfilename(
            initialdir="/",
            title="Choose a photo location",
            filetypes=filetypes)

        # saves the photo if the file prompt was not cancelled
        if len(file_location) > 0:
            self.data_handler.graph.figure.savefig(file_location)

    # CONNECTION PANEL FUNCTIONS

    def connect_sensor(self):
        if not self.connected_sensor:
            try:
                self.sensor_serial_handler = Serial_Handler(str(self.cb_sensor_com.get_value()))
            except TypeError as e:
                return

            self.connected_sensor = True
            self.ic_sensor_status.make_true()
            self.pb_connect_sensor.set_title("Disconnect")

        else:
            self.sensor_serial_handler.close_connection()
            self.connected_sensor = False
            self.ic_sensor_status.make_false()
            self.pb_connect_sensor.set_title("Connect")

    def connect_pump(self):
        if not self.connected_pump:
            self.pump = Connection_one(self.cb_fc_com.get_value(), 9600)  # self.cb_fc_com.get_value()

            self.connected_pump = True
            self.ic_pump_status.make_true()
            self.pb_connect_pump.set_title("Disconnect")

        else:
            self.pump.closeConnection()
            self.connected_sensor = False
            self.ic_sensor_status.make_false()
            self.pb_connect_pump.set_title("Connect")

    def connect_scale(self):
        if not self.connected_scale:
            self.scale = scale(self.cb_scale_com.get_value(), 9600, verbose=False)

            self.connected_scale = True
            self.ic_scale_status.make_true()
            self.pb_connect_scale.set_title("Disconnect")

        else:
            self.scale.closeConnection()
            self.connected_scale = False
            self.ic_scale_status.make_false()
            self.pb_connect_scale.set_title("Connect")


    def make_log_folders(self):
        log_name = self.ti_log_dir.get()
        log_path = r"..\Result_Logs\{}".format(log_name)
        log_indiv_tests_path = log_path + r"\individual_tests"

        if len(log_name) == 0:  # the test should not continue if there is no log name
            tk.messagebox.showwarning(message="Log Name is required")
            return False

        if os.path.exists(log_path):
            if not tkinter.messagebox.askyesno(message="There is already a log file with this name. Overwrite?"):
                return False  # indicates the test should not continue
            else:
                shutil.rmtree(log_path)  # deletes the directory that is currently in the path

        # creates a directory at the path
        os.mkdir(log_path)
        os.mkdir(log_indiv_tests_path)
        self.log_path = log_path
        return True  # indicates the test should continue

    def pause_resume_event(self):  # TODO Implement pause/resume functionality
        pass
