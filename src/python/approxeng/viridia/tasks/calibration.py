from approxeng.viridia.task import Task
from approxeng.holochassis.chassis import Motion
from euclid import Vector2
from time import time


class LinearCalibrationTask(Task):
    """
    Linear motion only depends on the relative angles of each of the wheels. If we define a motion with no rotation
    component we can calibrate the wheel sizes without having to have the chassis dimensions set correctly. We can then
    use the :class:`approxeng.viridia.task.calibration.AngularCalibrationTask` to find the correct chassis dimensions.
    """

    def __init__(self):
        super(LinearCalibrationTask, self).__init__(task_name='Linear calibration')
        self.motion = None
        self.start_time = 0

    def init_task(self, context):
        pass

    def poll_task(self, context, tick):
        if self.motion is None:
            self.motion = Motion(Vector2(0, 150), 0)
            self.start_time = time()  # Time in seconds
        elif time() - self.start_time > 3:
            self.motion = Motion(Vector2(0, 0), 0)
            print context.drive.dead_reckoning.pose
        context.drive.set_motion(self.motion)
        context.drive.update_dead_reckoning()


class AngularCalibrationTask(Task):
    """
    Angular calibration depends both on wheel size and chassis size, so only use this once wheel size has
    been determined by the linear calibration task.
    """

    def __init__(self):
        super(AngularCalibrationTask, self).__init__(task_name='Angular calibration')

    def init_task(self, context):
        pass

    def poll_task(self, context, tick):
        pass
