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

    def __init__(self, linear_speed=100, turn_speed=pi / 2, enable_drive=True, threshold=50, scan_region_height=20,
                 scan_region_position=0, scan_region_width_pad=0, min_detection_area=40, invert=True,
                 blur_kernel_size=9, physical_scan_width=140, physical_scan_distance=70, camera_resolution=128):
        """
        Create a new line follower task
        
        :param linear_speed: 
            The linear speed to move when we have a line in sight, mm/s, defaults to 100
        :param turn_speed: 
            The angular speed to use when turning to locate the line, radians/second, defaults to pi/2
        :param enable_drive: 
            True to enable drive operation, false to just show the lights, defaults to True
        :param threshold: 
            The threshold used to convert to black and white after a gaussian blur is applied, defaults to 100
        :param scan_region_height: 
            The height in pixels of the region to use, defaults to 20
        :param scan_region_position: 
            The position of the region relative to the entire frame. 0 is at the top, 1.0 is as far towards the bottom 
            as it will go. Defaults to 0, scanning the top 'scan_region_height' pixels of the image
        :param scan_region_width_pad:
            The number of pixels to discard at either edge of the region, defaults to 0
        :param min_detection_area:
            The minimum area of detected moments, any feature below this size will be ignored. Defaults to 40 pixels
        :param invert: 
            Boolean - set this to true if your pi camera is upside-down and you therefore want to have -1.0 at the right 
            hand edge of the image rather than the left, defaults to True for Viridia's camera mount
        :param blur_kernel_size:
            Size of the kernel used when applying the gaussian blur. Defaults to 9
        :param physical_scan_width:
            The width in mm of the region the camera is scanning for lines, used to map the line finder output to a
            physical distance. Defaults to 140
        :param physical_scan_distance:
            The distance from the robot's centre of the scan region. This can be artificially shortened to create more
            aggressive turning behaviour. Defaults to 70 even though the actual distance for Viridia is more like 150
        :param camera_resolution:
            The resolution of the square image frame used by the camera, defaults to 128 - we really don't need high
            resolutions for this algorithm
        """
        super(LineFollowerTask, self).__init__(task_name='Line follower')
        self.stream = None
        self.last_line_to_the_right = True
        self.display_interval = IntervalCheck(interval=0.1)
        self.linear_speed = linear_speed
        self.enable_drive = enable_drive
        self.turn_speed = turn_speed
        self.threshold = threshold
        self.scan_region_height = scan_region_height
        self.scan_region_position = scan_region_position
        self.scan_region_width_pad = scan_region_width_pad
        self.min_detection_area = min_detection_area
        self.invert = invert
        self.blur_kernel_size = blur_kernel_size
        self.physical_scan_width = physical_scan_width
        self.physical_scan_distance = physical_scan_distance
        self.camera_resolution = camera_resolution

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
        self.stream = VideoStream(usePiCamera=True, resolution=(self.camera_resolution, self.camera_resolution)).start()
        for i in range(0, 4):
            # We really need to make sure the drive is enabled!
            if self.enable_drive:
                context.drive.enable_drive()
            sleep(0.5)
        context.feather.set_ring_hue(200)
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
        lines = find_lines(image=frame, threshold=self.threshold, scan_region_height=self.scan_region_height,
                           scan_region_position=self.scan_region_position,
                           scan_region_width_pad=self.scan_region_width_pad, min_detection_area=self.min_detection_area,
                           invert=self.invert, blur_kernel_size=self.blur_kernel_size)
        if self.enable_drive:
            if len(lines) > 0:
                """
                Found at least one line, pick the left-most. Lines are detected about 15cm from the centre of the robot, 
                and far left is about 7cm to the left so multiplying the x centroid of the first line segment by 70 
                gives us the x coordinate of the target in mm.
                """
                target_x = lines[0] * self.physical_scan_width / 2
                target_y = self.physical_scan_distance
                context.drive.drive_at(x=target_x, y=target_y, speed=self.linear_speed, turn_speed=self.turn_speed)
                self.last_line_to_the_right = target_x >= 0
            else:
                # Can't see a line, so rotate towards the side where we last saw one!
                if self.last_line_to_the_right:
                    context.drive.set_motion(Motion(translation=Vector2(0, 0), rotation=self.turn_speed))
                else:
                    context.drive.set_motion(Motion(translation=Vector2(0, 0), rotation=-self.turn_speed))
        if self.display_interval.should_run():
            if len(lines) > 0:
                context.feather.set_direction(lines[0])
            else:
                context.feather.set_direction(-2)

    def shutdown(self, context):
        context.display.show('Disposing of streams')
        context.drive.disable_drive()
        context.drive.front = 0
        if self.stream is not None:
            self.stream.stop()
            self.stream = None
