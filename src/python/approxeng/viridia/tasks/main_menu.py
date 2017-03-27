from time import sleep

from approxeng.viridia.task import ClearStateTask, Task
from approxeng.viridia.tasks.manual_control import ManualMotionTask


class MenuTask(Task):
    """
    Top level menu class
    """

    def __init__(self):
        super(MenuTask, self).__init__(task_name='Menu')
        self.tasks = [ManualMotionTask()]
        self.selected_task_index = 0

    def init_task(self, context):
        context.lcd.set_backlight(10, 10, 10)
        context.arduino.set_lights(170, 255, 60)

    def _increment_index(self, delta):
        self.selected_task_index += delta
        self.selected_task_index %= len(self.tasks)

    def poll_task(self, context, tick):
        if context.pressed('dleft'):
            self._increment_index(-1)
        elif context.pressed('dright'):
            self._increment_index(1)
        elif context.pressed('cross'):
            return ClearStateTask(following_task=self.tasks[self.selected_task_index])
        context.display.show('Task {} of {}'.format(self.selected_task_index + 1, len(self.tasks)),
                             self.tasks[self.selected_task_index].task_name)
        sleep(0.1)