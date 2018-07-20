"""
This is an interface module for instruments produced by Sigma Koki
"""

try:
    from exceptions import ValueError
except:
    pass
import serial
import sys

class GSC02(object):
    """
    Stage controller GSC-02
    """
    def __init__(self):
        self.__baudRate = 9600 # 9600 bps
        self.__parityBit = 'N' # None
        self.__dataBit = 8
        self.__stopBit = 1
        self.__rtscts = True

    def setBaudRate(self, rate):
        if rate in (2400, 4800, 9600, 19200):
            self.__baudRate = rate
        else:
            raise ValueError('Invalid buard rate %d was given. Must be chosen from 2400/4800/9600/19200.' % rate)

    def open(self, port, readTimeOut = 1, writeTimeOut = 1):
        self.serial = serial.Serial(port         = port,
                                    baudrate     = self.__baudRate,
                                    bytesize     = self.__dataBit,
                                    parity       = self.__parityBit,
                                    stopbits     = self.__stopBit,
                                    timeout      = readTimeOut,
                                    writeTimeout = writeTimeOut,
                                    rtscts       = self.__rtscts)

    def write(self, command):
        self.serial.write(command + b'\r\n')

    def readline(self):
        return self.serial.readline()[:-2]

    def returnToMechanicalOrigin(self, stage1, stage2):
        """
        Moves the stages to the +/- end points and reset the coordinate values
        to zero.
        """
        if stage1 == b'+' and stage2 == b'+':
            self.write(b'H:W++')
        elif stage1 == b'+' and stage2 == b'-':
            self.write(b'H:W+-')
        elif stage1 == b'-' and stage2 == b'+':
            self.write(b'H:W-+')
        elif stage1 == b'-' and stage2 == b'-':
            self.write(b'H:W--')
        elif stage1 == b'+':
            self.write(b'H:1+')
        elif stage1 == b'-':
            self.write(b'H:1-')
        elif stage2 == b'+':
            self.write(b'H:2+')
        elif stage2 == b'-':
            self.write(b'H:2-')
        else:
            return

    def move(self, stage1, stage2):
        """
        Moves the stages with the specified values. Since GSC-02 is a half-step
        stepping driver, 1 pulse corresponds to "half-step movement" in the
        stage catalogues.
        """
        if not (-16777214 <= stage1 <= 16777214):
            raise ValueError('stage1 must be between -16777214 and 16777214.')

        if not (-16777214 <= stage2 <= 16777214):
            raise ValueError('stage2 must be between -16777214 and 16777214.')

        command = b'M:W'
        if stage1 >= 0:
            command += b'+P%d' % stage1
        else:
            command += b'-P%d' % -stage1

        if stage2 >= 0:
            command += b'+P%d' % stage2
        else:
            command += b'-P%d' % -stage2

        self.write(command)
        self.go()

    def jog(self, stage1, stage2):
        """
        Moves the stages continuously at the minimum speed.
        stage1: '+' positive direction, '-' negative direction
        stage2: '+' positive direction, '-' negative direction
        If other values are given, stages will not move.
        """
        if stage1 == b'+' and stage2 == b'+':
            self.write(b'J:W++')
        elif stage1 == b'+' and stage2 == b'-':
            self.write(b'J:W+-')
        elif stage1 == b'-' and stage2 == b'+':
            self.write(b'J:W-+')
        elif stage1 == b'-' and stage2 == b'-':
            self.write(b'J:W--')
        elif stage1 == b'+':
            self.write(b'J:1+')
        elif stage1 == b'-':
            self.write(b'J:1-')
        elif stage2 == b'+':
            self.write(b'J:2+')
        elif stage2 == b'-':
            self.write(b'J:2-')
        else:
            return
        
        self.go()

    def go(self):
        """
        Moves the stages. To be used internally.
        """
        self.write(b'G')

    def decelerate(self, stage1, stage2):
        """
        Decelerates and stop the stages. 
        """
        if stage1 and stage2:
            self.write(b'L:W')
        elif stage1:
            self.write(b'L:1')
        elif stage2:
            self.write(b'L:2')

    def stop(self):
        """
        Stops the stages immediately.
        """
        self.write(b'L:E')

    def initializeOrigin(self, stage1, stage2):
        """
        Sets the origin to the current position.
        stage1: If true, set the origin of the stage 1 to the current position
        stage2: If true, set the origin of the stage 1 to the current position
        """
        if stage1:
            self.write(b'R:1')

        if stage2:
            self.write(b'R:2')

    def setSpeed(self, highspeed, minSpeed1, maxSpeed1, accelerationTime1,
                 minSpeed2, maxSpeed2, accelerationTime2):
        """
        Sets the movement speeds of the stages
        highspeed: If true, speed range is 50-20000, else 1-200
        minSpeed1/2: Minimum speed (PPS)
        maxSpeed1/2: Maximum speed (PPS)
        accelerationTime1/2: Acceleration time to be taken from min to max (ms)

        |      _________        ... maximum speed (PPS)
        |    /          \
        |   /            \
        |  /              \     ... minimum speed (PPS)
        |  |              |
        |  |              |
        |__|______________|________
           <->              acceleration time (ms)
                        <-> deceleration time (ms)
        """
        if not highspeed:
            if not (1 <= minSpeed1 <= maxSpeed1 <= 200):
                raise ValueError('Must be 1 <= minSpeed1 <= maxSpeed1 <= 200 in low speed range.')
            if not (1 <= minSpeed2 <= maxSpeed2 <= 200):
                raise ValueError('Must be 1 <= minSpeed2 <= maxSpeed2 <= 200 in low speed range.')
        else:
            if not (50 <= minSpeed1 <= maxSpeed1 <= 20000):
                raise ValueError('Must be 50 <= minSpeed1 <= maxSpeed1 <= 20000 in high speed range.')
            if not (50 <= minSpeed2 <= maxSpeed2 <= 20000):
                raise ValueError('Must be 50 <= minSpeed2 <= maxSpeed2 <= 20000 in high speed range.')

        if not (0 <= accelerationTime1 <= 1000):
            raise ValueError('Must be 00 <= accelerationTime1 <= 1000.')

        if not (0 <= accelerationTime2 <= 1000):
            raise ValueError('Must be 00 <= accelerationTime2 <= 1000.')

        if highspeed:
            self.write(b'D:2S%dF%dR%dS%dF%dR%d' % (minSpeed1, maxSpeed1, accelerationTime1, minSpeed2, maxSpeed2, accelerationTime2))
        else:
            self.write(b'D:1S%dF%dR%dS%dF%dR%d' % (minSpeed1, maxSpeed1, accelerationTime1, minSpeed2, maxSpeed2, accelerationTime2))

    def enableMotorExcitation(self, stage1 = True, stage2 = False):
        """
        Enables motor excitation
        """
        if stage1 in (True, False):
            self.write(b'C:1%d' % stage1)

        if stage2 in (True, False):
            self.write(b'C:2%d' % stage2)

    def getStatus(self):
        """
        Returns the status of the controller
        """
        self.write(b'Q:')
        return self.readline()

    def getACK3(self):
        """
        Returns the status of ACK3
        """
        self.write(b'!:')
        return self.readline()

    def getVersion(self):
        """
        Returns the ROM version
        """
        self.write(b'?:V')
        return self.readline()
