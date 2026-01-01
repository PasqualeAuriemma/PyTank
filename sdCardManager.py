'''
 # Demonstrates ESP32 interface to MicroSD Card Adapter
 # Create a text file and write running numbers.
 # Open text file, read and print the content on debug port
   
 * The ESP32 pin connections for MicroSD Card Adapter SPI
 
 # MicroSD Card Adapter Power Pins
 * MicroSD VCC pin to ESP32 +5V
 * MicroSD GND pin to ESP32 GND
 
 # MicroSD SPI Pins
 * MicroSD MISO pin to ESP32 GPIO19
 * MicroSD MOSI pin to ESP32 GPIO23
 * MicroSD SCK pin to ESP32 GPIO18
 * MicroSD CS pin to ESP32 GPIO05
 
 Name:- M.Pugazhendi
 Date:-  20thOct2021
 Version:- V0.1
 e-mail:- muthuswamy.pugazhendi@gmail.com
'''

import machine
from machine import Pin, SPI, SoftSPI
import sdcard
import os
from time import sleep_ms
import json 
import uos

class sdCardManager():
    def __init__(self, sck_pin=Pin(18),mosi_pin=Pin(23),miso_pin=Pin(19),sd_pin=Pin(5, Pin.OUT)):
        # Initialize the SD card
        self._spi=SoftSPI(1,sck=sck_pin,mosi=mosi_pin,miso=miso_pin)
        self._sd=sdcard.SDCard(self._spi,sd_pin)
        # Create a instance of MicroPython Unix-like Virtual File System (VFS),
        self._vfs=os.VfsFat(self._sd)

    def set_configuration(self, data):
        uos.mount(self._vfs,'/sd')
        # Convert dictionary to JSON string
        json_data = json.dumps(data)
        # Write JSON data to a file on the SD card
        with open("/sd/data.json", "w") as file:
            file.write(json_data)
        # Unmount the filesystem
        uos.umount("/sd")

    def if_exist_configuration(self):
        uos.mount(self._vfs,'/sd')
        file_path = "/sd/data.json"
        try:
            if os.stat(file_path):
                # Unmount the filesystem
                uos.umount("/sd") 
                return True
        except OSError as e:
            if e.args[0] == 2:  # ENOENT: No such file or directory
                # Unmount the filesystem
                uos.umount("/sd")             
                return False
            else:
                # Unmount the filesystem
                uos.umount("/sd")                 
                print(f"Errore: {e}")
   

    def get_configuration(self):
        # Open the file in "read mode". 
        # Read the file and print the text on debug port.
        file_path = "/sd/data.json"
        #if os.path.exists(file_path):
        try:
            uos.mount(self._vfs,'/sd')
            with open(file_path, "r") as file:
                print("Reading from SD card")
                data = json.load(file)
            # Unmount the filesystem
            uos.umount("/sd")
            return data
        except OSError as e:
            if e.errno == 2:  # ENOENT: No such file or directory
                print(f"Errore: Il file '{file_path}' non è stato trovato.")
            else:
                print(f"Errore: {e}")    


