from time import sleep

from approxeng.viridia.task import ClearStateTask, Task
from triangula.tasks.compass_test import CompassTestTask
from triangula.tasks.manual_control import ManualMotionTask
from triangula.tasks.network_info import NetworkInfoTask
from triangula.tasks.patrol import SimplePatrolExample, TrianglePatrol


class MenuTask(Task):
    """
    Top level menu class
    """

    def __init__(self):
        super(MenuTask, self).__init__(task_name='Menu')
        self.tasks = [ManualMotionTask(), NetworkInfoTask(), CompassTestTask(), TrianglePatrol(), SimplePatrolExample()]
        self.selected_task_index = 0

    def init_task(self, context):
        context.lcd.set_backlight(10, 10, 10)
        context.arduino.set_lights(170, 255, 60)

    def _increment_index(self, delta):
        self.selected_task_index += delta
        self.selected_task_index %= len(self.tasks)

    def poll_task(self, context, tick):
        if context.joystick.BUTTON_D_LEFT in context.buttons_pressed:
            self._increment_index(-1)
        elif context.joystick.BUTTON_D_RIGHT in context.buttons_pressed:
            self._increment_index(1)
        elif context.joystick.BUTTON_CROSS in context.buttons_pressed:
            return ClearStateTask(following_task=self.tasks[self.selected_task_index])
        context.lcd.set_text(row1='Task {} of {}'.format(self.selected_task_index + 1, len(self.tasks)),
                             row2=self.tasks[self.selected_task_index].task_name)
        sleep(0.1)
