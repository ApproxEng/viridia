#!/home/pi/venv/bin/python
"""
Viridia top level service script
"""

import grp
import os
import pwd
from signal import signal, SIGINT, SIGTERM
from sys import exit
from time import sleep

from picamera import PiCamera
from picamera.array import PiRGBArray

from approxeng.holochassis.chassis import get_regular_triangular_chassis
from approxeng.input.asyncorebinder import ControllerResource
from approxeng.input.dualshock4 import DualShock4, CONTROLLER_NAME
from approxeng.pi2arduino import I2CHelper
from approxeng.viridia.display import PrintDisplay
from approxeng.viridia.feather import Feather
from approxeng.viridia.motors import Motors
from approxeng.viridia.task import TaskManager
from approxeng.viridia.tasks.main_menu import MenuTask


def drop_privileges(uid_name='nobody', gid_name='nogroup'):
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        return

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(uid_name).pw_uid
    running_gid = grp.getgrnam(gid_name).gr_gid

    # Reset group access list
    os.initgroups(uid_name, running_gid)

    # Try setting the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)

    # Ensure a very conservative umask
    old_umask = os.umask(077)


def get_shutdown_handler(message=None):
    """
    Build a shutdown handler, called from the signal methods in response to e.g. SIGTERM

    :param message:
        The message to show on the second line of the LCD, if any. Defaults to None
    """

    def handler(signum, frame):
        display.show('Service shutdown', message)
        motors.disable()
        exit(0)

    return handler


signal(SIGINT, get_shutdown_handler('SIGINT received'))
signal(SIGTERM, get_shutdown_handler('SIGTERM received'))

# I2CHelper used to communicate with I2C peripherals. Note that we must be root at this point, but can then
# drop root access and change to a regular user for better sanity - the initialisation of this class performs
# the memory mapping operation which requires root, but actually accessing that mapped memory can be done
# as a regular user.
i2c = I2CHelper()
# Become 'pi'
drop_privileges(uid_name='pi', gid_name='pi')

# Set up a display class, either interfacing to an actual display or printing to the console
display = PrintDisplay()

# Motors
motors = Motors(i2c=i2c)

print motors.read_angles()

while 1:
    try:
        with ControllerResource(controller=DualShock4(), device_name=CONTROLLER_NAME) as joystick:
            display.show("Found dualshock4 at {}".format(joystick))
            task_manager = TaskManager(
                # Chassis, configure for robot dimensions
                chassis=get_regular_triangular_chassis(
                    wheel_distance=160,
                    wheel_radius=29.5,
                    max_rotations_per_second=500 / 60),
                # Joystick bound by resource context
                joystick=joystick,
                # I2CHelper instance
                i2c=i2c,
                # Motors instance used to control the motors and read wheel positions
                motors=motors,
                # Feather, used to control lights and kicker solenoid
                feather=Feather(i2c=i2c),
                # Display, used to print messages either to hardware or to stdout
                display=display
            )
            task_manager.run(initial_task=MenuTask())
    except IOError:
        display.show("Waiting for joystick")
        sleep(0.3)
