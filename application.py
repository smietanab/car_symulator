from tkinter import *
from tkinter.ttk import *
from template import *
import serial
import time
import _thread
#from pycan.drivers.canusb import CANUSB
from common import CANMessage
from usb import CANUSB
from frames.frames import *
from entry_popup.popup import *

CR = b'\x0d'
BELL = b'\x07'
OPEN_CMD = b'O\r'
CLOSE_CMD = b'C\r'
BAUDRATE = 2004800
CMD_500K = b'1S6'
CMD_OPEN = b'1O'
CMD_CLOSE = b'1C'
CMD_OK = b'1\r'
CMD_ALREADY_OPENED = b'1E9\x07'

class ComException(Exception):
    def __init__(self, message):
        self.message = message

class SymException(Exception):
    def __init__(self, message):
        self.message = message
        
class Application(object):
    def __init__(self, connection, message, logs):


        self.is_CANopened = False
        self.cnt = connection
        self.cnt.btn_connect.config(command = self.connect_to_com)     
        self.msg = message
        self.msg.btn_send.config(command = self.send)
        self.log = logs
        self.tid = _thread.start_new_thread(self.__process_inbound_queue, ())
        self.msg.txt_messages.bind('<<ListboxSelect>>', self.on_select) 
        self.msg.listBox.bind('<Double-1>', self.set_cell_value)

        for f in Frames.values():
            self.msg.txt_messages.insert(END,(f.name))    

    def set_cell_value(self, event):

        item = self.msg.listBox.focus()

        rowid = self.msg.listBox.identify_row(event.y)
        column = self.msg.listBox.identify_column(event.x)
        x,y,width,height = self.msg.listBox.bbox(rowid, column)
        value = self.msg.listBox.set(rowid, column)
        pady = 0       
        text = self.msg.listBox.item(rowid, 'values')[3]
        self.entryPopup = EntryPopup(self.msg.listBox, self.msg.listBox.item(item, "values")[3],  self.actual_frame, self.msg.listBox.index(item))
        self.entryPopup.place( x=0, y=y+pady, anchor='w', relwidth=1)

    def on_select(self, event):
        w = event.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        
        for i in self.msg.listBox.get_children():
            self.msg.listBox.delete(i)

        self.actual_frame = Frames[value]
        
        for signal in Frames[value].signall_list:
            self.msg.listBox.insert('', 'end',values=(signal.get()))
        
    def send(self):
        self.serialPort.write(b't1008FFAAFFAAFFAAFFAA' + CR)

    def _thread_function(self):
        while(1):
            if(self.is_CANopened):

                if(self.serialPort.inWaiting() != 0):
                    self.cnt.txt_connect.insert(END,self.serialPort.read(31))

    def __process_inbound_queue(self):
        inWaiting = 0
        ile, ileT, ileE, ix = 0, 0, 0, 0
        self.rxMsg = b''
        inWaiting = 0
#      self.serialPort.flushInput()

        while(1):
            if(self.is_CANopened):  #and self.serialPort.inWaiting() != 0):
                #self.rxMsg += self.serialPort.read(31)  # Max len of frame = 31
                #print(self.rxMsg)
                
                if CR in self.rxMsg:
                    ix = self.rxMsg.find(CR)
                    if BELL in self.rxMsg[:ix]:
                        ix = self.rxMsg.find(BELL) + 1
#                       self.__handleInError(ix)
                    else:
                        ix += 1
                        self.__handleInMsg(ix)
                elif BELL in self.rxMsg:
                    ix = self.rxMsg.find(BELL) + 1
 #                  self.__handleInError(ix)
                else:

                    if(self.serialPort.inWaiting() != 0):
                       self.rxMsg += self.serialPort.read(31)  # Max len of frame = 31
                       print(self.rxMsg)
                       print("line 156")


    def __handleInMsg(self, ix):

        try:
            #tm = time.time()
            msg = self.rxMsg[:ix]
            self.rxMsg = self.rxMsg[ix:]
            if b'\0' in msg:
                print("MError 0 in msg:%s|" % msg.replace(b'\0', b'\\x00'))
                msg = msg.replace(b'\0', b'')
                #return
                                
            type = 0
            s_ix, e_ix = 0, 0

            if msg[0:1] in CHANNEL_NUMBERS:
                chNr, hdr, s_ix = msg[0:1], msg[1:2], 2
                ch = int(chNr.decode(), 16)
            else:
                hdr, s_ix = msg[0:1], 1
                ch = self.canNrInt
                
            new_msg = None
            
            if hdr in STD_MSG_HEADERS:
                if hdr in b'TQ':
                    type |= Type_Ext
                    e_ix = s_ix + 8
                else:
                    e_ix = s_ix + 3
                if hdr in b'Tt':
                    type |= Type_Tx

#                Get the CAN ID
                can_id = int(msg[s_ix:e_ix].decode(), 16)

#                Get the DLC (data length)
                s_ix = e_ix
                e_ix += 1
                dlc = int(msg[s_ix:e_ix].decode(), 16)

#               Get the payload
                s_ix = e_ix
                e_ix = s_ix + dlc*2

                if can_id == 0xFFF and type & Type_Ext == 0 and dlc == 6:
#                   The absolute time frame - resolution 1us
                    self.tt = int(msg[s_ix:e_ix].decode(), 16) 
                    self.time = self.tt & 0xFFFF
                    self.c_time = self.tt - self.time
                    return
                else:
                    payload = []
                    for x in range(s_ix, e_ix, 2):
                        val = int(msg[x:x+2].decode(), 16)
                        payload.append(val)
                    
#                   Build the message                    
                    new_msg = CANMessage(can_id, payload, type=type, 
                                         channel=ch)
                                         
#                   Get the timestamp (if any)
                    if len(msg[e_ix:-1]) == 4:
                        new_msg.time_stamp = self.calcTimeStamp( msg[e_ix:-1].decode(), ch )

            elif hdr in REM_MSG_HEADERS:
                print( __name__ + " Not supported" )
                return
            elif hdr in ACK_MSG or hdr in HEX_CHARS and len(msg) == 6:
                if len(msg) > 5: # Get the timestamp (if any)
                    ts = self.calcTimeStamp( msg[-5:-1].decode(), 0 )
                    new_msg = CANMessage(0, msg[:-5], type=Type_ACK, channel=ch)
                    new_msg.time_stamp = ts
                else:
                    new_msg = CANMessage(0, msg[:-1], type=Type_ACK, channel=ch)

            elif hdr in SET_MSG_HEADERS:
                print(msg)
                print( "line 235" )
                if len(msg) > 5 and msg[-6] == ord('T'): # Get the timestamp
                    ts = self.calcTimeStamp( msg[-5:-1].decode(), 0 )
                    new_msg = CANMessage(0, msg[:-6]+b'\r', type=Type_SET, channel=ch)
                    new_msg.time_stamp = ts
                else:
                    new_msg = CANMessage(0, msg, type=Type_SET, channel=ch)
            else:
                print("Unknown type of message header: |%s|" % hdr.decode() )
                # Unknown type --> assume it's a command response
                # TODO: Log an alarm on any <BELL> responses found
                self.response = msg
                return


#('Time','CAN', 'Type', 'ID', 'DLC', 'Payload')

            if(new_msg.id != 0):
                self.log.listBox.insert('', 'end',values=(new_msg.get() ))
            print( new_msg )
            print( "line 249 " )

        except IndexError as e:
            print( __name__ + " Bad message " + str(ch) + msg.decode() )
#                            print ord(msg[4]),  ord('\r')
            # TODO (A. Lewis) Log the bad message from the comport
            # Chuck partial messages
        except ValueError as e:
            m = msg.decode()
            m = m.replace('\a', '[BELL]')
            m = m.replace('\r', '[CR]')
            mCat = ''
            lnm = len(msg)
            if e_ix > lnm:
                print('__handleInMsg: index out of range', s_ix, e_ix,  lnm,  m)
            else:
                if s_ix > 0:
                    s_ix -= 1
                if e_ix < lnm:
                    e_ix += 1
                for k in range(s_ix, e_ix):
                    mCat += "%.2X" % ord(msg[k:k+1])
                print( "%s except: ValueError\n%s msg:%s|%d %d %d %s\n" \
                        % (__name__, str(e), m, s_ix, e_ix, lnm,  mCat)   )
            # Chuck malformed messages
        return

    def connect_to_com(self):
        try:
#Get COM PORTS
            self.com = self.cnt.comboBox_comlist.get()
            if self.com == "":
                raise ComException("No selected Com Port")
            self.cnt.txt_connect.insert(END,("Connecting to " + self.com + "...\n"))
#Try to open COM PORTS            
            self.serialPort = serial.Serial(port=self.com, baudrate=BAUDRATE,timeout=0.1, writeTimeout=5)
#If is not open raise except     
            if(self.serialPort.is_open == False):
                raise ComException("Can't open port " + self.com)
            self.cnt.txt_connect.insert(END,("Connected to: " + self.com + " Baudrate: " +str(BAUDRATE) + "\n"))
#Try to connect to canSimulator
            self.cnt.txt_connect.insert(END,("Connecting to CAN1... \n"))
            self.serialPort.write(CMD_CLOSE + CR)
            time.sleep(1)
            value = self.serialPort.read(31)
#Try set CAN baudrate         
            self.serialPort.write(CMD_500K + CR)
            time.sleep(1)
            value = self.serialPort.read(31)
            if(value != CMD_OK):
                print(value)
                raise SymException("Can't set CAN1 baudrate, please restart device ")
#Try open CAN port   
            self.serialPort.write(CMD_OPEN + CR)
            time.sleep(1)
            value = self.serialPort.read(31)
            if((value == CMD_OK) or (value == CMD_ALREADY_OPENED)):
                self.cnt.txt_connect.insert(END,("CAN1 opened, Baudrate: 500k \n"))
                print(value)
            else:
                raise SymException("Can't open CAN1 port, please restart device ")


            self.is_CANopened = True


        except ComException as e:
            self.cnt.txt_connect.insert(END,str(e.args) + "\n")
        except serial.serialutil.SerialException:
            self.cnt.txt_connect.insert(END,"Can't open port " + self.com + "\n")
        except SymException as e:
            self.cnt.txt_connect.insert(END,str(e.args) + "\n")
