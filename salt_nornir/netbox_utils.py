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
.. autofunction:: salt_nornir.netbox_utils.parse_config
.. autofunction:: salt_nornir.netbox_utils.update_config_context
.. autofunction:: salt_nornir.netbox_utils.update_vrf
"""
import logging
import json

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


def nb_rest(method: str = "get", api: str = "", __salt__=None, **kwargs) -> dict:
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
    hosts=None,
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
    :return: dictionary keyed by device name with interface details

    .. note:: ``add_inventory_items`` only supported with Netbox 3.4 and above.

    .. note: Either ``hosts`` or ``__salt__`` with ``Fx`` filters should be provided,
    otherwise ``CommandExecutionError`` raised.
    """
    # retrieve a list of hosts to get interfaces for
    hosts = hosts or __salt__["nr.nornir"](
        "hosts",
        **{k: v for k, v in kwargs.items() if k in FFun_functions},
    )
    if not hosts:
        raise CommandExecutionError("No hosts matched")
    # if no params provided extract them from minion pillar of master config
    params = params or get_salt_nornir_netbox_params(__salt__)
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
    intf_dict = {}
    while interfaces:
        intf = interfaces.pop()
        _ = intf.pop("id")
        device_name = intf.pop("device").pop("name")
        intf_name = intf.pop("name")
        intf_dict.setdefault(device_name, {})
        intf_dict[device_name][intf_name] = intf

    # save results to hosts inventory if requested to do so
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
    else:
        # make sure all hosts included in return data
        for host in hosts:
            intf_dict.setdefault(host, {})
        return intf_dict


def get_connections(
    params: list = None,
    trace: bool = False,
    sync=False,
    __salt__=None,
    hosts=None,
    **kwargs,
) -> dict:
    """
    Function to retrieve connections details from Netbox

    :param params: dictionary with salt_nornir_netbox parameters
    :param trace: if True traces full connection path between devices interfaces
    :param sync: if True, saves get connections results to host's in-memory
        inventory data under ``connections`` key, if sync is a string, provided
        value used as a key.
    :param __salt__: reference to ``__salt__`` execution modules dictionary
    :param kwargs: Fx filters to filter hosts to retrieve interfaces for
    :return: dictionary keyed by device name with connections details

    .. warning:: Get connections only supported for Netbox of 3.4 and above.

    .. note:: Either ``hosts`` or ``__salt__`` with ``Fx`` filters should be provided,
    otherwise ``CommandExecutionError`` raised.

    When ``trace`` set to False, only first segment of connection path returned. If
    first segment is a circuit termination, ``circuit`` details included, otherwise
    first segment ``remote_device`` details included.

    Path tracing only performed if first segment remote cable termination is of
    frontport, rearport or circuittermination type and only for interface and console
    ports connections, power cables trace not implemented.

    .. warning:: trace operation performed on an interface by interface basis and may
        take significant amount of time to complete for all device's interfaces.

    Get connections returns a dictionary keyed by device name with value being a
    dictionary keyed by local interface names.

    Sample return data with ``trace`` set to ``True``::

        {'fceos4': {'ConsolePort1': {'breakout': False,
                          'cable': {'custom_fields': {},
                                    'label': '',
                                    'last_updated': '2022-12-29T04:16:49.919563+00:00',
                                    'length': None,
                                    'length_unit': None,
                                    'status': 'CONNECTED',
                                    'tags': [],
                                    'tenant': {'name': 'SALTNORNIR'},
                                    'type': 'CAT6A'},
                          'reachable': True,
                          'remote_device': 'fceos5',
                          'remote_interface': 'ConsoleServerPort1',
                          'remote_termination_type': 'consoleserverport',
                          'termination_type': 'consoleport'},
         'eth1': {'breakout': True,
                  'cable': {'custom_fields': {},
                            'label': '',
                            'last_updated': '2022-12-29T06:54:16.036814+00:00',
                            'length': None,
                            'length_unit': None,
                            'status': 'CONNECTED',
                            'tags': [],
                            'tenant': {'name': 'SALTNORNIR'},
                            'type': 'CAT6A'},
                  'reachable': True,
                  'remote_device': 'fceos5',
                  'remote_interface': ['eth1', 'eth10'],
                  'remote_termination_type': 'interface',
                  'termination_type': 'interface'},
          'eth101': {'breakout': False,
                     'cables': [{'color': '',
                                 'description': '',
                                 'id': 28,
                                 'label': '',
                                 'length': None,
                                 'length_unit': '',
                                 'status': 'connected',
                                 'type': '',
                                 'url': 'http://192.168.75.200:8000/api/dcim/cables/28/'},
                                {'color': '',
                                 'description': '',
                                 'id': 29,
                                 'label': '',
                                 'length': None,
                                 'length_unit': '',
                                 'status': 'connected',
                                 'type': '',
                                 'url': 'http://192.168.75.200:8000/api/dcim/cables/29/'}],
                     'reachable': True,
                     'remote_device': 'fceos5',
                     'remote_interface': 'eth8',
                     'remote_termination_type': 'interface',
                     'termination_type': 'interface'},
          'eth3': {'breakout': False,
                   'cable': {'custom_fields': {},
                             'label': '',
                             'last_updated': '2022-12-29T06:56:23.629652+00:00',
                             'length': None,
                             'length_unit': None,
                             'status': 'CONNECTED',
                             'tags': [],
                             'tenant': {'name': 'SALTNORNIR'},
                             'type': 'CAT6A'},
                   'reachable': True,
                   'remote_device': 'fceos5',
                   'remote_interface': 'eth3',
                   'remote_termination_type': 'interface',
                   'termination_type': 'interface'},
         'eth7': {'breakout': False,
                  'cables': [{'color': '',
                              'description': '',
                              'id': 25,
                              'label': '',
                              'length': None,
                              'length_unit': '',
                              'status': 'connected',
                              'type': 'smf',
                              'url': 'http://192.168.75.200:8000/api/dcim/cables/25/'},
                             {'color': '',
                              'description': '',
                              'id': 26,
                              'label': '',
                              'length': None,
                              'length_unit': '',
                              'status': 'planned',
                              'type': '',
                              'url': 'http://192.168.75.200:8000/api/dcim/cables/26/'},
                             {'color': '',
                              'description': '',
                              'id': 27,
                              'label': '',
                              'length': None,
                              'length_unit': '',
                              'status': 'connected',
                              'type': '',
                              'url': 'http://192.168.75.200:8000/api/dcim/cables/27/'}],
                  'reachable': False,
                  'remote_device': 'fceos5',
                  'remote_interface': 'eth7',
                  'remote_termination_type': 'interface',
                  'termination_type': 'interface'}}}
    Where:

    * ``ConsolePort1`` is a direct cable between devices
    * ``eth101`` has circuit connected to it
    * ``eth1`` is a direct between devices breakout cable
    * ``eth3`` is a direct between devices normal (non-breakout) cable
    * ``eth7`` connected to another device through patch panels

    Same connections but with ``trace`` set to ``False``::

        {'fceos4': {'ConsolePort1': {'breakout': False,
                               'cable': {'custom_fields': {},
                                         'label': '',
                                         'last_updated': '2022-12-29T04:16:49.919563+00:00',
                                         'length': None,
                                         'length_unit': None,
                                         'status': 'CONNECTED',
                                         'tags': [],
                                         'tenant': {'name': 'SALTNORNIR'},
                                         'type': 'CAT6A'},
                               'reachable': True,
                               'remote_device': 'fceos5',
                               'remote_interface': 'ConsoleServerPort1',
                               'remote_termination_type': 'consoleserverport',
                               'termination_type': 'consoleport'},
              'eth1': {'breakout': True,
                       'cable': {'custom_fields': {},
                                 'label': '',
                                 'last_updated': '2022-12-29T06:54:16.036814+00:00',
                                 'length': None,
                                 'length_unit': None,
                                 'status': 'CONNECTED',
                                 'tags': [],
                                 'tenant': {'name': 'SALTNORNIR'},
                                 'type': 'CAT6A'},
                       'reachable': True,
                       'remote_device': 'fceos5',
                       'remote_interface': ['eth1', 'eth10'],
                       'remote_termination_type': 'interface',
                       'termination_type': 'interface'},
              'eth101': {'cable': {'custom_fields': {},
                                   'label': '',
                                   'last_updated': '2022-12-29T09:43:21.761420+00:00',
                                   'length': None,
                                   'length_unit': None,
                                   'status': 'CONNECTED',
                                   'tags': [],
                                   'tenant': None,
                                   'type': None},
                         'circuit': {'cid': 'CID1',
                                     'commit_rate': None,
                                     'custom_fields': {},
                                     'description': '',
                                     'provider': {'name': 'Provider1'},
                                     'status': 'ACTIVE',
                                     'tags': []},
                         'reachable': True,
                         'remote_termination_type': 'circuittermination',
                         'termination_type': 'interface'},
              'eth3': {'breakout': False,
                       'cable': {'custom_fields': {},
                                 'label': '',
                                 'last_updated': '2022-12-29T06:56:23.629652+00:00',
                                 'length': None,
                                 'length_unit': None,
                                 'status': 'CONNECTED',
                                 'tags': [],
                                 'tenant': {'name': 'SALTNORNIR'},
                                 'type': 'CAT6A'},
                       'reachable': True,
                       'remote_device': 'fceos5',
                       'remote_interface': 'eth3',
                       'remote_termination_type': 'interface',
                       'termination_type': 'interface'},
              'eth7': {'breakout': False,
                       'cable': {'custom_fields': {},
                                 'label': '',
                                 'last_updated': '2022-12-29T08:52:26.546559+00:00',
                                 'length': None,
                                 'length_unit': None,
                                 'status': 'CONNECTED',
                                 'tags': [],
                                 'tenant': None,
                                 'type': 'SMF'},
                       'reachable': True,
                       'remote_device': 'PatchPanel1',
                       'remote_interface': 'FrontPort1',
                       'remote_termination_type': 'frontport',
                       'termination_type': 'interface'}}}}

    Each connection has ``reachable`` status calculated based on cables status - set to
    ``True`` if all cables in the path have status ``connected``, path circuits' status
    not taken into account.
    """
    # retrieve a list of hosts to get interfaces for
    hosts = hosts or __salt__["nr.nornir"](
        "hosts",
        **{k: v for k, v in kwargs.items() if k in FFun_functions},
    )
    if not hosts:
        raise CommandExecutionError("No hosts matched")
    # if no params provided, extract Netbox params from mater config or minion pillar
    params = params or get_salt_nornir_netbox_params(__salt__)
    connections_dict = {}

    # retrieve full list of device cables with all terminations
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
        """terminations {
               termination {
                 __typename
                 ... on InterfaceType {
                   name device{name} id
                   link_peers {
                     __typename
                     ... on InterfaceType {name device{name}}
                     ... on FrontPortType {name device{name}}
                     ... on RearPortType {name device{name}}
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
                   }
                 }  
                 ... on ConsolePortType {
                   name device{name} id
                   link_peers {
                     __typename
                     ... on ConsoleServerPortType {name device{name}}
                   }
                 }
                 ... on ConsoleServerPortType {
                   name device{name} id
                   link_peers {
                     __typename
                     ... on ConsolePortType {name device{name}}
                   }
                 }
                 ... on PowerPortType {
                   name device{name} id
                   link_peers {
                     __typename
                     ... on PowerOutletType {name device{name}}
                   }
                 }
                 ... on PowerOutletType {
                   name device{name} id
                   link_peers {
                     __typename
                     ... on PowerPortType {name device{name}}
                   }
                 }
                 ... on FrontPortType {
                   name device{name} id
                   link_peers {
                     __typename
                     ... on InterfaceType {name device{name}}
                     ... on FrontPortType {name device{name}}
                     ... on RearPortType {name device{name}}
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
                   }
                 }
                 ... on RearPortType {
                   name device{name} id
                   link_peers {
                     __typename
                     ... on InterfaceType {name device{name}}
                     ... on FrontPortType {name device{name}}
                     ... on RearPortType {name device{name}}
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
                   }
                 }
               }
             }""",
    ]

    all_cables = nb_graphql("cable_list", {"device": hosts}, cable_fields, params)

    # form connections_dict keyed by device name and device's local interface name
    for cable in all_cables:
        terminations = cable.pop("terminations")
        for termination in terminations:
            termination = termination.pop("termination")
            termination_type = termination["__typename"].replace("Type", "").lower()
            # skip circuit termination point
            if termination_type == "circuittermination":
                continue
            # skip if cable has no peers
            if not termination["link_peers"]:
                continue
            device_name = termination["device"]["name"]
            # skip connections for non requested devices
            if device_name not in hosts:
                continue
            connections_dict.setdefault(device_name, {})
            link_peers = termination.pop("link_peers")
            remote_termination_type = (
                link_peers[0]["__typename"].replace("Type", "").lower()
            )
            # check if need to trace full path
            if trace and remote_termination_type in [
                "frontport",
                "rearport",
                "circuittermination",
            ]:
                if termination_type == "interface":
                    far_end_termination_type = "interface"
                    api = f"dcim/interfaces/{termination['id']}/trace"
                elif termination_type == "consoleport":
                    far_end_termination_type = "consoleserverport"
                    api = f"dcim/console-ports/{termination['id']}/trace"
                elif termination_type == "consoleserverport":
                    far_end_termination_type = "consoleport"
                    api = f"dcim/console-server-ports/{termination['id']}/trace"
                path_trace = nb_rest(method="get", api=api, __salt__=__salt__)
                # path_trace - list of path segments as a three-tuple of (termination, cable, termination)
                remote_device_terminations = path_trace[-1][-1]
                connections_dict[device_name][termination["name"]] = {
                    # path is reachable if all segments' cables are connected
                    "reachable": all(
                        c[1]["status"].lower() == "connected" for c in path_trace
                    ),
                    "cables": [c[1] for c in path_trace],
                    "remote_device": remote_device_terminations[0]["device"]["name"],
                    "remote_interface": (
                        remote_device_terminations[0]["name"]
                        if len(remote_device_terminations) == 1
                        else [i["name"] for i in remote_device_terminations]
                    ),
                    "termination_type": termination_type,
                    "remote_termination_type": far_end_termination_type,
                    "breakout": False if len(remote_device_terminations) == 1 else True,
                }
            # retrieve local cable connection to the circuit
            elif remote_termination_type == "circuittermination":
                connections_dict[device_name][termination["name"]] = {
                    "reachable": cable["status"].lower() == "connected",
                    "cable": cable,
                    "circuit": link_peers[0]["circuit"],
                    "termination_type": termination_type,
                    "remote_termination_type": remote_termination_type,
                }
            # retrieve local cable connections only, no full path trace
            else:
                connections_dict[device_name][termination["name"]] = {
                    "reachable": cable["status"].lower() == "connected",
                    "cable": cable,
                    "remote_device": link_peers[0]["device"]["name"],
                    "remote_interface": (
                        link_peers[0]["name"]
                        if len(link_peers) == 1
                        else [i["name"] for i in link_peers]
                    ),
                    "termination_type": termination_type,
                    "remote_termination_type": remote_termination_type,
                    "breakout": False if len(link_peers) == 1 else True,
                }

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
    else:
        # make sure all hosts included in return data
        for host in hosts:
            connections_dict.setdefault(host, {})
        return connections_dict


def parse_config(__salt__=None, **kwargs):
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
                f"netbox_utils:get_parse_config_tasks unsupported "
                f"platform '{platform}', host name '{host_name}'"
            )
            continue
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


def update_config_context(__salt__=None, **kwargs):
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


def update_vrf(__salt__=None, **kwargs):
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


# dispatch dictionary of Netbox tasks exposed for calling
netbox_tasks = {
    "parse_config": parse_config,
    "update_config_context": update_config_context,
    "update_vrf": update_vrf,
    "query": nb_graphql,
    "rest": nb_rest,
    "get_interfaces": get_interfaces,
    "get_connections": get_connections,
    "dir": run_dir,
}
