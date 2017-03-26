__author__ = 'tom'


class Feather:
    """
    Class used to access facilities on the ATMega328 based Feather board on the brain module. See the 'src/arduino' 
    code for what's going to be listening to messages from here.
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