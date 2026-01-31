from machine import Pin, I2C
import Icons.images_repo as im
import random
from Menu.pymenu import *
import Modules.ssd1306 as ssd1306
from time import sleep, localtime, time
from Manager.sdCardManager import sdCardManager
from Resource.Config import Config
from Modules.ds3231 import DS3231_RTC
import ntptime
from Manager.ConnectionManager import ConnectionManaging
import _thread

'''
def send_value_to_web(self, value, key, timestamp):
    """
    Invia un singolo valore con la sua chiave e timestamp a un endpoint web.
    Questo metodo tenterà di connettersi al WiFi se non già connesso,
    invierà i dati e quindi si disconnetterà.
    Considera di chiamare connect/disconnect a un livello superiore per efficienza.
    """
    if not self.host:
        self.log_message("Errore: L'host non è impostato. Impossibile inviare il valore al web.")
        return False

    # È generalmente più efficiente connettersi una volta e inviare più valori,
    # piuttosto che connettersi e disconnettersi per ogni valore.
    # Questa implementazione si connette/disconnette per ogni chiamata per semplicità.
    if self.connect():
        url = f"https://{self.host}/take{key}.php"
        data = {key: value, "Date": timestamp}
        
        self.log_message(f"Tentativo di invio del valore '{value}' per la chiave '{key}' a {url}")
        
        response_text = self.make_post_request(url, data)
        
        # Non disconnettere qui se vuoi mantenere la connessione attiva per invii successivi.
        # La disconnessione è gestita nel ciclo principale per maggiore efficienza.
        # self.disconnect() 
        
        return response_text is not None
    else:
        self.log_message("Impossibile connettersi al WiFi, impossibile inviare il valore.")
        return False
'''
class Viewer:
    def __init__(self, i2c=None, config:Config=None, _w = 128, _h = 64):
        # ESP32 Pin assignment 
        if i2c:
            self._i2c = i2c
        else:
            self._i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=800000)
            
        self.ds = DS3231_RTC(self._i2c) #RTC
        self.conn = ConnectionManaging('CasaPATC', 'CasaDiPT240!',"myfishtank.altervista.org") #'Wokwi-GUEST', '',
        # Start the thread
        self.set_ntp()
        self.oled_width = _w
        self.oled_height = _h
        self._is_enabled_menu = False
        self._exit_menu = True
        self._time_temp = None
        self._time = "00:00:00"
        self._temperature = "0"
        self._ec = "0"
        self._ph = "0"
        
        if config:
            self._config = config
        else:
            self._config = Config()

        # DS3231 on 0x68
        self.I2C_ADDR = 0x68     # DEC 104, HEX 0x68 
        
        self.sd = sdCardManager()
        
        if(self.sd.if_exist_configuration()):
            file_json = self.sd.get_configuration()
            self._config.from_json(file_json)
        else:
            self.sd.set_configuration(self._config.to_dict())

        self.display = ssd1306.SSD1306_I2C(self.oled_width, self.oled_height, self._i2c)
        self.show_rele_symbol(self._config.get_rele_list())
        self.menu = Menu(self)
        self.set_menu()
        # Define the pin number
        # Configure the pin as an output
        self._light_rele = Pin(27, Pin.OUT)
        self._filter_rele = Pin(26, Pin.OUT)
        self._heater_rele = Pin(25, Pin.OUT)
        self._feeder_rele = Pin(33, Pin.OUT)
        self._light_rele.value(0) 
        self._filter_rele.value(0) 
        self._heater_rele.value(0)
        self._feeder_rele.value(0)
        #self.init_screen()
        #self.display.poweroff()

    def set_ntp(self):
        #print(conn.connection_status())
        self.conn.connect()
        print(self.conn.connection_status())
        ntptime.settime()
        unix_epoch_time1 = str(self.ds.unix_epoch_time(time()))
        print("Unix epoch time:", unix_epoch_time1)
        self.conn.send_value_to_web("999", "Ec", unix_epoch_time1)
        #conn.post_https_request("Ec", "530", "Date", "1739311432")
        self.conn.disconnect()
        print(self.conn.connection_status())
        print(list(localtime()))
        self.ds.datetime = localtime()
        
    def toggle_on_off_light_auto(self):
        self._config._on_off_light_auto = not self._config._on_off_light_auto
        self._config._on_off_light_auto_temp = self._config._on_off_light_auto
        if self._config._on_off_light_auto:
            self._config.relay0 = True # Set the pin to HIGH
            self._light_rele.value(1)
        else:
            self._config.relay0 = False
            self._light_rele.value(0)  
        self._config.get_on_off_light_auto

    def toggle_on_off_filter(self):
        self._config._on_off_filter = not self._config._on_off_filter
        self._config._on_off_filter_temp = self._config._on_off_filter
        if self._config._on_off_filter:
            self._config.relay1 = True
            self._filter_rele.value(1)
        else:
            self._config.relay1 = False
            self._filter_rele.value(0)
        self._config.get_on_off_filter       

    def toggle_on_off_heater(self):
        self._config._on_off_heater = not self._config._on_off_heater
        self._config._on_off_heater_temp = self._config._on_off_heater
        if self._config._on_off_heater:
            self._config.relay2 = True
            self._heater_rele.value(1) # Set the pin to HIGH
        else:
            self._config.relay2 = False
            self._heater_rele.value(0)
        self._config.get_on_off_heater

    def toggle_on_off_feeder(self):
        self._config._on_off_feeder = not self._config._on_off_feeder
        self._config._on_off_feeder_temp = self._config._on_off_feeder
        if self._config._on_off_feeder:
            self._config.relay3 = True
            self._feeder_rele.value(1) # Set the pin to HIGH
        else:
            self._config.relay3 = False
            self._feeder_rele.value(0)  
        self._config.get_on_off_feeder    

    def toggle_on_off_heater_auto(self):
        self._config._on_off_heater_auto = not self._config._on_off_heater_auto
        self._config._on_off_heater_auto_temp = self._config._on_off_heater_auto            
        self._config.get_on_off_heater_auto   

    def toggle_on_off_filter_auto(self):
        self._config._on_off_filter_auto = not self._config._on_off_filter_auto
        self._config._on_off_filter_auto_temp = self._config._on_off_filter_auto
        self._config.get_on_off_filter_auto 

    def toggle_on_off_temperature(self):
        self._config._on_off_temperature = not self._config._on_off_temperature
        self._config._on_off_temperature_temp = self._config._on_off_temperature
        self._config.get_on_off_temperature 

    def toggle_on_off_ph(self):
        self._config._on_off_ph = not self._config._on_off_ph
        self._config._on_off_ph_temp = self._config._on_off_ph
        self._config.get_on_off_ph 

    def toggle_on_off_ec(self):
        self._config._on_off_ec = not self._config._on_off_ec
        self._config._on_off_ec_temp = self._config._on_off_ec
        self._config.get_on_off_ec

    def toggle_on_off_ec_sending(self):
        self._config._on_off_ec_sending = not self._config._on_off_ec_sending
        self._config._on_off_ec_sending_temp = self._config._on_off_ec_sending
        self._config.get_on_off_ec_sending     

    def toggle_on_off_ph_sending(self):
        self._config._on_off_ph_sending = not self._config._on_off_ph_sending
        self._config._on_off_ph_sending_temp = self._config._on_off_ph_sending
        self._config.get_on_off_ph_sending    

    def toggle_on_off_temperature_sending(self):
        self._config._on_off_temperature_sending = not self._config._on_off_temperature_sending
        self._config._on_off_temperature_sending_temp = self._config._on_off_temperature_sending
        self._config.get_on_off_temperature_sending            

    def _send_ec(self, value):
        # Get the Unix timestamp
        unix_epoch_time1 = str(self.ds.unix_epoch_time(time()))
        print("Unix epoch time:", unix_epoch_time1)
        if value:
            self.conn.send_value_to_web(self.ec, "Ec", str(unix_epoch_time1))

    def _send_ph(self, value):
        # Get the Unix timestamp
        unix_epoch_time1 = str(self.ds.unix_epoch_time(time()))
        print("Unix epoch time:", unix_epoch_time1)
        if value:
            self.conn.send_value_to_web(self.ph, "PH", str(unix_epoch_time1))


    def send_temperature(self, value):
        # Get the Unix timestamp
        unix_epoch_time1 = self.ds.unix_epoch_time(time())
        if value:
            self.conn.send_value_to_web(self.temperature, "Temp", str(unix_epoch_time1))

    @property
    def exit_menu(self):
        return self._exit_menu

    @exit_menu.setter
    def exit_menu(self, value):
        self._exit_menu = value

    @property
    def time(self):
        return self._time

    @property
    def temperature(self):
        return self._temperature

    @property
    def ec(self):
        return self._ec

    @property
    def ph(self):
        return self._ph

    @time.setter
    def time(self, value):
        self._time = value

    @temperature.setter
    def temperature(self, value):
        self._temperature = value

    @ec.setter
    def ec(self, value):
        self._ec = value

    @ph.setter
    def ph(self, value):
        self._ph = value

    def init_screen(self):
        #self.oled.invert(1)
        self.display.fill(0)
        self.display.invert(1)
        self.display.show_image(im.fishtank_logo, 128, 64)
        sleep(3)

        self.display.invert(0)
        #self.display.fill(0)   # fill entire screen with colour=0
        screen =  [[39, 0, "PIA12"], [28, 57, "AQUARIUM"]]
        self.display.scroll_portion(screen, 128, 20)
        rect_start_x = 10
        rect_start_y = 10
        rect_width = 105
        rect_height = 45
        self.display.rect(rect_start_x, rect_start_y, rect_width, rect_height, 1)        # draw a rectangle outline 10,10 to width=107, height=53, colour=1
        self.display.show()
        sleep(2)
        for xx in range(rect_start_x, rect_height/2 - 2, 4):
            self.display.fill(0)
            self.display.rect(xx+10, xx+10 , int(rect_width - 2 * xx), int(rect_height - 2 * xx), 1)
            self.display.show()
            sleep(0.05)
        
    def show_main_screen(self):
        '''
            Screen with time, temperature, ec and ph
        '''
        #self.display.fill(0) to clean wholw screen 
        self.display.fill_rect(0, 0, 128, 51, 0)       
        self.display.rect(25, 2, 75, 14, 1)
        self.display.text(self.time, 30, 5, 1)
        self.display.text("TEMP:", 0, 23)
        self.display.text("{0:02}".format(self.temperature), 48, 23)
        # Visualizza il simbolo del grado sul display
        self.display.show_custom_char(im.degree_symbol, 64 ,23)
        self.display.text("C", 72, 23)
        self.display.text("EC:", 0, 33)
        self.display.text("{0:03}".format(self.ec) +" uS/cm", 32, 33)
        #self.display.show_custom_char(self.micron_symbol, 48 ,30)
        #self.display.text("S/cm", 54, 30)
        self.display.text("PH:", 0, 43)
        self.display.text(self.ph, 32, 43)
        #self.display.rect(92, 48, 36, 14, 1)
        #self.display.text("MENU", 94, 52)
        
    def show_rele_symbol(self, rele):
        ''' 
            Screen portion with relays information though some symbols
        ''' 
        self.display.fill_rect(0, 52, 128, 12, 0)
        for index, rele_status in enumerate(rele):
            print(rele_status)
            if rele_status:
                self.display.show_fill_button_with_text(str(index+1), 70 + index * 14, 52, 12 , 12)
            else:
                self.display.show_blank_button_with_text(str(index+1), 70 + index * 14, 52, 12 , 12)
    
    def draw(self):
        self.is_enabled_menu = False
        
    def run(self):
        if self.is_enabled_menu and not(self.exit_menu):
            self.menu.draw()
            self.exit_menu = True
        elif self.exit_menu and not(self.is_enabled_menu):
            self.exit_menu = False
            self.menu.reset()
            self.time = self.ds.time
            self.show_main_screen()
            self.show_rele_symbol(self._config.get_rele_list())
            self.display.show() 
        elif not(self.exit_menu) and not(self.is_enabled_menu) and (self.ds.time != self.time): 
            #print(str(self.exit_menu) + " " + str(self.is_enabled_menu) + " " + str(time) + " " + str(self._time_temp))
            self.time = self.ds.time
            self.show_main_screen()
            self.display.show()   
        else:    
            pass  

    @property
    def is_enabled_menu(self):
        return self._is_enabled_menu    

    @is_enabled_menu.setter
    def is_enabled_menu(self, value):
        self._is_enabled_menu = value 
    
    def set_menu(self):
        self.menu.set_main_screen(
            MenuList(self.display, 'MENU')
            .add(MenuEnum(self.display, 'MODE', self._config.mode_list, (self._config.set_mode)))
            .add(MenuList(self.display, 'RELAYS')
                .add(ToggleItem(self.display, 'LIGHTS', (self._config.get_on_off_light_auto), (self.toggle_on_off_light_auto), ('ON', 'OFF')))
                .add(ToggleItem(self.display, 'FILTER', (self._config.get_on_off_filter), (self.toggle_on_off_filter), ('ON', 'OFF')))
                .add(ToggleItem(self.display, 'HEATER', (self._config.get_on_off_heater), (self.toggle_on_off_heater), ('ON', 'OFF')))
                .add(ToggleItem(self.display, 'FEEDER', (self._config.get_on_off_feeder), (self.toggle_on_off_feeder), ('ON', 'OFF')))
                .add(BackItem(self.display))    
                )
            .add(MenuList(self.display, 'SENSORS')
                .add(MenuList(self.display, 'EC')
                    .add(ToggleItem(self.display, 'ACTIVATION', (self._config.get_on_off_ec), (self.toggle_on_off_ec)))
                    .add(MenuMonitoringSensor(self.display, 'MONITORING', visible=(self._config.get_on_off_ec)))
                    .add(ToggleItem(self.display, 'WEB SERVER', (self._config.get_on_off_ec_sending), (self.toggle_on_off_ec_sending), visible=(self._config.get_on_off_ec)))
                    .add(MenuEnum(self.display, "WEB RATE", self._config.freq, self._config.set_freq_update_web_ec, visible=(self._config.get_on_off_ec_sending)))  
                    .add(MenuConfirm(self.display, "SEND TO WEB", ('-> SEND', '<- BACK'), self._send_ec, visible=(self._config.get_on_off_ec_sending))) 
                    .add(BackItem(self.display))
                    )
                .add(MenuList(self.display, 'PH')
                    .add(ToggleItem(self.display, 'ACTIVATION', (self._config.get_on_off_ph), (self.toggle_on_off_ph)))
                    .add(MenuMonitoringSensor(self.display, 'MONITORING', visible=(self._config.get_on_off_ph)))
                    .add(ToggleItem(self.display, 'WEB SERVER', (self._config.get_on_off_ph_sending), (self.toggle_on_off_ph_sending), visible=(self._config.get_on_off_ph)))
                    .add(MenuEnum(self.display, "WEB RATE", self._config.freq, self._config.set_freq_update_web_ph, visible=(self._config.get_on_off_ph_sending)))  
                    .add(MenuConfirm(self.display, "SEND TO WEB", ('-> SEND', '<- BACK'), self._send_ph, visible=(self._config.get_on_off_ph_sending))) 
                    .add(BackItem(self.display))
                    )
                .add(MenuList(self.display, 'THERMOMETER')
                    .add(ToggleItem(self.display, 'ACTIVATION', (self._config.get_on_off_temperature), (self.toggle_on_off_temperature)))
                    .add(ToggleItem(self.display, 'WEB SERVER', (self._config.get_on_off_temperature_sending), (self.toggle_on_off_temperature_sending), visible=(self._config.get_on_off_temperature)))
                    .add(MenuEnum(self.display, "WEB RATE", self._config.freq, self._config.set_freq_update_web_temperature, visible=(self._config.get_on_off_temperature_sending)))  
                    .add(MenuConfirm(self.display, "SEND TO WEB", ('-> SEND', '<- BACK'), self.send_temperature, visible=(self._config.get_on_off_temperature_sending))) 
                    .add(BackItem(self.display))
                    )
                .add(BackItem(self.display))
                )
            .add(MenuList(self.display, 'SETTINGS')
                .add(MenuList(self.display, 'WIFI')
                    .add(MenuWifiInfo(self.display, 'INFO'))
                    .add(MenuConfirm(self.display, "CONNECTING", ('-> YES', '<- NO'), self._config.set_connection_action)) 
                    .add(BackItem(self.display))
                    )
                .add(MenuSetDateTime(self.display, 'DATE/TIME', print))
                .add(MenuSetTimer(self.display, 'LIGHT TIMER', self._config.get_timer_time(), self._config.set_timer_time))
                .add(MenuList(self.display, 'HEATER AUTO')
                    .add(ToggleItem(self.display, 'ACTIVATION', (self._config.get_on_off_heater_auto), (self.toggle_on_off_heater_auto)))
                    .add(MenuHeaterManage(self.display, 'SETTING', self._config.get_timer_time(), self._config.set_auto_heater, visible=(self._config.get_on_off_heater_auto)))
                    .add(BackItem(self.display))
                    )
                .add(MenuList(self.display, 'FILTER AUTO')
                    .add(ToggleItem(self.display, 'ACTIVATION', (self._config.get_on_off_filter_auto), (self.toggle_on_off_filter_auto)))
                    .add(MenuEnum(self.display, "RATE", self._config.freq, self._config.set_freq_filter, visible=(self._config.get_on_off_filter_auto)))
                    .add(BackItem(self.display))
                    )
                .add(MenuConfirm(self.display, "RECOVERY", ('-> YES', '<- NO'), self._config.set_on_off_recovery)) 
                .add(BackItem(self.display))
            )        
            .add(BackItem(self.display))    
        )





    

 
