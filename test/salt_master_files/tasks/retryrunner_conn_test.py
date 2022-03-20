import logging

from nornir.core.task import Result, Task
from nornir_scrapli.tasks import netconf_get_config
from nornir_scrapli.tasks import send_command as scrapli_send_command
from nornir_netmiko.tasks import netmiko_send_command

log = logging.getLogger(__name__)


CONNECTION_NAME = "scrapli_netconf, netmiko, scrapli"


def task(task: Task) -> Result:

    task.run(
        name="Pull Configuration Using Scrapli Netconf",
        task=netconf_get_config,
        source="running"
    )
    
    task.run(
        name="Pull Configuration using Netmiko",
        task=netmiko_send_command,
        command_string="show run",
        enable=True
    )

    task.run(
        name="Pull Configuration using Scrapli",
        task=scrapli_send_command,
        command="show run"
    )
        
    return Result(host=task.host)
