__author__ = 'tom'


class Motors:
    """
    Handles the mechaduino servo motors over I2C
    """

    def __init__(self, i2c, base_address=0x61, motor_count=3):
        """
        Create a new instance, using the supplied :class:approxeng.pi2arduino.I2CHelper to manage communication
        
        :param i2c: 
            I2CHelper instance to use.
        :param base_address:
            Numeric I2C address on which the first of the motors is found, assuming that subsequent motors
            increment from this address. Defaults to 0x61
        :param motor_count:
            The number of motors, used when sending messages such as enable / disable to all controllers.
            Defaults to 3
        """
        self.i2c = i2c
        self.base_address = base_address
        self.motor_count = motor_count

    def set_speeds(self, speeds):
        """
        Set motor speeds, in RPM, for all motors
        :param speeds: 
            A sequence of numbers which will be used to set speeds for motors, with the first speed setting
            the motor at self.base_address and subsequent ones incrementing from there
        """
        for address_offset, speed in enumerate(speeds):
            # Command 0 sets velocity mode and setpoint
            self.i2c.send(self.base_address + address_offset, 0, float(speed))

    def enable_motor(self, motor):
        """
        Enable a single motor, motors are specified by offset from base address, so in [0,1,2] for our robot
        """
        # Command 1 enables closed loop control
        self.i2c.send(self.base_address + motor, 1)

    def enable(self):
        """
        Enable closed loop control on all motors, this must be called before you'll see any motion.
        """
        for motor in range(0, self.motor_count):
            self.enable_motor(motor)

    def disable_motor(self, motor):
        """
        Disable a single motor, motors are specified by offset from base address, so in [0,1,2] for our robot
        """
        # Command 2 disables closed loop control
        self.i2c.send(self.base_address + motor, 2)

    def disable(self):
        """
        Disable closed loop control on all motors, shutting them down and putting them into a static
        holding mode. Motor power is still active and will passively resist disturbance, but no active
        correction will be applied.
        """
        for motor in range(0, self.motor_count):
            self.disable_motor(motor)

    def read_angles(self):
        """
        Read angle data from all motors
        
        :return: 
            A sequence of floating point values, specified in overall revolutions since initialisation
        """
        return [self.i2c.read(self.base_address + address_offset, 'f')[0]
                for address_offset in range(0, self.motor_count)]
