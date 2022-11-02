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

def get_interfaces(device_name, params, add_ip=False, add_inventory_items=False):
    """
    Function to retrieve device interfaces from Netbox using GraphQL.
    
    :param add_ip: if True, retrieves interface IPs
    :param add_inventory_items: if True, retrieves interface inventory items
    :param device_name: name of the device to retrieve interfaces for
    :param params: dictionary with salt_nornir_netbox parameters
    """
    filt = {"device": device_name}
    intf_fields = [
        "name",
        "enabled",
        "description",
        "mtu",
        "parent {name}",
        "mac_address",
        "mode",
        "untagged_vlan {vid name}",
        "vrf {name}",
        "tagged_vlans {vid name}",
        "tags {name}",
        "custom_fields",
        "last_updated",
        "bridge {name}",
        "child_interfaces {name}",
        "bridge_interfaces {name}",
        "member_interfaces {name}",
        "wwn",
        "id",
    ]
    # add IP addresses to interfaces
    if add_ip:
        intf_fields.append(
            "ip_addresses {address status role dns_name description custom_fields last_updated tenant {name} tags {name}}"
        )
        
    interfaces = nb_graphql("interface", filt, intf_fields, params)
    
    if add_inventory_items:
        # retrieve inventory items for all device interfaces
        inv_filt = {
            "device": device_name,
            "component_id": [i["id"] for i in interfaces],
        }
        inv_fields = [
            "name",
            "component_id",
            "role {name}",
            "manufacturer {name}",
            "custom_fields",
            "label",
            "description",
            "tags {name}",
            "asset_tag",
            "serial",
            "part_id",
        ]
        inventory_items_list = nb_graphql("inventory_item", inv_filt, inv_fields, params)
        # transform inventory items list to a dictionary keyed by component_id
        inventory_items_dict = {}
        while inventory_items_list:
            inv_item = inventory_items_list.pop()
            component_id = str(inv_item.pop("component_id"))
            inventory_items_dict.setdefault(component_id, [])
            inventory_items_dict[component_id].append(inv_item)

        # iterate over interfaces and add inventory items
        for intf in interfaces:
            intf["inventory_items"] = inventory_items_dict.pop(
                intf["id"], []
            )
        
    # transform interfaces list to dictionary keyed by interfaces names
    intf_dict = {}
    while interfaces:
        intf = interfaces.pop()
        _ = intf.pop("id")
        intf_dict[intf.pop("name")] = intf
        
    return intf_dict
    
def get_connections(device_name, params):
    """
    Function to retrieve connections details from Netbox
    
    :param device_name: name of the device to retrieve interfaces for
    :param params: dictionary with salt_nornir_netbox parameters
    """
    # retrieve full list of device cables
    filt = {"device": device_name}
    cable_fields = [
        "type",
        "status",
        "tenant {name}",
        "label",
        "tags {name}",
        "length",
        "length_unit",
        "last_updated",
        "custom_fields",
        "terminations {termination_id termination_type {model} _device {name}}",
    ]
    cables = nb_graphql("cable", filt, cable_fields, params)

    # iterate over cables to form a list of termination interfaces to retrieve
    interface_ids = []
    console_port_ids = []
    console_server_port_ids = []
    device_names = set()
    for cable in cables:
        for i in cable["terminations"]:
            device_names.add(i["_device"]["name"])
            if i["termination_type"]["model"] == "interface":
                interface_ids.append(i["termination_id"])
            elif i["termination_type"]["model"] == "consoleport":
                console_port_ids.append(i["termination_id"])
            elif i["termination_type"]["model"] == "consoleserverport":
                console_server_port_ids.append(i["termination_id"])

    # retrieve interfaces and ports from Netbox
    interfaces = (
        nb_graphql(
            subject="interface",
            filt={"device": device_names, "id": interface_ids},
            fields=["name", "id", "device {name}"],
            params=params,
        )
        if interface_ids
        else []
    )
    console_ports = (
        nb_graphql(
            subject="console_port",
            filt={"device": device_names, "id": console_port_ids},
            fields=["name", "id", "device {name}"],
            params=params,
        )
        if console_port_ids
        else []
    )
    console_server_ports = (
        nb_graphql(
            subject="console_server_port",
            filt={"device": device_names, "id": console_server_port_ids},
            fields=["name", "id", "device {name}"],
            params=params,
        )
        if console_server_port_ids
        else []
    )

    # transform termination points data into dictionaries keyed by IDs
    interfaces = {str(i.pop("id")): i for i in interfaces}
    console_ports = {str(i.pop("id")): i for i in console_ports}
    console_server_ports = {str(i.pop("id")): i for i in console_server_ports}

    # process cables list to make cables ditionary keyed
    # by local interface name with connection details
    cables_dict = {}
    while cables:
        cable = cables.pop()
        # extract CableTerminationType items
        terminations = cable.pop("terminations")
        local_interface_index = None
        # map interface ID to interface data
        for index, i in enumerate(terminations):
            termination_type = i["termination_type"]["model"]
            termination_id = str(i["termination_id"])
            # record local interface index
            if i["_device"]["name"] == device_name:
                local_interface_index = index
            # retieve interfaces details
            if termination_type == "interface":
                i["interface"] = interfaces[termination_id]
            elif termination_type == "consoleport":
                i["interface"] = console_ports[termination_id]
            elif termination_type == "consoleserverport":
                i["interface"] = console_server_ports[termination_id]
        if local_interface_index is None:
            raise KeyError(
                f"salt_nornir_netbox '{device_name}' device, failed to find local "
                f"interface for connection '{cable}', terminations '{terminations}'"
            )
        # extract interface termiantion
        local_interface = terminations.pop(local_interface_index)
        remote_interface = terminations.pop()

        cables_dict[local_interface["interface"]["name"]] = {
            **cable,
            "remote_device": remote_interface["_device"]["name"],
            "remote_interface": remote_interface["interface"]["name"],
            "termination_type": local_interface["termination_type"]["model"],
            "remote_termination_type": remote_interface["termination_type"]["model"],
        }

    return cables_dict

        
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
    "get_interfaces": {"fun": get_interfaces},
    "get_connections": {"fun": get_connections},
}
