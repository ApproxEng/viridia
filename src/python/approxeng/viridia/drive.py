from approxeng.holochassis.chassis import rotate_vector, Motion, DeadReckoning, rotate_point
from approxeng.holochassis.dynamics import MotionLimit
from euclid import Vector2, Point2
from math import asin, pi, sqrt


class Drive:
    """
    High level class to manage the robot's motion, aggregates the chassis, motors and a bit of planning logic.
    """

    def __init__(self, motors, chassis):
        """
        Create a new Drive instance
        
        :param motors: 
            A :class:`approxeng.viridia.motors.Motors` instance used to set motor speeds and read wheel angles
        :param chassis: 
            A :class:`approxeng.holochassis.chassis.HoloChassis` used to compute kinematics
        """
        self.motors = motors
        self.chassis = chassis
        # Maximum translation speed in mm/s
        self.max_trn = chassis.get_max_translation_speed()
        # Maximum rotation speed in radians/2
        self.max_rot = chassis.get_max_rotation_speed()
        self.front = 0.0
        self.dead_reckoning = DeadReckoning(chassis=chassis, counts_per_revolution=1.0)
        self.motion_limit = None

    def set_motion_limit(self, accel_time):
        """
        Set a motion limit, or remove an existing one. The limit fixes the maximum rate of change in the requested
        motion.
        
        :param accel_time: 
            Either None to set no limit, or a number of seconds which will set the minimum time required to go from
            a standing start to full speed in any component of the requested motion.
        """
        if accel_time is None:
            self.motion_limit = None
        else:
            self.motion_limit = MotionLimit(
                linear_acceleration_limit=self.max_trn / accel_time,
                angular_acceleration_limit=self.max_rot / accel_time)

    def set_motion(self, motion):
        """
        Set the motor speeds according to the supplied motion relative to the robot's front.
        
        :param motion: 
            A motion, in robot space and relative to self.front. Any motion limit defined will be applied
            to the supplied motion. If this is None nothing will be done.
        """
        if motion is None:
            return
        if self.front != 0.0:
            motion = Motion(translation=rotate_vector(motion.translation, self.front), rotation=motion.rotation)
        if self.motion_limit is not None:
            motion = self.motion_limit.limit_and_return(motion)
        speeds = [speed * -60 for speed in self.chassis.get_wheel_speeds(motion=motion).speeds]
        self.motors.set_speeds(speeds)

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

    def update_dead_reckoning(self):
        """
        Read angles from the motors and use them to update the current dead reckoning pose. 
        
        :returns:
            A :class:`approxeng.holochassis.chassis.Pose` containing the current dead reckoning pose
        """
        self.dead_reckoning.update_from_revolutions(self.motors.read_angles())
        return self.dead_reckoning.pose

    def drive_at(self, x, y, speed, turn_speed=pi, min_distance=10):
        """
        Set and return a motion to get to a target specified relative to the robot's coordinate system. Note 
        that the 'front' is added when the motion is applied to the robot, so this implicitly is relative to that,
        with positive y axis in the direction of the robot's front.
        
        :param x: 
            X coordinate of the target in mm    
        :param y: 
            Y coordinate of the target in mm
        :param speed:
            Desired linear speed
        :param turn_speed:
            If a motion can't be calculated then turn on the spot instead, at turn_speed radians per second
        :param min_distance:
            If defined, and the target is closer, then stop
        :return: 
            The :class:`approxeng.holochassis.chassis.Motion` that was applied.
        """
        if min_distance is not None and sqrt(x ^ 2 + y ^ 2) < min_distance:
            motion = Motion(translation=Vector2(0, 0), rotation=0)
        else:
            if x == 0:
                # Straight ahead, avoid future division by zero!
                motion = Motion(translation=Vector2(0, speed), rotation=0)
            elif abs(y) < x < 0:
                # Turn first without moving
                if x > 0:
                    motion = Motion(translation=Vector2(0, 0), rotation=turn_speed)
                else:
                    motion = Motion(translation=Vector2(0, 0), rotation=-turn_speed)
            else:
                radius = y ^ 2 / x
                # Angle is clockwise rotation
                angle = asin(x / y)
                arc_length = angle * radius
                motion = Motion(translation=Vector2(0, speed), rotation=angle * speed / arc_length)
        self.set_motion(motion)
        return motion

    def drive_at_world(self, x, y, speed, turn_speed=pi, min_distance=10):
        """
        Similar to drive_at, but x and y are specified in world coordinates, and the method uses the dead reckoning
        logic to map from world to robot coordinates
        
        :param x: 
        :param y: 
        :param speed: 
        :param turn_speed: 
        :param min_distance: 
        :return: 
        """
        p = self.dead_reckoning.pose.position
        target_point = Point2(x=x - p.x, y=y - p.y)
        rotate_point(target_point, -self.dead_reckoning.pose.orientation)
        return self.drive_at(target_point.x, target_point.y, speed, turn_speed, min_distance)
