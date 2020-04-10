from enum import Enum

class ENUM_CTR_NWM_NFC(Enum):
    CTR_NWM_NFC_POWM = 0
    CTR_NWM_NFC_RST_FBD = 1

class ENUM_NFC_DIAG(Enum):
    NFC_RDUN_ID = 0
    NFC_DIAG_TYP = 1
    NFC_DIAG_BYTE_1_DT = 2
    NFC_DIAG_BYTE_2_DT = 3
    NFC_DIAG_BYTE_3_DT = 4
    NFC_DIAG_BYTE_4_DT = 5
    NFC_DIAG_BYTE_5_DT = 6
    NFC_DIAG_BYTE_6_DT = 7


class Signal():
    def __init__(self, name, pos, length, value):
        self.name = name
        self.pos = pos
        self.length = length
        self.default_value = value

    def get(self):
        return (self.name.name, self.pos, self.length, hex(self.default_value))

class Frame(object):
    def __init__(self,id, name, frame_type, platform, signall_list, dlc):
        self.id = id
        self.name = name
        self.frame_type = frame_type
        self.platform = platform
        self.signall_list = signall_list
        self.payload = [0] * dlc
        for l in self.signall_list:
            self.SetSignall(l.name, l.default_value)



        

    def SetSignall(self,Signal, value):
        p = 0
        va = Signal.value
        leng  = self.signall_list[va].length
        pos  = self.signall_list[va].pos

        for i in range(pos,pos+leng):
            byte = i//8
            bit = i%8
            temp = value >> p & 1

            if temp != 0:
                self.payload[byte] |= 1 << bit;
            else:
                self.payload[byte] &= ~(1 << bit)
            p=p+1

    def ReadSignall(self,Signal):

        va = Signal.value
        leng  = self.signall_list[va].length
        pos  = self.signall_list[va].pos

        p = 0
        value_to_return = 0
        shortValue = 0
        j = 0
        for i in range(pos,pos+leng):
            byte = i//8;
            bit = i%8;
            if ((self.payload[byte] & (1 << bit)) != 0):
                pow = 2**(p%8)
                #if(pow < 256):
                shortValue  = shortValue + pow
            if((p%8) == 7):
                value_to_return= value_to_return + (shortValue << j)
                shortValue = 0
                j = j+8
            p = p+1
        value_to_return = value_to_return + (shortValue << j)
        return value_to_return







ctr_nwm_nfc = [
        Signal(ENUM_CTR_NWM_NFC.CTR_NWM_NFC_POWM, 0, 8, 0xff),
        Signal(ENUM_CTR_NWM_NFC.CTR_NWM_NFC_RST_FBD, 8, 4, 0x0d),
    ]

#print(ctr_nwm_nfc[0].pos)
nfc = Frame(1888,'nfc_frame', 'rx', 'sp2015', ctr_nwm_nfc, 8)


Frames = {nfc.name : nfc}


print(nfc.payload)


#print(ENUM_CTR_NWM_NFC.CTR_NWM_NFC_POWM.name.value)
print(nfc.ReadSignall(ENUM_CTR_NWM_NFC.CTR_NWM_NFC_POWM))

nfc.SetSignall(ENUM_CTR_NWM_NFC.CTR_NWM_NFC_POWM,12)
print(nfc.payload)
