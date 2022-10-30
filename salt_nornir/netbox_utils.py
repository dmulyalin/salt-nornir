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


def nb_graphql(subject, filt, fields, params):
    """
    Helper function to send query to Netbox GraphQL API and
    return results

    :param subject: string, subject to return data for e.g. device, interface, ip_address
    :param filt: dictionary of key-value pairs to filter by
    :param fields: list of data fields to return
    :param params: dictionary with salt_nornir_netbox parameters
    """
    # form GraphQL query string
    filters = []
    for k, v in filt.items():
        if isinstance(v, (list, set, tuple)):
            items = ", ".join(f'"{i}"' for i in v)
            filters.append(f"{k}: [{items}]")
        else:
            filters.append(f'{k}: "{v}"')
    filters = ", ".join(filters)
    fields = " ".join(fields)
    query = f"query {{{subject}_list({filters}) {{ {fields} }}}}"
    log.debug(f"salt_nornir_netbox sending GraphQL query '{query}'")
    # send request to Netbox GraphQL API
    req = requests.get(
        url=f"{params['url']}/graphql",
        headers={
            "content-cype": "application/json",
            "accept": "application/json",
            "authorization": f"Token {params['token']}",
        },
        params={"query": query},
    )
    if req.status_code == 200:
        return req.json()["data"][f"{subject}_list"]
    else:
        log.error(
            f"netbox_utils Netbox GraphQL query failed, query '{query}', "
            f"URL '{req.url}', status-code '{req.status_code}', reason '{req.reason}', "
            f"response content '{req.text}'"
        )
        return None

    
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
netbox_tasks = {
    "load_config": {"fun": load_config, "tasks": get_load_config_tasks},
    "query": {"fun": nb_graphql},
}
