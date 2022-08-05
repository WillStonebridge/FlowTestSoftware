import serial
import time as tm
from threading import Lock

weight_lock = Lock()


"""
This class connects to the Ohaus scale
"""
class scale(object):

    def __init__(self, port, baudrate = 9600, verbose = False):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.continous_printing_active = False
        self.verbose = verbose

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
            self.ser.timeout = 0.2  # Must be at least 1 second
            self.ser.open()
            if self.ser.isOpen():
                if self.verbose:
                    print("Opened port")
                    print(self.ser)
                self.ser.flushInput()
                self.ser.flushOutput()
        except Exception as e:
            if self.verbose:
                print('Failed to connect to scale')
                print(e)
            pass

    def closeConnection(self):
        self.ser.close()
        if self.verbose:
            print("Closed connection")

    "tares the scale weight"
    def tare(self):
        cmd = ('T\n').encode()
        self.ser.write(cmd)

        if self.verbose:
            print("Scale Tared")

    "gets a single weight from the scale"
    def getWeight(self):

        weight_lock.acquire()
        self.ser.flushInput()
        self.ser.flushOutput

        cmd = ('IP\n').encode()
        self.ser.write(cmd)

        weight = self.ser.read_until(expected=('g').encode())
        weight_lock.release()

        weight = float(weight[:-1].decode().strip())

        if self.verbose:
            print("Weight: " + str(weight))

        return weight

    # currently unused. The scale continuously prints for only ~30s. This overcomplicates the weight acquisition process.
    def start_continous_printing(self):
        self.ser.flushOutput()
        self.ser.flushInput()

        cmd = ('CP\n').encode()
        self.ser.write(cmd)

        self.continous_printing_active = True

        if self.verbose:
            print("Continuous Printing activated")

        lines = self.ser.readlines()
        print("lines read")




if __name__ == '__main__':
    scale = scale('COM16', verbose=True)
    scale.openConnection()







