import serial
from liquid_flow_dialect import *
import datetime
import csv
from plot import *
import collections
import moving_average


class Time_Clock:
    def __init__(self, ticks_frequency):
        self.ticks_frequency = ticks_frequency
        self.ticks_interval_ms = 1000.0 / ticks_frequency

        self.elapsed_ms = (-1) * self.ticks_interval_ms
        self.time_ms_counter = 0
        self.time_sec = " "
        self.is_alarm_scheduled = 0
        self.total_elapsed_ms = 0
        self.timestamp = 0

    def update_sampling_freq(self, freq):
        self.ticks_frequency = freq
        self.ticks_interval_ms = 1000.0 / self.ticks_frequency

    def start_clock(self):
        self.timestamp = int(time.time())
        timestamp_ns = time.time_ns()
        self.time_ms_counter = int(((timestamp_ns % 1000000000) / 1000000))
        self.time_sec = self.convert_timestamp_to_time_sec()

    def advance_number_of_ticks(self, ticks):
        elapsed_ms = self.ticks_interval_ms * ticks

        self.time_ms_counter += elapsed_ms
        if self.time_ms_counter >= 1000:
            self.time_ms_counter = self.time_ms_counter - 1000
            self.timestamp += 1
            self.time_sec = self.convert_timestamp_to_time_sec()

        self.total_elapsed_ms += elapsed_ms

        if self.is_alarm_scheduled != 0:
            self.alarm_elapsed_ms += elapsed_ms

    def get_time_sec(self):
        return self.time_sec[:-1]

    def get_time_milli_sec(self):
        return self.time_sec + str(int(self.time_ms_counter))

    def get_elapsed_milli_sec(self):
        return self.total_elapsed_ms

    def schedule_alarm_after_milli_sec(self, ms):
        self.alarm_elapsed_ms = 0
        self.alarm_period_ms = ms
        self.is_alarm_scheduled = 1

    def is_alarm_went_off(self):
        if self.alarm_elapsed_ms > self.alarm_period_ms:
            x = 1
        else:
            x = 0
        return x

    def turn_off_alarm(self):
        self.alarm_elapsed_ms = 0
        self.alarm_period_ms = 1
        self.is_alarm_scheduled = 0

    def convert_timestamp_to_time_sec(self):
        return time.strftime("%H:%M:%S.", time.localtime(self.timestamp))


class CSV_Data_Logger:
    def __init__(self, file_name, max_csv_row_count, field_names):
        self.file_name = file_name

        self.max_data_count_csv = max_csv_row_count
        self.field_names = field_names
        self.file_row_count = 0
        self.csv_file_count = 0
        self.open_csv()

    def open_csv(self):
        self.csv_file = open(self.file_name + "__" + str(int(self.csv_file_count)) + ".csv", "w")  # create .csv file
        data = csv.DictWriter(self.csv_file, delimiter=',', fieldnames=self.field_names, lineterminator='\n')
        data.writeheader()

        self.csv_write_handler = csv.writer(self.csv_file, delimiter=',', lineterminator='\n', quoting=csv.QUOTE_ALL)

    def write_row(self, data):
        self.csv_write_handler.writerow(data)

        self.file_row_count += 1
        if self.file_row_count == self.max_data_count_csv:
            self.change_csv()

    def close_csv(self):
        self.csv_file.close()

    def change_csv(self):
        self.close_csv()
        self.file_row_count = 0
        self.csv_file_count += 1
        self.open_csv()


class Interface_Data_Handler:
    def __init__(self) -> None:
        pass

    def add_entry_sensor_data(self, lost_entries, raw_value, corrected_value, temperature_value):
        print(raw_value)

    def add_entry_sensirion_data(self, sensor_flow_data, sensor_temp_data, sensor_status_data):
        print(sensor_flow_data)

    def add_entry_heater_control_data(self, v_h, v_t, i_h, i_t, v_drop_t):
        pass

    def mav_msg_read_segment_coeffs_callback(self, mavmsg):
        print(mavmsg)
        pass

    def mav_msg_write_segment_coeffs_callback(self, mavmsg):
        pass

    def mav_msg_response_read_segment_coeffs_callback(self, mavmsg):
        # print(mavmsg.get_seq(), mavmsg)
        pass

    def mav_msg_response_sensor_raw_data_callback(self, mavmsg):
        # print(mavmsg.get_seq(), mavmsg)
        self.add_entry_sensor_data(0, mavmsg.sensor_raw_data, 0, mavmsg.sensor_temperature_data)

    def mav_msg_response_sensor_flow_data_callback(self, mavmsg):
        # print(mavmsg.get_seq(), mavmsg)
        self.add_entry_sensor_data(0, 0, mavmsg.sensor_flow_data, mavmsg.sensor_temperature_data)

    def mav_msg_response_sensor_both_data_callback(self, mavmsg):
        # print(mavmsg.get_seq(), mavmsg)
        self.add_entry_sensor_data(0, mavmsg.sensor_raw_data, mavmsg.sensor_flow_data, mavmsg.sensor_temperature_data)

    def mav_msg_response_sensirion_data_callback(self, mavmsg):
        # print(mavmsg.get_seq(), mavmsg)
        self.add_entry_sensirion_data(mavmsg.sensor_flow_data, mavmsg.sensor_temp_data, mavmsg.sensor_status_data)
        # self.add_entry_sensirion_data(10, 20, 30)
        # self.printhello()

    def mav_msg_response_heater_control_data_callback(self, mavmsg):
        # print(mavmsg.get_seq(), mavmsg)
        self.add_entry_heater_control_data(mavmsg.v_h, mavmsg.v_t, mavmsg.i_h, mavmsg.i_t, mavmsg.v_drop_t)

    def close_files(self):
        pass

    def update_plot(self):
        pass

    def capture_timestamp_for_data_logging_about_to_start(self):
        pass

    def printhello(self):
        print("Hello")


class Char_Test_Data_Handler(Interface_Data_Handler):
    def __init__(self, app, folder_name, sampling_frequency, settling_time, capture_time, flow_points,
                 log_discrete_data):
        self.sampling_frequency = sampling_frequency
        self.flow_points = flow_points
        self.log_discrete_data = log_discrete_data

        self.clock = Time_Clock(self.sampling_frequency)

        self.char_data_file_name = r"..\\" + folder_name + "\Liquid Flow Char Test Data " + str(
            time.strftime("%d %b %Y %H_%M_%S", time.localtime()))
        self.char_data_fields = ['Time [ms]', 'Timestamp', 'Actual Temperature', 'Actual Flow', 'Raw Value',
                                 'Corrected Value', 'Temperature Value',
                                 'LD20 Flow', 'LD20 Temperature']
        self.char_data_logger = CSV_Data_Logger(self.char_data_file_name, 100000, self.char_data_fields)

        if self.log_discrete_data != 0:
            self.discrete_data_file_name = r"..\\" + folder_name + "\\Discrete Data" + "\\Liquid Flow Discrete Data " + str(
                time.strftime("%d %b %Y %H_%M_%S", time.localtime()))
            self.discrete_data_fields = ['Time [ms]', 'Timestamp', 'Actual Temperature', 'Actual Flow', 'Raw Value',
                                         'Corrected Value', 'Temperature Value',
                                         'LD20 Flow', 'LD20 Temperature', 'LD20 Status',
                                         'Heater Voltage', 'Thermistor Voltage', 'Heater Current', 'Thermistor Current',
                                         'Series R Voltage']
            self.discrete_data_logger = CSV_Data_Logger(self.discrete_data_file_name, 100000, self.discrete_data_fields)

        self.honeywell_corrected_value = []
        self.honeywell_raw_value = []
        self.LD20_corrected_value = []
        self.actual_flow_points = []
        #        self.graph = Data_Plot(app, self.actual_flow_points, self.honeywell_raw_value, self.LD20_corrected_value,
        #                               "Characterization Plot", "Actual Flow [ml/hr]", "Honeywell Sensor Raw Value [Red]",
        #                               "LD20 Corrected Flow Value [ml/hr] [Blue]", True)
        self.graph = Data_Plot3(app, self.actual_flow_points, self.honeywell_raw_value, self.LD20_corrected_value,
                                self.honeywell_corrected_value,
                                "Characterization Plot", "Actual Flow [ml/hr]", "Honeywell Sensor Raw Value [Red]",
                                "LD20 Corrected Flow Value [ml/hr] [LD20 Blue, HW Green]", True)
        self.set_plot_limits()
        self.graph.update_plot()

        self.sensirion_flow = 0
        self.sensirion_temp = 0
        self.sensirion_status = 0

        self.v_h = 0
        self.v_t = 0
        self.i_h = 0
        self.i_t = 0
        self.v_drop_t = 0

        self.flow_point = 0
        self.temp_point = 0
        self.test_count = 0
        self.str_flow_point = ""
        self.str_temp_point = ""
        self.str_test_count = ""

        self.settling_time = settling_time * 1000
        self.capture_time = capture_time * 1000

        self.avg_raw_value = 0
        self.avg_corrected_value = 0
        self.avg_temperature_value = 0
        self.avg_sensirion_flow = 0
        self.avg_sensirion_temp = 0
        self.avg_counter = 0

        self.is_settling_time_over = 0
        self.is_one_flow_point_completed = 1

    def close_files(self):
        if self.log_discrete_data != 0:
            self.discrete_data_logger.close_csv()
        self.char_data_logger.close_csv()

    def float_to_string(self, value):
        return ("%.4f" % value)

    def set_plot_limits(self):
        flow_l_limit = min(self.flow_points)
        flow_l_limit = flow_l_limit - abs(flow_l_limit) * 0.1 - 10
        flow_h_limit = max(self.flow_points)
        flow_h_limit = flow_h_limit + abs(flow_h_limit) * 0.1 + 10

        # self.graph.set_axes_limits(flow_l_limit, flow_h_limit, 0, pow(2,23), flow_l_limit, flow_h_limit)
        self.graph.set_axes_limits(flow_l_limit, flow_h_limit, 1000000, 3000000, flow_l_limit, flow_h_limit)

    def add_entry_sensor_data(self, lost_entries, raw_value, corrected_value, temperature_value):
        corrected_value = (corrected_value - 2 ** 23) / 2 ** 24 * 600 / .8
        self.clock.advance_number_of_ticks(lost_entries + 1)

        if self.log_discrete_data != 0:
            data = []
            data = [str(self.clock.get_elapsed_milli_sec()), self.clock.get_time_milli_sec(), self.str_temp_point,
                    self.str_flow_point,
                    self.float_to_string(raw_value), self.float_to_string(corrected_value),
                    self.float_to_string(temperature_value),
                    self.float_to_string(self.sensirion_flow / 20.0), self.float_to_string(self.sensirion_temp / 200.0),
                    self.float_to_string(self.sensirion_status),
                    self.float_to_string(self.v_h), self.float_to_string(self.v_t), self.float_to_string(self.i_h),
                    self.float_to_string(self.i_t), self.float_to_string(self.v_drop_t)]

            self.discrete_data_logger.write_row(data)

        if self.is_one_flow_point_completed == 0:
            if self.is_settling_time_over == 0:
                if self.clock.is_alarm_went_off() == 1:
                    self.is_settling_time_over = 1
                    self.clock.schedule_alarm_after_milli_sec(self.capture_time)

            else:
                if self.clock.is_alarm_went_off() == 0:
                    self.avg_raw_value += raw_value
                    self.avg_corrected_value += corrected_value
                    self.avg_temperature_value += temperature_value
                    self.avg_sensirion_flow += self.sensirion_flow
                    self.avg_sensirion_temp += self.sensirion_temp
                    self.avg_counter += 1

                else:
                    self.clock.turn_off_alarm()
                    self.avg_raw_value = self.avg_raw_value / self.avg_counter
                    self.avg_corrected_value = self.avg_corrected_value / self.avg_counter
                    self.avg_temperature_value = self.avg_temperature_value / self.avg_counter
                    self.avg_sensirion_flow = (self.avg_sensirion_flow / self.avg_counter) / 20.0
                    self.avg_sensirion_temp = (self.avg_sensirion_temp / self.avg_counter) / 200.0

                    data = []
                    data = [str(self.clock.get_elapsed_milli_sec()), self.clock.get_time_milli_sec(),
                            self.str_temp_point, self.str_flow_point,
                            self.float_to_string(self.avg_raw_value), self.float_to_string(self.avg_corrected_value),
                            self.float_to_string(self.avg_temperature_value),
                            self.float_to_string(self.avg_sensirion_flow),
                            self.float_to_string(self.avg_sensirion_temp)]

                    self.char_data_logger.write_row(data)

                    self.graph.append_values(self.flow_point, self.avg_raw_value, self.avg_sensirion_flow,
                                             self.avg_corrected_value)
                    self.graph.update_plot()

                    self.is_one_flow_point_completed = 1

    def add_entry_sensirion_data(self, sensor_flow_data, sensor_temp_data, sensor_status_data):
        self.sensirion_flow = sensor_flow_data
        self.sensirion_temp = sensor_temp_data
        self.sensirion_status = sensor_status_data

    def add_entry_heater_control_data(self, v_h, v_t, i_h, i_t, v_drop_t):
        self.v_h = v_h
        self.v_t = v_t
        self.i_h = i_h
        self.i_t = i_t
        self.v_drop_t = v_drop_t

    def update_plot(self):
        self.graph.update_plot()

    def is_one_point_completed(self):
        return self.is_one_flow_point_completed

    def reset_fields_for_new_flow_point(self):
        self.avg_raw_value = 0
        self.avg_corrected_value = 0
        self.avg_temperature_value = 0
        self.avg_sensirion_flow = 0
        self.avg_sensirion_temp = 0
        self.avg_counter = 0

    def update_new_flow_point(self, point):
        self.flow_point = point
        self.str_flow_point = str(self.flow_point)

        self.reset_fields_for_new_flow_point()
        self.is_one_flow_point_completed = 0
        self.is_settling_time_over = 0
        self.clock.schedule_alarm_after_milli_sec(self.settling_time)

    def update_new_temp_point(self, point):
        self.temp_point = point
        self.str_temp_point = str(self.temp_point)

    def update_test_count(self, point):
        self.test_count = point
        self.str_test_count = str(self.test_count)

    def hault_test(self):
        self.is_one_flow_point_completed = 1

    def capture_timestamp_for_data_logging_about_to_start(self):
        self.clock.start_clock()


class Coeffs_Data_Handler(Interface_Data_Handler):
    def __init__(self, app, folder_name):
        self.app = app
        self.discrete_data_logger_file_name = folder_name + "\\Liquid Flow Monitor Test Data " + str(
            time.strftime("%d %b %Y %H_%M_%S", time.localtime()))
        self.data = bytes(4 * 16)

    def add_entry_read_coeffs_response_data(self, id, data):
        self.mavlink_handler.parse_received_data()

        print(id, data)


class Monitor_Test_Data_Handler(Interface_Data_Handler):
    def __init__(self, app, folder_name, sampling_frequency, time_period_to_display_data, smoothing_settings=None):
        self.sampling_frequency = sampling_frequency
        self.smoothing_settings = smoothing_settings
        self.max_buffer_len = int(time_period_to_display_data * self.sampling_frequency)

        self.clock = Time_Clock(self.sampling_frequency)

        # sends the data to the file location selected (if one was selected)
        if folder_name != 'Data files':
            self.discrete_data_logger_file_name = folder_name
        else:
            self.discrete_data_logger_file_name = "../" + folder_name + "/" + str(
                time.strftime("%d %b %Y %H_%M_%S", time.localtime()))

        self.discrete_data_fields = ['Time [ms]', 'Measured Flow', 'Simple Moving Average Flow',
                                     'Exponential Moving Average Flow']

        """OLD DATA FIELDS
        self.discrete_data_fields = ['Time [ms]', 'Timestamp', 'Raw Value', 'Corrected Value', 'Temperature Value',
                                     'LD20 Flow', 'LD20 Temperature', 'LD20 Status',
                                     'Heater Voltage', 'Thermistor Voltage', 'Heater Current', 'Thermistor Current',
                                     'Series R Voltage']
        """

        self.discrete_data_logger = CSV_Data_Logger(self.discrete_data_logger_file_name, 100000,
                                                    self.discrete_data_fields)

        self.honeywell_raw_value = collections.deque(maxlen=self.max_buffer_len)
        self.honeywell_corrected_value = collections.deque(maxlen=self.max_buffer_len)
        self.LD20_corrected_value = collections.deque(maxlen=self.max_buffer_len)
        self.time_points = collections.deque(maxlen=self.max_buffer_len)

        #        self.graph = Data_Plot(app, self.time_points, self.honeywell_raw_value, self.LD20_corrected_value,
        #                               "Plot", "Elapsed time [seconds]", "Honeywell Sensor Raw Value [Red]",
        #                               "LD20 Corrected Flow Value [ml/hr] [Blue]", False)
        self.graph = Data_Plot3(app, self.time_points, self.honeywell_raw_value, self.LD20_corrected_value,
                                self.honeywell_corrected_value,
                                "Plot", "Elapsed time [seconds]", "Honeywell Sensor Raw Value [Red]",
                                "Corrected Flow Value [ml/hr] [LD20 Blue, HW Green]", False)
        # self.graph.set_axes_limits(0, 100, -1*pow(2,23), pow(2,23), -1500, 1500)
        self.graph.set_axes_limits(0, 100, 1500000, 3000000, -5, 20)  # THIS IS THE AXES

        self.sensirion_flow = 0
        self.sensirion_temp = 0
        self.sensirion_status = 0

        self.v_h = 0
        self.v_t = 0
        self.i_h = 0
        self.i_t = 0
        self.v_drop_t = 0

    def close_files(self):
        self.discrete_data_logger.close_csv()

    def float_to_string(self, value):
        return ("%.4f" % value)

    # Controls logging and graphing at the receipt of new data
    def add_entry_sensor_data(self, lost_entries, raw_value, honeywell_flow, temperature_value):

        honeywell_flow = (honeywell_flow - 2 ** 23) / 2 ** 24 * 600 / .8
        sma_flow = 0
        ema_flow = 0

        if(self.smoothing_settings['sma_active']):
            self.smoothing_settings['prev_k_points'].append(honeywell_flow)

            if self.smoothing_settings['sma_k'] > len(self.smoothing_settings['prev_k_points']):
                sma_flow = moving_average.SMA(self.smoothing_settings)
            else:
                sma_flow = moving_average.SMA(self.smoothing_settings)
                self.smoothing_settings['prev_k_points'].pop(0)

        if(self.smoothing_settings['ema_active']):
            ema_flow = moving_average.EMA(honeywell_flow, self.smoothing_settings)
            self.smoothing_settings['previous_ema'] = ema_flow

        self.clock.advance_number_of_ticks(lost_entries + 1)
        self.graph.append_values(float(self.clock.get_elapsed_milli_sec() / 1000.0), sma_flow,
                                 ema_flow, honeywell_flow)

        data = [str(self.clock.get_elapsed_milli_sec()), self.float_to_string(honeywell_flow),
                self.float_to_string(sma_flow), self.float_to_string(ema_flow)]



        """ OLD DATA ROW
        data = [str(self.clock.get_elapsed_milli_sec()), self.clock.get_time_milli_sec(),
                self.float_to_string(raw_value), self.float_to_string(corrected_value),
                self.float_to_string(temperature_value),
                self.float_to_string(self.sensirion_flow), self.float_to_string(self.sensirion_temp / 200.0),
                self.float_to_string(self.sensirion_status),
                self.float_to_string(self.v_h), self.float_to_string(self.v_t), self.float_to_string(self.i_h),
                self.float_to_string(self.i_t), self.float_to_string(self.v_drop_t)]
        """

        # data = [str(self.clock.get_elapsed_milli_sec()), str(self.clock.get_time_milli_sec()),
        #                                      str(raw_value), str(corrected_value), str(temperature_value), 
        #                                      str(self.sensirion_flow), str(self.sensirion_temp), str(self.sensirion_status), 
        #                                      str(self.v_h), str(self.v_t), str(self.i_h), str(self.i_t), str(self.v_drop_t)]

        self.discrete_data_logger.write_row(data)

    def add_entry_sensirion_data(self, sensor_flow_data, sensor_temp_data, sensor_status_data):
        self.sensirion_flow = sensor_flow_data
        self.sensirion_temp = sensor_temp_data
        self.sensirion_status = sensor_status_data

    def add_entry_heater_control_data(self, v_h, v_t, i_h, i_t, v_drop_t):
        # print(i_t)
        self.v_h = v_h
        self.v_t = v_t
        self.i_h = i_h
        self.i_t = i_t
        self.v_drop_t = v_drop_t

    def update_plot(self):
        self.graph.update_plot()

    def capture_timestamp_for_data_logging_about_to_start(self):
        self.clock.start_clock()


class Serial_Handler:
    def __init__(self, comport):
        self.handler = serial.Serial()
        self.handler.port = comport
        self.open_connection()

    def write(self, buffer):
        self.handler.write(buffer)

    def open_connection(self):
        self.handler.open()

    def close_connection(self):
        self.handler.close()
        print("Closed connection")


class MAVLink_Handler:
    def __init__(self, serial_handler, sys_id, comp_id, data_logger):
        self.serial_handler = serial_handler
        self.mavlink = MAVLink(self.serial_handler, sys_id, comp_id)
        self.mavlink.set_callback(self.mav_msg_detected_callback)

        self.data_logger = data_logger
        self.configure_message_received_callbacks()
        self.serial_handler.handler.reset_input_buffer()

    def configure_message_received_callbacks(self):
        self.mav_msg_callback_dictionary = {
            'WRITE_SEGMENT_COEFFS': self.data_logger.mav_msg_write_segment_coeffs_callback,
            'READ_SEGMENT_COEFFS': self.data_logger.mav_msg_read_segment_coeffs_callback,
            'RESPONSE_READ_SEGMENT_COEFFS': self.data_logger.mav_msg_response_read_segment_coeffs_callback,
            'CONFIGURE_DATA_STREAM': self.data_logger.mav_msg_read_segment_coeffs_callback,
            'RESPONSE_SENSOR_RAW_DATA': self.data_logger.mav_msg_response_sensor_raw_data_callback,
            'RESPONSE_SENSOR_FLOW_DATA': self.data_logger.mav_msg_response_sensor_flow_data_callback,
            'RESPONSE_SENSOR_BOTH_DATA': self.data_logger.mav_msg_response_sensor_both_data_callback,
            'RESPONSE_SENSIRION_DATA': self.data_logger.mav_msg_response_sensirion_data_callback,
            'RESPONSE_HEATER_CONTROL_DATA': self.data_logger.mav_msg_response_heater_control_data_callback
        }

    def mav_msg_detected_callback(self, mavmsg):
        # print(mavmsg.get_seq(), mavmsg)
        #        self.parse_received_data()
        self.mav_msg_callback_dictionary[mavmsg.name](mavmsg)

    def parse_received_data(self):
        data = self.serial_handler.handler.read_all()
        # print(data)
        try:
            self.mavlink.parse_buffer(data)
        except:
            pass
