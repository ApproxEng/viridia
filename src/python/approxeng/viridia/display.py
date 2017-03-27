from abc import ABCMeta, abstractmethod


class Display:
    """
    Superclass for classes which can display textual information to the user
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def show(self, message1=None, message2=None):
        """
        Show a message made up of two parts, both of which are optionsl and default to None
        """
        pass


class PrintDisplay(Display):
    """
    Simple implementation of Display which prints to stdout
    """

    def __init__(self):
        super(PrintDisplay, self).__init__()
        self.last_message1 = None
        self.last_message2 = None

    def show(self, message1=None, message2=None):
        """
        Show a message, made up of two components both of which are optional and default to None. Only print the message
        to stdout if there's a change from the last message. This avoids spamming logs in cases where the code is
        expecting to be writing to a display module, but still shows all messages we actually care about.

        :param message1: 
            String 1
        :param message2:
            String 2
        """
        if message1 != self.last_message1 and message2 != self.last_message2:
            if message2 is not None and message1 is not None:
                print '{}\n{}'.format(message1, message2)
            elif message2 is None and message1 is not None:
                print message1
            elif message1 is None and message2 is not None:
                print message2
        self.last_message1 = message1
        self.last_message2 = message2
