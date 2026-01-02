# ESP32 Application Template for PyTank Project

# -------------------
# --- 1. IMPORTS  ---
# -------------------
# Import necessary libraries from MicroPython, and existing project modules.
# Standard Libraries
import random
from time import sleep, localtime, time

# MicroPython Libraries
from machine import Pin, I2C, ADC

# Project-specific Modules
from viewer import Viewer
from Config import Config
from ds3231 import DS3231_RTC
import onewire, ds18x20
import ntptime

# -----------------------------
# --- 2. HARDWARE CONSTANTS ---
# -----------------------------
# Define the GPIO pins and other hardware-related constants here.

# --- Analog Inputs (Potentiometers for menu control) ---
# NOTE: These potentiometers simulate button presses.
# A value > 2000 is considered a "press".
POT_UP_PIN = 34      # KEY 1 -> UP
POT_DOWN_PIN = 35    # KEY 3 -> DOWN (Note: main.py has this as key 3, not 2)
POT_RIGHT_PIN = 12   # KEY 4 -> SHIFT +1
POT_LEFT_PIN = 4     # KEY 5 -> CLICK/ENTER
POT_CLICK_PIN = 32   # KEY 2 -> SHIFT -1 (Note: main.py has this as key 2, not 5)

# --- OneWire Temperature Sensor ---
DS18B20_PIN = 13

# --- I2C Devices (OLED Display and RTC) ---
# Pins for I2C bus might need to be configured depending on the ESP32 board.
# Default for many boards are: SDA=21, SCL=22
# I2C_SDA_PIN = 21
# I2C_SCL_PIN = 22


# ----------------------------
# --- 3. APPLICATION CLASS ---
# ----------------------------
# A class to encapsulate the entire application's logic.

class PyTankApp:
    """
    Main application class for the PyTank project.
    It handles hardware initialization, the main loop, and user input.
    """
    def __init__(self):
        """
        Constructor for the application. Initializes all components.
        """
        print("Initializing PyTank Application...")
        
        # --- Configuration ---
        # The Config class holds all runtime settings.
        self.config = Config()

        # --- Hardware Components ---
        self._init_hardware()
        
        # --- Viewer / UI ---
        # The Viewer class manages the OLED display and the menu system.
        self.viewer = Viewer(i2c=self.i2c, config=self.config)

        # --- Application State ---
        self.menu_countdown = 0
        self.MENU_TIMEOUT_SECONDS = 10 # Hide menu after 10 seconds of inactivity
        
        # --- Sync Time ---
        self._sync_time()

    def _init_hardware(self):
        """
        Initializes all hardware components.
        """
        print("Initializing hardware...")
        
        # --- Analog Inputs for Menu Control ---
        self.pot_up = ADC(Pin(POT_UP_PIN))
        self.pot_up.atten(ADC.ATTN_11DB)
        
        self.pot_down = ADC(Pin(POT_DOWN_PIN))
        self.pot_down.atten(ADC.ATTN_11DB)
        
        self.pot_click = ADC(Pin(POT_CLICK_PIN))
        self.pot_click.atten(ADC.ATTN_11DB)

        self.pot_right = ADC(Pin(POT_RIGHT_PIN))
        self.pot_right.atten(ADC.ATTN_11DB)

        self.pot_left = ADC(Pin(POT_LEFT_PIN))
        self.pot_left.atten(ADC.ATTN_11DB)

        # --- I2C Bus for Display and RTC ---
        # Modify pins if needed for your board
        print("Initializing I2C...")
        self.i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
        
        # --- Real-Time Clock (RTC) ---
        print("Initializing DS3231 RTC...")
        self.rtc = DS3231_RTC(self.i2c)

        # --- Temperature Sensor (DS18B20) ---
        print("Scanning for DS18B20 sensor...")
        try:
            ds_pin = Pin(DS18B20_PIN)
            self.ds18b20_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
            roms = self.ds18b20_sensor.scan()
            if roms:
                self.ds18b20_rom = roms[0] # Use the first sensor found
                print(f"Found DS18B20 device: {self.ds18b20_rom}")
            else:
                self.ds18b20_rom = None
                print("Warning: DS18B20 sensor not found.")
        except Exception as e:
            self.ds18b20_sensor = None
            self.ds18b20_rom = None
            print(f"Error initializing DS18B20: {e}")

    def _sync_time(self):
        """
        Synchronizes the RTC time with an NTP server.
        """
        # This part requires a network connection.
        # Assuming ConnectionManaging.py handles the WiFi connection.
        print("Attempting to sync time from NTP server...")
        try:
            # Make sure you are connected to WiFi before calling this.
            ntptime.settime() 
            # Update the DS3231 RTC with the new time
            tm = localtime()
            self.rtc.set_time(tm)
            print(f"Time synchronized successfully: {tm}")
        except Exception as e:
            print(f"Could not sync time from NTP: {e}. Using time from RTC.")

    def read_temperature(self):
        """
        Reads the temperature from the DS18B20 sensor.
        """
        if self.ds18b20_sensor and self.ds18b20_rom:
            try:
                self.ds18b20_sensor.convert_temp()
                sleep(0.75) # Wait for conversion
                temp = self.ds18b20_sensor.read_temp(self.ds18b20_rom)
                if isinstance(temp, float):
                    self.config.temperature = round(temp, 2)
                    return self.config.temperature
            except Exception as e:
                print(f"Could not read temperature: {e}")
        return None

    def _handle_input(self):
        """
        Reads the potentiometers and translates them into menu actions.
        """
        key = 0
        if self.pot_up.read() > 2000: key = 1 # UP
        if self.pot_click.read() > 2000: key = 2 # DOWN (was key 3)
        if self.pot_left.read() > 2000: key = 5 # CLICK
        if self.pot_right.read() > 2000: key = 4 # SHIFT +1
        if self.pot_down.read() > 2000: key = 3 # SHIFT -1 (was key 2)

        if key != 0:
            # If any key is pressed, reset the menu inactivity timer
            self.menu_countdown = 0
            if not self.viewer.is_enabled_menu:
                # Activate menu on first key press
                self.viewer.is_enabled_menu = True

            # --- Process menu actions ---
            if self.viewer.is_enabled_menu:
                if key == 1: self.viewer.menu.move(-1)   # Move Up
                if key == 2: self.viewer.menu.move(1)    # Move Down
                if key == 5: self.viewer.menu.click()    # Click/Enter
                if key == 4: self.viewer.menu.shift(1)   # Shift Right
                if key == 3: self.viewer.menu.shift(-1)  # Shift Left
            return True # Input was handled
        return False # No input

    def _update_menu_timeout(self):
        """
        Manages the auto-hiding of the menu after a period of inactivity.
        """
        if self.viewer.is_enabled_menu:
            self.menu_countdown += 1
            # Assuming the main loop runs every 0.1s, 100 counts = 10 seconds
            if self.menu_countdown > (self.MENU_TIMEOUT_SECONDS * 10):
                self.menu_countdown = 0
                self.viewer.is_enabled_menu = False
                print("Menu timed out, hiding.")
                # Here you might want to save the configuration
                # e.g., self.sd_manager.set_configuration(self.config.to_dict())

    def run(self):
        """
        The main application loop.
        """
        print("Starting main application loop...")
        loop_count = 0
        while True:
            # --- 1. Handle User Input ---
            self._handle_input()
            
            # --- 2. Update Application Logic ---
            # This is where you would place recurring tasks.
            
            # Example: Read temperature every 5 seconds
            if loop_count % 50 == 0: # 50 loops * 0.1s = 5 seconds
                self.read_temperature()
                print(f"Current Temperature: {self.config.temperature}°C")

            # --- 3. Update the Display ---
            # The viewer's run method handles drawing the screen.
            self.viewer.run()

            # --- 4. Handle Menu Timeout ---
            self._update_menu_timeout()

            # --- 5. Housekeeping ---
            loop_count += 1
            sleep(0.1) # Main loop delay.

# ---------------------------------
# --- 4. APPLICATION ENTRYPOINT ---
# ---------------------------------
if __name__ == "__main__":
    # This is the main entry point of the application.
    # It creates an instance of the app and runs it.
    # Before running, ensure your network is connected if you need NTP.
    
    # from ConnectionManaging import ConnectionManager
    # wifi = ConnectionManager()
    # wifi.connect() # Make sure this is implemented in ConnectionManaging.py
    
    app = PyTankApp()
    app.run()
