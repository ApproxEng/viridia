import time
import traceback
from abc import ABCMeta, abstractmethod
from approxeng.viridia.drive import ViridiaDrive


class TaskManager:
    """
    Manages the task loop
    """

    def __init__(self, chassis, joystick, i2c, motors, feather, camera, raw_capture, display):
        self.chassis = chassis
        self.joystick = joystick
        self.i2c = i2c
        self.motors = motors
        self.feather = feather
        self.camera = camera
        self.raw_capture = raw_capture
        self.display = display
        self.drive = ViridiaDrive(chassis=self.chassis, motors=self.motors)
        self.home_task = None

    def _build_context(self):
        return TaskContext(chassis=self.chassis,
                           joystick=self.joystick,
                           buttons_pressed=self.joystick.buttons.get_and_clear_button_press_history(),
                           i2c=self.i2c, feather=self.feather, camera=self.camera, raw_capture=self.raw_capture,
                           motors=self.motors, display=self.display,
                           drive=self.drive)

    def run(self, initial_task):
        """
        Start the task loop. Handles task switching and initialisation as well as any exceptions thrown within tasks.

        :param initial_task:
            An instance of :class:`approxeng.viridia.task.Task` to use as the first task. Typically this is a menu or 
            startup task of some kind.
        """
        active_task = initial_task
        task_initialised = False
        tick = 0

        if self.home_task is None:
            self.home_task = initial_task

        while 1:
            try:
                context = self._build_context()
                if context.pressed('home'):
                    active_task = ClearStateTask(self.home_task)
                    task_initialised = False
                    tick = 0
                if task_initialised:
                    new_task = active_task.poll_task(context=context, tick=tick)
                    if new_task is None:
                        tick += 1
                    else:
                        active_task.shutdown(context)
                        active_task = new_task
                        if isinstance(active_task, ExitTask):
                            active_task = ClearStateTask(self.home_task)
                        task_initialised = False
                        tick = 0
                else:
                    active_task.init_task(context=context)
                    task_initialised = True
            except Exception as e:
                active_task = ClearStateTask(ErrorTask(e))
                task_initialised = False


class TaskContext:
    """
    Contains the resources a task might need to perform its function

    :ivar timestamp:
        The time, in seconds since the epoch, that this context was created. In effect this is also the task creation
        time as they're created at the same time.

    """

    def __init__(self, chassis, joystick, buttons_pressed, i2c, motors, feather, camera, raw_capture, display, drive):
        """
        Create a new task context

        :param chassis:
            An instance of :class:`approxeng.holochassis.HoloChassis` defining the motion dynamics for the robot.
        :param joystick:
            An instance of :class:`approxeng.input.dualshock4.DualShock4` which can be used to get the joystick axes.
        :param buttons_pressed:
            An instance of :class:`approxeng.input.ButtonPresses` containing the buttons pressed since the last tick
            started
        :param i2c:
            An instance of :class:`approxeng.pi2arduino.I2CHelper` used to send and receive data to and from I2C 
            peripherals
        :param motors:
            An instance of :class:`approxeng.viridia.motors.Motors` used to control the mechaduinos and read their
            current positions
        :param feather:
            An instance of :class:`approxeng.viridia.feather.Feather` used to interface to everything attached to
            the Adafruit Feather over I2C. This includes the lights and the solenoid kicker actuator
        :param camera:
            An instance of :class:`picamera.Camera`
        :param raw_capture:
            An instance of :class:`picamera.array.PiRGBArray` used to contain raw data read from the camera to avoid
            having to mess around with JPEG encoding etc.
        :param display:
            An instance of :class:`approxeng.viridia.display.Display` used to show textual messages to the user either
            by displaying them on a hardware module or by printing to stdout
        :param drive:
            An instance of :class:`approxeng.viridia.drive.Drive` providing high level motion functionality
        """
        self.chassis = chassis
        self.joystick = joystick
        self.buttons_pressed = buttons_pressed
        self.timestamp = time.time()
        self.i2c = i2c
        self.motors = motors
        self.feather = feather
        self.camera = camera
        self.raw_capture = raw_capture
        self.display = display
        self.drive = drive

    def pressed(self, sname):
        return self.buttons_pressed.was_pressed(sname)


class Task:
    """
    Base class for tasks. Tasks are single-minded activities which are run, one at a time, on Triangula's
    processor. The service script is responsible for polling the active task, providing it with an appropriate
    set of objects and properties such that it can interact with its environment.
    """

    __metaclass__ = ABCMeta

    def __init__(self, task_name='New Task'):
        """
        Create a new task with the specified name

        :param task_name:
            Name for this task, used in debug mostly. Defaults to 'New Task'
        """
        self.task_name = task_name

    def __str__(self):
        return 'Task[ task_name={} ]'.format(self.task_name)

    @abstractmethod
    def init_task(self, context):
        """
        Called exactly once, the first time a new task is activated. Use this to set up any properties which weren't
        available during construction.

        :param context:
            An instance of :class:`approxeng.viridia.task.TaskContext` containing objects and properties which allow 
            the task to comprehend and act on its environment.
        """
        return None

    @abstractmethod
    def poll_task(self, context, tick):
        """
        Polled to perform the task's action, you shouldn't hang around too long in this method but there's no explicit
        requirement for timely processing.

        :param context:
            An instance of :class:`approxeng.viridia.task.TaskContext` containing objects and properties which allow 
            the task to comprehend and act on its environment.
        :param int tick:
            A counter, incremented each time poll is called.
        :return:
            Either None, to continue this task, or a subclass of :class:`approxeng.viridia.task.Task` to switch to 
            that task.
        """
        return None

    def shutdown(self, context):
        """
        Called when the task exits, clear up any state which won't be handled by the ClearStateTask
        
        :param context:
            The context
        """
        pass


class ClearStateTask(Task):
    """
    Task which clears the state, turns the lights off and stops the motors, then immediately passes control to another
    task.
    """

    def __init__(self, following_task):
        """
        Create a new clear state task, this will effectively reset the robot's peripherals and pass control to the
        next task. Use this when switching to ensure we're not leaving the wheels running etc.

        :param following_task:
            Another :class:`approxeng.viridia.task.Task` which is immediately returned from the first poll operation.
        :return:
        """
        super(ClearStateTask, self).__init__(task_name='Clear state task')
        self.following_task = following_task

    def init_task(self, context):
        # Do init stuff here
        pass

    def poll_task(self, context, tick):
        return self.following_task


class ErrorTask(Task):
    """
    Task used to display an error message
    """

    def __init__(self, exception):
        """
        Create a new error display task

        :param exception:
            An exception which caused this display to be shown
        """
        super(ErrorTask, self).__init__(task_name='Error')
        self.exception = exception
        print exception
        traceback.print_exc()

    def init_task(self, context):
        # Show scary lights if we can
        pass

    def poll_task(self, context, tick):
        # Just hang around, if we had a display we'd print the error message
        time.sleep(0.2)


class ExitTask(Task):
    """
    Special case Task, used to indicate that the current level of the task manager has completed and should take no
    further actions.
    """

    def __init__(self):
        """
        No argument constructor
        """
        super(ExitTask, self).__init__(task_name='Exit')

    def init_task(self, context):
        pass

    def poll_task(self, context, tick):
        pass


class PauseTask(Task):
    """
    Task which will pause for at least the specified number of seconds, then yield to the specified task. If no task
    is specified an ExitTask is used.
    """

    def __init__(self, pause_time, following_task=None):
        """
        Constructor

        :param pause_time:
            This task should wait for at least this number of seconds before yielding.
        :param following_task:
            A task to which this will yield, if this is None an instance of ExitTask will be used.
        :param led_hue:
            Optional, if specified must be an integer between 0 and 255 and requests that all LEDs on the robot
            are set to the specified hue value.
        """
        super(PauseTask, self).__init__(task_name='Pause')
        self.start_time = None
        self.task = following_task
        if self.task is None:
            self.task = ExitTask()
        self.pause_time = pause_time

    def init_task(self, context):
        self.start_time = time.time()

    def poll_task(self, context, tick):
        now = time.time()
        if now - self.start_time >= self.pause_time:
            return self.task
        else:
            return None
