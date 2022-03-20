import time
from nornir.core.task import Result, Task
from nornir_netmiko.tasks import netmiko_send_command
from nornir_scrapli.tasks import send_command as scrapli_send_command

CONNECTION_NAME="netmiko, scrapli"

def task(task):
    task.run(
        task=scrapli_send_command,
        command="show clock",
        name="scrapli_send_command",
    )
    task.run(
        task=netmiko_send_command,
        command_string="show clock",
        name="netmiko_send_command",
    )
    return Result(host=task.host, skip_results=True)