from approxeng.holochassis.drive import Drive


class ViridiaDrive(Drive):
    """
    Implementation of Drive to use Viridia's motors
    """

    def __init__(self, chassis, motors):
        """
        Create a new Drive instance
        :param motors: 
            A :class:`approxeng.viridia.motors.Motors` instance used to set motor speeds and read wheel angles
        :param chassis: 
            A :class:`approxeng.holochassis.chassis.HoloChassis` used to compute kinematics
        """
        super(ViridiaDrive, self).__init__(chassis=chassis)
        self.motors = motors

    def enable_drive(self):
        """
        Enable the motors. This will also set the motor speeds to zero first to avoid unpleasant surprises.
        """
        self.motors.set_speeds(0.0, 0.0, 0.0)
        self.motors.enable()

    def disable_drive(self):
        """
        Disable the motors. This will in effect execute a hard stop irrespective of any defined limit.
        """
        self.motors.disable()

    def set_wheel_speeds_from_motion(self, motion):
        speeds = [speed * -60 for speed in self.chassis.get_wheel_speeds(motion=motion).speeds]
        self.motors.set_speeds(speeds)

    def update_dead_reckoning(self):
        self.dead_reckoning.update_from_revolutions(self.motors.read_angles())
        return self.dead_reckoning.pose
