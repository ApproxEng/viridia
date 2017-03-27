from euclid import Vector2

from approxeng.holochassis.chassis import rotate_vector, Motion, DeadReckoning
from approxeng.holochassis.dynamics import RateLimit, MotionLimit
from approxeng.viridia import IntervalCheck
from approxeng.viridia.task import Task


class ManualMotionTask(Task):
    """
    Class enabling manual control of the robot from the joystick. Uses dead-reckoning for bearing lock.
    """

    ACCEL_TIME = 1.0
    'Time to reach full speed from a standing start'

    def __init__(self):
        super(ManualMotionTask, self).__init__(task_name='Manual motion')
        self.bearing_zero = None
        self.max_trn = 0
        self.max_rot = 0
        self.dead_reckoning = None
        self.pose_display_interval = IntervalCheck(interval=0.2)
        self.pose_update_interval = IntervalCheck(interval=0.1)
        self.rate_limit = None
        ':type : approxeng.holochassis.dynamics.RateLimit'
        self.motion_limit = None
        ':type : approxeng.holochassis.dynamics.MotionLimit'
        self.limit_mode = 0

    def init_task(self, context):
        # Maximum translation speed in mm/s
        self.max_trn = context.chassis.get_max_translation_speed()
        # Maximum rotation speed in radians/2
        self.max_rot = context.chassis.get_max_rotation_speed()
        self._set_relative_motion(context)
        self.dead_reckoning = DeadReckoning(chassis=context.chassis, counts_per_revolution=1.0, max_count_value=None)
        self.motion_limit = MotionLimit(
            linear_acceleration_limit=context.chassis.get_max_translation_speed() / ManualMotionTask.ACCEL_TIME,
            angular_acceleration_limit=context.chassis.get_max_rotation_speed() / ManualMotionTask.ACCEL_TIME)
        self.rate_limit = RateLimit(limit_function=RateLimit.fixed_rate_limit_function(1 / ManualMotionTask.ACCEL_TIME))
        self.limit_mode = 0

    def _set_absolute_motion(self, context):
        """
        Lock motion to be compass relative, zero point (forwards) is the current bearing
        """
        self.bearing_zero = self.dead_reckoning.pose.orientation
        context.display.show("Absolute motion engaged")

    def _set_relative_motion(self, context):
        """
        Set motion to be relative to the robot's reference frame
        """
        self.bearing_zero = None
        context.display.show("Relative motion engaged")

    def _toggle_limit_mode(self, context):
        """
        Toggle the motion limit mode
        """
        self.limit_mode = (self.limit_mode + 1) % 3
        if self.limit_mode == 0:
            context.display.show("Motion limit disabled")
        elif self.limit_mode == 1:
            context.display.show("Motion limit enabled")

    def poll_task(self, context, tick):

        # Check joystick buttons to see if we need to change mode or reset anything
        if context.pressed('triangle'):
            self._set_relative_motion(context)
        elif context.pressed('square'):
            self._set_absolute_motion(context)
        elif context.pressed('circle'):
            self.dead_reckoning.reset()
            context.display.show("Absolute bearing reset")
        elif context.pressed('cross'):
            self._toggle_limit_mode(context)

        # Check to see whether the minimum interval between dead reckoning updates has passed
        if self.pose_update_interval.should_run():
            self.dead_reckoning.update_from_counts(context.motors.read_angles())

        # Get a vector from the left hand analogue stick and scale it up to our
        # maximum translation speed, this will mean we go as fast directly forward
        # as possible when the stick is pushed fully forwards

        translate = Vector2(
            context.joystick.get_axis_value('lx'),
            context.joystick.get_axis_value('ly')) * self.max_trn
        ':type : euclid.Vector2'

        # If we're in absolute mode, rotate the translation vector appropriately
        if self.bearing_zero is not None:
            translate = rotate_vector(translate,
                                      self.bearing_zero - self.dead_reckoning.pose.orientation)

        # Get the rotation in radians per second from the right hand stick's X axis,
        # scaling it to our maximum rotational speed. When standing still this means
        # that full right on the right hand stick corresponds to maximum speed
        # clockwise rotation.
        rotate = context.joystick.get_axis_value('rx') * self.max_rot

        # Given the translation vector and rotation, use the chassis object to calculate
        # the speeds required in revolutions per second for each wheel. We'll scale these by the
        # wheel maximum speeds to get a range of -1.0 to 1.0
        # This is a :class:`approxeng.holochassis.chassis.WheelSpeeds` containing the speeds and any
        # scaling applied to bring the requested velocity within the range the chassis can
        # actually perform.
        motion = Motion(translation=translate, rotation=rotate)
        if self.limit_mode == 1:
            motion = self.motion_limit.limit_and_return(motion)

        # Send desired motor speed values over the I2C bus to the motors
        context.motors.set_speeds(context.chassis.get_wheel_speeds(motion=motion).speeds)
