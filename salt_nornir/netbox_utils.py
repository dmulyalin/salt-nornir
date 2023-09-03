"""
Netbox Utils
============

Collection of functions for Salt-Nornir to interact with Netbox
using Execution module ``nr.netbox`` function.

To be able to retrieve data from netbox need to define Netbox URL 
and API token parameters either under proxy minion pillar 
``salt_nornir_netbox_pillar`` section or in salt-master' ext pillar 
configuration. To be able to retrieve URL and toekn parameters from 
master need to set ``pillar_opts`` parameter to True in salt-master's 
configuration.

Reference
+++++++++

.. autofunction:: salt_nornir.netbox_utils.nb_graphql
.. autofunction:: salt_nornir.netbox_utils.nb_rest
.. autofunction:: salt_nornir.netbox_utils.get_interfaces
.. autofunction:: salt_nornir.netbox_utils.get_connections
.. autofunction:: salt_nornir.netbox_utils.get_circuits
.. autofunction:: salt_nornir.netbox_utils.parse_config
.. autofunction:: salt_nornir.netbox_utils.update_config_context
.. autofunction:: salt_nornir.netbox_utils.update_vrf
"""
import logging
import json
import ipaddress
import traceback

log = logging.getLogger(__name__)

try:
    from nornir_salt.plugins.functions import FFun_functions
except ImportError:
    log.warning("Failed importing Nornir-Salt library")

try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
except ImportError:
    log.warning("Failed importing requests module")

try:
    import pynetbox
except ImportError:
    log.warning("Failed importing pynetbox module")

try:
    from salt.exceptions import CommandExecutionError
except:
    log.warning("Failed importing SALT libraries")

try:
    from diskcache import FanoutCache

    HAS_DISKCACHE = True
except ImportError:
    HAS_DISKCACHE = False
    log.warning("Failed importing pynetbox module")


def get_salt_nornir_netbox_params(__salt__) -> dict:
    """
    Function to retreive Netbox Params from minion pillar or salt-master
    configuration.

    :param __salt__: reference to ``__salt__`` execution modules dictionary
    """
    # get Netbox params from Pillar and Master config
    params = __salt__["config.get"](
        key="salt_nornir_netbox_pillar",
        omit_pillar=False,
        omit_opts=True,
        omit_master=True,
        omit_grains=True,
        default={},
    )
    ext_pillar_params = __salt__["config.get"](
        key="ext_pillar",
        omit_pillar=True,
        omit_opts=True,
        omit_master=False,
        omit_grains=True,
        default={},
    )
    # extraxt Netbox ext pillar config if any
    for i in ext_pillar_params:
        if "salt_nornir_netbox" in i:
            master_params = i["salt_nornir_netbox"]
            params = {**master_params, **params}
            break
    # sanity check sourced params
    if not all(k in params for k in ["url", "token"]):
        raise RuntimeError(
            "Failed to source Netbox configuration from minion pillar "
            f"or salt master configuration, 'url' and 'token' not defined"
        )
    # retrieve proxy parameters
    params["proxy"] = __salt__["config.get"](
        key="proxy",
        omit_pillar=False,
        omit_opts=True,
        omit_master=True,
        omit_grains=True,
        default={},
    )
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


def _form_query(field, filters, fields, alias=None):
    """
    Helper function to form graphql query

    :param field: string, field to return data for e.g. device, interface, ip_address
    :param filters: dictionary of key-value pairs to filter by
    :param fields: list of data fields to return
    :param alias: string, alias value for requested field
    """
    filters_list = []
    for k, v in filters.items():
        if isinstance(v, (list, set, tuple)):
            items = ", ".join(f'"{i}"' for i in v)
            filters_list.append(f"{k}: [{items}]")
        else:
            filters_list.append(f'{k}: "{v}"')
    filters_string = ", ".join(filters_list)
    fields = " ".join(fields)
    if alias:
        query = f"{alias}: {field}({filters_string}) {{{fields}}}"
    else:
        query = f"{field}({filters_string}) {{{fields}}}"

    return query


def nb_graphql(
    field: dict = None,
    filters: dict = None,
    fields: list = None,
    params: dict = None,
    queries: dict = None,
    query_string: str = None,
    raise_for_status: bool = False,
    __salt__=None,
    proxy_id=None,
):
    """
    Function to send query to Netbox GraphQL API and return results.

    :param field: dictionary of queies or string, field to return data for e.g. device, interface, ip_address
    :param filters: dictionary of key-value pairs to filter by
    :param fields: list of data fields to return
    :param params: dictionary with salt_nornir_netbox parameters
    :param queries: dictionary keyed by GraphQL aliases with query data
    :param query_string: string with GraphQL query
    :param raise_for_status: raise exception if requests response is not ok
    :param __salt__: reference to ``__salt__`` execution modules dictionary
    """
    # if no params provided, extract Netbox params from pillar or master config
    params = params or get_salt_nornir_netbox_params(__salt__)
    # disable SSL warnings if requested so
    if params.get("ssl_verify") == False:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    # form graphql query(ies) payload
    if queries:
        queries_list = []
        for alias, query_data in queries.items():
            query_data["alias"] = alias
            queries_list.append(_form_query(**query_data))
        queries_strings = "    ".join(queries_list)
        query = f"query {{{queries_strings}}}"
    elif field and filters and fields:
        query = _form_query(field, filters, fields)
        query = f"query {{{query}}}"
    elif query_string:
        query = query_string
    else:
        raise RuntimeError(
            f"nb_graphql expect quieries argument or field, filters, "
            f"fields arguments or query_string argument provided"
        )
    payload = json.dumps({"query": query})
    log.debug(
        f"salt_nornir_netbox sending GraphQL query '{payload}' to URL '{params['url']}/graphql/'"
    )
    # send request to Netbox GraphQL API
    req = requests.post(
        url=f"{params['url']}/graphql/",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {params['token']}",
        },
        data=payload,
        verify=params.get("ssl_verify", True),
    )
    # return results
    if req.status_code == 200:
        if queries or query_string:
            return req.json()["data"]
        else:
            return req.json()["data"][field]
    elif raise_for_status:
        req.raise_for_status()
    else:
        log.error(
            f"netbox_utils Netbox GraphQL query failed, query '{query}', "
            f"URL '{req.url}', status-code '{req.status_code}', reason '{req.reason}', "
            f"response content '{req.text}'"
        )
        return None


def nb_rest(
    method: str = "get", api: str = "", __salt__=None, proxy_id=None, **kwargs
) -> dict:
    """
    Function to query Netbox REST API.

    :param method: requests method name e.g. get, post, put etc.
    :param api: api url to query e.g. "extras" or "dcim/interfaces" etc.
    :param kwargs: any additional requests method's arguments
    :param __salt__: reference to ``__salt__`` execution modules dictionary
    """
    nb_params = get_salt_nornir_netbox_params(__salt__)

    # disable SSL warnings if requested so
    if nb_params.get("ssl_verify") == False:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # send request to Netbox REST API
    response = getattr(requests, method)(
        url=f"{nb_params['url']}/api/{api}/",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {nb_params['token']}",
        },
        verify=nb_params.get("ssl_verify", True),
        **kwargs,
    )

    response.raise_for_status()

    return response.json()


def get_interfaces(
    add_ip=False,
    add_inventory_items=False,
    sync=False,
    params=None,
    __salt__=None,
    proxy_id=None,
    hosts=None,
    cache=True,
    cache_ttl=3600,
    **kwargs,
):
    """
    Function to retrieve device interfaces from Netbox using GraphQL API.

    :param add_ip: if True, retrieves interface IPs
    :param add_inventory_items: if True, retrieves interface inventory items
    :param sync: if True, saves get interfaces results to host's in-memory
        inventory data under ``interfaces`` key, if sync is a string, provided
        value used as a key.
    :param __salt__: reference to ``__salt__`` execution modules dictionary
    :param kwargs: Fx filters to filter hosts to retrieve interfaces for
    :param hosts: list of hosts to retrieve interface for
    :param cache: boolean indicating whether to cache Netbox response or string
        ``refresh`` to delete cached data, if set to False cached data ignored
        but not refreshed
    :param cache_ttl: integer indicating cache time to live
    :return: dictionary keyed by device name with interface details

    .. note:: ``add_inventory_items`` only supported with Netbox 3.4 and above.

    .. note:: Either ``hosts`` or ``__salt__`` with ``Fx`` filters should be provided,
      otherwise ``CommandExecutionError`` raised.

    Starting with version ``0.20.0`` support added to cache data retrieved from
    Netbox on a per-device basis. For this functionality to work need to have
    `diskcache <https://github.com/grantjenks/python-diskcache>`_ library installed
    on salt-nornir proxy minion. Cache is persistent and stored on the minion's
    local file system.

    Sample data returned for interfaces when ``add_ip`` and ``add_inventory_items``
    set to True::

        {'fceos4': {'Port-Channel1': {'bridge': None,
                                      'bridge_interfaces': [],
                                      'child_interfaces': [],
                                      'custom_fields': {},
                                      'description': 'Main uplink interface',
                                      'duplex': None,
                                      'enabled': True,
                                      'inventory_items': [],
                                      'ip_addresses': [],
                                      'last_updated': '2023-08-22T09:47:57.256446+00:00',
                                      'mac_address': None,
                                      'member_interfaces': [{'name': 'eth101'},
                                                            {'name': 'eth102'}],
                                      'mode': None,
                                      'mtu': None,
                                      'parent': None,
                                      'speed': None,
                                      'tagged_vlans': [],
                                      'tags': [],
                                      'untagged_vlan': None,
                                      'vrf': None,
                                      'wwn': None},
                             'eth1': {'bridge': None,
                                      'bridge_interfaces': [],
                                      'child_interfaces': [{'name': 'eth1.11'}],
                                      'custom_fields': {},
                                      'description': 'Interface 1 description',
                                      'duplex': None,
                                      'enabled': True,
                                      'ip_addresses': [{'address': '1.0.10.1/32',
                                                        'custom_fields': {},
                                                        'description': '',
                                                        'dns_name': '',
                                                        'last_updated': '2023-08-22T09:48:03.287649+00:00',
                                                        'role': None,
                                                        'status': 'ACTIVE',
                                                        'tags': [],
                                                        'tenant': None},
                                                       {'address': '1.0.100.1/32',
                                                        'custom_fields': {},
                                                        'description': '',
                                                        'dns_name': '',
                                                        'last_updated': '2023-08-22T09:48:01.692965+00:00',
                                                        'role': None,
                                                        'status': 'ACTIVE',
                                                        'tags': [],
                                                        'tenant': None}],
                                      'inventory_items': [{'asset_tag': None,
                                                           'custom_fields': {},
                                                           'description': '',
                                                           'label': '',
                                                           'manufacturer': None,
                                                           'name': 'SFP-1G-T',
                                                           'part_id': '',
                                                           'role': {'name': 'Transceiver'},
                                                           'serial': '',
                                                           'tags': []}],
                                      'ip_addresses': [],
                                      'last_updated': '2023-08-22T09:47:57.809307+00:00',
                                      'mac_address': None,
                                      'member_interfaces': [],
                                      'mode': 'TAGGED',
                                      'mtu': 1500,
                                      'parent': None,
                                      'speed': None,
                                      'tagged_vlans': [],
                                      'tags': [],
                                      'untagged_vlan': None,
                                      'vrf': None,
                                      'wwn': None},
                        'loopback0': {'bridge': None,
                                      'bridge_interfaces': [],
                                      'child_interfaces': [],
                                      'custom_fields': {},
                                      'description': '',
                                      'duplex': None,
                                      'enabled': True,
                                      'inventory_items': [],
                                      'ip_addresses': [{'address': '1.0.1.4/32',
                                                        'custom_fields': {},
                                                        'description': '',
                                                        'dns_name': '',
                                                        'last_updated': '2023-08-22T09:48:00.728097+00:00',
                                                        'role': None,
                                                        'status': 'ACTIVE',
                                                        'tags': [],
                                                        'tenant': None}],
                                      'last_updated': '2023-08-22T09:47:57.148611+00:00',
                                      'mac_address': None,
                                      'member_interfaces': [],
                                      'mode': None,
                                      'mtu': None,
                                      'parent': None,
                                      'speed': None,
                                      'tagged_vlans': [],
                                      'tags': [],
                                      'untagged_vlan': None,
                                      'vrf': None,
                                           'wwn': None}}}}
    """
    # retrieve a list of hosts to get interfaces for
    hosts = hosts or __salt__["nr.nornir"](
        "hosts",
        **{k: v for k, v in kwargs.items() if k in FFun_functions},
    )
    if not hosts:
        raise CommandExecutionError("No hosts matched")

    # form final result dictionary
    intf_dict = {h: {} for h in hosts}

    # if no params provided extract them from minion pillar or master config
    params = params or get_salt_nornir_netbox_params(__salt__)

    # check if need to use cache
    if HAS_DISKCACHE and cache:
        cache_directory = (
            params["proxy"]
            .get("cache_base_path", "/var/salt-nornir/{proxy_id}/cache/")
            .format(proxy_id=proxy_id)
        )
        cache_obj = FanoutCache(directory=cache_directory, shards=1)
        # remove expired items from cache
        _ = cache_obj.expire()
        # iterate over a copy of hosts list
        for host in list(hosts):
            key = f"nr.netbox:get_interfaces, {host}, add_ip {add_ip}, add_inventory_items {add_inventory_items}"
            if key in cache_obj and cache is True:
                intf_dict[host] = cache_obj[key]
                hosts.remove(host)
                log.debug(
                    f"netbox_utils:get_interfaces '{host}' retrieved get_interfaces from cache"
                )
            elif key in cache_obj and cache == "refresh":
                cache_obj.delete(key)
                log.debug(
                    f"netbox_utils:get_interfaces '{host}' deleted get_interfaces data from cache"
                )

        cache_obj.close()

    # check if still has hosts left to retrieve data for
    if hosts:
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
            "device {name}",
        ]
        # add IP addresses to interfaces fields
        if add_ip:
            intf_fields.append(
                "ip_addresses {address status role dns_name description custom_fields last_updated tenant {name} tags {name}}"
            )
        # form interfaces query dictioney
        queries = {
            "interfaces": {
                "field": "interface_list",
                "filters": {"device": hosts},
                "fields": intf_fields,
            }
        }

        # add query to retrieve inventory items
        if add_inventory_items:
            inv_filters = {"device": hosts, "component_type": "dcim.interface"}
            inv_fields = [
                "name",
                "component {... on InterfaceType {id}}",
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
            queries["inventor_items"] = {
                "field": "inventory_item_list",
                "filters": inv_filters,
                "fields": inv_fields,
            }

        interfaces_data = nb_graphql(queries=queries, params=params)

        interfaces = interfaces_data.pop("interfaces")

        # process inventory items
        if add_inventory_items:
            inventory_items_list = interfaces_data.pop("inventor_items")
            # transform inventory items list to a dictionary keyed by intf_id
            inventory_items_dict = {}
            while inventory_items_list:
                inv_item = inventory_items_list.pop()
                # skip inventory items that does not assigned to components
                if inv_item.get("component") is None:
                    continue
                intf_id = str(inv_item.pop("component").pop("id"))
                inventory_items_dict.setdefault(intf_id, [])
                inventory_items_dict[intf_id].append(inv_item)
            # iterate over interfaces and add inventory items
            for intf in interfaces:
                intf["inventory_items"] = inventory_items_dict.pop(intf["id"], [])

        # transform interfaces list to dictionary keyed by device and interfaces names
        while interfaces:
            intf = interfaces.pop()
            _ = intf.pop("id")
            device_name = intf.pop("device").pop("name")
            intf_name = intf.pop("name")
            intf_dict[device_name][intf_name] = intf

        # cache interfaces data for each host
        if HAS_DISKCACHE and cache:
            cache_obj = FanoutCache(directory=cache_directory, shards=1)
            for host in hosts:
                key = f"nr.netbox:get_interfaces, {host}, add_ip {add_ip}, add_inventory_items {add_inventory_items}"
                cache_obj.set(key, intf_dict[host], expire=cache_ttl)
                log.debug(
                    f"netbox_utils:get_interfaces '{host}' cached get_interfaces data"
                )
            cache_obj.close()

    # save results into hosts inventory if requested to do so
    if sync:
        key = sync if isinstance(sync, str) else "interfaces"
        return __salt__["nr.nornir"](
            fun="inventory",
            call="load",
            data=[
                {"call": "update_host", "name": host, "data": {key: intf_data}}
                for host, intf_data in intf_dict.items()
            ],
        )

    return intf_dict


def get_connections(
    params: dict = None,
    sync=False,
    __salt__=None,
    proxy_id=None,
    hosts=None,
    cache=True,
    cache_ttl=3600,
    **kwargs,
) -> dict:
    """
    Function to retrieve connections details from Netbox for interface and
    console ports.

    :param params: dictionary with salt_nornir_netbox parameters
    :param sync: if True, saves get connections results to host's in-memory
        inventory data under ``connections`` key, if sync is a string, provided
        value used as a key.
    :param __salt__: reference to ``__salt__`` execution modules dictionary
    :param hosts: list of hosts to get connections for
    :param cache: boolean indicating whether to cache Netbox response or string
        ``refresh`` to delete cached data, if set to False cached data ignored
        but not refreshed
    :param cache_ttl: integer indicating cache time to live
    :param kwargs: Fx filters to filter hosts to retrieve connections for
    :return: dictionary keyed by device name with connections details

    .. warning:: Get connections only supported for Netbox of 3.4 and above.

    .. note:: Either ``hosts`` or ``__salt__`` with ``Fx`` filters should be provided,
      otherwise ``CommandExecutionError`` raised.

    Get connections returns a dictionary keyed by device name with value being a
    dictionary keyed by device interface names.

    Sample return data::

        {'fceos4': {'ConsolePort1': {'breakout': False,
                                     'cable': {'custom_fields': {},
                                               'label': '',
                                               'length': None,
                                               'length_unit': None,
                                               'peer_device': 'fceos5',
                                               'peer_interface': 'ConsoleServerPort1',
                                               'peer_termination_type': 'consoleserverport',
                                               'status': 'CONNECTED',
                                               'tags': [],
                                               'tenant': {'name': 'SALTNORNIR'},
                                               'type': 'CAT6A'},
                                     'remote_device': 'fceos5',
                                     'remote_interface': 'ConsoleServerPort1',
                                     'remote_termination_type': 'consoleserverport',
                                     'termination_type': 'consoleport'},
                    'eth1': {'breakout': True,
                             'cable': {'custom_fields': {},
                                       'label': '',
                                       'length': None,
                                       'length_unit': None,
                                       'peer_device': 'fceos5',
                                       'peer_interface': ['eth1', 'eth10'],
                                       'peer_termination_type': 'interface',
                                       'status': 'CONNECTED',
                                       'tags': [],
                                       'tenant': {'name': 'SALTNORNIR'},
                                       'type': 'CAT6A'},
                             'remote_device': 'fceos5',
                             'remote_interface': ['eth1', 'eth10'],
                             'remote_termination_type': 'interface',
                             'termination_type': 'interface'},
                    'eth101': {'breakout': False,
                               'cable': {'custom_fields': {},
                                         'label': '',
                                         'length': None,
                                         'length_unit': None,
                                         'peer_termination_type': 'circuittermination',
                                         'status': 'CONNECTED',
                                         'tags': [],
                                         'tenant': None,
                                         'type': 'SMF'},
                               'circuit': {'cid': 'CID1',
                                           'commit_rate': None,
                                           'custom_fields': {},
                                           'description': '',
                                           'provider': {'name': 'Provider1'},
                                           'status': 'ACTIVE',
                                           'tags': []},
                               'remote_device': 'fceos5',
                               'remote_interface': 'eth8',
                               'remote_termination_type': 'interface',
                               'termination_type': 'interface'},
                    'eth3': {'breakout': False,
                             'cable': {'custom_fields': {},
                                       'label': '',
                                       'length': None,
                                       'length_unit': None,
                                       'peer_device': 'fceos5',
                                       'peer_interface': 'eth3',
                                       'peer_termination_type': 'interface',
                                       'status': 'CONNECTED',
                                       'tags': [],
                                       'tenant': {'name': 'SALTNORNIR'},
                                       'type': 'CAT6A'},
                             'remote_device': 'fceos5',
                             'remote_interface': 'eth3',
                             'remote_termination_type': 'interface',
                             'termination_type': 'interface'},
                    'eth7': {'breakout': False,
                             'cable': {'custom_fields': {},
                                       'label': '',
                                       'length': None,
                                       'length_unit': None,
                                       'peer_device': 'PatchPanel-1',
                                       'peer_interface': 'FrontPort1',
                                       'peer_termination_type': 'frontport',
                                       'status': 'CONNECTED',
                                       'tags': [],
                                       'tenant': {'name': 'SALTNORNIR'},
                                       'type': 'SMF'},
                             'remote_device': 'fceos5',
                             'remote_interface': 'eth7',
                             'remote_termination_type': 'interface',
                             'termination_type': 'interface'}}}}

    Where:

    * ``ConsolePort1`` is a direct cable between devices
    * ``eth101`` has circuit connected to it
    * ``eth1`` is a direct between devices breakout cable
    * ``eth3`` is a direct between devices normal (non-breakout) cable
    * ``eth7`` connected to another device through patch panels
    """
    # retrieve a list of hosts to get interfaces for
    hosts = hosts or __salt__["nr.nornir"](
        "hosts",
        **{k: v for k, v in kwargs.items() if k in FFun_functions},
    )
    if not hosts:
        raise CommandExecutionError("No hosts matched")

    # form final result dictionary
    connections_dict = {h: {} for h in hosts}

    # if no params provided, extract Netbox params from mater config or minion pillar
    params = params or get_salt_nornir_netbox_params(__salt__)

    # check if need to use cache
    if HAS_DISKCACHE and cache:
        cache_directory = (
            params["proxy"]
            .get("cache_base_path", "/var/salt-nornir/{proxy_id}/cache/")
            .format(proxy_id=proxy_id)
        )
        cache_obj = FanoutCache(directory=cache_directory, shards=1)
        # remove expired items from cache
        _ = cache_obj.expire()
        # iterate over a copy of hosts list
        for host in list(hosts):
            key = f"nr.netbox:get_connections, {host}"
            if key in cache_obj and cache is True:
                connections_dict[host] = cache_obj[key]
                hosts.remove(host)
                log.debug(
                    f"netbox_utils:get_connections '{host}' retrieved get_connections from cache"
                )
            elif key in cache_obj and cache == "refresh":
                cache_obj.delete(key)
                log.debug(
                    f"netbox_utils:get_connections '{host}' deleted get_connections data from cache"
                )
        cache_obj.close()

    # check if still has hosts left to retrieve data for
    if hosts:
        # forem lists of fields to request from netbox
        cable_fields = """
            cable {
                type
                status
                tenant {name}
                label
                tags {name}
                length
                length_unit
                custom_fields
            }
        """
        interfaces_fields = [
            "name",
            "device {name}",
            """connected_endpoints {
              __typename 
              ... on InterfaceType {name device {name}}
            }""",
            """link_peers {
              __typename
              ... on InterfaceType {name device {name}}
              ... on FrontPortType {name device {name}}
              ... on RearPortType {name device {name}}
              ... on CircuitTerminationType {
                circuit{
                  cid 
                  description 
                  tags{name} 
                  provider{name} 
                  status
                  custom_fields
                  commit_rate
                }
              }
            }""",
            str(cable_fields),
        ]
        console_ports_fields = [
            "name",
            "device {name}",
            """connected_endpoints {
              __typename 
              ... on ConsoleServerPortType {name device {name}}
            }""",
            """link_peers {
              __typename
              ... on ConsoleServerPortType {name device {name}}
              ... on FrontPortType {name device {name}}
              ... on RearPortType {name device {name}}
            }""",
            str(cable_fields),
        ]
        console_server_ports_fields = [
            "name",
            "device {name}",
            """connected_endpoints {
              __typename 
              ... on ConsolePortType {name device {name}}
            }""",
            """link_peers {
              __typename
              ... on ConsolePortType {name device {name}}
              ... on FrontPortType {name device {name}}
              ... on RearPortType {name device {name}}
            }""",
            str(cable_fields),
        ]
        # form query dictionary with aliases to get data from Netbox
        queries = {
            "interface": {
                "field": "interface_list",
                "filters": {"device": hosts, "type__n": ["lag", "virtual"]},
                "fields": interfaces_fields,
            },
            "consoleport": {
                "field": "console_port_list",
                "filters": {"device": hosts},
                "fields": console_ports_fields,
            },
            "consoleserverport": {
                "field": "console_server_port_list",
                "filters": {"device": hosts},
                "fields": console_server_ports_fields,
            },
        }
        # retrieve full list of devices interface with all cables
        all_ports = nb_graphql(queries=queries, params=params)

        # extract interfaces
        for port_type, ports in all_ports.items():
            for port in ports:
                endpoints = port["connected_endpoints"]
                cable = port["cable"]
                # skip ports that have no cable connected
                if not cable:
                    continue
                # skip ports that have no remote device connected
                # that will ignore cases when port connectes to
                # provider network via circuit as well
                if not endpoints or not all(i for i in endpoints):
                    continue
                # etract required parameters
                device_name = port["device"]["name"]
                port_name = port["name"]
                link_peers = port["link_peers"]
                # add interface and its connection to results
                connections_dict[device_name][port_name] = {
                    "breakout": len(endpoints) > 1,
                    "cable": cable,
                    "remote_device": endpoints[0]["device"]["name"],
                    "remote_interface": [i["name"] for i in endpoints]
                    if len(endpoints) > 1
                    else endpoints[0]["name"],
                    "remote_termination_type": endpoints[0]["__typename"]
                    .replace("Type", "")
                    .lower(),
                    "termination_type": port_type,
                }
                # if cable connected to circuit add circuit details
                if link_peers and "circuit" in link_peers[0]:
                    connections_dict[device_name][port_name]["circuit"] = link_peers[0][
                        "circuit"
                    ]
                    cable["peer_termination_type"] = "circuittermination"
                # add cable peers details
                else:
                    cable["peer_device"] = link_peers[0]["device"]["name"]
                    cable["peer_interface"] = (
                        [i["name"] for i in link_peers]
                        if len(link_peers) > 1
                        else link_peers[0]["name"]
                    )
                    cable["peer_termination_type"] = (
                        link_peers[0]["__typename"].replace("Type", "").lower()
                    )

        # cache connections data for each host
        if HAS_DISKCACHE and cache:
            cache_obj = FanoutCache(directory=cache_directory, shards=1)
            for host in hosts:
                key = f"nr.netbox:get_connections, {host}"
                cache_obj.set(key, connections_dict[host], expire=cache_ttl)
                log.debug(
                    f"netbox_utils:get_connections '{host}' cached get_connections data"
                )
            cache_obj.close()

    # save results to hosts inventory if requested to do so
    if sync:
        key = sync if isinstance(sync, str) else "connections"
        return __salt__["nr.nornir"](
            fun="inventory",
            call="load",
            data=[
                {"call": "update_host", "name": host, "data": {key: connections}}
                for host, connections in connections_dict.items()
            ],
        )

    return connections_dict


def parse_config(__salt__=None, proxy_id=None, **kwargs):
    """
    Function to return results of devices configuration parsing
    produced by TTP Templates for Netbox.

    :param __salt__: reference to ``__salt__`` execution modules dictionary
    :param kwargs: dictionary of Fx filters
    """
    ret = {}
    platforms_added = set()

    # get a list of hosts and their platforms to run Salt Jobs for
    hosts = __salt__["nr.nornir"](
        "inventory",
        "list_hosts_platforms",
        **{k: v for k, v in kwargs.items() if k in FFun_functions},
    )
    if not hosts:
        raise CommandExecutionError("No hosts matched")

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
                f"netbox_utils:parse_config unsupported "
                f"platform '{platform}', host name '{host_name}'"
            )
            continue
        log.debug(
            f"netbox_utils:parse_config parsing '{platform}' devices configurations using '{template}' template"
        )
        ret.update(
            __salt__["nr.cli"](
                **task_kwargs,
                FL=[h for h, p in hosts.items() if p == platform],
                run_ttp=template,
                ttp_structure="dictionary",
            )
        )
        platforms_added.add(platform)

    return ret


def update_config_context(__salt__=None, proxy_id=None, **kwargs):
    """
    Function to populate device configuration context with parsed results.

    :param __salt__: reference to ``__salt__`` execution modules dictionary
    """
    ret = {}
    netbox_params = get_salt_nornir_netbox_params(__salt__)
    parsing_job_results = parse_config(__salt__, **kwargs)

    # instantiate pynetbox object
    nb = get_pynetbox(netbox_params)

    # update devices context
    for host_name, host_data in parsing_job_results.items():
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


def update_vrf(__salt__=None, proxy_id=None, **kwargs):
    """
    Function to create or update VRFs and Route-Targets in Netbox.

    This function creates or updates:

    * VRFs with their names and description (if present in confiugration)
    * Route-Targets values
    * Reference to import and export RT for VRFs

    :param __salt__: reference to ``__salt__`` execution modules dictionary
    """
    all_rt, all_vrf = set(), {}  # variables to hold all parsed RT and VRFs names
    rt_create, rt_update, vrf_create, vrf_update = {}, {}, {}, {}
    netbox_params = get_salt_nornir_netbox_params(__salt__)
    parsing_job_results = parse_config(__salt__, **kwargs)

    # instantiate pynetbox object
    nb = get_pynetbox(netbox_params)

    # iterate over VRF parsing results
    hosts_done = []
    for host_name, host_data in parsing_job_results.items():
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
        field="route_target_list",
        filters={"name": all_rt},
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
        field="route_target_list",
        filters={"name": all_rt},
        fields=["name", "id"],
        params=netbox_params,
    )
    existing_rt = {i["name"]: int(i["id"]) for i in existing_rt}
    # retrieve a list of existing VRFs
    existing_vrf = nb_graphql(
        field="vrf_list",
        filters={"name": list(all_vrf)},
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


def run_dir(**kwargs):
    """
    Function to return a list of supported Netbox Utils tasks
    """
    return list(netbox_tasks.keys())


def _calculate_peer_ip(address):
    """
    Helper function to claculate peer IP for ptp subnets

    :param address: Netbox IP adddress string of '10.0.0.1/30' format
    """
    if not any(address.endswith(k) for k in ["/30", "/31", "/120", "126", "/127"]):
        return None
    ip_interface = ipaddress.ip_interface(address)
    net_hosts = list(ip_interface.network.hosts())
    peer_ip = net_hosts[0] if net_hosts[0] != ip_interface.ip else net_hosts[1]
    return f"{str(peer_ip)}"


def get_circuits(
    params=None,
    sync=False,
    __salt__=None,
    proxy_id=None,
    hosts=None,
    cache=True,
    cache_ttl=3600,
    get_interface_details=True,
    **kwargs,
) -> dict:
    """
    Function to retrieve circuits details from Netbox

    :param params: dictionary with salt_nornir_netbox parameters
    :param sync: if True, saves get circuits results to host's in-memory
        inventory data under ``circuits`` key, if sync is a string, provided
        value used as a key.
    :param __salt__: reference to ``__salt__`` execution modules dictionary
    :param hosts: list of hosts to get circuits for
    :param cache: boolean indicating whether to cache Netbox response or string
        ``refresh`` to delete cached data, if set to False cached data ignored
        but not refreshed
    :param cache_ttl: integer indicating cache time to live
    :param kwargs: Fx filters to filter hosts to retrieve circuits for
    :param get_interface_details: boolen, indicating if need to retrieve interface
        details, inventory items and IP addresses
    :return: dictionary keyed by device name with circuits details

    Circuits data retrived for a set of hosts first by queriyng netbox for a
    list of sites where hosts belongs to, next all circuits for given sites
    retrived from Netbox using GraphQL API, after that for each circuit one
    of the terminations path traced using REST API endpoint -
    `/api/circuits/circuit-terminations/{id}/paths/`. Once full path for the
    circuit retrived interface and device details extracted from path data
    for each end and stored in circuits data.

    When `get_interface_details` set to True interface details retrieved from
    Netbox using `get_interfaces` function together with inventory items,
    child interfaces and IP addresses. For each IP address `peer_ip` calculated
    and added to IP data if subnet is one of prefix length - `/30`, `/31`,
    `/127`, `/126`, `/120` by calculating second IP value.

    When circuit connects to provider network, no interface, instead of
    `remote_device` and `remote_interface` keys, circuit contains
    `provider_network` key with value referring to provider network name.

    Sample circuits data with ``get_interface_details`` set to True::

        {'CID2': {'comments': 'some comments',
                  'commit_rate': 10000,
                  'custom_fields': {},
                  'description': 'some description',
                  'interface': {'bridge': None,
                                'bridge_interfaces': [],
                                'custom_fields': {},
                                'description': '',
                                'duplex': None,
                                'enabled': True,
                                'inventory_items': [],
                                'ip_addresses': [{'address': '10.0.1.1/30',
                                                  'custom_fields': {},
                                                  'description': '',
                                                  'dns_name': '',
                                                  'last_updated': '2023-08-06T01:15:09.847777+00:00',
                                                  'peer_ip': '10.0.1.2/30',
                                                  'role': None,
                                                  'status': 'ACTIVE',
                                                  'tags': [],
                                                  'tenant': None}],
                                'last_updated': '2023-08-06T01:15:09.790266+00:00',
                                'mac_address': None,
                                'member_interfaces': [],
                                'mode': None,
                                'mtu': None,
                                'name': 'eth11',
                                'parent': None,
                                'speed': None,
                                'tagged_vlans': [],
                                'tags': [],
                                'untagged_vlan': None,
                                'vrf': 'OOB_CTRL',
                                'wwn': None},
                  'is_active': True,
                  'provider': 'Provider1',
                  'provider_account': '',
                  'remote_device': 'fceos5',
                  'remote_interface': 'eth11',
                  'status': 'ACTIVE',
                  'subinterfaces': {'eth11.123': {'bridge': None,
                                                  'bridge_interfaces': [],
                                                  'child_interfaces': [{'name': 'eth123.123'}],
                                                  'custom_fields': {},
                                                  'description': '',
                                                  'duplex': None,
                                                  'enabled': True,
                                                  'inventory_items': [],
                                                  'ip_addresses': [{'address': '10.0.0.1/30',
                                                                    'custom_fields': {},
                                                                    'description': '',
                                                                    'dns_name': '',
                                                                    'last_updated': '2023-08-06T01:15:09.227279+00:00',
                                                                    'peer_ip': '10.0.0.2/30',
                                                                    'role': None,
                                                                    'status': 'ACTIVE',
                                                                    'tags': [],
                                                                    'tenant': None}],
                                                  'last_updated': '2023-08-06T01:15:09.175047+00:00',
                                                  'mac_address': None,
                                                  'member_interfaces': [],
                                                  'mode': None,
                                                  'mtu': None,
                                                  'parent': {'name': 'eth11'},
                                                  'speed': None,
                                                  'tagged_vlans': [],
                                                  'tags': [],
                                                  'untagged_vlan': None,
                                                  'vrf': 'MGMT',
                                                  'wwn': None}},
                  'tags': ['ACCESS'],
                  'tenant': None,
                  'type': 'DarkFibre'},
        }

    """
    device_sites_fields = ["site {slug}"]
    circuit_fields = [
        "cid",
        "tags {name}",
        "provider {name}",
        "commit_rate",
        "description",
        "status",
        "type {name}",
        "provider_account {name}",
        "tenant {name}",
        "termination_a {id}",
        "termination_z {id}",
        "custom_fields",
        "comments",
    ]

    # retrieve a list of hosts to get circuits for
    hosts = hosts or __salt__["nr.nornir"](
        "hosts",
        **{k: v for k, v in kwargs.items() if k in FFun_functions},
    )
    if not hosts:
        raise CommandExecutionError("No hosts matched")

    # form final result dictionary
    circuits_dict = {h: {} for h in hosts}

    # if no params provided, extract Netbox params from mater config or minion pillar
    params = params or get_salt_nornir_netbox_params(__salt__)

    # check if need to use cache
    if HAS_DISKCACHE and cache:
        cache_directory = (
            params["proxy"]
            .get("cache_base_path", "/var/salt-nornir/{proxy_id}/cache/")
            .format(proxy_id=proxy_id)
        )
        cache_obj = FanoutCache(directory=cache_directory, shards=1)
        # remove expired items from cache
        _ = cache_obj.expire()
        # iterate over a copy of hosts list
        for host in list(hosts):
            key = f"nr.netbox:get_circuits, {host}"
            if key in cache_obj and cache is True:
                circuits_dict[host] = cache_obj[key]
                hosts.remove(host)
                log.debug(
                    f"netbox_utils:get_circuits '{host}' retrieved get_circuits data from cache"
                )
            elif key in cache_obj and cache == "refresh":
                cache_obj.delete(key)
                log.debug(
                    f"netbox_utils:get_circuits '{host}' deleted get_circuits data from cache"
                )
        cache_obj.close()

    # check if still has hosts left to retrieve data for
    if hosts:
        # retrieve list of hosts' sites
        hosts_sites = nb_graphql(
            "device_list", {"name": hosts}, device_sites_fields, params
        )
        hosts_sites = [i["site"]["slug"] for i in hosts_sites]

        # retrieve all circuits for hists' sites
        all_circuits = nb_graphql(
            "circuit_list", {"site": hosts_sites}, circuit_fields, params
        )

        # iterate over circuits and map them to hosts
        for circuit in all_circuits:
            cid = circuit.pop("cid")
            circuit["tags"] = [i["name"] for i in circuit["tags"]]
            circuit["type"] = circuit["type"]["name"]
            circuit["provider"] = circuit["provider"]["name"]
            circuit["tenant"] = circuit["tenant"]["name"] if circuit["tenant"] else None
            circuit["provider_account"] = (
                circuit["provider_account"]["name"]
                if circuit["provider_account"]
                else None
            )
            termination_a = circuit.pop("termination_a")
            termination_z = circuit.pop("termination_z")
            termination_a = termination_a["id"] if termination_a else None
            termination_z = termination_z["id"] if termination_z else None

            # retrieve A or Z termination path using Netbox REST API
            if termination_a is not None:
                circuit_path = nb_rest(
                    method="get",
                    api=f"/circuits/circuit-terminations/{termination_a}/paths/",
                    __salt__=__salt__,
                )
            elif termination_z is not None:
                circuit_path = nb_rest(
                    method="get",
                    api=f"/circuits/circuit-terminations/{termination_z}/paths/",
                    __salt__=__salt__,
                )
            else:
                continue

            # check if circuit ends connect to device or provider network
            if (
                not circuit_path
                or "name" not in circuit_path[0]["path"][0][0]
                or "name" not in circuit_path[0]["path"][-1][-1]
            ):
                continue

            # forma A and Z connection endpoints
            end_a = {
                "device": circuit_path[0]["path"][0][0]
                .get("device", {})
                .get("name", False),
                "provider_network": "provider-network"
                in circuit_path[0]["path"][0][0]["url"],
                "name": circuit_path[0]["path"][0][0]["name"],
            }
            end_z = {
                "device": circuit_path[0]["path"][-1][-1]
                .get("device", {})
                .get("name", False),
                "provider_network": "provider-network"
                in circuit_path[0]["path"][-1][-1]["url"],
                "name": circuit_path[0]["path"][-1][-1]["name"],
            }
            circuit["is_active"] = circuit_path[0]["is_active"]

            # map path ends to devices
            if end_a["device"] and end_a["device"] in hosts:
                circuits_dict[end_a["device"]][cid] = circuit
                circuits_dict[end_a["device"]][cid]["interface"] = end_a["name"]
                if end_z["device"]:
                    circuits_dict[end_a["device"]][cid]["remote_device"] = end_z[
                        "device"
                    ]
                    circuits_dict[end_a["device"]][cid]["remote_interface"] = end_z[
                        "name"
                    ]
                elif end_z["provider_network"]:
                    circuits_dict[end_a["device"]][cid]["provider_network"] = end_z[
                        "name"
                    ]
            if end_z["device"] and end_z["device"] in hosts:
                circuits_dict[end_z["device"]][cid] = circuit
                circuits_dict[end_z["device"]][cid]["interface"] = end_z["name"]
                if end_a["device"]:
                    circuits_dict[end_z["device"]][cid]["remote_device"] = end_a[
                        "device"
                    ]
                    circuits_dict[end_z["device"]][cid]["remote_interface"] = end_a[
                        "name"
                    ]
                elif end_a["provider_network"]:
                    circuits_dict[end_z["device"]][cid]["provider_network"] = end_a[
                        "name"
                    ]

        # retrieve itnerfaces details
        if get_interface_details:
            interfaces_data = get_interfaces(
                add_ip=True,
                add_inventory_items=True,
                sync=False,
                params=params,
                __salt__=__salt__,
                proxy_id=proxy_id,
                hosts=hosts,
                cache=cache,
                **kwargs,
            )
            # iterate over hosts and add interface details for each circuit
            for hostname, host_interfaces in interfaces_data.items():
                for cid, circuit_data in circuits_dict[hostname].items():
                    interface_name = circuit_data["interface"]
                    circuit_data["interface"] = host_interfaces[interface_name]
                    circuit_data["interface"]["name"] = interface_name
                    circuit_data["interface"]["vrf"] = (
                        circuit_data["interface"]["vrf"]["name"]
                        if circuit_data["interface"]["vrf"]
                        else None
                    )
                    circuit_data["subinterfaces"] = {}
                    # add peer IP details for ptp subnets
                    for ip_address in circuit_data["interface"]["ip_addresses"]:
                        ip_address["peer_ip"] = _calculate_peer_ip(
                            ip_address["address"]
                        )
                    # add child interfaces details
                    for child_interface in circuit_data["interface"].pop(
                        "child_interfaces"
                    ):
                        child_interface_data = host_interfaces[child_interface["name"]]
                        child_interface_data["vrf"] = (
                            child_interface_data["vrf"]["name"]
                            if child_interface_data["vrf"]
                            else None
                        )
                        circuit_data["subinterfaces"][
                            child_interface["name"]
                        ] = child_interface_data
                        # add peer IP details for ptp subnets
                        for ip_address in child_interface_data["ip_addresses"]:
                            ip_address["peer_ip"] = _calculate_peer_ip(
                                ip_address["address"]
                            )

        # cache connections data for each host
        if HAS_DISKCACHE and cache:
            cache_obj = FanoutCache(directory=cache_directory, shards=1)
            for host in hosts:
                key = f"nr.netbox:get_circuits, {host}"
                cache_obj.set(key, circuits_dict[host], expire=cache_ttl)
                log.debug(
                    f"netbox_utils:get_circuits '{host}' cached get_circuits data"
                )
            cache_obj.close()

    # save results to hosts inventory if requested to do so
    if sync:
        key = sync if isinstance(sync, str) else "circuits"
        return __salt__["nr.nornir"](
            fun="inventory",
            call="load",
            data=[
                {"call": "update_host", "name": host, "data": {key: circuits}}
                for host, circuits in circuits_dict.items()
            ],
        )

    return circuits_dict


# dispatch dictionary of Netbox tasks exposed for calling
netbox_tasks = {
    "parse_config": parse_config,
    "update_config_context": update_config_context,
    "update_vrf": update_vrf,
    "query": nb_graphql,
    "rest": nb_rest,
    "get_interfaces": get_interfaces,
    "get_connections": get_connections,
    "get_circuits": get_circuits,
    # get_config_context
    # get_configuration
    "dir": run_dir,
}
