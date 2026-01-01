
from machine import Pin, I2C, ADC
import random
from time import sleep, localtime, time
from viewer import Viewer
from ds3231 import DS3231_RTC
import ntptime
import onewire, ds18x20

ds_pin = Pin(13)

DS18B20_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = DS18B20_sensor.scan()
print('Found DS18B20 devices: ', roms)
print('Temperatures: ')
DS18B20_sensor.convert_temp()
for rom in roms:
  temp =  DS18B20_sensor.read_temp(rom)
  if isinstance(temp, float):
    msg = round(temp, 2)
    print(temp, end=' ')
    print('DS18B20 Temperature is Valid')

pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB)       #Full range: 3.3v

pot1 = ADC(Pin(35))
pot1.atten(ADC.ATTN_11DB)       #Full range: 3.3v

pot2 = ADC(Pin(4))
pot2.atten(ADC.ATTN_11DB)       #Full range: 3.3v

pot3 = ADC(Pin(12))
pot3.atten(ADC.ATTN_11DB)       #Full range: 3.3v

pot4 = ADC(Pin(32))
pot4.atten(ADC.ATTN_11DB)       #Full range: 3.3v

countdown_menu = 0
viewer = Viewer()
#viewer.send_temperature(True)

while True:
    key=0  
    if pot.read() > 2000:
        key=1
    if pot4.read() > 2000:
        key=2
    if pot2.read() > 2000:
        key=5
    if pot3.read() > 2000:
        key=4
    if pot1.read() > 2000:
        key=3      

    if key == 1: 
        if viewer.is_enabled_menu:
            countdown_menu = 0
            viewer.menu.move(-1)
    if key == 2:
        if viewer.is_enabled_menu: 
            countdown_menu = 0   
            viewer.menu.move(1)    
    if key == 5:
        if not viewer.is_enabled_menu:
            viewer.is_enabled_menu = True
        else:
            countdown_menu = 0
            viewer.menu.click()
    if key == 4:     
        if viewer.is_enabled_menu:
            countdown_menu = 0
            viewer.menu.shift(1)
    if key == 3:     
        if viewer.is_enabled_menu:
            countdown_menu = 0    
            viewer.menu.shift(-1)    

    viewer.run()
    #print(config.get_connection_action())
    if viewer.is_enabled_menu:
        countdown_menu = countdown_menu + 1
    
    if countdown_menu == 100:
        countdown_menu = 0
        viewer.is_enabled_menu = False
        #sd.set_configuration(config.to_dict()) 
        #print(config.to_dict())
    
    #print(str(countdown_menu) + " " + str(ds.time))

    sleep(0.1)
