import smbus
import time
from typing import List, Tuple

class Emc2101(object):
    MFG_ID_SMSC = 0x5D
    PART_ID_EMC2101 = 0x16
    PART_ID_EMC2101R = 0x28

    I2C_ADDR = 0x4C

    MAX_LUT_SPEED = 0x3F  # 6-bit value
    MAX_LUT_TEMP = 0x7F  # 7-bit

    # Bits in device status register for masks etc.
    STATUS_BUSY = 0x80
    STATUS_INTHIGH = 0x40
    STATUS_EEPROM = 0x20
    STATUS_EXTHIGH = 0x10
    STATUS_EXTLOW = 0x08
    STATUS_FAULT = 0x04
    STATUS_TCRIT = 0x02
    STATUS_TACH = 0x01

    STATUS_ALERT = (
        STATUS_TACH
        | STATUS_TCRIT
        | STATUS_FAULT
        | STATUS_EXTLOW
        | STATUS_EXTHIGH
        | STATUS_INTHIGH
    )

    # Bits in device configuration register for masks etc.
    CONFIG_MASK = 0x80
    CONFIG_STANDBY = 0x40
    CONFIG_FAN_STANDBY = 0x20
    CONFIG_DAC = 0x10
    CONFIG_DIS_TO = 0x08
    CONFIG_ALT_TACH = 0x04
    CONFIG_TCRIT_OVR = 0x02
    CONFIG_QUEUE = 0x01

    # Values of external temp register for fault conditions.
    TEMP_FAULT_OPENCIRCUIT = 0x3F8
    TEMP_FAULT_SHORT = 0x3FF

    # See datasheet section 6.14:
    FAN_RPM_DIVISOR = 5400000

    #
    # EMC2101 Register Addresses
    #
    INTERNAL_TEMP = 0x00  # Readonly
    EXTERNAL_TEMP_MSB = 0x01  # Readonly, Read MSB first
    EXTERNAL_TEMP_LSB = 0x10  # Readonly
    REG_STATUS = 0x02  # Readonly
    REG_CONFIG = 0x03  # Also at 0x09
    CONVERT_RATE = 0x04  # Also at 0x0A
    INT_TEMP_HI_LIM = 0x05  # Also at 0x0B
    TEMP_FORCE = 0x0C
    ONESHOT = 0x0F  # Effectively Writeonly
    SCRATCH_1 = 0x11
    SCRATCH_2 = 0x12
    EXT_TEMP_LO_LIM_LSB = 0x14
    EXT_TEMP_LO_LIM_MSB = 0x08  # Also at 0x0E
    EXT_TEMP_HI_LIM_LSB = 0x13
    EXT_TEMP_HI_LIM_MSB = 0x07  # Also at 0x0D
    ALERT_MASK = 0x16
    EXT_IDEALITY = 0x17
    EXT_BETACOMP = 0x18
    TCRIT_TEMP = 0x19
    TCRIT_HYST = 0x21
    TACH_LSB = 0x46  # Readonly, Read MSB first
    TACH_MSB = 0x47  # Readonly
    TACH_LIMIT_LSB = 0x48
    TACH_LIMIT_MSB = 0x49
    FAN_CONFIG = 0x4A
    FAN_SPINUP = 0x4B
    REG_FAN_SETTING = 0x4C
    PWM_FREQ = 0x4D
    PWM_FREQ_DIV = 0x4E
    FAN_TEMP_HYST = 0x4F
    AVG_FILTER = 0xBF

    REG_PARTID = 0xFD  # Readonly, 0x16 (or 0x28 for -R part)
    REG_MFGID = 0xFE  # Readonly, SMSC is 0x5D
    REG_REV = 0xFF  # Readonly, e.g. 0x01

    
    REG_LOOKUP_T = range(0x50, 0x5F, 2)
    REG_LOOKUP_S = range(0x51, 0x5F + 1 , 2)
    

    LUT_HYSTERESIS = 0x4F
    LUT_BASE = 0x50

    I2CADDRESS = 0x4C

    def __init__(self, i2cbus):
        self.BUS = smbus.SMBus(i2cbus)

    def _read(self, register_address):
        return self.BUS.read_byte_data(Emc2101.I2CADDRESS, register_address)
    
    def _write(self, register_address, data_byte):
        self.BUS.write_byte_data(Emc2101.I2CADDRESS, register_address, data_byte)

    def _writeBool(self, register_address, registermask, value):
        reg = self._read(register_address)
        if value:
            self._write(register_address, reg | registermask)
        else:
            self._write(register_address, reg & ~registermask)
    
    def close(self):
        self.BUS.close()
    
    @property
    def internalTemp(self):
        return int(self._read(Emc2101.INTERNAL_TEMP))

    @property
    def dacMode(self):
        return bool(self._read(Emc2101.REG_CONFIG) & Emc2101.CONFIG_DAC)

    @dacMode.setter
    def dacMode(self, value):
        self._writeBool(Emc2101.REG_CONFIG, Emc2101.CONFIG_DAC, bool(value))

    @property
    def fanControlLookupTable(self):
        return [(self._read(Emc2101.REG_LOOKUP_T[i]), self._read(Emc2101.REG_LOOKUP_T[i])) for i in range(8)]

    @fanControlLookupTable.setter
    def fanControlLookupTable(self, value: List[Tuple[int, int]]):
        for i in range(len(value)):
            x,y = value[i]
            self._write(Emc2101.REG_LOOKUP_T[i], x)
            self._write(Emc2101.REG_LOOKUP_S[i], y)
