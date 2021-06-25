import time
from nornir.core.task import Result, Task
from nornir_netmiko.tasks import netmiko_send_command
import logging

log = logging.getLogger(__name__)

# define connection name for RetryRunner to properly detect it using:
# connection_name = task.task.__globals__.get("CONNECTION_NAME", None)
CONNECTION_NAME = "netmiko"


def task(task, commands, interval=0.01, **kwargs):
    """
    Nornir Task function to send show commands to devices using
    ``nornir_netmiko.tasks.netmiko_send_command`` plugin

    :param kwargs: might contain ``netmiko_kwargs`` argument dictionary
        with parameters for ``nornir_netmiko.tasks.netmiko_send_command``
        method
    :param commands: (list) commands to send to device
    :param interval: (int) interval between sending commands, default 0.01s
    :return result: Nornir result object with task execution results named
        after commands
    """
    # run interval sanity check
    interval = interval if isinstance(interval, (int, float)) else 0.01

    # run commands
    for command in commands:
        task.run(
            task=netmiko_send_command,
            command_string=command,
            name=command,
            **kwargs.get("netmiko_kwargs", {})
        )
        time.sleep(interval)

    return Result(host=task.host, skip_results=True)
