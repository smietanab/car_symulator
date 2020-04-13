from frames.frames import *
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

ctr_nwm_nfc = [
        Signal(ENUM_CTR_NWM_NFC.CTR_NWM_NFC_POWM, 0, 8, 0xff),
        Signal(ENUM_CTR_NWM_NFC.CTR_NWM_NFC_RST_FBD, 8, 4, 0x0d),
    ]

nfc = Frame(1888,'nfc_frame', 'rx', 'sp2015', ctr_nwm_nfc, 8)

Frames = {nfc.name : nfc}