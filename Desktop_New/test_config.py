#import pytomlpp
import toml

class Test_Spec_TypeDef :
    def __init__(self, path_to_spec_file) :
        with open(path_to_spec_file, 'r') as file:
            data = file.read()
            
        test_spec = toml.loads(data)
        #print(test_spec)
        self.test_setting = test_spec["test_settings"]
        self.flow_points = []

        if self.test_setting["flow_point_type"] == 0 :
            flow_point_data = test_spec["flow_point_type_0"]
            flow_point_sequence_type = self.test_setting["flow_point_type_0_sequence_type"]

            if flow_point_data["flow_lower_limit"] <= flow_point_data["flow_upper_limit"] :
                if (flow_point_data["flow_lower_limit"] > 0) == (flow_point_data["flow_upper_limit"] > 0) :
                    f_value = flow_point_data["flow_lower_limit"]
                    while f_value < flow_point_data["flow_upper_limit"] :
                        self.flow_points.append(f_value)
                        f_value += flow_point_data["flow_step_size"]
                    self.flow_points.append(flow_point_data["flow_upper_limit"])

                else :
                    if flow_point_sequence_type != 0 :
                        f_value = flow_point_data["flow_lower_limit"]

                        while f_value < 0 :
                            self.flow_points.append(f_value)
                            f_value += flow_point_data["flow_step_size"]
                        self.flow_points.append(0)

                        f_value = flow_point_data["flow_upper_limit"]
                        while f_value > 0 :
                            self.flow_points.append(f_value)
                            f_value -= flow_point_data["flow_step_size"]
                        self.flow_points.append(0)

                    else :
                        f_value = flow_point_data["flow_lower_limit"]
                        while f_value < flow_point_data["flow_upper_limit"] :
                            self.flow_points.append(f_value)
                            f_value += flow_point_data["flow_step_size"]
                        self.flow_points.append(flow_point_data["flow_upper_limit"])

            else :
                if (flow_point_data["flow_lower_limit"] > 0) == (flow_point_data["flow_upper_limit"] > 0) :
                    f_value = flow_point_data["flow_lower_limit"]
                    while f_value > flow_point_data["flow_upper_limit"] :
                        self.flow_points.append(f_value)
                        f_value -= flow_point_data["flow_step_size"]
                    self.flow_points.append(flow_point_data["flow_upper_limit"])

                else :
                    if flow_point_sequence_type != 0 :
                        f_value = flow_point_data["flow_lower_limit"]

                        while f_value > 0 :
                            self.flow_points.append(f_value)
                            f_value -= flow_point_data["flow_step_size"]
                        self.flow_points.append(0)

                        f_value = flow_point_data["flow_upper_limit"]
                        while f_value < 0 :
                            self.flow_points.append(f_value)
                            f_value += flow_point_data["flow_step_size"]
                        self.flow_points.append(0)

                    else :
                        f_value = flow_point_data["flow_lower_limit"]
                        while f_value > flow_point_data["flow_upper_limit"] :
                            self.flow_points.append(f_value)
                            f_value -= flow_point_data["flow_step_size"]
                        self.flow_points.append(flow_point_data["flow_upper_limit"])

        elif self.test_setting["flow_point_type"] == 1 :
            self.flow_points = test_spec["flow_point_type_1"]["flow_points"]

        self.sampling_frequency = self.test_setting["sampling_frequency"]
        self.temperature_points = self.test_setting["temperature_points"]
        self.flow_points_count = len(self.flow_points)
        self.temperature_points_count = len(self.temperature_points)
        self.numbers_of_test = self.test_setting["numbers_of_test"]
        self.flow_settling_time = self.test_setting["flow_settling_time"]
        self.flow_capture_time = self.test_setting["flow_capture_time"]
        self.ld20_data = self.test_setting["ld20_data"]
        self.syringe_pump = self.test_setting["syringe_pump"]
        self.syringe_inner_dia = self.test_setting["syringe_inner_dia"]
        self.heater_control_data = self.test_setting["Heater_Control_data"]
        self.log_discrete_data = self.test_setting["Log_Discrete_data"]
        self.initial_warm_up_run_at_each_cycle = self.test_setting["initial_warm_up_run_at_each_cycle"]

        self.initial_warm_up_run_flow_rate = self.test_setting["initial_warm_up_run_flow_rate"]
        self.initial_warm_up_run_flow_duration = self.test_setting["initial_warm_up_run_flow_duration"]
        self.flow_direction_change_warm_up_run_flow_rate = self.test_setting["flow_direction_change_warm_up_run_flow_rate"]
        self.flow_direction_change_warm_up_run_flow_duration = self.test_setting["flow_direction_change_warm_up_run_flow_duration"]

