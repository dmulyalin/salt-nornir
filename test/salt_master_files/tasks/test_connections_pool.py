import time
from nornir.core.task import Result, Task
import logging

log = logging.getLogger(__name__)

# define connection name for RetryRunner to properly detect it using:
# connection_name = task.task.__globals__.get("CONNECTION_NAME", None)
CONNECTION_NAME = "netmiko"


def task(task, command, **kwargs):
    """
    Nornir Task function to send show commands to devices using
    ConnectionsPool plugin

    :param commands: (list) commands to send to device
    :return result: Nornir result object with task execution results named
        after commands
    """
    conn_pool = task.host.get_connection("ConnectionsPool", task.nornir.config)
    
    log.debug("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    log.debug(conn_pool.parameters)
    log.debug(conn_pool.connections)
    
    with conn_pool.get_connection("netmiko", task.host) as nc:
        result = nc.send_command(command)
        
    return Result(host=task.host, result=result, skip_results=False)
