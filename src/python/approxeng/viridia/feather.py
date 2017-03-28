__author__ = 'tom'


class Feather:
    """
    Class used to access facilities on the ATMega328 based Feather board on the brain module. See the 
    'src/arduino/feather' code for what's going to be listening to messages from here.
    """

    def __init__(self, i2c, i2c_address=0x31):
        """
        Create a new Feather proxy
        
        :param i2c: 
            An instance of :class:`approxeng.pi2arduino.I2CHelper` used to communicate with the feather
        :param i2c_address:
            I2C address of the feather, defaults to 0x31
        """
        self.i2c = i2c
        self.i2c_address = i2c_address

    def set_ring_hue(self, hue, spread=30):
        """
        Set the hue and hue spread values for the LED ring
        :param hue: 
            Byte hue value
        :param spread: 
            Optional, the amount of hue spread. Defaults to 30, not used by all modes
        """
        self.i2c.send(self.i2c_address, 1, hue, spread)

    def set_lighting_mode(self, mode):
        """
        Set the mode used for the light ring
        
        :param mode: 
            Mode, byte.
            0 - Show semi-random rotating pattern
            1 - Show direction bar
        """
        self.i2c.send(self.i2c_address, 0, mode)

    def set_direction(self, radians):
        """
        For modes which use the direction property on the lighting ring, set that property
        
        :param radians: 
            Angle in radians to display
        """
        self.i2c.send(self.i2c_address, 3, float(radians))
