import time
import serial
import serial.tools.list_ports
import sys
import glob

from serial import Serial


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


class Connection(object):

    def __init__(self, port, baudrate, x=0, mode=0, verbose=False):
        self.port = port
        self.baudrate = baudrate
        self.x = x
        self.verbose = verbose
        self.mode_index = mode
        self.modeList = ['PMP', 'VOL', 'PGM']
        self.mode = self.modeList[self.mode_index]
        self.mode_dict = {'PMP': 'PUMP',
                          'VOL': 'VOLUME',
                          'PGM': 'PRGRAM'
                          }
        # if self.verbose:
        #    print("Mode set to", mode, ',', self.mode, ',', self.mode_dict[self.mode][:])
        self.name = 'Harvard Pump'
        self.ser = None
        self.rx_data = [] #received data
        self.output = 0
        self.units = 'mL/hr'          # Define units, default mL/hr
        self.units_dict = { 'mL/min': 'MM',
                            'mL/hr' : 'MH',
                            'μL/min': 'UM',
                            'μL/hr' : 'UH'
                            }
        # if self.verbose:
        #    print("Units set to", self.units, ',', self.units_dict[self.units])
        self.diameter = 15.9
        self.direction = 'INF'
        self.rate = 0
        self.volume = 4
        self.status = '0'
        self.status_dict = {'0': 'Stopped',
                            '1': 'Running',
                            '2': 'Paused',
                            '3': 'Delayed',
                            '4': 'Stalled'
                            }
        # if self.verbose:
        # print("Pump status is", self.status, ',', self.status_dict[self.status])
        # print(self.status_dict[self.status[0][-1:]])

    def __enter__(self):
        self.ser = serial.Serial(self.port)
        return self.ser

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.ser is not None:
            self.ser.close()

    def openConnection(self):
        try:
            self.ser = serial.Serial()
            self.ser.baudrate = self.baudrate
            self.ser.port = self.port
            self.ser.stopbits = serial.STOPBITS_TWO
            self.ser.timeout = 0.2   # Must be at least 1 second
            self.ser.open()
            if self.ser.isOpen():
                if self.verbose:
                    print("Opened port")
                    print(self.ser)
                self.ser.flushInput()
                self.ser.flushOutput()
                self.stopPump()                        # Stop a running pump
                self.setMode(self.mode_index)
                self.setUnits(self.units)
                self.setPumpDirection(self.direction)  # Initialize to infuse
                return self.port
            return -1
        except Exception as e:
            if self.verbose:
                print('Failed to connect to pump')
                print(e)
            pass

    def closeConnection(self):
        self.ser.close()
        self.status = '0'
        if self.verbose:
            print("Closed connection")

    def updateChannel(self, t_x):
        self.x = t_x

    def startPump(self):
        if self.rate:
            self.rx_data = self.ser.readlines() # Clear the rx buffer
            command = ('RUN\r').encode()        # send the command
            self.ser.write(command)
            self.rx_data = self.ser.readlines()
            self.status = '1'
            if self.verbose:
                print("Pump started")

    def stopPump(self):
        self.rx_data = self.ser.readlines() # Clear the rx buffer
        command = ('STP\r').encode()        # send the command
        self.ser.write(command)
        self.rx_data = self.ser.readlines()
        self.status = '0'
        if self.verbose:
            print("Pump stopped")

    def setMode(self, mode):    # 0,1,2 = PMP, VOL, or PGM
        self.rx_data = self.ser.readlines() # Clear the rx buffer
        self.mode_index = mode
        self.mode = self.modeList[self.mode_index]
        command = ('MOD ' + self.mode + '\r').encode()
        self.ser.write(command)
        self.rx_data = self.ser.readlines()
        command = ('MOD' + '\r').encode()  # Readback the mode
        self.ser.write(command)
        self.rx_data = self.ser.readlines()
        # Verify the response
        if any(['{}'.format(self.mode_dict[self.mode][:]).encode() in a for a in self.rx_data]):
            if self.verbose:
                print("Mode set to", mode, ',', self.mode, ',', self.mode_dict[self.mode][:])

    def setUnits(self, units):
        self.units = units
        if self.verbose:
            print("Units set to", self.units, ',', self.units_dict[self.units])

    def setDiameter(self, diameter):  # Syringe diameter in mm, CLEARS INFUSE/REFILL RATES
        self.rx_data = self.ser.readlines() # Clear the rx buffer
        if (type(diameter) != float):
            diameter = float(diameter)
        if diameter != self.diameter:
            command = ('DIA' + ' {:5.1f}\r'.format(diameter)).encode()
            self.ser.write(command)
            self.rx_data = self.ser.readlines()
            command = ('DIA' + '\r').encode()     # Readback the diameter
            self.ser.write(command)
            self.rx_data = self.ser.readlines()
            # Verify the response
            if any(['{:5.1f}'.format(diameter).encode() in a for a in self.rx_data]):
                self.diameter = diameter
                if self.verbose:
                    print("Diameter set to ", self.diameter)

    def setRate(self, rate):
        if (type(rate) != float):
            rate = float(rate)
        if rate >= 0:
            cmd = 'RAT'
            direction = 'INF'
        else:
            cmd = 'RFR'
            direction = 'REF'

        if direction != self.direction:
            self.stopPump()     # If changing directions, stop pump first
            self.setPumpDirection(direction)

        if rate != self.rate:
            self.rx_data = self.ser.readlines() # Clear the rx buffer
            # Pump only takes positive values for rate
            command = (cmd + ' {:5.1f} {}\r'.format(abs(rate), self.units_dict[self.units])).encode()
            self.ser.write(command)     # Send the command
            self.rx_data = self.ser.readlines()
            command = (cmd + '\r').encode()     # Readback the rate
            self.ser.write(command)
            self.rx_data = self.ser.readlines()
            # Verify the response
            if any(['{:5.1f}'.format(abs(rate)).encode() in a for a in self.rx_data]):
                self.rate = rate
                if self.verbose:
                    print("Rate set to ", self.rate)

    def setVolume(self, volume):
        if (type(volume) != float):
            volume = float(volume)
        if volume < 0:
            volume = abs(volume)
        if volume > 50:
            if self.verbose:
                print("Volume out of range ", self.volume)
            return
        if volume != self.volume:
            self.rx_data = self.ser.readlines() # Clear the rx buffer
            command = ('TGT {:1.4f}\r'.format(volume)).encode()  # Send the command
            self.ser.write(command)
            self.rx_data = self.ser.readlines()
            command = ('TGT\r').encode()
            self.ser.write(command)
            self.rx_data = self.ser.readlines()     # Readback the volume
            # Verify the response
            if any(['{:1.4f}'.format(volume).encode() in a for a in self.rx_data]):
                self.volume = volume
                if self.verbose:
                    print("Volume set to ", self.volume)

    def setPumpDirection(self, direction):
        if 'INF' in direction.upper():
            cmd = 'INF'
            response = 'INFUSE'
        elif 'REF' in direction.upper():
            cmd = 'REF'
            response = 'REFILL'

        self.rx_data = self.ser.readlines() # Clear the rx buffer
        command = ('DIR ' + cmd + '\r').encode()    # Send the command
        self.ser.write(command)
        self.rx_data = self.ser.readlines()
        command = ('DIR\r').encode()    # Readback the direction
        self.ser.write(command)
        self.rx_data = self.ser.readlines()
        # Verify the response
        if any([response.encode() in a for a in self.rx_data]):
            self.direction = direction
            if self.verbose:
                print("Pump direction set", self.direction)

    def getDisplacedVolume(self):
        self.rx_data = self.ser.readlines() # Clear the rx buffer
        command = ('DEL\r').encode()        # send the command
        self.ser.write(command)
        self.rx_data = self.ser.readlines()
        actual_volume = float(self.rx_data[1])
        if self.verbose:
            print("{:.4f}".format(actual_volume))
        return actual_volume

    def zeroDisplacedVolume(self):
        self.rx_data = self.ser.readlines() # Clear the rx buffer
        command = ('CLD\r').encode()        # send the command
        self.ser.write(command)             # Clear the delivered volume
        self.rx_data = self.ser.readlines()
        zeroed_volume = self.getDisplacedVolume()
        return zeroed_volume

    def getPumpStatus(self):
        if self.verbose:
            self.rx_data = self.ser.readlines()     # Clear the rx buffer
            command = 'VER\r'.encode()              # Send the command
            self.ser.write(command)
            self.rx_data = self.ser.readlines()
            if any([b'PHD1.2' in a for a in self.rx_data]):     # Verify the response
                print("Status is Harvard PHD1.2,", self.status_dict[self.status])
        return self.status

    def setFlow(self, rate, duration=10):
        return


class PumpError(Exception):
    pass


if __name__ == '__main__':
#    result = getOpenPorts()
#    print(result)
    Pump = Connection(port='COM8', baudrate=9600, x=1, mode=0, verbose=True)
    Pump.openConnection()
    Pump.updateChannel(0)
    Pump.stopPump()
    Pump.updateChannel(1)
    Pump.setUnits('mL/hr')
    Pump.setDiameter(15.9)
    Pump.setVolume(1)
    Pump.setRate(-300)
    Pump.startPump()
    while True:
        displaceVol = Pump.getDisplacedVolume()  # Returns list
        print("{:.4f}".format(displaceVol))
        if displaceVol >= 1.0:
            break
    time.sleep(2)       # Pump should be stopped here
    Pump.stopPump()     # Clear delivery volume
    Pump.zeroDisplacedVolume()
    Pump.setDiameter(15.9)
    Pump.setVolume(1)
    Pump.setRate(300)
    Pump.startPump()
    while True:
        displaceVol = Pump.getDisplacedVolume()  # Returns list
        print("{:.4f}".format(displaceVol))
        if displaceVol >= .4998:
            Pump.stopPump()
            break

    Pump.updateChannel(1)
    Pump.setUnits('mL/hr')
    Pump.setRate(-10)
    Pump.startPump()
    time.sleep(3)
    Pump.stopPump()
    displaceVol = Pump.getDisplacedVolume()  # Returns list
    print("{:.4f}".format(displaceVol))
    Pump.stopPump()
    Pump.closeConnection()
    del Pump

