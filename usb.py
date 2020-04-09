import serial
import _thread
import time
import sys
major = sys.version_info.major
VERSION = '2.30.0'

QUEUE_DELAY = .1
CAN_TX_TIMEOUT = 100  # ms
CAN_RX_TIMEOUT = 10  # ms
MAX_BUFFER_SIZE = 1000
COMMAND_TIMEOUT = 1.0  # seconds
CR = b'\x0d'
BELL = b'\x07'
TERMINATORS = [CR, BELL ]
STD_MSG_HEADERS = [b't', b'T', b'q', b'Q']
REM_MSG_HEADERS = [b'r', b'R', b'p', b'P']
ERR_MSG_HEADERS = [b'e', b'E']
SET_MSG_HEADERS = [b'N', b'V', b'F']
ACK_MSG = [b'z', b'Z', CR]
# 0-GPIO; 1..6-CAN; 7,8-LIN; 9-POT; A,B-ADC; D-UART
CHANNEL_NUMBERS = b'0123456789ABD'
S_CHANNELS = b'12345678D'
HEX_CHARS = b'0123456789ABCDEF'

BIT_RATE_CMD = {}
#CAN speeds
BIT_RATE_CMD['10K'] = b'S0\r'
BIT_RATE_CMD['20K'] = b'S1\r'
BIT_RATE_CMD['50K'] = b'S2\r'
BIT_RATE_CMD['100K'] = b'S3\r'
BIT_RATE_CMD['125K'] = b'S4\r'
BIT_RATE_CMD['250K'] = b'S5\r'
BIT_RATE_CMD['500K'] = b'S6\r'
BIT_RATE_CMD['800K'] = b'S7\r'
BIT_RATE_CMD['1M'] = b'S8\r'
BIT_RATE_CMD['83K'] = b'S9\r'

#LIN,UART speeds
BIT_RATE_CMD['1.2K'] = b'S0\r'
BIT_RATE_CMD['2.4K'] = b'S1\r'
BIT_RATE_CMD['4.8K'] = b'S2\r'
BIT_RATE_CMD['9.6K'] = b'S3\r'
BIT_RATE_CMD['19.2K'] = b'S4\r'
BIT_RATE_CMD['57.6K'] = b'S5\r'
BIT_RATE_CMD['115.2K'] = b'S6\r'
BIT_RATE_CMD['230.4K'] = b'S7\r'
BIT_RATE_CMD['460.8K'] = b'S8\r'
BIT_RATE_CMD['921.6K'] = b'S9\r'

OPEN_CMD = b'O\r'
CLOSE_CMD = b'C\r'
TIME_STAMP_CMD = [b'Z0\r',b'Z1\r',b'Z2\r',b'Z3\r']
TIME_STAMP_SYNC_CMD = b'ZF\r'
GET_VERSION_CMD = b'V\r'
GET_SERIAL_CMD = b'N\r'
MIN_VERSION = 0x0222
LIN_VERSION = 0x0225    # Maybe :) with this version will be OK. 
                        # With 222 is not stabil
ALL_INTERFACE = 0x226

# Identifiers for FTDI chip on CanSimulator
FTDI_QUAD_VID = 0x0403
FTDI_QUAD_PID = 0x6011

Type_Raw = 0    
Type_ISO = 1
Type_BAP = 2
Type_UDS = 3
Type_JRE = 4

Type_Conf = 8
Type_E2E = 9        # end to end


Type_ACK = 13       #
Type_RTR = 14       # request, get
Type_SET = 15       # set
#    Reserved (5 to 7 and 10,11,12) for another protocols
# ......
# Type_Parameter
Type_Tx = 16
Type_Cyclic = 32
Type_Ext = 64
Type_Addr = 128
Type_Error = 256



class CANUSB(object):
    """LAWICEL CANUSB CAN driver interface
    """
    def __init__(self, **kwargs):
        """com_port - path to the usb com port
                eg. /dev/ttyUSB0, /dev/ttyUSB1 on Linux
                COM7,COM5 on windows.
                Windows maps the ports do not necessarily consecutively !!!!
            com_baud - baud rate of com port default 2000000
                (do not set  any other value)
            bit_rate - on CAN default 500K;
                possible values: ['10K',  '20K', '50K', '100K', '125K', '250K',
                                        '500K', '800K', '1M', '83K']
            can_nr - connect to this driver ( 1 - 6 ) if not set
                default connect to port 1,3,5,(7) on com_port0
                                and to port 2,4,6,(8) on com port1
            set_all - set speed and open the channel if True (default True)
            verbose - if True (default False)
            vv      - very verbose if True (default False)
        """
        # Open the COM port
        port = kwargs['com_port']  # Throws key error
        baud = int(kwargs.get('com_baud', 2000000))
        br = kwargs.get('bit_rate', '500K')
        canNr = kwargs.get('can_nr', None)
        self.setAll = kwargs.get('set_all', True)
        print( "self.setAll =", self.setAll )
        print( kwargs )
        self.verbose = kwargs.get('verbose', False)
        self.vverbose = kwargs.get('vv', False)
        self.canNr = ''
        self.canNrInt = 0
        self.busIsOn = False
        # self.multi value is used for calculate real time from timestamps
        # calculate multi to convert time to 1us
        multi = 1
        if br[-1] != 'M':
            if br == '800K':
                self.chMulti[channel] = 1.25
            else:
                multi = 1000 // int(br[:-1])
        #               GPIO      CAN1 to CAN6    LIN,ADC,POT,UART,..
        self.chMulti = [1] + [multi] * 6 + [1] * 9
        #print (self.multi)
        self.time_stamp = kwargs.get('time_stamp', 0)
        self.port = serial.Serial(port=port, baudrate=baud,
                                  timeout=0.1, writeTimeout=5)
        self.port.flushInput()
        self.rx_buffer = ''
        self.rxMsg = ''
        self.response = ''
        self.c_time = 0
        self.time = 0
        self.versionHW = b'0'
        self.serialNr = b''
        self.ileE = 0
        self.ileT = 0
        self.ileR = 0
        self.ile = 0
        self.ob_t = None
        self.ib_t = None
        self.cmd_logger_cb = None
        # values to group of 'Queue Full' message
        self.nrOfqf = 0
        self.lasttime = time.time()

        self._send_command(CLOSE_CMD)
        #self.event = threading.Event()
        self.nrTimeouts = 0
        self._TypeOfSend = [self.__send_Raw] * 16
        self._TypeOfSend[Type_ISO] = self.__send_ISO
        self._TypeOfSend[Type_BAP] = self.__send_BAP
        self._TypeOfSend[Type_UDS] = self.__send_UDS
        self._TypeOfSend[Type_JRE] = self.__send_JRE
        self._TypeOfSend[Type_SET] = self.__send_SET
        self._TypeOfSend[Type_RTR] = self.__send_RTR

        self.lastPrint = ""
        self.nrOfLastPrints = 0
        self.timeOfLastPrint = time.time()
        self.tt = None;    # absolute time
        
        # Clear out the rx/tx buffers per manual
        for x in range(5):
            self.port.write(b'\r')

        self.port.flushInput()

        #self.event.wait(0.2)
        time.sleep(1)
        if not self.__test_version():
            msg = 'Error SW version %s required minimum %X !'
            raise ValueError(msg % (str(self.versionHW), MIN_VERSION))
        if not self.__get_serial_nr():
            raise ValueError("No serial nr")
        version = int(self.versionHW.decode(), 16)
        #if canNr and canNr.isdigit() and int(canNr) < 7 and int(canNr) > 0:
        if 1:
            self.canNr = canNr
            self.canNrInt = int(canNr)
        elif self.serialNr[3:4] == b'0':
            if version >= ALL_INTERFACE:
                self.canNr = b'13579BD'
            elif version >= LIN_VERSION:
                self.canNr = b'1357'     # software with LIN
            else:
                self.canNr = b'135'
            self.canNrInt = 1
        elif self.serialNr[3:4] == b'1':
            if version >= ALL_INTERFACE:
                self.canNr = b'02468A'
            elif version >= LIN_VERSION:
                self.canNr = b'2468'     # software with LIN
            else:
                self.canNr = b'246'
            self.canNrInt = 2
        else:
            msg = 'Error Serial Number %s the last char should be 0 or 1'
            raise ValueError(msg % self.serialNr)

        self.drukuj( 'SW version ' + str(self.versionHW) )
        # Turn on the time stamps
        ts = self.time_stamp
        if 0 <= ts <= 3:
            self.drukuj( 'ts=%d' % ts )
            self._send_command(TIME_STAMP_CMD[ts])

        # Build the inbound and output buffers
       # self.inbound = queue.Queue(MAX_BUFFER_SIZE)
       # self.inbound_count = 0
       # self.outbound = queue.Queue(MAX_BUFFER_SIZE)
       # self.outbound_count = 0

        # Tell python to check for signals less often (default 1000)
        #   - This yeilds better threading performance for timing
        #     accuracy
        sys.setcheckinterval(10000)
        #self._running = threading.Event()
        print("before setAll")
        if self.setAll:
            # Set the default paramters
            self.update_bus_parameters(br)
            # Go on bus
          #  self.bus_on()
            print("after setAll")

    def _send_command(self, cmd, timeout=COMMAND_TIMEOUT):
        # Due to the CANUSB driver not sending confirmation during moderate
        # bus loads, waiting for any amount of will likely be useless.

        # Send the command
        bytes_sent = 0
        try:
            bytes_sent = self.port.write(cmd)
            if self.cmd_logger_cb:
                self.cmd_logger_cb(cmd)
            if self.vverbose:
                print(cmd)
        except serial.SerialTimeoutException:
            self.nrTimeouts += 1
            pass

        return (bytes_sent == len(cmd))

    def __send_BAP(self, msg):
        self.drukuj( "BAP" )

    def __send_JRE(self, msg):
        self.drukuj( "JRE" )

    def __send_UDS(self, msg):
        self.drukuj( "UDS" )

    def __send_SET(self, msg):

        t = type(msg.payload)
        if t == bytes:
            cmd = msg.payload + CR
        #elif t == type(''):
        #    cmd = msg.payload.encode('ascii') + CR
        else:
            raise ValueError("wrong type of msg.payload for Type_SET")
            return
            
#        if self._running.is_set():
#            self._send_command(CLOSE_CMD)
#            self._send_command(cmd)
#            self._send_command(OPEN_CMD)
#        else:
        #print(("cmdNr(%d) = %s" % (self.ile, cmd)).replace('\r', '[cr]'))
        self._send_command(cmd)
        self.drukuj( "sended SET cmd = |%s| by driver %s" % (str(cmd), str(self.serialNr)) )
        print( "sended SET cmd = |%s| by driver %s" % (str(cmd), str(self.serialNr)) )
        

    def __send_ISO(self, msg):
        outbound_msg = b''
        if msg.chan >= 0 and msg.chan < 15:
            outbound_msg += ('%X' % msg.chan).encode()

        if msg.delay > 0:
            outbound_msg += ('o%06X' % (msg.delay & 0xFFFFFF)).encode()

        if msg.type & Type_Cyclic:
            outbound_msg += ('c%04X' % (msg.time_stamp & 0xFFFF)).encode()

        if msg.type & Type_Ext:
            id_str = ("I%08X" % (msg.id & 0x1FFFFFFF)).encode()
            ack = b'Z\r'
        else:
            id_str = ("i%03X" % (msg.id & 0x7FF)).encode()
            ack = b'z\r'

        outbound_msg += id_str
        outbound_msg += ("%03X" % (msg.dlc)).encode()

        for c in msg.payload:
            outbound_msg += ("%02X" % c).encode()

        self.drukuj( 'ISO:' + str(outbound_msg) + '[CR]' )
        outbound_msg += CR
        self._send_command(outbound_msg)


    def __send_Raw(self, msg):
        outbound_msg = b''

        if msg.chan >= 0 and msg.chan < 15:
            outbound_msg += ('%01X' % msg.chan).encode()

        if msg.delay > 0:
            outbound_msg += ('o%06X' % (msg.delay & 0xFFFFFF)).encode()

        if msg.type & Type_Cyclic:
            outbound_msg += ('c%04X' % (msg.time_stamp & 0xFFFF)).encode()

        if msg.type & Type_Ext:
            id_str = ("T%08X" % (msg.id & 0x1FFFFFFF)).encode()
            ack = b'Z\r'
        else:
            id_str = ("t%03X" % (msg.id & 0xFFF)).encode()
            ack = b'z\r'

        outbound_msg += id_str
        outbound_msg += ("%X" % (msg.dlc)).encode()

        for x in range(msg.dlc):
            outbound_msg += ("%02X" % (msg.payload[x])).encode()

        self.drukuj( 'Raw: ' + outbound_msg.decode() + '[CR]' )
        outbound_msg += b"\r"
        self._send_command(outbound_msg)


    def __send_RTR(self, msg):
        outbound_msg = b''

        if msg.chan >= 0 and msg.chan < 15:
            outbound_msg += ('%X' % msg.chan).encode()

        if msg.delay > 0:
            outbound_msg += ('o%06X' % (msg.delay & 0xFFFFFF)).encode()

        if msg.type & Type_Cyclic:
            outbound_msg += ('c%04X' % (msg.time_stamp & 0xFFFF)).encode()

        if msg.type & Type_Ext:
            id_str = ("R%08X" % (msg.id & 0x1FFFFFFF)).encode()
            ack = b'Z\r'
        else:
            id_str = ("r%03X" % (msg.id & 0xFFF)).encode()
            ack = b'z\r'

        outbound_msg += id_str
        outbound_msg += ("%X" % (msg.dlc)).encode()

        self.drukuj( 'RTR: ' + outbound_msg.decode() + '[CR]' )
        outbound_msg += b"\r"
        self._send_command(outbound_msg)
        

    def drukuj(self, message):
        if self.verbose:
            tmptime = time.time()
            if message == self.lastPrint:
                self.nrOfLastPrints += 1
                if tmptime - self.timeOfLastPrint > 10:
                    port = chr(self.serialNr[3])
                    print("%s %s (+%d times)" % 
                        (port, message, self.nrOfLastPrints))
                else:
                    return
            else:
                port = chr(self.serialNr[3])
                if self.nrOfLastPrints > 0:
                    print("%s %s (+%d times)" % 
                        (port, self.lastPrint, self.nrOfLastPrints))
                print("%s %s" % (port, message))
                self.lastPrint = message
                
            self.nrOfLastPrints = 0
            self.timeOfLastPrint = tmptime

    def __test_version(self):
        sz = 6          # "V1234\r" - 6 chars
        ret = False
        self._send_command(GET_VERSION_CMD)
        timeout = time.time() + 1.
        readed = b""
        bytes_to_read = 0

        while timeout > time.time():
            bytes_to_read = self.port.inWaiting()
            if bytes_to_read >= sz:
                readed += self.port.read(sz)
                ix = readed.find(b'V')
                if ix == -1:
                    readed = b''
                    continue
                ix += 1
                tmp = len(readed) - ix
                if tmp >= 4:
                    self.versionHW = readed[ix:ix+4]
                else:
                    sz = 4 - tmp
                    continue
                if int((self.versionHW).decode(), 16) >= MIN_VERSION:
                    ret = True
                else:
                    ret = False
                break
        return ret

    def __get_serial_nr(self):
        sz = 6          # "N1234\r" - 6 chars
        ret = False
        self._send_command(GET_SERIAL_CMD)
        timeout = time.time() + 1.
        readed = b''
        bytes_to_read = 0

        while timeout > time.time():
            bytes_to_read = self.port.inWaiting()
            if bytes_to_read >= sz:
                readed += self.port.read(sz)
                ix = readed.find(b'N')
                if ix == -1:
                    readed = b''
                    continue
                ix += 1
                tmp = len(readed) - ix
                if tmp >= 4:
                    self.serialNr = readed[ix:ix+4]
                    self.drukuj( "serial number = " + str(self.serialNr) )
                    ret = True
                    break
                else:
                    sz = 4 - tmp
                    continue
        return ret

    def update_bus_parameters(self, bit_rate):
        # Default values are setup for a 500k connetion
        br_cmd = BIT_RATE_CMD.get(bit_rate, None)
        if br_cmd:
            for k in range(len(self.canNr)):
                c = self.canNr[k:k+1]
                if c in S_CHANNELS:
                    cmd = c + br_cmd
                elif c == b'0':
                    cmd = c + b's77777777\r'
                elif c in b'9AB':
                    cmd = c + b'sE1000000\r'
                else:
                    continue
                if not self._send_command( cmd ):
                    return False
        return True
