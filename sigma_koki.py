"""
This is an interface module for instruments produced by Sigma Koki
"""

try:
    # It is not needed to import ValueError in newer Python versions
    from exceptions import ValueError
except:
    pass
import serial
import time

class BaseStageController(object):
    """
    Stage controller class commonly used for Sigma Koki GSC02 and SHOT702
    """
    def __init__(self, baudrate, product):
        self.__baudRate = baudrate
        self.__parityBit = 'N' # None
        self.__dataBit = 8
        self.__stopBit = 1
        self.__rtscts = True
        self.__product = product
        self.__acknowledge =  True

    def setBaudRate(self, rate):
        rates = {'GSC-02': (2400, 4800, 9600, 19200),
                 'SHOT-702' : (38400,),
                 'SHOT-702H' : (38400,)}
        if rate in rates[self.__product]:
            self.__baudRate = rate
        else:
            raise ValueError('Attempting to set an invalid buard rate of %d to %s. The rate must be chosen from %s.' % (rate, self.__product, rates[self.__product]))

    def disableAcknowledge(self):
        self.__acknowledge = False

    def write(self, command, acknowledge=True):
        # 'str' class needs be converted into 'bytes'
        # e.g., 'command' -> b'command'
        self.serial.write((command + '\r\n').encode())

        if not self.__acknowledge or not acknowledge:
            return
        
        ack = self.readline()
        if ack == 'OK':
            return
        else:
            raise RuntimeError('%s returned bad acknowledge "%s"' % (self.__product, ack))

    def query(self, command):
        self.write(command, False)
        return self.readline()

    def readline(self):
        # convert 'bytes' to 'str'
        result = str(self.serial.readline())
        if result[:2] == "b'" and result[-1:] == "'":
            result = result[2:-1] # drop byte code prefix and suffix
        if result[-4:] == '\\r\\n':
            result = result[:-4] # drop delimeter

        return result

    def open(self, port, readTimeOut = 1, writeTimeOut = 1):
        self.serial = serial.Serial(port         = port,
                                    baudrate     = self.__baudRate,
                                    bytesize     = self.__dataBit,
                                    parity       = self.__parityBit,
                                    stopbits     = self.__stopBit,
                                    timeout      = readTimeOut,
                                    writeTimeout = writeTimeOut,
                                    rtscts       = self.__rtscts)

    def close(self):
        self.serial.close()

    def returnToMechanicalOrigin(self, stage1, stage2):
        """
        Moves the stages to the +/- end points and reset the coordinate values
        to zero.
        """
        if self.__product == 'GSC-02':
            if stage1 == '+' and stage2 == '+':
                self.write('H:W++')
            elif stage1 == '+' and stage2 == '-':
                self.write('H:W+-')
            elif stage1 == '-' and stage2 == '+':
                self.write('H:W-+')
            elif stage1 == '-' and stage2 == '-':
                self.write('H:W--')
            elif stage1 == '+':
                self.write('H:1+')
            elif stage1 == '-':
                self.write('H:1-')
            elif stage2 == '+':
                self.write('H:2+')
            elif stage2 == '-':
                self.write('H:2-')
            else:
                return
        elif self.__product == 'SHOT-702':
            if stage1 == True and stage2 == True:
                self.write('H:W')
            elif stage1 == True:
                self.write('H:1')
            elif stage2 == True:
                self.write('H:2')
            else:
                return

    def move(self, stage1, stage2):
        """
        Moves the stages with the specified values. Since GSC-02 is a half-step
        stepping driver, 1 pulse corresponds to "half-step movement" in the
        stage catalogues.
        """
        if self.__product == 'GSC-02':
            limit = 16777214
        elif self.__product == 'SHOT-702':
            limit = 268435455

        if not (-limit <= stage1 <= limit):
            raise ValueError('stage1 must be between -%d and %d.' % (limit, limit))

        if not (-limit <= stage2 <= limit):
            raise ValueError('stage2 must be between -%d and %d.' % (limit, limit))

        command = 'M:W'
        if stage1 >= 0:
            command += '+P%d' % stage1
        else:
            command += '-P%d' % -stage1

        if stage2 >= 0:
            command += '+P%d' % stage2
        else:
            command += '-P%d' % -stage2

        self.write(command)
        self.go()

    def jog(self, stage1, stage2):
        """
        Moves the stages continuously at the minimum speed.
        stage1: '+' positive direction, '-' negative direction
        stage2: '+' positive direction, '-' negative direction
        If other values are given, stages will not move.
        """
        if stage1 == '+' and stage2 == '+':
            self.write('J:W++')
        elif stage1 == '+' and stage2 == '-':
            self.write('J:W+-')
        elif stage1 == '-' and stage2 == '+':
            self.write('J:W-+')
        elif stage1 == '-' and stage2 == '-':
            self.write('J:W--')
        elif stage1 == '+':
            self.write('J:1+')
        elif stage1 == '-':
            self.write('J:1-')
        elif stage2 == '+':
            self.write('J:2+')
        elif stage2 == '-':
            self.write('J:2-')
        else:
            return
        
        self.go()

    def go(self):
        """
        Moves the stages. To be used internally.
        """
        self.write('G')

    def decelerate(self, stage1, stage2):
        """
        Decelerates and stop the stages. 
        """
        if stage1 and stage2:
            self.write('L:W')
        elif stage1:
            self.write('L:1')
        elif stage2:
            self.write('L:2')

    def stop(self):
        """
        Stops the stages immediately.
        """
        self.write('L:E')

    def initializeOrigin(self, stage1, stage2):
        """
        Sets the origin to the current position.
        stage1: If true, set the origin of the stage 1 to the current position
        stage2: If true, set the origin of the stage 1 to the current position
        """
        if stage1:
            self.write('R:1')

        if stage2:
            self.write('R:2')

    def enableMotorExcitation(self, stage1 = True, stage2 = False):
        """
        Enables motor excitation
        """
        if stage1 in (True, False):
            self.write('C:1%d' % stage1)

        if stage2 in (True, False):
            self.write('C:2%d' % stage2)

    def getStatus(self):
        """
        Returns the status of the controller
        """
        return self.query('Q:')

    def getACK3(self):
        """
        Returns the status of ACK3
        """
        return self.query('!:')

    def waitForReady(self, timeout_in_sec):
        """
        Sleep up to timeout_in_sec until the ACK3 state becomes ready.
        """
        for i in range(timeout_in_sec*10):
            ack3 = self.getACK3()
            if ack3 == 'R': # ready
                break
            elif ack3 == 'B': # busy
                time.sleep(0.1)
            else: # unknown state
                time.sleep(0.1) # wait anyway 

    def getVersion(self):
        """
        Returns the ROM version
        """
        return self.query('?:V')

class GSC02(BaseStageController):
    """
    Stage controller GSC-02
    """
    def __init__(self):
        # 9600 bps the initial factory setting
        BaseStageController.__init__(self, 9600, 'GSC-02')
        self.disableAcknowledge()

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
            raise ValueError('Must be 0 <= accelerationTime1 <= 1000.')

        if not (0 <= accelerationTime2 <= 1000):
            raise ValueError('Must be 0 <= accelerationTime2 <= 1000.')

        if highspeed:
            self.write('D:2S%dF%dR%dS%dF%dR%d' % (minSpeed1, maxSpeed1, accelerationTime1, minSpeed2, maxSpeed2, accelerationTime2))
        else:
            self.write('D:1S%dF%dR%dS%dF%dR%d' % (minSpeed1, maxSpeed1, accelerationTime1, minSpeed2, maxSpeed2, accelerationTime2))

class SHOT702(BaseStageController):
    """
    Stage controller SHOT-702
    """
    def __init__(self):
        # 9600 bps the initial factory setting
        BaseStageController.__init__(self, 38400, 'SHOT-702')

    def setSpeed(self, minSpeed1, maxSpeed1, accelerationTime1, minSpeed2, maxSpeed2, accelerationTime2):
        """
        Sets the movement speeds of the stages
        minSpeed1/2: Minimum speed (PPS)
        maxSpeed1/2: Maximum speed (PPS)
        accelerationTime1/2: Acceleration time to be taken from min to max (ms)     
        """
        if not (1 <= minSpeed1 <= maxSpeed1 <= 500000):
            raise ValueError('Must be 1 <= minSpeed1 <= maxSpeed1 <= 500000.')

        if not (1 <= minSpeed2 <= maxSpeed2 <= 500000):
            raise ValueError('Must be 1 <= minSpeed2 <= maxSpeed2 <= 500000.')

        if not (0 <= accelerationTime1 <= 1000):
            raise ValueError('Must be 0 <= accelerationTime <= 1000.')

        if not (0 <= accelerationTime2 <= 1000):
            raise ValueError('Must be 0 <= accelerationTime <= 1000.')

        self.write('D:WS%dF%dR%dS%dF%dR%d' % (minSpeed1, maxSpeed1, accelerationTime1, minSpeed2, maxSpeed2, accelerationTime2))

    # Some query commands, ?:P, ?:S, ?:D, and ?:B, are not implemented yet
    
