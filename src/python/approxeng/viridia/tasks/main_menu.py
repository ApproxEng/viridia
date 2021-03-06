from time import sleep

from approxeng.viridia.task import ClearStateTask, Task


class MenuTask(Task):
    """
    Top level menu class
    """

    def __init__(self, tasks):
        super(MenuTask, self).__init__(task_name='Menu')
        self.tasks = tasks
        self.selected_task_index = 0

    def init_task(self, context):
        context.feather.set_lighting_mode(0)
        context.feather.set_ring_hue(100)
        context.motors.disable()
        pass

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
