"""
Netbox Utils
============

Collection of functions for Salt-Nornir to interact with Netbox
using Execution module ``nr.netbox`` function.

Reference
+++++++++

.. autofunction:: salt_nornir.netbox_utils.nb_graphql
.. autofunction:: salt_nornir.netbox_utils.get_interfaces
.. autofunction:: salt_nornir.netbox_utils.get_connections
.. autofunction:: salt_nornir.netbox_utils.parse_config
.. autofunction:: salt_nornir.netbox_utils.update_config_context
.. autofunction:: salt_nornir.netbox_utils.update_vrf
"""
import logging
import json

log = logging.getLogger(__name__)

try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
except ImportError:
    log.warning("Failed importing requests module")

try:
    import pynetbox
except ImportError:
    log.warning("Failed importing pynetbox module")

manufacturers_platforms = {
    "Cisco": ["cisco", "iosxr", "ios", "nxos"],
    "Juniper": ["juniper", "junos"],
    "Arista": ["arista", "eos"],
}


def extract_salt_nornir_netbox_params(salt_jobs_results):
    """
    Function to retreive Netbox Params from salt_jobs_results.

    :param salt_jobs_results: list with config.get jobs results
    """
    # extract salt_nornir_netbox pillar configuration
    for i in salt_jobs_results[0]:
        if "salt_nornir_netbox" in i:
            master_params = i["salt_nornir_netbox"]
            if master_params.get("use_pillar") is True:
                pillar_params = salt_jobs_results[1]
                params = {**master_params, **pillar_params}
            else:
                params = master_params
            break
    else:
        raise KeyError("Failed to find salt_nornir_netbox pillar configuration")

    return params


def get_pynetbox(params):
    """Helper function to instantiate pynetbox api object"""
    if params.get("ssl_verify") == False:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        nb = pynetbox.api(url=params["url"], token=params["token"])
        nb.http_session.verify = False
    else:
        nb = pynetbox.api(url=params["url"], token=params["token"])

    return nb


def nb_graphql(subject, filt, fields, params=None, salt_jobs_results=None):
    """
    Helper function to send query to Netbox GraphQL API and
    return results

    :param subject: string, subject to return data for e.g. device, interface, ip_address
    :param filt: dictionary of key-value pairs to filter by
    :param fields: list of data fields to return
    :param params: dictionary with salt_nornir_netbox parameters
    """
    # if salt_jobs_results provided, extract Netbox params from it
    params = params or extract_salt_nornir_netbox_params(salt_jobs_results)
    # disable SSL warnings if requested so
    if params.get("ssl_verify") == False:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
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
        verify=params.get("ssl_verify", True),
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


def get_interfaces(
    device_name,
    salt_jobs_results=None,
    params=None,
    add_ip=False,
    add_inventory_items=False,
):
    """
    Function to retrieve device interfaces from Netbox using GraphQL.

    :param add_ip: if True, retrieves interface IPs
    :param add_inventory_items: if True, retrieves interface inventory items
    :param device_name: name of the device to retrieve interfaces for
    :param salt_jobs_results: list with config.get job results
    """
    # if salt_jobs_results provided, extract Netbox params from it
    params = params or extract_salt_nornir_netbox_params(salt_jobs_results)
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
        "duplex",
        "speed",
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
        inventory_items_list = nb_graphql(
            "inventory_item", inv_filt, inv_fields, params
        )
        # transform inventory items list to a dictionary keyed by component_id
        inventory_items_dict = {}
        while inventory_items_list:
            inv_item = inventory_items_list.pop()
            component_id = str(inv_item.pop("component_id"))
            inventory_items_dict.setdefault(component_id, [])
            inventory_items_dict[component_id].append(inv_item)

        # iterate over interfaces and add inventory items
        for intf in interfaces:
            intf["inventory_items"] = inventory_items_dict.pop(intf["id"], [])

    # transform interfaces list to dictionary keyed by interfaces names
    intf_dict = {}
    while interfaces:
        intf = interfaces.pop()
        _ = intf.pop("id")
        intf_dict[intf.pop("name")] = intf

    return intf_dict


def get_connections(device_name, salt_jobs_results=None, params=None):
    """
    Function to retrieve connections details from Netbox

    :param device_name: name of the device to retrieve interfaces for
    :param params: dictionary with salt_nornir_netbox parameters
    :param salt_jobs_results: list with config.get job results
    """
    # if salt_jobs_results provided, extract Netbox params from it
    params = params or extract_salt_nornir_netbox_params(salt_jobs_results)
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
        # cables can be added without remote terminations
        if terminations:
            remote_interface = terminations.pop()
        else:
            remote_interface = {}

        cables_dict[local_interface["interface"]["name"]] = {
            **cable,
            "remote_device": remote_interface.get("_device", {}).get("name"),
            "remote_interface": remote_interface.get("interface", {}).get("name"),
            "termination_type": local_interface["termination_type"]["model"],
            "remote_termination_type": remote_interface.get("termination_type", {}).get(
                "model"
            ),
        }

    return cables_dict


def get_netbox_params_salt_jobs(hosts: dict):
    """
    Function to return a list of __salt__ execution functions to run
    to retrieve Netbox configuration parameters.
    """
    return [
        {
            "salt_exec_fun_name": "config.get",
            "kwargs": {
                "key": "ext_pillar",
                "omit_pillar": True,
                "omit_opts": True,
                "omit_grains": True,
                "omit_master": False,
                "default": [],
            },
        },
        {
            "salt_exec_fun_name": "config.get",
            "kwargs": {
                "key": "salt_nornir_netbox_pillar",
                "omit_pillar": False,
                "omit_opts": True,
                "omit_master": True,
                "omit_grains": True,
                "default": {},
            },
        },
    ]


def get_parse_config_salt_jobs(hosts: dict):
    """
    Function to produce a list of tasks to collect output from devices
    for parse_config function.

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
                f"netbox_utils:get_parse_config_tasks unsupported "
                f"platform '{platform}', host name '{host_name}'"
            )
            continue
        ret.append(
            {
                "salt_exec_fun_name": "nr.cli",
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


def parse_config(salt_jobs_results: dict, **kwargs):
    """
    Function to return results of devices confgiuration parsing
    produced by TTP Templates for Netbox.

    :param salt_jobs_results: dictionary keyed by hosts with run_ttp results
    """
    return salt_jobs_results[0]


def get_create_devices_salt_jobs(hosts: dict):
    """
    To create devices need to retrieve their inventory data.

    Hosts to platform mapping retrieved separately in case platform
    for host defined using groups.
    """
    ret = [
        {
            "salt_exec_fun_name": "nr.nornir",
            "args": ["inventory", "list_hosts_platforms"],
            "kwargs": {"FL": list(hosts.keys())},
        },
        {
            "salt_exec_fun_name": "nr.nornir",
            "args": ["inventory"],
            "kwargs": {"FL": list(hosts.keys())},
        },
    ]
    ret.extend(get_netbox_params_salt_jobs(hosts))
    return ret


def create_devices(salt_jobs_results: list, **kwargs):
    """
    Function to interate over hosts inventory data and create
    or update devices in Netbox.
    """
    return "Not Implemented"

    hosts_platforms = salt_jobs_results[0]
    inventory = salt_jobs_results[1]
    netbox_params = extract_salt_nornir_netbox_params(salt_jobs_results[2:])

    new_manufacturers = []
    new_device_types = []
    new_platforms = []
    new_devices = []

    # instantiate pynetbox object
    nb = get_pynetbox(netbox_params)

    # get a list of all existing manufacturers from Netbox
    existing_manufacturers = nb_graphql(
        subject="manufacturer", filt={"name": ""}, fields=["name"], params=netbox_params
    )
    existing_manufacturers = [i["name"] for i in existing_manufacturers]

    # get a list of all existing platforms from Netbox
    existing_platforms = nb_graphql(
        subject="platform", filt={"name": ""}, fields=["name"], params=netbox_params
    )
    existing_platforms = [i["name"] for i in existing_platforms]

    # get a list of existing devices from Netbox
    existing_devices = nb_graphql(
        subject="device",
        filt={"name": list(hosts_platforms.keys())},
        fields=["name"],
        params=netbox_params,
    )
    existing_devices = [i["name"] for i in existing_devices]

    # iterate over hosts and create them in Netbox
    for host_name, platform in hosts_platforms.items():
        host_inventory = inventory[host_name]

        # skip already existing devices
        if host_name in existing_devices:
            continue

        # determine device manufacturer
        for manufacturer, platforms in manufacturers_platforms.items():
            for m_platform in platforms:
                if platform in m_platform:
                    if manufacturer not in existing_manufacturers:
                        new_manufacturers.append({"name": manufacturer})
                        # add generic device type
                        new_device_types.append(
                            {
                                "manufacturer": manufacturer,
                                "model": f"{manufacturer} Network Device",
                            }
                        )
                    break
        else:
            log.info(
                f"netbox_utils: failed determine manufacturer for "
                f"'{host_name}' platform '{platform}', skipping host"
            )
            continue

        # decide if need to create device platform
        if platform not in existing_platforms:
            new_platforms.append({"name": platform})

        new_devices.append(
            {
                "name": host_name,
            }
        )

        # create host vendor

    # Decided to skip this for know, as need to create manufacturer, platform and
    # device type, device hardware type is the most dificult one as have to define
    # based on output from device, not sure yet on the most reliable way to do that,
    # especially for multichassis devices, it seems support for device types need to
    # be added on a case by case basis mapping information obtained from device to
    # device-type in https://github.com/netbox-community/devicetype-library, which lead
    # ro neccesaty to create device type templates and modules templates, which in turn
    # coud rely on code here - https://github.com/minitriga/Netbox-Device-Type-Library-Import
    # Because of above, decided for now to skip adding devcies from Nornir Inventory
    #
    # To create device need to provide device_type, site, device_role attributes,
    # site and device role are usually not derivable from Nornir inventory, possible workaround
    # is to use data.netbox... path data and instruct user to populate that section with
    # device details required to create it in netbox, but IMHO simple csv import into netbox
    # is a better alternative


def get_params_parse_config_salt_jobs(hosts):
    """
    Function to produce a list of jobs to run to parse devices configs
    and to retrieve Netbox connection details.
    """
    # get a list of jobs to retrieve Netbox params
    jobs = get_netbox_params_salt_jobs(hosts)
    # add jobs to parse devices configs
    jobs.extend(get_parse_config_salt_jobs(hosts))
    return jobs


def update_config_context(salt_jobs_results: list, **kwargs):
    """
    Function to populate device configuration context with parsed results.

    :param salt_jobs_results: list with Netbox Params and config parsing job results
    """
    ret = {}
    netbox_params = extract_salt_nornir_netbox_params(salt_jobs_results[:2])
    parsing_job_results = salt_jobs_results[2:]

    # instantiate pynetbox object
    nb = get_pynetbox(netbox_params)

    # update devices context
    for hosts_results in parsing_job_results:
        for host_name, host_data in hosts_results.items():
            nb_device = nb.dcim.devices.get(name=host_name)
            if not nb_device:
                ret[host_name] = f"ERROR: '{host_name}' device not found in Netbox;"
            elif not host_data.get("run_ttp", {}).get("netbox_data", {}):
                ret[
                    host_name
                ] = f"ERROR: '{host_name}' device has bad parsing results: '{host_data.get('run_ttp')}';"
            else:
                context_data = nb_device.local_context_data or {}
                context_data.update(host_data["run_ttp"]["netbox_data"])
                nb_device.update(data={"local_context_data": context_data})
                nb_device.save()
                ret[host_name] = "Configuration Context data updated;"

    return ret


def update_vrf(salt_jobs_results: list, **kwargs):
    """
    Function to create or update VRFs and Route-Targets in Netbox.

    This function creates or updates:

    * VRFs with their names and description (if present in confiugration)
    * Route-Targets values
    * Reference to import and export RT for VRFs

    :param salt_jobs_results: list with Netbox Params and config parsing job results
    """
    all_rt, all_vrf = set(), {}  # variables to hold all parsed RT and VRFs names
    rt_create, rt_update, vrf_create, vrf_update = {}, {}, {}, {}
    netbox_params = extract_salt_nornir_netbox_params(salt_jobs_results[:2])
    parsing_job_results = salt_jobs_results[2:]

    # instantiate pynetbox object
    nb = get_pynetbox(netbox_params)

    # iterate over VRF parsing results
    hosts_done = []
    for hosts_results in parsing_job_results:
        for host_name, host_data in hosts_results.items():
            hosts_done.append(host_name)
            # check if parsing results are good
            if not host_data.get("run_ttp", {}).get("netbox_data", {}):
                log.error(
                    f"ERROR: '{host_name}' device has bad parsing results: '{host_data.get('run_ttp')}'"
                )
                continue
            # process parsing results
            for vrf in host_data["run_ttp"]["netbox_data"]["vrf"]:
                vrf_import_rt, vrf_export_rt = [], []
                # update IPv4 import route-targets
                for rt in (
                    vrf.get("afi", {})
                    .get("ipv4_unicast", {})
                    .get("route_target", {})
                    .get("import", [])
                ):
                    vrf_import_rt.append(rt)
                # update IPv4 export route-targets
                for rt in (
                    vrf.get("afi", {})
                    .get("ipv4_unicast", {})
                    .get("route_target", {})
                    .get("export", [])
                ):
                    vrf_export_rt.append(rt)
                # update IPv6 import route-targets
                for rt in (
                    vrf.get("afi", {})
                    .get("ipv6_unicast", {})
                    .get("route_target", {})
                    .get("import", [])
                ):
                    vrf_import_rt.append(rt)
                # update IPv6 export route-targets
                for rt in (
                    vrf.get("afi", {})
                    .get("ipv6_unicast", {})
                    .get("route_target", {})
                    .get("export", [])
                ):
                    vrf_export_rt.append(rt)

                # form RT data
                for i in vrf_import_rt:
                    all_rt.add(i)
                for i in vrf_export_rt:
                    all_rt.add(i)

                # form VRF data dictionary
                all_vrf[vrf["name"]] = {
                    "name": vrf["name"],
                    "description": vrf.get("description", ""),
                    "import_targets": vrf_import_rt,
                    "export_targets": vrf_export_rt,
                }

    # retrieve a list of existing route-targets
    existing_rt = nb_graphql(
        subject="route_target",
        filt={"name": all_rt},
        fields=["name", "id"],
        params=netbox_params,
    )
    existing_rt = {i["name"]: int(i["id"]) for i in existing_rt}
    # form RT data to update/create
    for rt in all_rt:
        rt_data = {"name": rt}
        if rt in existing_rt:
            rt_data["id"] = existing_rt[rt]
            rt_update.setdefault(rt, rt_data)
        else:
            rt_create.setdefault(rt, rt_data)
    # create and update RT
    log.debug(
        f"netbox_utils: creating rt '{list(rt_create)}'; updating rt '{list(rt_update)}'"
    )
    nb.ipam.route_targets.create(list(rt_create.values()))
    nb.ipam.route_targets.update(list(rt_update.values()))

    # retrieve a list of existing route-targets IDs to add VRF references
    existing_rt = nb_graphql(
        subject="route_target",
        filt={"name": all_rt},
        fields=["name", "id"],
        params=netbox_params,
    )
    existing_rt = {i["name"]: int(i["id"]) for i in existing_rt}
    # retrieve a list of existing VRFs
    existing_vrf = nb_graphql(
        subject="vrf",
        filt={"name": list(all_vrf)},
        fields=["name", "id"],
        params=netbox_params,
    )
    existing_vrf = {i["name"]: int(i["id"]) for i in existing_vrf}
    # form VRF data to update/create
    for vrf in all_vrf.values():
        vrf["import_targets"] = [existing_rt[rt] for rt in vrf["import_targets"]]
        vrf["export_targets"] = [existing_rt[rt] for rt in vrf["export_targets"]]
        if vrf["name"] in existing_vrf:
            vrf["id"] = existing_vrf[vrf["name"]]
            vrf_update.setdefault(vrf["name"], vrf)
        else:
            vrf_create.setdefault(vrf["name"], vrf)
    # create and update VRF
    log.debug(
        f"netbox_utils: creating vrf '{list(vrf_create)}'; updating vrf '{list(vrf_update)}'"
    )
    nb.ipam.vrfs.create(list(vrf_create.values()))
    nb.ipam.vrfs.update(list(vrf_update.values()))

    return (
        f"Hosts processed: '{(', ').join(hosts_done)}'\n"
        f"Created RT: '{(', ').join(rt_create)}'\n"
        f"Updated RT: '{(', ').join(rt_update)}'\n"
        f"Created VRF: '{(', ').join(vrf_create)}'\n"
        f"Updated VRF: '{(', ').join(vrf_update)}'"
    )


def no_jobs(hosts):
    return []


def run_dir(salt_jobs_results: list, **kwargs):
    """
    Function to return a list of supported Netbox Utils tasks
    """
    return list(netbox_tasks.keys())


# dispatch dictionary of Netbox tasks exposed for calling
# salt_jobs - returns a list of salt jobs to run to retrieve data for task function
# task_function - callable function to run on data from salt jobs
netbox_tasks = {
    "parse_config": {
        "salt_jobs": get_parse_config_salt_jobs,
        "task_function": parse_config,
    },
    "update_config_context": {
        "salt_jobs": get_params_parse_config_salt_jobs,
        "task_function": update_config_context,
    },
    "update_vrf": {
        "salt_jobs": get_params_parse_config_salt_jobs,
        "task_function": update_vrf,
    },
    # "create_devices": {"salt_jobs": get_create_devices_salt_jobs, "task_function": create_devices},
    "query": {"salt_jobs": get_netbox_params_salt_jobs, "task_function": nb_graphql},
    "get_interfaces": {
        "salt_jobs": get_netbox_params_salt_jobs,
        "task_function": get_interfaces,
    },
    "get_connections": {
        "salt_jobs": get_netbox_params_salt_jobs,
        "task_function": get_connections,
    },
    "dir": {"salt_jobs": no_jobs, "task_function": run_dir},
}
