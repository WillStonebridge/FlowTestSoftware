"""
Pololu Glue dispenser used as syringe control
Equations:
    Volume of cylinder =  length * 𝜋 * (diameter/2)
    Length of a syringe = (Volume/𝜋) * ((diameter/2)^2) * 1000
    Speed in mm/hour = rate/mL per hour
    Pulses per mL = 7850
    Displaced Volume = rate in ml/hour * time in seconds / 3600
    Displaced Volume = current position / positions per mL
"""
import pytic    # Fix pytic.py add Loader= to 'cfg = yaml.load(ymlfile, Loader=yaml.FullLoader'

import serial
import serial.tools.list_ports
import sys
import glob


def getOpenPorts():
    # portinfo = []
    # for port in serial.tools.list_ports.comports():
    #     if port[2] != 'n/a':
    #         info = [port.device, port.name, port.description, port.hwid]
    #         portinfo.append(info)
    # return portinfo

    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    results = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            results.append(port)
            # print(port)
        except (OSError, serial.SerialException):
            pass
    # print(results)
    return results

    # Search for Harvard Pump devices by vendor ID
#    VENDOR_FTDI = "0403"  # FTDI USB Cable (Pump)
#    for comport in serial.tools.list_ports.grep(VENDOR_FTDI):
#        if "FTFBGIK9A" in comport.hwid:
#            usb_serial_ports.append(comport.device)
#            port_val = comport.device
#            break

def parsePortName(portinfo):
    """
    On macOS and Linux, selects only usbserial options and parses the 8 character serial number.
    """
    portlist = []
    for port in portinfo:
        if sys.platform.startswith('win'):
            portlist.append(port[0])
        elif sys.platform.startswith('darwin') or sys.platform.startswith('linux'):
            if 'usbserial' in port[0]:
                namelist = port[0].split('-')
                portlist.append(namelist[-1])
    return portlist


PI = 3.141592654
ONE_MM = 4325       # Pulses per mm
POS_ML = 7841.7     # Positions per mL

class Connection(object):
    def __init__(self, port, baudrate, x=0, mode=0, verbose=False):
        self.port = port
        self.baudrate = baudrate
        self.x = x
        self.mode = mode
        self.verbose = verbose
        self.serial_number = '0'
        self.name = 'Pololu'
        self.tic = None
        self.rx_data = []
        self.units = 'MH'           # Define units, default ml/hr
        self.speed = 0              # Speed of plunger in pulse counts
        self.volume = 12            # Syringe size or dispense volume
        self.diameter = 15.9        # Default 12mm syringe
        self.direction = 1
#        self.length = 60.44         # Syringe length, not used
        self.displacedVolume = 0    # Amount of dispensed liquid since start pump
        self.rate = 0               # Rate of flow in units
        self.multiplier = 1         # Multiplier to change units, ie.uL,mL..
        self.time_mult = 1          # 1 for hours, 60 for minutes
        self.status = '0'
        self.status_dict = {'0': 'Stopped',
                            '1': 'Running',
                            '2': 'Paused',
                            '3': 'Delayed',
                            '4': 'Stalled'
                            }
        print(self.status[0][-1:])
        print(self.status_dict[self.status[0][-1:]])
        print(self.status)
        print(self.status_dict[self.status])

    def openConnection(self):
        try:
            if not self.tic:
                self.tic = pytic.PyTic()    # Initialization
                # Connect to first available Tic Device serial number over USB
                serial_nums = self.tic.list_connected_device_serial_numbers()
                self.tic.connect_to_serial_number(serial_nums[0])
                self.serial_number = serial_nums[0]
            # Load configuration file and apply settings
            self.tic.settings.load_config('config\\config.yml')
            self.tic.settings.apply()
            # Or
            self.tic.reset()
            self.tic.set_max_speed(16000000)    # 20M max times 1/8 steps
            self.tic.set_starting_speed(8000000)  # Pulses per 100 pulses/sec
            self.tic.set_max_accel(4000000)
            self.tic.set_max_decel(4000000)
            self.tic.set_step_mode(3)       # TIC_STEP_MODE_MICROSTEP8
            self.tic.set_current_limit(634)
            self.tic.set_decay_mode(0)      # TIC_DECAY_MODE_T500_AUTO
            self.tic.set_target_velocity(0)
            self.tic.settings.apply()
            self.tic.exit_safe_start()
            self.tic.halt_and_set_position(0)
            if self.verbose:
                print("{} Motor Driver: {} connected".format(self.name, self.serial_number))
                print("Current Limit: ", self.tic.settings.current_limit)
            return self.serial_number
        except Exception as e:
            if self.verbose:
                print('Failed to connect to pump')
                print(e)
            pass

    def closeConnection(self):
        # De-energize motor and get error status
        self.tic.enter_safe_start()
        self.tic.deenergize()
        self.status = '0'
        if self.verbose:
            print("Errors: {}".format(self.tic.variables.error_status))
            print("Closed connection")
#        self.tic.
#        del self.tic

    def updateChannel(self, t_x):
        self.x = t_x

    def startPump(self):
        radius_squared = (self.diameter/2)**2
        mLPermm = PI * radius_squared / 1000.0
        mmPerHr = self.rate / mLPermm
        self.speed = (int)(mmPerHr * ONE_MM * self.multiplier * self.time_mult)
        if self.verbose:
            print("Calculated Speed: ", self.speed)

        if self.speed:
            self.displacedVolume = 0        # Zero motor position & volume
            self.tic.halt_and_set_position(0)
            self.tic.energize()             # Energize Motor
            self.tic.exit_safe_start()
            self.tic.set_target_velocity((int)(self.speed))
            if self.verbose:
                print("Start Position: ", self.tic.variables.current_position)
                print("Speed in {}: {:.0f}".format(self.units, self.speed/ONE_MM))
            self.status = '1'

    def setVolume(self, volume):        # Dispense volume
        return

    def set_Volume(self, volume):        # Dispense volume
        self.volume = float(volume) * -1 * self.multiplier     # Adjust for units mL/uL
        self.displacedVolume = 0  # Zero motor position & volume
        self.tic.halt_and_set_position(0)
        self.tic.energize()  # Energize Motor
        self.tic.exit_safe_start()
        self.tic.set_target_position((int)(POS_ML * self.volume))
        self.status = '1'
        if self.verbose:
            print("Start Position: ", self.tic.variables.current_position)
            print("Speed: {}".format(self.speed))
            print("Volume: {:.3f}\tTarget position: {}".format(self.volume, (int)(POS_ML * self.volume)))

    def stopPump(self):
        # De-energize motor and get error status
        self.tic.set_target_velocity(0)
        self.status = '0'
        if self.verbose:
            print("Stop Position: ", self.tic.variables.current_position)

    def pausePump(self):
        # If motor is running
        if self.tic.variables.target_velocity:
            self.tic.set_target_velocity(0)
            self.status = '2'
            if self.verbose:
                print("Pump paused")
        elif self.status == '2':     # Unpause only if paused
            self.tic.set_target_velocity(self.speed)
            self.status = '1'
            if self.verbose:
                print("Pump Un-paused")


    def setUnits(self, units):
        if 'mL/min' in units:
            self.units = 'MM'
            self.multiplier = 1
            self.time_mult = 60
        elif 'mL/hr' in units:
            self.units = 'MH'
            self.multiplier = 1
            self.time_mult = 1
        elif 'μL/min' in units:
            self.units = 'UM'
            self.multiplier = .001
            self.time_mult = 60
        elif 'μL/hr' in units:
            self.units = 'UH'
            self.multiplier = .001
            self.time_mult = 1

    def setDiameter(self, diameter):    # Syringe diameter in mm
        self.diameter = float(diameter)

    def setRate(self, rate):            # Syringe dispense rate in units (mL/hr)
        self.rate = float(rate) * self.direction

    def setPumpDirection(self, direction):
        if 'INF' in direction.upper():
            self.direction = -1
        elif 'REF' in direction.upper():
            self.direction = 1

    def getDisplacedVolume(self):
        self.displacedVolume = self.tic.variables.current_position / POS_ML
        if self.verbose:
            print("Displaced volume: {:.3f}".format(self.displacedVolume))
        return self.displacedVolume

    def getPumpStatus(self):
        if self.verbose:
            print("Status: ", self.status_dict[self.status])
        return self.status

    def setFlow(self, rate, duration=10):
        return


class PumpError(Exception):
    pass


if __name__ == '__main__':
    from time import sleep

    #    result = getOpenPorts()
    Pump = Connection(port='COM7', baudrate=9600, x=1, mode=1, verbose=True)
    Pump.openConnection()
    Pump.closeConnection()
    Pump.openConnection()

    Pump.updateChannel(0)
    Pump.stopPump()
    Pump.setUnits('mL/hr')
    Pump.setDiameter(15.9)
    status = Pump.getPumpStatus()
    print("Status: ", Pump.status_dict[status[0][-1:]])
    # Dispense using speed/time method
    Pump.setRate(240)
    Pump.startPump()
    status = Pump.getPumpStatus()
    print("Status: ", Pump.status_dict[status[0][-1:]])
    sleep(1)
    Pump.pausePump()
    status = Pump.getPumpStatus()
    print("Status: ", Pump.status_dict[status[0][-1:]])
    sleep(5)
    Pump.pausePump()
    status = Pump.getPumpStatus()
    print("Status: ", Pump.status_dict[status[0][-1:]])
    sleep(15)
    Pump.stopPump()
    Pump.getDisplacedVolume()
    sleep(3)

    # Dispense using volume method
    Pump.setUnits('μL/hr')
    Pump.setVolume(1000)
    sleep(10)
    Pump.getDisplacedVolume()
    Pump.setUnits('mL/hr')
    Pump.set_Volume(-3)
    sleep(15)
    Pump.getDisplacedVolume()

    Pump.stopPump()
    Pump.closeConnection()
    del Pump

    # back @ 7mL



"""
# - Initialization -------------------------------------------

tic = pytic.PyTic()

# Connect to first available Tic Device serial number over USB
serial_nums = tic.list_connected_device_serial_numbers()
print("Motor Drivers: {}".format(serial_nums))
tic.connect_to_serial_number(serial_nums[0])

# Load configuration file and apply settings
tic.settings.load_config('config\\config.yml')
tic.settings.apply()
# Or
tic.set_starting_speed(1000000)     # Pulses per 100 pulses/sec
tic.set_max_speed(2000000)
tic.set_target_velocity(2000000)
tic.set_starting_speed
tic.set_max_accel(40000)
tic.set_max_decel(40000)
# tic.set_step_mode(TIC_STEP_MODE_MICROSTEP8)
tic.set_current_limit(634)
# tic.set_decay_mode(TIC_DECAY_MODE_T500_AUTO)


# - Motion Command Sequence ----------------------------------

# Zero current motor position
tic.halt_and_set_position(0)

# Energize Motor
tic.energize()
tic.exit_safe_start()

# Move to listed positions
positions = [1000, 2000, 3000, 0]
speeds = [250000, -500000, 1000000, -2000000, 4000000, 0]
for s in speeds:
    sleep(0.5)
    tic.set_target_velocity(s)

for p in positions:
    tic.set_target_position(p)
    while tic.variables.current_position != tic.variables.target_position:
        print(tic.variables.current_position, tic.variables.target_position)
        sleep(0.1)



# De-energize motor and get error status
tic.enter_safe_start()
tic.deenergize()
print(tic.variables.error_status)
"""