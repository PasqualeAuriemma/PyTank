#! /usr/bin/env micropython

# Micropython driver for the DS3231 RTC Module

# Inspiration from work done by Mike Causer (mcauser) for the DS1307
# https://github.com/mcauser/micropython-tinyrtc-i2c/blob/master/ds1307.py

# The MIT License (MIT)
#
# Copyright (c) 2020 Willem Peterse
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from micropython import const

DATETIME_REG    = const(0) # 7 bytes
ALARM1_REG      = const(7) # 5 bytes
ALARM2_REG      = const(11) # 4 bytes
CONTROL_REG     = const(14)
STATUS_REG      = const(15)
AGING_REG       = const(16)
TEMPERATURE_REG = const(17) # 2 bytes

class DS3231_RTC:
    """ DS3231 RTC driver.

    Hard coded to work with year 2000-2099."""
    FREQ_1      = const(1)
    FREQ_1024   = const(2)
    FREQ_4096   = const(3)
    FREQ_8192   = const(4)
    SQW_32K     = const(1)

    AL1_EVERY_S     = const(15) # Alarm every second
    AL1_MATCH_S     = const(14) # Alarm when seconds match (every minute)
    AL1_MATCH_MS    = const(12) # Alarm when minutes, seconds match (every hour)
    AL1_MATCH_HMS   = const(8) # Alarm when hours, minutes, seconds match (every day)
    AL1_MATCH_DHMS  = const(0) # Alarm when day|wday, hour, min, sec match (specific wday / mday) (once per month/week)

    AL2_EVERY_M     = const(7) # Alarm every minute on 00 seconds
    AL2_MATCH_M     = const(6) # Alarm when minutes match (every hour)
    AL2_MATCH_HM    = const(4) # Alarm when hours and minutes match (every day)
    AL2_MATCH_DHM   = const(0) # Alarm when day|wday match (once per month/week)

    def __init__(self, i2c, addr=0x68):
        """
        Constructs a new instance

        :param      i2c:    I2C object
        :type       i2c:    I2C
        :param      addr:   The I2C bus address of the EEPROM
        :type       addr:   int

        """
        self.i2c = i2c
        self._addr = addr
        self._timebuf = bytearray(7) # Pre-allocate a buffer for the time data
        self._buf = bytearray(1) # Pre-allocate a single bytearray for re-use
        self._al1_buf = bytearray(4)
        self._al2buf = bytearray(3)
        self._weekday_start = 0
    
    @property
    def weekday_start(self) -> int:
        """
        Get the start of the weekday

        :returns:   Weekday start
        :rtype:     int
        """
        return self._weekday_start

    @weekday_start.setter
    def weekday_start(self, value: int) -> None:
        """Set the start of the weekday"""
        if 0 <= value <= 6:
            self._weekday_start = value
        else:
            raise ValueError("Weekday can only be in range 0-6")

    @property
    def addr(self) -> int:
        """
        Get the DS1307 I2C bus address

        :returns:   DS1307 I2C bus address
        :rtype:     int
        """
        return self._addr
    
    @property
    def time(self) -> str:
        """
        Get the current time
        """
        return "{0:02d}:{1:02d}:{2:02d}".format(self.hour, self.minute, self.second)
        
    @property
    def datetime(self):
        """
        Get the current datetime

        (2023, 4, 18, 0, 10, 34, 4, 108)
            y, m,  d, h, m,  s, wd, yd

        :returns:   (year, month, day, hour, minute, second, weekday, yearday)
        :rtype:     Tuple[int, int, int, int, int, int, int, int]

        returns in 24h format, converts to 24h if clock is set to 12h format
        datetime : tuple, (0-year, 1-month, 2-day, 3-hour, 4-minutes[, 5-seconds[, 6-weekday]])
        """

        try:
            self.i2c.readfrom_mem_into(self.addr, DATETIME_REG, self._timebuf)
        except OSError as e:
            if e.errno == 19:  # ENODEV: No such module
                print(f"Errore: RTC DS3231 module doesn't exist.")
            else:
                print(f"Errore: {e}")  
        
        # 0x00 - Seconds    BCD
        # 0x01 - Minutes    BCD
        # 0x02 - Hour       0 12/24 AM/PM/20s BCD
        # 0x03 - WDay 1-7   0000 0 BCD
        # 0x04 - Day 1-31   00 BCD
        # 0x05 - Month 1-12 Century 00 BCD
        # 0x06 - Year 0-99  BCD (2000-2099)
        seconds = self._bcd_to_dec(self._timebuf[0] & 0x7F)
        minutes = self._bcd_to_dec(self._timebuf[1])

        if (self._timebuf[2] & 0x40) >> 6: # Check for 12 hour mode bit
            hour = self._bcd_to_dec(self._timebuf[2] & 0x9f) # Mask out bit 6(12/24) and 5(AM/PM)
            if (self._timebuf[2] & 0x20) >> 5: # bit 5(AM/PM)
                # PM
                hour += 12
        else:
            # 24h mode
            hour = self._bcd_to_dec(self._timebuf[2] & 0xbf) # Mask bit 6 (12/24 format)

        weekday = self._bcd_to_dec(self._timebuf[3] - self._weekday_start) # Can be set arbitrarily by user (1,7)
        day = self._bcd_to_dec(self._timebuf[4])
        month = self._bcd_to_dec(self._timebuf[5] & 0x7f) # Mask out the century bit
        year = self._bcd_to_dec(self._timebuf[6]) + 2000
        yearday = self.day_of_year(year=year, month=month, day=day)
        try:
            if self.OSF():
                print("WARNING: Oscillator stop flag set. Time may not be accurate.")
        except OSError as e:
            if e.errno == 19:  # ENODEV: No such module
                print(f"Errore: RTC DS3231 module doesn't exist.")
            else:
                print(f"Errore: {e}")  

        return (year, month, day, hour, minutes, seconds, weekday, yearday) # Conforms to the ESP8266 RTC (v1.13)

    @datetime.setter
    def datetime(self, value=None):
        """
        Set datetime

        (2023, 4, 18, 20, 23, 38, 1, 108) by time.gmtime(time.time())
        y,     m,  d,  h, min,sec,wday, yday
        0,     1,  2,  3,  4,   5,   6, 7

        :param      value:  The datetime
        :type       value:  Tuple[int, int, int, int, int, int, int, int]

        Always sets in 24h format, converts to 24h if clock is set to 12h format
        value : tuple, (0-year, 1-month, 2-day, 3-hour, 4-minutes[, 5-seconds[, 6-weekday]])
        """
    
        try:
            self._timebuf[3] = self._dec_to_bcd(value[6] + self._weekday_start) # Day of week
        except IndexError:
            self._timebuf[3] = 0
        try:
            self._timebuf[0] = self._dec_to_bcd(value[5]) & 0x7F # Seconds
        except IndexError:
            self._timebuf[0] = 0
        self._timebuf[1] = self._dec_to_bcd(value[4]) # Minutes
        self._timebuf[2] = self._dec_to_bcd(value[3]) # Hour + the 24h format flag
        self._timebuf[4] = self._dec_to_bcd(value[2]) # Day
        self._timebuf[5] = self._dec_to_bcd(value[1]) & 0xff # Month + mask the century flag
        self._timebuf[6] = self._dec_to_bcd(int(str(value[0])[-2:])) # Year can be yyyy, or yy
        self.i2c.writeto_mem(self.addr, DATETIME_REG, self._timebuf)
        self._OSF_reset()
        return True    
    
    @property
    def year(self) -> int:
        """
        Get the year from the RTC

        :returns:   Year of RTC
        :rtype:     int
        """
        return self.datetime[0]

    @property
    def month(self) -> int:
        """
        Get the month from the RTC

        :returns:   Month of RTC
        :rtype:     int
        """
        return self.datetime[1]

    @property
    def day(self) -> int:
        """
        Get the day from the RTC

        :returns:   Day of RTC
        :rtype:     int
        """
        return self.datetime[2]

    @property
    def hour(self) -> int:
        """
        Get the hour from the RTC

        :returns:   Hour of RTC
        :rtype:     int
        """
        return self.datetime[3]

    @property
    def minute(self) -> int:
        """
        Get the minute from the RTC

        :returns:   Minute of RTC
        :rtype:     int
        """
        return self.datetime[4]

    @property
    def second(self) -> int:
        """
        Get the second from the RTC

        :returns:   Second of RTC
        :rtype:     int
        """
        return self.datetime[5]

    @property
    def weekday(self) -> int:
        """
        Get the weekday from the RTC

        :returns:   Weekday of RTC
        :rtype:     int
        """
        return self.datetime[5]

    @property
    def yearday(self) -> int:
        """
        Get the yearday from the RTC

        :returns:   Yearday of RTC
        :rtype:     int
        """
        return self.datetime[7]

    def square_wave(self, freq=None):
        """Outputs Square Wave Signal

        The alarm interrupts are disabled when enabling a square wave output. Disabling SWQ out does
        not enable the alarm interrupts. Set them manually with the alarm_int() method.
        freq : int,
            Not given: returns current setting
            False = disable SQW output,
            1 =     1 Hz,
            2 = 1.024 kHz,
            3 = 4.096 kHz,
            4 = 8.192 kHz"""
        if freq is None:
            return self.i2c.readfrom_mem(self.addr, CONTROL_REG, 1)[0]

        if not freq:
            # Set INTCN (bit 2) to 1 and both ALIE (bits 1 & 0) to 0
            self.i2c.readfrom_mem_into(self.addr, CONTROL_REG, self._buf)
            self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([(self._buf[0] & 0xf8) | 0x04]))
        else:
            # Set the frequency in the control reg and at the same time set the INTCN to 0
            freq -= 1
            self.i2c.readfrom_mem_into(self.addr, CONTROL_REG, self._buf)
            self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([(self._buf[0] & 0xe3) | (freq << 3)]))
        return True

    def day_of_year(self, year: int, month: int, day: int) -> int:
        """
        Get the day of the year

        :param      year:   The year
        :type       year:   int
        :param      month:  The month
        :type       month:  int
        :param      day:    The day
        :type       day:    int

        :returns:   Day of the year, January 1 is day 1
        :rtype:     int
        """
        month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        year -= 2000
        days16 = day

        for x in range(1, month):
            days16 += month_days[x - 1]

        if month >= 2 and self.is_leap_year(year=year):
            days16 += 1

        return days16

    def is_leap_year(self, year: int) -> bool:
        """
        Determines whether the specified year is a leap year.

        :param      year:  The year
        :type       year:  int

        :returns:   True if the specified year is leap year, False otherwise.
        :rtype:     bool
        """
        return (year % 4 == 0)       

    def alarm1(self, time=None, match=AL1_MATCH_DHMS, int_en=True, weekday=False):
        """Set alarm1, can match mday, wday, hour, minute, second

        time    : tuple, (second,[ minute[, hour[, day]]])
        weekday : bool, select mday (False) or wday (True)
        match   : int, match const
        int_en  : bool, enable interrupt on alarm match on SQW/INT pin (disables SQW output)"""
        if time is None:
            # TODO Return readable string
            self.i2c.readfrom_mem_into(self.addr, ALARM1_REG, self._al1_buf)
            return self._al1_buf

        if isinstance(time, int):
            time = (time,)

        a1m4 = (match & 0x08) << 4
        a1m3 = (match & 0x04) << 5
        a1m2 = (match & 0x02) << 6
        a1m1 = (match & 0x01) << 7

        dydt = (1 << 6) if weekday else 0 # day / date bit

        self._al1_buf[0] = dectobcd(time[0]) | a1m1 # second
        self._al1_buf[1] = (dectobcd(time[1]) | a1m2) if len(time) > 1 else a1m2 # minute
        self._al1_buf[2] = (dectobcd(time[2]) | a1m3) if len(time) > 2 else a1m3 # hour
        self._al1_buf[3] = (dectobcd(time[3]) | a1m4 | dydt) if len(time) > 3 else a1m4 | dydt # day (wday|mday)

        self.i2c.writeto_mem(self.addr, ALARM1_REG, self._al1_buf)

        # Set the interrupt bit
        self.alarm_int(enable=int_en, alarm=1)

        # Check the alarm (will reset the alarm flag)
        self.check_alarm(1)

        return self._al1_buf

    def alarm2(self, time=None, match=AL2_MATCH_DHM, int_en=True, weekday=False):
        """Get/set alarm 2 (can match minute, hour, day)

        time    : tuple, (minute[, hour[, day]])
        weekday : bool, select mday (False) or wday (True)
        match   : int, match const
        int_en  : bool, enable interrupt on alarm match on SQW/INT pin (disables SQW output)
        Returns : bytearray(3), the alarm settings register"""
        if time is None:
            # TODO Return readable string
            self.i2c.readfrom_mem_into(self.addr, ALARM2_REG, self._al2buf)
            return self._al2buf

        if isinstance(time, int):
            time = (time,)

        a2m4 = (match & 0x04) << 5 # masks
        a2m3 = (match & 0x02) << 6
        a2m2 = (match & 0x01) << 7

        dydt = (1 << 6) if weekday else 0 # day / date bit

        self._al2buf[0] = dectobcd(time[0]) | a2m2 if len(time) > 1 else a2m2 # minute
        self._al2buf[1] = dectobcd(time[1]) | a2m3 if len(time) > 2 else a2m3 # hour
        self._al2buf[2] = dectobcd(time[2]) | a2m4 | dydt if len(time) > 3 else a2m4 | dydt # day

        self.i2c.writeto_mem(self.addr, ALARM2_REG, self._al2buf)

        # Set the interrupt bits
        self.alarm_int(enable=int_en, alarm=2)

        # Check the alarm (will reset the alarm flag)
        self.check_alarm(2)

        return self._al2buf

    def alarm_int(self, enable=True, alarm=0):
        """Enable/disable interrupt for alarm1, alarm2 or both.

        Enabling the interrupts disables the SQW output
        enable : bool, enable/disable interrupts
        alarm : int, alarm nr (0 to set both interrupts)
        returns: the control register"""
        if alarm in (0, 1):
            self.i2c.readfrom_mem_into(self.addr, CONTROL_REG, self._buf)
            if enable:
                self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([(self._buf[0] & 0xfa) | 0x05]))
            else:
                self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([self._buf[0] & 0xfe]))

        if alarm in (0, 2):
            self.i2c.readfrom_mem_into(self.addr, CONTROL_REG, self._buf)
            if enable:
                self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([(self._buf[0] & 0xf9) | 0x06]))
            else:
                self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([self._buf[0] & 0xfd]))

        return self.i2c.readfrom_mem(self.addr, CONTROL_REG, 1)

    def check_alarm(self, alarm):
        """Check if the alarm flag is set and clear the alarm flag"""
        self.i2c.readfrom_mem_into(self.addr, STATUS_REG, self._buf)
        if (self._buf[0] & alarm) == 0:
            # Alarm flag not set
            return False

        # Clear alarm flag bit
        self.i2c.writeto_mem(self.addr, STATUS_REG, bytearray([self._buf[0] & ~alarm]))
        return True

    def output_32kHz(self, enable=True):
        """Enable or disable the 32.768 kHz square wave output"""
        status = self.i2c.readfrom_mem(self.addr, STATUS_REG, 1)[0]
        if enable:
            self.i2c.writeto_mem(self.addr, STATUS_REG, bytearray([status | (1 << 3)]))
        else:
            self.i2c.writeto_mem(self.addr, STATUS_REG, bytearray([status & (~(1 << 3))]))

    def OSF(self):
        """Returns the oscillator stop flag (OSF).

        1 indicates that the oscillator is stopped or was stopped for some
        period in the past and may be used to judge the validity of
        the time data.
        returns : bool"""
        return bool(self.i2c.readfrom_mem(self.addr, STATUS_REG, 1)[0] >> 7)

    def _OSF_reset(self):
        """Clear the oscillator stop flag (OSF)"""
        self.i2c.readfrom_mem_into(self.addr, STATUS_REG, self._buf)
        self.i2c.writeto_mem(self.addr, STATUS_REG, bytearray([self._buf[0] & 0x7f]))

    def _is_busy(self):
        """Returns True when device is busy doing TCXO management"""
        return bool(self.i2c.readfrom_mem(self.addr, STATUS_REG, 1)[0] & (1 << 2))

    def _dec_to_bcd(self, value: int) -> int:
        """
        Convert decimal to binary coded decimal (BCD) format

        :param      value:  The value
        :type       value:  int

        :returns:   Binary coded decimal (BCD) format
        :rtype:     int
        """
        return (value // 10) << 4 | (value % 10)

    def _bcd_to_dec(self, value: int) -> int:
        """
        Convert binary coded decimal (BCD) format to decimal

        :param      value:  The value
        :type       value:  int

        :returns:   Decimal value
        :rtype:     int
        """
        return ((value >> 4) * 10) + (value & 0x0F)

    def unix_epoch_time(self, value):
        return value + 946684800    