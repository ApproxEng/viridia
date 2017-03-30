__author__ = 'tom'

import RPi.GPIO as gpio

class Feather:
    """
    Class used to access facilities on the ATMega328 based Feather board on the brain module. See the 
    'src/arduino/feather' code for what's going to be listening to messages from here. This class wraps any calls
    to i2c send with a GPIO operation to pause the light-show, otherwise we get a lot of I2C failures as the FastLED
    library on the feather clashes badly with the I2C reception.
    """

    def __init__(self, i2c, i2c_address=0x31, led_disable_pin=27):
        """
        Create a new Feather proxy
        
        :param i2c: 
            An instance of :class:`approxeng.pi2arduino.I2CHelper` used to communicate with the feather
        :param i2c_address:
            I2C address of the feather, defaults to 0x31
        :param led_disable_pin:
            The BCM number of the pin which is used to signal that the feather should pause and wait for data
        """
        self.i2c = i2c
        self.i2c_address = i2c_address
        self.led_disable_pin = led_disable_pin
        gpio.setmode(gpio.BCM)
        gpio.setup(led_disable_pin, gpio.OUT)

    def set_ring_hue(self, hue, spread=30):
        """
        Set the hue and hue spread values for the LED ring
        :param hue: 
            Byte hue value
        :param spread: 
            Optional, the amount of hue spread. Defaults to 30, not used by all modes
        """
        self._send(1, hue, spread)

    def set_lighting_mode(self, mode):
        """
        Set the mode used for the light ring
        
        :param mode: 
            Mode, byte.
            0 - Show semi-random rotating pattern
            1 - Show direction bar
        """
        self._send(0, mode)

    def set_direction(self, radians):
        """
        For modes which use the direction property on the lighting ring, set that property
        
        :param radians: 
            Angle in radians to display
        """
        self._send(3, float(radians))

    def _send(self, *sequence):
        gpio.output(self.led_disable_pin, 1)
        self.i2c.send(self.i2c_address, *sequence)
        gpio.output(self.led_disable_pin, 0)