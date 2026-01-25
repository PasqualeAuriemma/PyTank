from machine import Pin
import time

class SensorTemplate:
    """
    A template class for a sensor or actuator in the PyTank project.
    Follows the project's conventions for properties and private members.
    """

    def __init__(self, pin_number, label="Sensor"):
        """
        Initialize the sensor.
        
        Args:
            pin_number (int): The GPIO pin number.
            label (str): A human-readable label for the sensor.
        """
        self._pin_number = pin_number
        self._label = label
        self._value = 0.0
        self._last_update = 0
        
        # Initialize hardware (Example: Input pin)
        # If using I2C, pass the i2c object in __init__ instead
        self._pin = Pin(self._pin_number, Pin.IN)

    @property
    def label(self):
        """Get the sensor label."""
        return self._label

    @property
    def value(self):
        """Get the last read value."""
        return self._value

    @value.setter
    def value(self, new_val):
        """Set the value manually (if needed)."""
        self._value = new_val

    def read(self):
        """
        Read the sensor data. 
        Returns the value and updates the internal state.
        """
        try:
            # Implement hardware reading logic here
            # Example: raw_val = self._pin.value()
            
            # Simulation for template purposes
            raw_val = 1 
            
            self._value = float(raw_val)
            self._last_update = time.time()
            return self._value
            
        except Exception as e:
            print(f"Error reading {self._label}: {e}")
            return None

    def __str__(self):
        return f"[{self._label}] Value: {self._value}"