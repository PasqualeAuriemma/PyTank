import network
import time
import urequests
import json
import gc

# La tua classe ConnectionManaging (come definita nel Canvas "Gestore di Connessione WiFi (MicroPython)")
class ConnectionManaging:
    """
    Gestisce la connessione WiFi e le richieste HTTP/HTTPS per dispositivi MicroPython.
    """
    
    def __init__(self, ssid=None, password=None, host=None):
        """
        Inizializza il gestore di connessione.
        
        Args:
            ssid (str, optional): Il nome della rete WiFi (SSID). Defaults to None.
            password (str, optional): La password della rete WiFi. Defaults to None.
            host (str, optional): L'indirizzo host per le richieste HTTP/HTTPS. Defaults to None.
        """
        self._host = host
        self._ssid = ssid
        self._password = password
        # Crea un'interfaccia station per la connessione client WiFi.
        self._station = network.WLAN(network.STA_IF)

    @property
    def host(self):
        """Restituisce l'host configurato."""
        return self._host

    @host.setter
    def host(self, value):
        """Imposta l'host."""
        self._host = value 

    @property
    def ssid(self):
        """Restituisce l'SSID configurato."""
        return self._ssid

    @ssid.setter
    def ssid(self, value):
        """Imposta l'SSID."""
        self._ssid = value    

    @property
    def password(self):
        """Restituisce la password configurata."""
        return self._password     

    @password.setter
    def password(self, value):
        """Imposta la password."""
        self._password = value    
    
    def connect(self):
        """
        Tenta di connettersi alla rete WiFi configurata.
        Restituisce True in caso di successo, False in caso di fallimento.
        """
        self.log_message("Attivazione dell'interfaccia WiFi...")
        self._station.active(True) # Assicura che l'interfaccia sia attiva

        if self.is_connected():
            self.log_message(f"Già connesso al WiFi. Indirizzo IP: {self._station.ifconfig()[0]}")
            return True
        
        self.log_message(f"Connessione al WiFi: {self.ssid}", end="")
        self._station.connect(self.ssid, self.password)
        
        max_attempts = 40 # Tentativi aumentati per maggiore robustezza (20 secondi)
        attempts = 0
        while not self.is_connected() and attempts < max_attempts:
            self.log_message(".", end="")
            time.sleep(0.5)
            attempts += 1

        if self.is_connected(): 
            self.log_message("\nWiFi Connesso!")
            self.log_message(f"Indirizzo IP: {self._station.ifconfig()[0]}")
            return True
        else:
            self.log_message("\nImpossibile connettersi al WiFi dopo più tentativi.")
            self.log_message(f"Stato della connessione: {self.connection_status()}")
            self._station.active(False) # Disattiva se la connessione fallisce
            return False

    def disconnect(self):
        """
        Disconnette dalla rete WiFi e disattiva l'interfaccia.
        Restituisce True se la disconnessione ha avuto successo o se era già disconnesso.
        """
        if self.is_connected():
            self._station.disconnect()
            self._station.active(False)
            self.log_message("WiFi Disconnesso.")
            return True
        else:
            self.log_message("Non connesso al WiFi.")
            return True # Già disconnesso o non connesso

    def is_connected(self):
        """Verifica se l'interfaccia station è connessa a un punto di accesso."""
        return self._station.isconnected()

    def connection_status(self):
        """
        Restituisce una stringa leggibile che descrive lo stato attuale della connessione WiFi.
        """ 
        status = self._station.status()
        if status == network.STAT_IDLE:
            return "ESSUNA CONNESSIONE"
        elif status == network.STAT_CONNECTING:
            return "CONNESSIONE IN CORSO"
        elif status == network.STAT_WRONG_PASSWORD:
            return "PASSWORD ERRATA"
        elif status == network.STAT_NO_AP_FOUND:
            return "NESSUN AP TROVATO"
        elif status == network.STAT_GOT_IP:
            return "CONNESSO"
        else:    
            return "ALTRO" 

    def log_message(self, message, end='\n'):
        """Funzione di supporto per la stampa dei messaggi, può essere estesa per il logging su file/UART."""
        print(message, end=end)



    def _post_https_request(self, url, data, headers=None, max_retries=3, retry_delay=2):
        """
        Esegue una richiesta POST HTTPS all'URL specificato con i dati forniti.
        Include un meccanismo di ritentativi per gestire errori transitori.
        I dati dovrebbero essere un dizionario che verrà convertito in JSON.
        Gestisce potenziali errori e assicura che la risposta sia chiusa.
        """
        response = None # Inizializza la risposta a None

        if headers is None:
            headers = {'Content-Type': 'application/json'}

        for attempt in range(1, max_retries + 1):
            try:
                gc.collect() # Esegue la garbage collection per liberare memoria.
                self.log_message(f"\nEffettuando richiesta POST a: {url} (Tentativo {attempt}/{max_retries})")
                self.log_message(f"Invio dati: {json.dumps(data)}")

                response = urequests.post(url, headers=headers, data=json.dumps(data), timeout=20)

                if 200 <= response.status_code < 300:
                    self.log_message(f"Richiesta completata con successo! (Codice di stato: {response.status_code})")
                    self.log_message("Contenuto della risposta:")
                    self.log_message(response.text)
                    return response.text # Successo, esci dalla funzione
                else:
                    self.log_message(f"Errore HTTP: Codice di stato {response.status_code}")
                    self.log_message(f"Motivo della risposta: {response.reason}")
                    self.log_message(f"Testo della risposta: {response.text}")
                    # Non è un errore di connessione, ma un errore del server. Potrebbe non valere la pena riprovare.
                    # Per ora, usciamo se il server risponde con un errore non-2xx.
                    return None 
            except OSError as e:
                self.log_message(f"Errore di rete durante la richiesta POST (Tentativo {attempt}): {e}")
                if attempt < max_retries:
                    # Implementa il backoff esponenziale per dare alla rete/server il tempo di recuperare.
                    backoff_time = retry_delay * (2 ** (attempt - 1))
                    self.log_message(f"Riprovo tra {backoff_time} secondi...")
                    time.sleep(backoff_time)
                else:
                    self.log_message("Tutti i tentativi di richiesta POST sono falliti dopo il backoff esponenziale.")
                    return None
            except Exception as e:
                self.log_message(f"Si è verificato un errore imprevisto: {e}")
                return None
            finally:
                if response:
                    response.close()
                    self.log_message("Risposta chiusa.")
        return None # Tutti i tentativi sono falliti



    def send_value_to_web(self, value, key, timestamp):
        # String fileName = key + "_v.jso";
        # saveValue(fileName, value, timestamp, key);
        url = f"http://{self.host}/take{key}.php"
        data = {key: value, "Date": timestamp}
            
        self.log_message(f"Tentativo di invio del valore '{value}' per la chiave '{key}' a {url}")
                        
        if self.connect():
            self._post_https_request(url, data)
            self.disconnect()
            return True
        else:
            return False



'''
        // void ConnectionManaging::chackIfSendValue(byte pivot, byte Minute, float value, String key, String now) {
        //   if (key == "Temp" && value != -1000.00 && value != 0.0) {
        //     if (H % pivot == 0 && M == Minute && S == int(H / pivot) && S != previousSecSend) {
        //       sendValueToWeb(value, key, now);
        //       previousSecSend = S;
        //     }
        //   }else if (key == "Ec" && int(value) != 1) {
        //     if (H % pivot == 0 && M == Minute && S == int(H / pivot) && S != previousSecSendEC) {
        //       previousSecSendEC = S;
        //       sendValueToWeb(value, key, now);
        //     }
        //   }else (key == "Ph" && int(value) != 1) {
        //     if (H % pivot == 0 && M == Minute && S == int(H / pivot) && S != previousSecSendPh) {
        //       previousSecSendPh = S;
        //       sendValueToWeb(value, key, now);
        //     }
        //   }
        // }

        // void resendValueToWeb(String value, String key,  String timeStamp) {
        //   String payload = "";
        //   payload += key;
        //   payload += "=";
        //   payload += value;
        //   payload += ":";
        //   payload += "Date=";
        //   payload +=  timeStamp;
        //   payload += ";";
        //   Serial.println(payload);
        //   Serial3.println(payload);
        // }

        // void chackWhenResendMeasure(byte _hour, byte _minute) {
        //     if (H == _hour && M == _minute && S == 0 && S != previousSecResend) {
        //     Serial.println("Sono qui! 1");
        //     loadingNotSendedMeasure();
        //     previousSecResend = S;
        //     }else{

        //       if(S > 0 && previousSecResend == 0){
        //         Serial.println("Sono qui! 2");
        //         previousSecResend = S;
        //       }
        //     }
        // }    
'''