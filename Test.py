class Test:
    def __init__(self, flow, time, duplicate = 0):
        self.time = time
        self.flow = flow  # This refers to the flow rate that the pump is set to during testing
        self.duplicate = duplicate
        self.completed = False
        self.scale_error = -1000
        self.pump_error = -1000
        self.required_volume = self.flow * (self.time / 60)  # The volume of water that this test would dispense

        self.start_weight = -100  # the weight on the scale at the start of the test, initialized to -100 for exception handling

    # weight is in mg (1 ml water = 1 mg water) and time is in minutes, returns flow in ml/hr
    def calculate_scale_flow(self, current_weight, current_time):
        assert (not self.start_weight == -100), "The start weight was not initialized!"
        if current_time <= 0.01:
            return -1
        else:
            return (current_weight - self.start_weight) / current_time * 60

    # returns the % error of measured flow, using the scale water weight over time as the actual flow. Time is min,
    # weight is mg, flow is ml/hr
    def calculate_scale_error(self, meas_flow, current_weight, current_time):
        actual = self.calculate_scale_flow(current_weight, current_time)
        self.scale_error = (meas_flow - actual) / actual * 100

    # returns the % error of measured flow, using the pump flow setting as the actual flow
    def calculate_pump_error(self, meas_flow):
        self.pump_error = (meas_flow - self.flow) / self.flow * 100
        return self.pump_error

    def __str__(self, file=False):
        min = int(self.time)
        sec = int((self.time % 1) * 60)
        if self.completed:
            return "Flow: {0}ml/hr - Time: {1:d}min, {2:d}s - {3:.1f}% pump error, {4:.1f}% scale error".format(str(self.flow)[0:5], min, sec, self.pump_error, self.scale_error)
        else:
            return "Flow: {}ml/hr - Time: {:d}min, {:d}s".format(str(self.flow)[0:5], min, sec)

    def __eq__(self, other):
        if type(other) == Test:
            if other.time == self.time and other.flow == self.flow:
                return True

        return False

    def getFileName(self):
        min = int(self.time)
        sec = int((self.time % 1) * 60)

        fname = "Flow_{}ml_hr_Time_{:d}min_{:d}s".format(str(self.flow)[0:5], min, sec)
        fname = fname.replace(".", "_")
        if self.duplicate:
            fname = fname + "_round{}".format(self.duplicate + 1)
        return fname

    def mark_complete(self):
        assert not self.pump_error == -1000, "pump error is uncalculated"
        assert not self.scale_error == -1000, "scale error is uncalculated"

        self.completed = True


if __name__ == "__main__":
    test = Test(1, 3)
    test.start_weight = 50

    test.calculate_scale_error(55, 60, 3)
    test.calculate_pump_error(55)

    test.mark_complete()

    print(str(test))