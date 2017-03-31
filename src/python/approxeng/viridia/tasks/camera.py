from math import pi
from time import sleep

from euclid import Vector2
from imutils.video import VideoStream

from approxeng.holochassis.chassis import Motion
from approxeng.picamera import find_lines
from approxeng.viridia import IntervalCheck
from approxeng.viridia.task import Task


class LineFollowerTask(Task):
    """
    Follow all the lines!
    """

    def __init__(self):
        super(LineFollowerTask, self).__init__(task_name='Line follower')
        self.stream = None
        self.last_line_to_the_right = True
        self.display_interval = IntervalCheck(interval=0.1)

    def init_task(self, context):

        """
        Create the video stream, which should activate the camera, and then pause for a couple of seconds
        to let it gather its thoughts.
        """
        # Set up lighting
        context.feather.set_lighting_mode(2)
        context.feather.set_direction(-2.0)
	context.feather.set_ring_hue(0)
        # Create stream and pause
        self.stream = VideoStream(usePiCamera=True, resolution=(128, 128)).start()
        sleep(2.0)
	context.feather.set_ring_hue(200)
        context.drive.enable_drive()
        # The camera is on the back of the robot, so set the front to be at PI radians
        context.drive.front = pi
        # Disable any motion limit we may have in action, it'll just confuse things
        context.drive.set_motion_limit(None)
        # Reset dead reckoning, we don't really use it but it'll save confusion later if this changes
        context.drive.reset_dead_reckoning()
        # Determine whether, if we lose the line, we should rotate clockwise (True) or counter-clockwise (False)
        self.last_line_to_the_right = True

    def poll_task(self, context, tick):
        frame = self.stream.read()
        lines = find_lines(image=frame, threshold=50, scan_region_height=20, scan_region_position=0,
                           scan_region_width_pad=0, min_detection_area=40, invert=True, blur_kernel_size=9)
        if len(lines) > 0:
            """
            Found at least one line, pick the left-most. Lines are detected about 15cm from the centre of the robot, 
            and far left is about 7cm to the left so multiplying the x centroid of the first line segment by 70 gives
            us the x coordinate of the target in mm.
            """
            target_x = lines[0] * 70
            target_y = 70
            context.drive.drive_at(x=target_x, y=target_y, speed=250, turn_speed=pi / 2)
            self.last_line_to_the_right = target_x >= 0
        else:
            # Can't see a line, so rotate towards the side where we last saw one!
            if self.last_line_to_the_right:
                context.drive.set_motion(Motion(translation=Vector2(0, 0), rotation=pi / 2))
            else:
                context.drive.set_motion(Motion(translation=Vector2(0, 0), rotation=-pi / 2))

        if self.display_interval.should_run():
            if len(lines) > 0:
                context.feather.set_direction(lines[0])
            else:
                context.feather.set_direction(-2)

    def shutdown(self, context):
        print 'Disposing of streams'
        context.drive.disable_drive()
        context.drive.front = 0
        if self.stream is not None:
            self.stream.stop()
            self.stream = None
