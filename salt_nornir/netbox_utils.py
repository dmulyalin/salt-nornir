"""
Netbox Utils
============

Collection of functions for Salt-Nornir to interact with Netbox.


"""
import logging
import json
import requests

log = logging.getLogger(__name__)

try:
    import pynetbox

    HAS_PYNETBOX = True
except ImportError:
    HAS_PYNETBOX = False


def get_load_config_tasks(hosts: dict):
    """
    Function to produce a list of tasks to collect output from devices
    for load_config function.

    :param data: dictionary with Nornir Inventory data of hosts to produce tasks for
    """
    ret = []
    platforms_added = set()
    for host_name, platform in hosts.items():
        task_kwargs = {}
        if platform in platforms_added:
            continue
        elif platform in ["cisco_xr", "iosxr"]:
            template = "ttp://misc/Netbox/parse_cisco_xr_config.txt"
        elif platform in ["juniper_junos", "junos", "juniper"]:
            template = "ttp://misc/Netbox/parse_juniper_junos_config.txt"
        elif platform in ["arista_eos", "eos"]:
            template = "ttp://misc/Netbox/parse_arista_eos_config.txt"
            task_kwargs["enable"] = True
        else:
            log.info(
                f"netbox_utils:get_load_config_tasks unsupported "
                f"platform '{platform}', host name '{host_name}'"
            )
            continue
        ret.append(
            {
                "fun": "cli",
                "kwargs": {
                    **task_kwargs,
                    "FL": [h for h, p in hosts.items() if p == platform],
                    "run_ttp": template,
                    "ttp_structure": "dictionary",
                },
            }
        )
        platforms_added.add(platform)

    return ret


def load_config(data: dict):
    """
    Function to parse devices confgiuration and load it into Netbox device
    confguration context.
    """
    pass


# dispatch dictionary of Netbox tasks exposed for calling
netbox_tasks = {"load_config": {"fun": load_config, "tasks": get_load_config_tasks}}
