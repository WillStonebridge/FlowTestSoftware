"""
Frames.py -

To Change flow controllers comment one of the following:

from flow_controllerPhd import *
from flow_controllerPolo import 
"""
import subprocess
import time
from tkinter import filedialog as fd
from tkinter.constants import BOTTOM, RIGHT

import openpyxl
from PIL import ImageTk, Image
from transitions import Machine, State

from Widget import *
from convert_csv_excel import create_matlab_input_file
# from flow_controllerPhd import *
from flow_controllerPolo import *
from mavlink_interface import *
from plot import *
from test_config import *


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
        self.logo = Logo_Title(self.logo_frame)
        self.panel_frame = tk.Frame(self.frame, background="#ffffff")
        self.input_panel = Input_Panel(self.panel_frame, self)

        self.logo_frame.grid(row=0, column=0, sticky=tk.NW)
        self.panel_frame.grid(row=1, column=0, sticky=tk.NW)


class Input_Panel:
    def __init__(self, parent, t_app):

        self.fonts = User_Fonts()
        self.parent = parent
        self.app = t_app

        self.portinfo = getOpenPorts()

        self.connected_flow_controller = False
        self.connected_sensor = False
        self.test_started = False
        self.starting_first_time = True
        self.timer_ticks = 0
        self.calibration_filename = None
        self.average_monitor = None

        self.log_file = 'Data files'

        self.mav_stream_type_dictionary = {
            'Raw Data': SENSOR_DATA_TYPE_RAW,
            'Corrected Data': SENSOR_DATA_TYPE_FLOW,
            'Both Data': SENSOR_DATA_TYPE_BOTH,
        }

        self.create()

        self.state_list = [
            State(name='idle', on_enter=[], on_exit=[]),
            State(name='run_monitor_test', on_enter=['callback_on_enter_run_monitor_test'],
                  on_exit=['callback_on_exit_run_monitor_test']),
            State(name='run_char_test', on_enter=[], on_exit=[]),
            State(name='pause_char_test', on_enter=[], on_exit=[]),
        ]

        self.transition_list = [
            {'trigger': 'start_monitor_test', 'source': 'idle', 'dest': 'run_monitor_test'},
            {'trigger': 'stop_monitor_test', 'source': 'run_monitor_test', 'dest': 'idle'},
            {'trigger': 'start_char_test', 'source': 'idle', 'dest': 'run_char_test',
             'after': 'callback_on_enter_run_char_test'},
            {'trigger': 'stop_char_test', 'source': ['run_char_test',
                                                     'pause_char_test'], 'dest': 'idle',
             'after': 'callback_on_exit_run_char_test'},
            {'trigger': 'pause_char_test', 'source': 'run_char_test', 'dest': 'pause_char_test',
             'after': 'callback_on_enter_pause_char_test'},
            {'trigger': 'resume_char_test', 'source': 'pause_char_test', 'dest': 'run_char_test',
             'after': 'callback_on_exit_pause_char_test'}
        ]

        self.state_machine = Machine(model=self, states=self.state_list, transitions=self.transition_list,
                                     initial='idle')

    def create(self):
        self.input_panel = Module(self.parent, 'Input Panel', 500, 690, 'red')
        self.test_panel = Module(self.parent, 'Test Control', 750, 150, 'red')
        self.flow_panel = Module(self.parent, 'Flow Control Panel', 300, 690, 'red')

        self.input_panel.grid(row=0, column=0, sticky=tk.NW, padx=(15, 15), rowspan=2)
        # self.test_panel.grid(row=1, column=1, sticky=tk.S, padx=(15,15), rowspan=1)
        self.flow_panel.grid(row=0, column=2, sticky=tk.NE, padx=(15, 15), rowspan=2)

        self.sensor_detail = Module(self.input_panel, 'Liquid Flow Sensor', 280, 170)
        self.cb_sensor_com = Combo_Box(self.sensor_detail, 'COM Port', self.portinfo)
        self.pb_log_dir = tk.Button(self.sensor_detail, text="Log File Location", command=self.select_log_file)
        self.pb_detect = Push_Button(self.sensor_detail, 'Connect', self.callback_control_detect)
        self.ic_sensor_status = Indicator(self.sensor_detail, 'Connection Status', 'Connected', 'Not Connected')

        self.cb_sensor_com.place(10, 10)
        self.pb_detect.place(10, 65)
        self.pb_log_dir.place(x=100, y=65)
        self.ic_sensor_status.place(10, 95)

        self.test_control = Module(self.input_panel, 'Monitor Test Control', 280, 275)
        self.cb_sensor_data_type = Combo_Box(self.test_control, 'Sensor Data Type',
                                             ['Raw Data', 'Corrected Data', 'Both Data'], self.callback_cb_sensor_type)
        self.ti_sensor_data_freq = Text_Input(self.test_control, 'Sensor Data frequency [0-1000]')
        self.chb_sensirion_enable = Check_Button(self.test_control, 'LD20 Data')
        self.chb_heater_control_data_enable = Check_Button(self.test_control, 'Heater Control Data')
        self.pb_start_test = Push_Button(self.test_control, 'Start Test', self.callback_control_start_test)
        self.pb_stop_test = Push_Button(self.test_control, 'Stop Test', self.callback_control_stop_test)
        self.ic_test_status = Indicator(self.test_control, 'Test Status', 'Running', 'Stopped')

        x = 10
        self.cb_sensor_data_type.place(10, x)
        x = x + 50
        self.ti_sensor_data_freq.place(10, x)
        x = x + 50
        self.chb_sensirion_enable.place(10, x)
        self.chb_heater_control_data_enable.place(100, x)
        x = x + 30
        self.pb_start_test.place(10, x)
        x = x + 30
        self.pb_stop_test.place(10, x)
        x = x + 30
        self.ic_test_status.place(10, x)

        self.char_test_control = Module(self.input_panel, 'Char Test Control', 180, 330)
        self.pb_char_start_test = Push_Button(self.char_test_control, 'Start Test',
                                              self.callback_control_char_start_test)
        self.pb_char_stop_test = Push_Button(self.char_test_control, 'Stop Test', self.callback_control_char_stop_test)
        self.pb_char_pause_test = Push_Button(self.char_test_control, 'Pause Test',
                                              self.callback_control_char_pause_test)
        self.pb_char_resume_test = Push_Button(self.char_test_control, 'Resume Test',
                                               self.callback_control_char_resume_test)
        self.ic_char_test_status = Indicator(self.char_test_control, 'Test Status', 'Running', 'Stopped')
        self.id_char_test_stage = Indicator(self.char_test_control, 'Test Stage', 'Running', 'Stopped', 'Light Grey',
                                            20, 3, tk.NW)

        x = 10
        self.pb_char_start_test.place(10, x)
        x = x + 30
        self.pb_char_stop_test.place(10, x)
        x = x + 40
        self.pb_char_pause_test.place(10, x)
        x = x + 30
        self.pb_char_resume_test.place(10, x)
        x = x + 30
        self.ic_char_test_status.place(10, x)
        x = x + 50
        self.id_char_test_stage.place(10, x)

        self.flow_comms = Module(self.input_panel, 'Flow Controller', 280, 170)
        self.portinfo.append('00363558')
        self.cb_fc_com = Combo_Box(self.flow_comms, 'COM port/Serial Number', self.portinfo)
        self.pb_connect = Push_Button(self.flow_comms, 'Connect', self.callback_control_connect)
        self.ic_fc_status = Indicator(self.flow_comms, 'Connection Status', 'Connected', 'Not Connected')

        self.cb_fc_com.place(10, 10)
        self.pb_connect.place(10, 65)
        self.ic_fc_status.place(10, 95)
        self.cb_sensor_data_type.set_index(2)
        self.ti_sensor_data_freq.set("50")

        self.fram_control = Module(self.input_panel, 'Fram Test Control', 180, 275)
        self.pb_coeffs_create = Push_Button(self.fram_control, 'Create Coeffs', self.callback_fram_create_coeffs)
        self.pb_write_coeffs_fram = Push_Button(self.fram_control, 'Write Coeffs', self.callback_fram_write_coeffs)
        self.pb_read_coeffs_fram = Push_Button(self.fram_control, 'Read Coeffs', self.callback_fram_read_coeffs)
        self.ti_serial_number = Text_Input(self.fram_control, 'Serial Number', 18, 15)

        x = 10
        self.pb_coeffs_create.place(10, x)
        x = x + 40
        self.pb_write_coeffs_fram.place(10, x)
        x = x + 40
        self.pb_read_coeffs_fram.place(10, x)
        x = x + 40
        self.ti_serial_number.place(10, x)

        self.sensor_detail.place(x=10, y=10)
        self.flow_comms.place(x=10, y=190)
        self.test_control.place(x=10, y=370)
        self.char_test_control.place(x=300, y=10)
        self.fram_control.place(x=300, y=370)

        self.syringe_pump1 = Flow_Controller(self.flow_panel, 'Syringe Pump 1', 1)
        self.syringe_pump2 = Flow_Controller(self.flow_panel, 'Syringe Pump 2', 1)
        self.data_smoothing = Data_Smoothing(self.flow_panel, 'Data Smoothing')

        self.syringe_pump1.module.place(x=10, y=10)
        self.data_smoothing.module.place(x=10, y=330)
        # self.syringe_pump2.module.place(x = 10, y = 330)

    def callback_on_enter_run_monitor_test(self):
        self.sampling_freq = int(self.ti_sensor_data_freq.get())
        if self.sampling_freq > 1000:
            self.sampling_freq = 1000

        elif self.sampling_freq < 0:
            self.sampling_freq = 0

        self.data_handler = Monitor_Test_Data_Handler(self.parent, self.log_file, self.sampling_freq, 5,
                                                      self.data_smoothing.smoothing_settings)

        self.mavlink_handler = MAVLink_Handler(self.sensor_serial_handler, 1, 2, self.data_handler)

        self.ic_test_status.make_true()

        self.mavlink_handler.mavlink.configure_heater_control_data_stream_send(
            self.chb_heater_control_data_enable.get_value(), 100)
        self.mavlink_handler.mavlink.configure_sensirion_data_stream_send(self.chb_sensirion_enable.get_value())
        self.mavlink_handler.mavlink.configure_data_stream_send(
            self.mav_stream_type_dictionary[self.cb_sensor_data_type.get_value()], self.sampling_freq)

        self.data_handler.capture_timestamp_for_data_logging_about_to_start()

        self.setup_test_panel()

        self.timer_interrupt_handler()

    def callback_on_exit_run_monitor_test(self):
        self.mavlink_handler.mavlink.configure_data_stream_send(self.mav_stream_type_dictionary['Both Data'], 0)
        time.sleep(1)
        self.mavlink_handler.parse_received_data()
        self.data_handler.close_files()
        self.ic_test_status.make_false()

    def callback_on_enter_run_char_test(self):
        self.char_test_specs = Test_Spec_TypeDef("test_specs.txt")

        self.test_count = 0
        self.current_temp_point = 0
        self.current_flow_point = 0

        self.sampling_freq = self.char_test_specs.sampling_frequency
        if self.sampling_freq > 1000:
            self.sampling_freq = 1000

        elif self.sampling_freq < 0:
            self.sampling_freq = 0

        self.stop_pump_at_ticks = 0
        self.timer_ticks = 1
        self.previous_flow_rate = self.char_test_specs.flow_points[self.current_flow_point]
        self.initial_warm_up_run_at_first_cycle = 1
        self.is_warm_up_flow_in_progress = 0

        folder_name = "Data files\\Char Test Data"
        self.data_handler = Char_Test_Data_Handler(self.parent, folder_name, self.sampling_freq,
                                                   self.char_test_specs.flow_settling_time,
                                                   self.char_test_specs.flow_capture_time,
                                                   self.char_test_specs.flow_points,
                                                   self.char_test_specs.log_discrete_data)

        self.data_handler.update_new_temp_point(self.char_test_specs.temperature_points[self.current_temp_point])
        self.data_handler.update_test_count(self.test_count)

        if self.char_test_specs.syringe_pump == 1:
            self.ref_char_test_syringe_pump = self.syringe_pump1
        else:
            self.ref_char_test_syringe_pump = self.syringe_pump2

        self.ref_char_test_syringe_pump.update_syringe_inner_dia(self.char_test_specs.syringe_inner_dia)
        self.ref_char_test_syringe_pump.update_flow_rate_unit('mL/hr')

        self.status_string_flow = "Flow \t" + str(
            self.char_test_specs.flow_points[self.current_flow_point]) + "\t" + str(
            self.current_flow_point + 1) + "\\" + str(self.char_test_specs.flow_points_count) + "\n"
        self.status_string_test = "Test \t" + str(self.test_count + 1) + "\t" + str(self.test_count + 1) + "\\" + str(
            self.char_test_specs.numbers_of_test)
        self.status_string_temp = "Temp \t" + str(
            self.char_test_specs.temperature_points[self.current_temp_point]) + "\t" + str(
            self.current_temp_point + 1) + "\\" + str(self.char_test_specs.temperature_points_count) + "\n"
        self.id_char_test_stage.write_value(self.status_string_flow + self.status_string_temp + self.status_string_test)

        self.ic_char_test_status.make_true()

        self.mavlink_handler = MAVLink_Handler(self.sensor_serial_handler, 1, 2, self.data_handler)
        if self.char_test_specs.ld20_data != 0:
            self.mavlink_handler.mavlink.configure_sensirion_data_stream_send(1)

        if self.char_test_specs.heater_control_data != 0:
            self.mavlink_handler.mavlink.configure_heater_control_data_stream_send(1, 100)

        self.mavlink_handler.mavlink.configure_data_stream_send(self.mav_stream_type_dictionary['Both Data'],
                                                                self.sampling_freq)
        self.data_handler.capture_timestamp_for_data_logging_about_to_start()
        self.timer_interrupt_handler()

    def callback_on_exit_run_char_test(self):
        self.mavlink_handler.mavlink.configure_data_stream_send(self.mav_stream_type_dictionary['Both Data'], 0)
        self.data_handler.close_files()
        self.update_pump_flow_rate_volume(0, 15)
        self.ic_char_test_status.make_false()
        max_flow = max(self.char_test_specs.flow_points)
        print(max_flow, type(max_flow))
        self.calibration_filename = self.data_handler.char_data_file_name
        create_matlab_input_file(self.ti_serial_number.get(), self.calibration_filename,
                                 self.char_test_specs.flow_points_count, max_flow)

    def callback_on_enter_pause_char_test(self):
        self.data_handler.hault_test()
        self.update_pump_flow_rate_volume(0, 15)
        self.ic_char_test_status.write_value_bg('Paused', 'orange')
        pass

    def callback_on_exit_pause_char_test(self):
        self.current_flow_point -= 1
        self.update_pump_flow_rate_volume(self.char_test_specs.flow_points[self.current_flow_point], 15)
        self.ic_char_test_status.make_true()

        self.mavlink_handler.parse_received_data()
        self.data_handler.update_new_flow_point(self.char_test_specs.flow_points[self.current_flow_point])
        self.current_flow_point += 1
        pass

    def timer_interrupt_handler(self):
        if self.state == 'run_monitor_test':
            self.mavlink_handler.parse_received_data()
            self.data_handler.update_plot()
            self.update_average_monitor()
            self.app.after(100, self.timer_interrupt_handler)

        elif self.state == 'run_char_test':
            self.mavlink_handler.parse_received_data()

            if self.current_flow_point <= self.char_test_specs.flow_points_count:
                if self.data_handler.is_one_point_completed() == 1:
                    if self.current_flow_point < self.char_test_specs.flow_points_count:
                        self.status_string_flow = "Flow \t" + str(
                            self.char_test_specs.flow_points[self.current_flow_point]) + "\t" + str(
                            self.current_flow_point + 1) + "\\" + str(self.char_test_specs.flow_points_count) + "\n"
                        self.id_char_test_stage.write_value(
                            self.status_string_flow + self.status_string_temp + self.status_string_test)

                        self.update_pump_flow_rate_volume(self.char_test_specs.flow_points[self.current_flow_point], 15)
                        self.mavlink_handler.parse_received_data()
                        self.data_handler.update_new_flow_point(
                            self.char_test_specs.flow_points[self.current_flow_point])

                        if self.current_flow_point == 0:
                            if (self.char_test_specs.initial_warm_up_run_flow_duration != 0) and (
                                    self.initial_warm_up_run_at_first_cycle != 0):
                                self.is_warm_up_flow_in_progress = 1
                                self.pause_char_test()
                                self.update_pump_flow_rate_volume(self.char_test_specs.initial_warm_up_run_flow_rate,
                                                                  15)
                                self.stop_pump_at_ticks = int(
                                    time.time()) + self.char_test_specs.initial_warm_up_run_flow_duration
                                self.initial_warm_up_run_at_first_cycle = self.char_test_specs.initial_warm_up_run_at_each_cycle

                        else:
                            if (self.previous_flow_rate == 0):
                                if (self.char_test_specs.flow_direction_change_warm_up_run_flow_duration != 0):
                                    self.is_warm_up_flow_in_progress = 1
                                    self.pause_char_test()
                                    self.update_pump_flow_rate_volume(
                                        self.char_test_specs.flow_direction_change_warm_up_run_flow_rate, 15)
                                    self.stop_pump_at_ticks = time.time() + self.char_test_specs.flow_direction_change_warm_up_run_flow_duration

                        self.previous_flow_rate = self.char_test_specs.flow_points[self.current_flow_point]
                    self.current_flow_point += 1

            else:
                self.current_temp_point += 1

                if self.current_temp_point < self.char_test_specs.temperature_points_count:
                    self.data_handler.update_new_temp_point(
                        self.char_test_specs.temperature_points[self.current_temp_point])
                    self.current_flow_point = 0
                    self.status_string_temp = "Temp \t" + str(
                        self.char_test_specs.temperature_points[self.current_temp_point]) + "\t" + str(
                        self.current_temp_point + 1) + "\\" + str(self.char_test_specs.temperature_points_count) + "\n"

                else:
                    self.test_count += 1
                    self.current_temp_point = 0
                    self.current_flow_point = 0
                    self.status_string_test = "Test \t" + str(self.test_count + 1) + "\t" + str(
                        self.test_count + 1) + "\\" + str(self.char_test_specs.numbers_of_test)
                    self.status_string_temp = "Temp \t" + str(
                        self.char_test_specs.temperature_points[self.current_temp_point]) + "\t" + str(
                        self.current_temp_point + 1) + "\\" + str(self.char_test_specs.temperature_points_count) + "\n"
                    self.data_handler.update_new_temp_point(
                        self.char_test_specs.temperature_points[self.current_temp_point])

                    if self.test_count < self.char_test_specs.numbers_of_test:
                        self.data_handler.update_test_count(self.test_count)

                    else:
                        self.stop_char_test()

            self.app.after(100, self.timer_interrupt_handler)

        elif self.state == 'pause_char_test':
            self.mavlink_handler.parse_received_data()
            if self.is_warm_up_flow_in_progress != 0:
                if (int(time.time()) > self.stop_pump_at_ticks):
                    self.resume_char_test()
                    self.is_warm_up_flow_in_progress = 0
            self.app.after(100, self.timer_interrupt_handler)

    def update_pump_flow_rate_volume(self, rate, volume):
        if rate == 0:
            self.ref_char_test_syringe_pump.callback_pb_pump_stop()

        elif rate < 0:  # Fix your syringe pump driver to accept negative rates
            # self.ref_char_test_syringe_pump.update_flow_rate_volume(abs(rate), -1*abs(volume))
            self.ref_char_test_syringe_pump.update_flow_rate_volume(-1 * abs(rate), -1 * abs(volume))

        else:
            self.ref_char_test_syringe_pump.update_flow_rate_volume(abs(rate), abs(volume))

    def connect_sensor(self):
        if not self.connected_sensor:
            try:
                self.sensor_serial_handler = Serial_Handler(str(self.cb_sensor_com.get_value()))
            except TypeError as e:
                return

            self.connected_sensor = True
            self.ic_sensor_status.make_true()
            self.pb_detect.set_title("Disconnect")

        else:
            self.sensor_serial_handler.close_connection()
            self.connected_sensor = False
            self.ic_sensor_status.make_false()
            self.pb_detect.set_title("Connect")

    def connect_flow_controller(self):
        if not self.connected_flow_controller:
            self.connection_flow_controller = Connection(port=str(self.cb_fc_com.get_value()),
                                                         baudrate=9600, x=0, mode=1, verbose=False)

            try:
                self.connection_flow_controller.openConnection()
            except TypeError as e:
                return

            self.connected_flow_controller = True
            self.ic_fc_status.make_true()
            self.syringe_pump1.update_connection(self.connection_flow_controller)
            self.syringe_pump2.update_connection(self.connection_flow_controller)
            self.pb_connect.set_title("Disconnect")


        else:
            self.connection_flow_controller.closeConnection()
            self.connected_flow_controller = False
            self.ic_fc_status.make_false()
            self.pb_connect.set_title("Connect")

    def callback_control_connect(self):
        self.connect_flow_controller()

    def callback_control_detect(self):
        self.connect_sensor()

    def callback_control_start_test(self):
        self.start_monitor_test()

    def callback_control_stop_test(self):
        self.stop_monitor_test()

    def callback_control_char_start_test(self):
        self.start_char_test()

    def callback_control_char_stop_test(self):
        self.stop_char_test()

    def callback_control_char_pause_test(self):
        self.pause_char_test()

    def callback_control_char_resume_test(self):
        self.resume_char_test()

    def callback_cb_sensor_type(self, event):
        pass

    def callback_fram_create_coeffs(self):
        filetypes = (('Excel files', '*.xlsx'), ('All files', '*.*'))
        current_dir = os.getcwd()
        cal_dir = os.path.join(current_dir, "Data files\Char Test Data")
        print(cal_dir)
        matlab_exe_file = os.path.join(cal_dir, "Jims_ULF_TF_New.exe")
        if self.calibration_filename == None:
            self.calibration_filename = fd.askopenfilename(title='Open Calibration file', initialdir=cal_dir,
                                                           filetypes=filetypes)  # ('Excel Worksheets', '*.xlsx'))
            if self.calibration_filename != '':
                wb = openpyxl.load_workbook(self.calibration_filename)
                sh = wb.active
                serial_num = sh['A2']
                self.ti_serial_number.set(serial_num.value)
                self.app.update()
                wb.close()
                char_test_file = self.calibration_filename
                self.calibration_filename = None  # Started as None, stay as None
            else:
                self.calibration_filename = None  # Started as None, stay as None
                return
        elif (self.calibration_filename != None):
            char_test_file = os.path.join(current_dir, (self.calibration_filename + '__0.xlsx'))
            self.calibration_filename = None  # Started as None, stay as None
        else:
            print("No cal output file found")
            return
        char_temp_file = os.path.join(cal_dir, ('temp_cal_data' + '.xlsx'))
        if os.path.exists(char_temp_file):
            os.path.remove(char_temp_file)
        os.rename(char_test_file, char_temp_file)
        matlab_exe = subprocess.Popen([matlab_exe_file, char_temp_file],
                                      cwd=cal_dir)  # , shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  #, cwd=cal_dir)
        return_code = matlab_exe.wait()
        print("Matlab.exe Return code: ", return_code)
        os.rename(char_temp_file, char_test_file)

    def callback_fram_write_coeffs(self):
        folder_name = "Data files\Char Test Data"
        self.coeffs_handler = Coeffs_Data_Handler(self.parent, folder_name)
        self.mavlink_handler = MAVLink_Handler(self.sensor_serial_handler, 1, 2, self.coeffs_handler)
        self.mavlink_handler.mavlink.set_callback(self.mavlink_handler.mav_msg_detected_callback)
        sn = self.ti_serial_number.get()
        if not len(sn) or sn == "":
            sn = "Forgot0123456789"
        serialnum = folder_name + '\\' + sn.ljust(16, '-') + '.dat'
        print(sn)
        file = open(serialnum, "rb")
        for address in range(0, 64):
            data = list(file.read(16))
            print("".join("{:02x} ".format(x) for x in data))
            self.mavlink_handler.mavlink.write_segment_coeffs_send(address, data, force_mavlink1=False)
            time.sleep(.2)
        file.close()
        time.sleep(2)
        del self.coeffs_handler
        del self.mavlink_handler

    def callback_fram_read_coeffs(self):
        # pass
        # self.filename = str(self.cal_coeffs_filename.get())

        folder_name = "Data files"
        self.coeffs_handler = Coeffs_Data_Handler(self.parent, folder_name)
        self.mavlink_handler = MAVLink_Handler(self.sensor_serial_handler, 1, 2, self.coeffs_handler)
        self.mavlink_handler.mavlink.set_send_callback(self.mavlink_handler.mav_msg_detected_callback)
        id = 2
        self.mavlink_handler.mavlink.response_read_segment_coeffs_send(id, self.coeffs_handler.data,
                                                                       force_mavlink1=False)
        # self.ic_test_status.make_true()

    #        self.timer_interrupt_handler()

    def select_log_file(self):
        filetypes = (
            ('csv files', '*.csv'),
            ('All files', '*.*'))

        self.log_file = fd.asksaveasfilename(
            initialdir="/",
            title="Choose a log location",
            filetypes=filetypes)

        if len(self.log_file) < 1:
            self.log_file = 'Data files'


    def setup_test_panel(self):
        self.test_panel.grid(row=1, column=1, sticky=tk.S, padx=(15, 15), rowspan=1)

        self.save_fig_pb = tk.Button(self.test_panel, text="Save Plot", command=self.save_plot)
        self.average_monitor = tk.Label(self.test_panel, text="functional", font=("Helvetica", 14), background='white', justify='left')

        self.save_fig_pb.place(x=350, y=50)
        self.average_monitor.place(x=10, y=10)

        self.update_average_monitor()

    def update_average_monitor(self):
        # Acquires various overall test statistics from the data handler
        packet = self.data_handler.test_packet

        # formats the data received from the packet
        text = "TIME: " + packet["time"] + "\n" + "Actual Average: " + packet[
            "reg_avg"] + " ml/hr\n" + "SMA Average: " + packet["sma_avg"] + " ml/hr\n" + "EMA Average: " + packet[
                   "ema_avg"] + " ml/hr"

        # updates the monitor
        self.average_monitor["text"] = text

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


class Logo_Title:
    def __init__(self, app):
        self.fonts = User_Fonts()
        self.img = Image.open("images/Honeywell-Logo.png")
        self.img = self.img.resize((300, 60), Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(self.img)
        self.logo = tk.Label(app, image=self.img, bg='white')
        self.title = tk.Label(app, text='Liquid Flow Char Application', font=self.fonts.cal32, height=1, fg='black',
                              bg='white', bd=2)
        self.logo.grid(row=0, column=0, sticky=tk.W, padx=(10, 5), pady=(15, 10))
        self.title.grid(row=0, column=2, sticky=tk.W, padx=(30, 5))
        self.canvas = tk.Canvas(app, width=5, height=60, bg='black', highlightthickness=0, relief='ridge')
        self.canvas.grid(row=0, column=1, padx=5, pady=5)


class Data_Smoothing():
    def __init__(self, parent, title):
        self.smoothing_settings = {}  # A dictionary of the smoothing settings given by the user

        self.module = Module(parent, title, 280, 310)
        self.regular_waveform = Check_Button(self.module, 'Actual Waveform', val=1)
        self.sma_waveform = Check_Button(self.module, 'Simple Moving Average Waveform', val=1)
        self.ema_waveform = Check_Button(self.module, 'Exponential Moving Average Waveform', val=1)
        self.sma_k = Text_Input(self.module, "Average Window")
        self.ema_k = Text_Input(self.module, "Average Window")
        self.ema_s = Text_Input(self.module, "Smoothing Value")
        self.config_button = Push_Button(self.module, "Configure", self.configure_settings)

        x = 10
        self.regular_waveform.place(10, x)
        x += 20
        self.sma_waveform.place(10, x)
        x += 20
        self.sma_k.place(10, x)
        x += 70
        self.ema_waveform.place(10, x)
        x += 20
        self.ema_k.place(10, x)
        x += 40
        self.ema_s.place(10, x)
        x += 60
        self.config_button.place(10, x)

        self.sma_k.set("10")
        self.ema_k.set("10")
        self.ema_s.set("2")

        self.configure_settings()  # initializes the smoothing settings at startup

    def configure_settings(self):  # updates the smoothing settings
        self.smoothing_settings['reg_active'] = self.regular_waveform.get_value()

        self.smoothing_settings['sma_active'] = self.sma_waveform.get_value()
        self.smoothing_settings['sma_k'] = int(self.sma_k.get())
        self.smoothing_settings['prev_k_points'] = []

        self.smoothing_settings['ema_active'] = self.ema_waveform.get_value()
        self.smoothing_settings['ema_k'] = int(self.ema_k.get())
        self.smoothing_settings['ema_s'] = float(self.ema_s.get())
        self.smoothing_settings['previous_ema'] = None


class Flow_Controller():
    def __init__(self, parent, title, pump):
        self.pump = pump
        self.module = Module(parent, title, 280, 310)
        self.cb_syringe_dia = Combo_Box(self.module, 'Syringe Diameter [mms]',
                                        ['28.60', '26.6', '23', '20.4', '19.13', '15.9', '12.60', '9.53'])
        self.cb_flow_unit = Combo_Box(self.module, 'Flow Unit', ['mL/min', 'mL/hr', 'μL/min', 'μL/hr'])
        self.ti_flow = Text_Input(self.module, 'Flow Rate', 18, 15)
        self.ti_volume = Text_Input(self.module, 'Flow Volume', 18, 15)
        self.pb_configure = Push_Button(self.module, 'Configure', self.callback_pb_config_flow)
        self.pb_pump_start = Push_Button(self.module, 'Start', self.callback_pb_pump_start)
        self.pb_pump_stop = Push_Button(self.module, 'Stop', self.callback_pb_pump_stop)
        self.pb_pump_pause = Push_Button(self.module, 'Pause', self.callback_pb_pump_pause)
        self.pb_pump_update = Push_Button(self.module, 'Update Status', self.callback_pb_pump_update)
        self.id_status = Indicator(self.module, 'Pump Status', 'Running', 'Stopped', 'Light Grey')

        self.status_dict = {'0': 'Stopped',
                            '1': 'Running',
                            '2': 'Paused',
                            '3': 'Delayed',
                            '4': 'Stalled'
                            }

        x = 10
        self.cb_syringe_dia.place(10, x)
        x = x + 50
        self.cb_flow_unit.place(10, x)
        x = x + 50
        self.ti_flow.place(10, x)
        self.ti_volume.place(130, x)
        x = x + 50
        self.pb_configure.place(10, x)
        x = x + 30
        self.pb_pump_start.place(10, x)
        self.pb_pump_update.place(110, x)
        x = x + 30
        self.pb_pump_stop.place(10, x)
        self.id_status.place(110, x)
        x = x + 30
        self.pb_pump_pause.place(10, x)

        self.cb_flow_unit.set_index(1)
        self.ti_flow.set("100")
        self.ti_volume.set("5")
        self.cb_syringe_dia.set_index(5)

    # self.status = []

    def update_connection(self, connection):
        self.connection_flow_controller = connection

    def update_flow_rate(self, flow):
        self.callback_pb_pump_stop()
        self.connection_flow_controller.updateChannel(self.pump)
        self.connection_flow_controller.setRate(flow)
        self.callback_pb_pump_start()

    def update_flow_rate_volume(self, rate, volume):
        self.callback_pb_pump_stop()
        self.connection_flow_controller.updateChannel(self.pump)
        self.connection_flow_controller.setVolume(volume)
        self.connection_flow_controller.setRate(rate)
        self.callback_pb_pump_start()

    def update_syringe_inner_dia(self, id):
        self.connection_flow_controller.setDiameter(id)

    def update_flow_rate_unit(self, unit):
        self.connection_flow_controller.setUnits(unit)

    def callback_pb_config_flow(self):
        self.callback_pb_pump_stop()
        self.connection_flow_controller.updateChannel(self.pump)
        self.connection_flow_controller.setUnits(self.cb_flow_unit.get_value())
        self.connection_flow_controller.setDiameter(self.cb_syringe_dia.get_value())
        self.syringe_dia = self.cb_syringe_dia.get_value()
        self.connection_flow_controller.setVolume(self.ti_volume.get())
        self.flow_volume = float(self.ti_volume.get())
        self.connection_flow_controller.setRate(self.ti_flow.get())
        self.callback_pb_pump_start()

    def callback_pb_pump_start(self):
        self.connection_flow_controller.updateChannel(self.pump)
        self.connection_flow_controller.startPump()
        self.callback_pb_pump_update()  # Add this

    def callback_pb_pump_stop(self):
        self.connection_flow_controller.updateChannel(self.pump)
        self.connection_flow_controller.stopPump()
        self.callback_pb_pump_update()  # Add this

    def callback_pb_pump_pause(self):
        self.connection_flow_controller.updateChannel(self.pump)
        self.connection_flow_controller.pausePump()
        self.callback_pb_pump_update()  # Add this

    def callback_pb_pump_update(self):
        self.connection_flow_controller.updateChannel(self.pump)
        self.status = self.connection_flow_controller.getPumpStatus()
        self.id_status.write_value(self.status_dict[self.status[0][-1:]])
