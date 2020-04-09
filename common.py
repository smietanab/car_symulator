# -*- coding: utf-8 -*-
# Copyright (c) 2013 The pycan developers. All rights reserved.
# Project site: http://172.20.10.175/polarion/#/project/T0048/repository/browser/trunk/30_Development/3040_Software-Engineering/304040_SW-Construction/304040_Source-Code/pyCAN',
# Use of this source code is governed by a MIT-style license that
# can be found in the LICENSE.txt file   for the project.


# Type_Protocol 0 - 15
Type_Raw = 0
Type_ISO = 1
Type_BAP = 2
Type_UDS = 3
Type_JRE = 4

Type_Conf = 8
Type_E2E = 9

Type_ACK = 13
Type_RTR = 14
Type_SET = 15
#    Reserved (5 to 14) for another protocols
# ......
# Type_Parameter
Type_Tx = 16
Type_Cyclic = 32
Type_Ext = 64
Type_Addr = 128
Type_Error = 256


# Type_of_message = Type_Protocol | TypeParameter1 | TypeParameter2 | ....


class CANMessage(object):
    """Models the CAN message

    Attributes:
        id: An integer representing the raw CAN id
        payload: Message payload to be transmitted or received
        extended: A boolean indicating if the message is a 29 bit message
        ts: An integer representing the time stamp
        cyclic: A boolean indicating if the message is cyclic with the time period ts in ms
        channel: An integer ( 1 to 6 ) representing the CAN channel of message
        type: Type_of_message - see below
    """

    TS_SECONDS = 1.0
    TS_MILLI_SEC = 1.0e3
    TS_MICRO_SEC = 1.0e6
    # if exponential the value is in resolution 10 us
    # and has hex value in form:
    #   -  'MMMP' for cyclic time = 0xMMM * 2**0xP
    #   - 'MMMMMP' for one_shot time = 0xMMMMM * 2**0xP
    # so if we set value 1234 = 0x4d2
    # the value is 0x4d * 2**2 = 308 = 3,08 ms
    # if we set value out of min/max the min/max will be set
    TS_EXPONENT = 0

    def __init__(
        self,
        id,
        payload,
        extended=True,
        ts=0,
        scale=TS_MILLI_SEC,
        cyclic=False,
        channel=None,
        tx=False,
        type=None,
        delay=0,
    ):
        """Inits CANMesagge."""
        self.id = id
        self.name = None
        self.dlc = len(payload)
        self.payload = payload
        self.time_scale = scale
        self.chan = channel

        if type == None:
            self.cyclic = cyclic
            self.tx = tx
            self.extended = extended
            self.type = 0
            if cyclic:
                self.type = Type_Cyclic
            if tx:
                self.type |= Type_Tx
            if extended:
                self.type |= Type_Ext
        else:
            self.type = type
            self.cyclic = type & Type_Cyclic != 0
            self.tx = type & Type_Tx != 0
            self.extended = type & Type_Ext != 0

        if scale:
            self.delay = self.set_HexE(delay * self.TS_MILLI_SEC / scale, 0xFFFFF)
            if self.cyclic:
                self.time_stamp = int(
                    self.set_HexE(ts * self.TS_MILLI_SEC / scale, 0xFFF)
                )
            else:
                self.time_stamp = int(ts)

        else:
            self.time_stamp = int(ts)
            self.delay = delay

    def set_HexE(elf, value, mm):
        value = int(value * 100 + 0.5)
        if value <= 0:
            return 0

        power = 0
        while value > mm:
            value //= 2
            power += 1
        if power > 15:
            return mm * 16 + 0xF
        else:
            return value * 16 + power

    def __str__(self):
        data = ""
        tx = "Rx "
        cyclic = ""
        delayed = ""
        cd = False
        if self.type == Type_SET:
            tmp = self.payload
            if type(tmp) == type(b""):
                tmp = tmp.decode("ascii")
            return "chan:%X %s" % (self.chan, tmp.replace("\r", "\\r"))
        for d in self.payload:
            data += "{0},".format(hex(d)[2:])
        try:
            id = hex(self.id)[2:]
        except TypeError:
            id = self.id

        if self.type & Type_Ext:
            id += "x"
        else:
            id += " "

        if self.type & Type_Tx:
            tx = "Tx "

            if self.type & Type_Cyclic:
                cyclic = "Cyclic:%d " % self.time_stamp
                cd = True
            if self.delay > 0:
                delayed = "Delay:%d " % self.delay
                cd = True
        if cd:
            return "%s%s %s %s%s,%d : %s" % (
                delayed,
                cyclic,
                self.chan,
                tx,
                id,
                self.dlc,
                data,
            )
        else:
            return "%f %s %s%s,%d : %s" % (
                self.time_stamp,
                self.chan,
                tx,
                id,
                self.dlc,
                data,
            )



    def get(self):
        data = ""
        tx = "Rx "
        cyclic = ""
        delayed = ""
        cd = False
        if self.type == Type_SET:
            tmp = self.payload
            if type(tmp) == type(b""):
                tmp = tmp.decode("ascii")
            return "chan:%X %s" % (self.chan, tmp.replace("\r", "\\r"))
        for d in self.payload:
            data += "{0},".format(hex(d)[2:])
        try:
            id = hex(self.id)[2:]
        except TypeError:
            id = self.id

        if self.type & Type_Ext:
            id += "x"
        else:
            id += " "

        if self.type & Type_Tx:
            tx = "Tx "

            if self.type & Type_Cyclic:
                cyclic = "Cyclic:%d " % self.time_stamp
                cd = True
            if self.delay > 0:
                delayed = "Delay:%d " % self.delay
                cd = True
        if cd:
            return "%s%s %s %s%s,%d : %s" % (
                delayed,
                cyclic,
                self.chan,
                tx,
                id,
                self.dlc,
                data,
            )
        else:
            return (
                self.time_stamp,
                tx,
                id,
                self.dlc,
                data,
            )

class IDMaskFilter(object):
    """CAN ID Mask Filter

    Attributes:
        mask: An integer representing the bit fields required to match
        code: An integer representing the id to apply the mask against
        extended: A boolean indicating if the message is a 29 bit message
    """

    def __init__(self, mask, code, extended=True):
        """Inits Mask Filter."""
        self.mask = mask
        self.code = code
        self.extended = extended

    def filter_match(self, msg):
        """Tests if the given CAN message should pass through the filter"""
        if not msg:
            return False

        # Check the extended bit
        if msg.extended != self.extended:
            return False

        # Check the mask / code combo
        target = self.mask & self.code
        try:
            if (msg.id & self.mask) == target:
                return True
            else:
                return False
        except ValueError:
            return False


class CANTimeoutWarning(UserWarning):
    def __unicode__(self):
        return "Warning: pyCAN Timeout Detected"
