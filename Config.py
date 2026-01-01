
class Config():
    def __init__(self):
        self._start_hour = 0
        self._start_minutes = 0
        self._end_hour = 0
        self._end_minutes = 0
        self._temp_max = 0
        self._temp_min = 0
        self._auto_enabled = True
        self._mantein_enabled = False
        self._stand_by = False
        self._on_off_light_auto = False
        self._on_off_light_auto_temp = False
        self._on_off_heater_temp = False
        self._on_off_heater = False
        self._on_off_ec = False
        self._on_off_ec_temp = False
        self._on_off_ph = False
        self._on_off_ph_temp = False
        self._on_off_temperature = False
        self._on_off_temperature_temp = False
        self._on_off_filter_temp = False
        self._on_off_filter = False
        self._on_off_feeder_temp = False
        self._on_off_feeder = False
        self._on_off_temperature_sending_temp = False
        self._on_off_temperature_sending = False
        self._on_off_ec_sending = False
        self._on_off_ec_sending_temp = False
        self._on_off_ph_sending = False
        self._on_off_ph_sending_temp = False
        self._on_off_filter_auto = False
        self._on_off_filter_auto_temp = False
        self._on_off_heater_auto_temp = False
        self._on_off_heater_auto = False
        self._on_off_recovery = False
        self._freq_update_web_temperature = 1
        self._freq_update_web_ec = 1
        self._freq_update_web_ph = 1
        self._freq_filter = 1
        self._hour_loading = 0
        self._min_loading = 0
        self._relay0 = False
        self._relay1 = False
        self._relay2 = False
        self._relay3 = False
        self._temperature = 0.0
        self._ec = 0.0
        self._ph = 0.0
        self.freq = ['1', '2', '3', '4', '6', '8', '12', '24']
        self.mode_list = ['AUTO', 'MAINTENANCE', 'STAND BY']
        self._connection_action = False
        self._send_action_ec = False
        self._send_action_ph = False
        self._send_action_temp = False

    def set_timer_time(self, list_time = [0, 0, 0, 0]):
        self._start_hour = list_time[0]
        self._start_minutes = list_time[1]
        self._end_hour = list_time[2]
        self._end_minutes = list_time[3]
        
    def get_timer_time(self):
        return [self._start_hour,
                self._start_minutes,
                self._end_hour,
                self._end_minutes]

    def set_auto_heater(self, list_temp = [0, 0]):
        self._temp_max = list_temp[0]
        self._temp_min = list_temp[1]

    def get_auto_heater(self):
        return [self._temp_max,
                self._temp_min]

    def get_connection_action(self):
        return self._connection_action

    def set_connection_action(self, value):
        self._connection_action = value

    def get_send_action_ec(self):     
        return self._send_action_ec

    def set_send_action_ec(self, value):
        self._send_action_ec = value

    def get_send_action_ph(self):            
        return self._send_action_ph

    def set_send_action_ph(self, value):
        self._send_action_ph = value

    def get_send_action_temp(self):        
        return self._send_action_temp

    def set_send_action_temp(self, value):
        self._send_action_temp = value

    def set_on_off_recovery(self, value):
        self._on_off_recovery = value

    def get_on_off_recovery(self):
        return self._on_off_recovery
     
    def get_rele_list(self):
        return [self._relay0, self._relay1, self._relay2, self._relay3]

    def off_automatic_process(self):
        self._on_off_light_auto_temp = self._on_off_light_auto
        self.set_on_off_light_auto(False)
        self._on_off_heater_temp = self._on_off_heater
        self.set_on_off_heater(False)
        self._on_off_filter_temp = self._on_off_filter
        self.set_on_off_filter(False)
        self._on_off_feeder_temp = self._on_off_feeder
        self.set_on_off_feeder(False)
        self._on_off_ec_temp = self._on_off_ec
        self.set_on_off_ec(False)
        self._on_off_ph_temp = self._on_off_ph
        self.set_on_off_ph(False)
        self._on_off_temperature_temp = self._on_off_temperature
        self.set_on_off_temperature(False)
        self._on_off_temperature_sending_temp = self._on_off_temperature_sending
        self.set_on_off_temperature_sending(False)
        self._on_off_ec_sending_temp = self._on_off_ec_sending
        self.set_on_off_ec_sending(False)
        self._on_off_ph_sending_temp = self._on_off_ph_sending
        self.set_on_off_ph_sending(False)
        self.auto_enabled = False
        self.mantein_enabled = True
        self.stand_by = False

    def on_automatic_process(self):
        self.set_on_off_light_auto(self._on_off_light_auto_temp)
        self.set_on_off_heater(self._on_off_heater_temp)
        self.set_on_off_filter(self._on_off_filter_temp)
        self.set_on_off_feeder(self._on_off_feeder_temp)
        self.set_on_off_ec(self._on_off_ec_temp)
        self.set_on_off_ph(self._on_off_ph_temp)
        self.set_on_off_temperature(self._on_off_temperature_temp)
        self.set_on_off_temperature_sending(self._on_off_temperature_sending_temp)
        self.set_on_off_ec_sending(self._on_off_ec_sending_temp)
        self.set_on_off_ph_sending(self._on_off_ph_sending_temp)
        self.auto_enabled = True
        self.mantein_enabled = False
        self.stand_by = False

    def stand_by_Process(self):
        pass    

    def active_temperature_monitoring(self, value):
        self._on_off_temperature_sending = value
        self._on_off_temperature = value

    def active_ec_monitoring(self, value):
        self._on_off_ec_sending = value
        self._on_off_ec = value

    def active_ph_monitoring(self, value):
        self._on_off_ph_sending = value
        self._on_off_ph = value

    def to_dict(self):
        return {
        "startHour": self._start_hour,
        "startMinutes": self._start_minutes,
        "endHour": self._end_hour,
        "endMinutes": self._end_minutes,
        "tempMax": self._temp_max,
        "tempMin": self._temp_min,
        "autoEnabled": self._auto_enabled,
        "manteinEnabled": self._mantein_enabled,
        "standBy": self._stand_by,
        "onOffLightAuto": self._on_off_light_auto,
        "onOffHeater": self._on_off_heater,
        "onOffEC": self._on_off_ec,
        "onOffPH": self._on_off_ph,
        "onOffTemperature": self._on_off_temperature,
        "onOffFilter": self._on_off_filter,
        "onOffFeeder": self._on_off_feeder,
        "onOffTemperatureSending": self._on_off_temperature_sending,
        "onOffECSending": self._on_off_ec_sending,
        "onOffPhSending": self._on_off_ph_sending,
        "onOffFilterAuto": self._on_off_filter_auto,
        "onOffHeaterAuto": self._on_off_heater_auto,
        "freqUpdateWebTemperature": self._freq_update_web_temperature,
        "freqUpdateWebEC": self._freq_update_web_ec,
        "freqUpdateWebPH": self._freq_update_web_ph,
        "freqFilter": self._freq_filter,
        "hourLoading": self._hour_loading,
        "minLoading": self._min_loading,
        "relay0": self._relay0,
        "relay1": self._relay1,
        "relay2": self._relay2,
        "relay3": self._relay3,
        "temperature": self._temperature,
        "ec": self._ec,
        "ph": self._ph,
        "onOffRecovery": self._on_off_recovery,
        }

    def from_json(self, json):
        self.start_hour = json["startHour"]
        self.start_minutes = json["startMinutes"]
        self.end_hour = json["endHour"]
        self.end_hour = json["endMinutes"]
        self.temp_max = json["tempMax"]
        self.temp_min = json["tempMin"]
        self.auto_enabled = json["autoEnabled"]
        self.mantein_enabled = json["manteinEnabled"]
        self.stand_by = json["standBy"]
        self.set_on_off_light_auto = json["onOffLightAuto"]
        self.set_on_off_heater = json["onOffHeater"]
        self.set_on_off_ec = json["onOffEC"]
        self.set_on_off_ph = json["onOffPH"]
        self.set_on_off_temperature = json["onOffTemperature"]
        self.set_on_off_filter = json["onOffFilter"]
        self.set_on_off_feeder = json["onOffFeeder"]
        self.set_on_off_temperature_sending = json["onOffTemperatureSending"]
        self.set_on_off_ec_sending = json["onOffECSending"]
        self.set_on_off_ph_sending = json["onOffPhSending"]
        self.set_on_off_filter_auto = json["onOffFilterAuto"]
        self.set_on_off_heater_auto = json["onOffHeaterAuto"]
        self.set_freq_update_web_temperature = json["freqUpdateWebTemperature"]
        self.set_freq_update_web_ec = json["freqUpdateWebEC"]
        self.set_freq_update_web_ph = json["freqUpdateWebPH"]
        self.set_freq_filter = json["freqFilter"]
        self.hour_loading = json["hourLoading"]
        self.min_loading = json["minLoading"]
        self.relay0 = json["relay0"]
        self.relay1 = json["relay1"]
        self.relay2 = json["relay2"]
        self.relay3 = json["relay3"]
        self.temperature = json["temperature"]
        self.ec = json["ec"]
        self.ph = json["ph"]
        self._on_off_heater_auto = json["onOffRecovery"]

    @property
    def start_hour(self):
        return self._start_hour
    
    @start_hour.setter
    def start_hour(self, value):
        self._start_hour = value

    @property
    def start_minutes(self):
        return self._start_minutes
    
    @start_minutes.setter
    def start_minutes(self, value):
        self._start_minutes = value

    @property
    def end_hour(self):
        return self._end_hour
    
    @end_hour.setter
    def end_hour(self, value):
        self._end_hour = value

    @property
    def end_minutes(self):
        return self._end_minutes
    
    @end_minutes.setter
    def end_minutes(self, value):
        self._end_minutes = value

    @property
    def temp_max(self):
        return self._temp_max
    
    @temp_max.setter
    def temp_max(self, value):
        self._temp_max = value

    @property
    def temp_min(self):
        return self._temp_min
    
    @temp_min.setter
    def temp_min(self, value):
        self._temp_min = value

    @property
    def auto_enabled(self):
        return self._auto_enabled
    
    @auto_enabled.setter
    def auto_enabled(self, value):
        self._auto_enabled = value

    @property
    def stand_by(self):
        return self._stand_by
    
    @stand_by.setter
    def stand_by(self, value):
        self._stand_by = value    

    @property
    def mantein_enabled(self):
        return self._mantein_enabled
    
    @mantein_enabled.setter
    def mantein_enabled(self, value):
        self._mantein_enabled = value
        
    def set_mode(self, value):
        if value == 0:
            self.on_automatic_process()
        elif value == 1:
            self.off_automatic_process()
        else:
            self.stand_by_process()

    def get_on_off_light_auto(self):
        try:
            return self._on_off_light_auto
        except KeyError:
            self._on_off_light_auto = False
            return False
        
    def set_on_off_light_auto(self, value):
        self._on_off_light_auto = value

    def get_on_off_heater(self):
        return self._on_off_heater
    
    def set_on_off_heater(self, value):
        self._on_off_heater = value        
        
    def get_on_off_ec(self):
        return self._on_off_ec
    
    def set_on_off_ec(self, value):
        self._on_off_ec = value
 
    def get_on_off_ph(self):
        return self._on_off_ph
    
    def set_on_off_ph(self, value):
        self._on_off_ph = value        
        
    def get_on_off_temperature(self):
        return self._on_off_temperature
    
    def set_on_off_temperature(self, value):
        self._on_off_temperature = value        
 
    def get_on_off_filter(self):
        return self._on_off_filter
    
    def set_on_off_filter(self, value):
        self._on_off_filter = value

    def get_on_off_feeder(self):
        return self._on_off_feeder

    def set_on_off_feeder(self, value):
        self._on_off_feeder = value

    def get_on_off_temperature_sending(self):
        return self._on_off_temperature_sending and self._on_off_temperature
    
    def set_on_off_temperature_sending(self, value):
        self._on_off_temperature_sending = value        

    def get_on_off_ec_sending(self):
        return self._on_off_ec_sending and self._on_off_ec
    
    def set_on_off_ec_sending(self, value):
        self._on_off_ec_sending = value

    def get_on_off_ph_sending(self):
        return self._on_off_ph_sending and self._on_off_ph

    def set_on_off_ph_sending(self, value):
        self._on_off_ph_sending = value

    def get_on_off_heater_auto(self):
        return self._on_off_heater_auto
    
    def set_on_off_heater_auto(self, value):
        self._on_off_heater_auto = value

    def get_on_off_filter_auto(self):
        return self._on_off_filter_auto
    
    def set_on_off_filter_auto(self, value):
        self._on_off_filter_auto = value        

    def get_freq_update_web_temperature(self):
        return self._freq_update_web_temperature
    
    def set_freq_update_web_temperature(self, value):
        self._freq_update_web_temperature = self.freq[value]

    def get_freq_update_web_ec(self):
        return self._freq_update_web_ec
    
    def set_freq_update_web_ec(self, value):
        self._freq_update_web_ec = self.freq[value]

    def get_freq_update_web_ph(self):
        return self._freq_update_web_ph
    
    def set_freq_update_web_ph(self, value):
        self._freq_update_web_ph = self.freq[value]

    def get_freq_filter(self):
        return self._freq_filter
    
    def set_freq_filter(self, value):
        self._freq_filter = self.freq[value]

    @property
    def hour_loading(self):
        return self._hour_loading
    
    @hour_loading.setter
    def hour_loading(self, value):
        self._hour_loading = value

    @property
    def min_loading(self):
        return self._min_loading
    
    @min_loading.setter
    def min_loading(self, value):
        self._min_loading = value

    @property
    def relay0(self):
        return self._relay0
    
    @relay0.setter
    def relay0(self, value):
        self._relay0 = value

    @property
    def relay1(self):
        return self._relay1
    
    @relay1.setter
    def relay1(self, value):
        self._relay1 = value

    @property
    def relay2(self):
        return self._relay2
    
    @relay2.setter
    def relay2(self, value):
        self._relay2 = value

    @property
    def relay3(self):
        return self._relay3
    
    @relay3.setter
    def relay3(self, value):
        self._relay3 = value

    @property
    def temperature(self):
        return self._temperature
    
    @temperature.setter
    def temperature(self, value):
        self._temperature = value

    @property
    def ec(self):
        return self._ec
    
    @ec.setter
    def ec(self, value):
        self._ec = value

    @property
    def ph(self):
        return self._ph
    
    @ph.setter
    def ph(self, value):
        self._ph = value    
           