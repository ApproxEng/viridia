__author__ = 'tom'


class Mechaduino():
    """
    Class to communicate with a modified mechaduino
    """

    def __init__(self, address):
        """
        Create a new proxy to the mechaduino, communicating on the specified I2C address

        :param address: I2C address on which to communicate
        """

        self.address = address
