import tkinter as tk

from serial import Serial
import time as t

from scale_ohaus import scale
from flow_controllerPhd import *

class Connection_one(object):

    def __init__(self, port, baudrate, scale=None, buffer=5, volume = -1, verbose=False):
        self.port = port
        self.baudrate = baudrate
        self.verbose = verbose
        self.name = 'Syringe One Pump'
        self.scale = scale
        self.ser = None
        self.rx_data = []  # received data
        self.output = 0
        # if self.verbose:
        #    print("Units set to", self.units, ',', self.units_dict[self.units])
        self.direction = 'INF' #pump direction, either INF or WDR
        self.rate = 0 #pump rate in ml/hr
        self.capacity = 50 #pump capacity in ml
        if volume == -1: #if no volume is set, the pump is assumed to be full
            self.volume = self.capacity
        else:
            self.volume = volume
        self.buffer = 5 #the minimum amount of volume that the syringe should be from either clamp, this reduces the likelihood of the pump stalling
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
            self.ser.timeout = 0.2  # Must be at least 1 second
            self.ser.open()
            if self.ser.isOpen():
                if self.verbose:
                    print("Opened port")
                    print(self.ser)
                self.ser.flushInput()
                self.ser.flushOutput()
                self.stopPump()  # Stop a running pump
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

    def setScale(self, scale):
        self.scale = scale

    def startPump(self, rate = 0):
        if rate:
            self.setRate(rate)
        if self.rate:
            cmd = ('RUN\r').encode()
            self.ser.write(cmd)
            self.status = '1'

            if self.verbose:
                print("Pump started")

    def stopPump(self):
        self.rx_data = self.ser.readlines()
        cmd = ('STP\r').encode()
        self.ser.write(cmd)
        self.rx_data = self.ser.readlines()
        self.status = '0'
        if self.verbose:
            print("Pump stopped")

    def setPumpDirection(self, direction):
        if 'INF' in direction.upper():
            cmd = 'INF'
            response = 'INFUSE'
        elif 'WDR' in direction.upper():
            cmd = 'WDR'
            response = 'REFILL'
        else:
            raise Exception("Invalid direction")

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

    def setRate(self, rate):
        assert rate < 1000 and rate > -1000, "Choose a rate between -1000 and 1000"
        if (type(rate) != float):
            rate = float(rate)
        if rate >= 0:
            direction = 'INF'
        else:
            direction = 'WDR'


        if direction != self.direction:
            self.setPumpDirection(direction)
            self.direction = direction

        if rate != self.rate:
            self.rx_data = self.ser.readlines() # Clear the rx buffer
            # Pump only takes positive values for rate
            command = ('RAT {:5.1f}\r'.format(abs(rate))).encode()
            self.ser.write(command)     # Send the command
            self.rx_data = self.ser.readlines()
            command = ('RAT\r').encode()     # Readback the rate
            self.ser.write(command)
            self.rx_data = self.ser.readlines()
            self.rate = rate
            if self.verbose:
                print("Rate set to ", self.rate)


    def vol_lost(self, VolumeLoss):
        self.volume = self.volume - VolumeLoss
        return self.volume

    def set_vol(self, volume):
        self.volume = volume

    """pushes water through the system for 5s to get consistent readings"""
    def prime(self, rate=300, time=5, stop_pump_after=True):

        Vol_used = rate * (time / 60 / 60) #the Volume in mL that would be used in priming
        if (self.volume - Vol_used) < self.buffer:
            self.refill()
        if self.verbose:
            print("priming pump")
        self.startPump(rate = rate)

        if stop_pump_after:
            tk.after(time * 1000, self.stopPump)

    """Refills the pump at 900ml/hr, automatically updates the volume of the pump"""
    def refill(self):
        if self.status == '1':
            self.stopPump()

        #Calculations needed to refill the pump
        vol_fill = (self.capacity - self.buffer) #the volume to fill to in ml
        vol_needed = vol_fill - self.volume #the volume of water required to reach that volume
        time_needed = (vol_needed/900) * 60 * 60 #the time in seconds required to fill the pump at 900 ml/hr

        #Refills the pump
        self.startPump(rate=-999)
        if (self.verbose):
            print("refilling pump...")
        while self.scale.getWeight() > self.buffer:
            t.sleep(0.1)
        self.stopPump()
        self.set_vol(self.capacity - self.scale.getWeight())

        if (self.verbose):
            print("pump refilled to" + str(self.capacity))


    def prep_test(self, rate, time, priming_time = 5, testing=False):
        # primes the pump before testing
        if testing: #shortens the length of priming if testing is underway
            self.prime(time=1, stop_pump_after=False)
        else:
            self.prime(rate=rate, time=priming_time, stop_pump_after=False)

        vol_to_be_used = rate * (time / 60)
        if vol_to_be_used > 40:
            raise Exception("This test would use more than 40ml of water!!! Run a shorter test or lower the flow rate")
        elif self.volume - vol_to_be_used < self.buffer:
            self.refill()
            self.prep_test(rate, time)  # the pump must be reprimed after a refill

    """This is the primary function that is used in testing. It is called as a thread so that the sleep function does
     not completely halt the program during testing. This automatically updates the volume when run.
     rate is ml/hr and time is minutes
     """
    def run_test(self, rate, time):

        start_weight = self.scale.getWeight()

        #runs the pump at a set rate for the test time
        self.setRate(rate=rate)
        t.sleep(time*60)
        self.stopPump()

        end_weight = self.scale.getWeight()
        self.vol_lost(start_weight - end_weight)




if __name__ == '__main__':
    scale = scale('COM16')
    scale.openConnection()
    pump = Connection_one('COM15', 9600, scale=scale, verbose=True)
    pump.openConnection()
    pump.run_test(900, 1.5) #should dispense 11ml (10ml from testing, 1ml from priming)
    pump.refill() #should refill to 45ml
    pump.closeConnection()
    scale.closeConnection()