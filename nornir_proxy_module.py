# -*- coding: utf-8 -*-
"""
Nornir
======

Nornir proxy-minion pillar example::

    proxy:
      proxytype: nornir
      num_workers: 100         
      process_count_max: 3     
      multiprocessing: True        
      
    hosts:
      IOL1:
        hostname: 192.168.217.10
        platform: ios
        location: B1
        groups: [lab]
      IOL2:
        hostname: 192.168.217.7
        platform: ios
        location: B2
        groups: [lab]
      IOL3:
        hostname: 192.168.217.11
        platform: ios
        location: B3
        groups: [lab]
        
    groups: 
      lab:
        username: nornir
        password: nornir
        connection_options: 
          napalm:
            optional_args: {dest_file_system: "system:"}
              
    defaults: {}
    
proxy_always_alive amd multiprocessing
--------------------------------------

`proxy_always_alive` is ignored, `multiprocessing=True` is a
recommended way to run this proxy. 

Nornir object and connections to devices initiated on each function
call, connections closed after completion.

Filtering Hosts
---------------

Filtering order::

    FO -> FB -> FG -> FP -> FL
    
If multiple filters provided, returned hosts must comply all checks - AND logic.

FO - Filter Object
++++++++++++++++++

Filter using `Nornir Filter Object <https://nornir.readthedocs.io/en/latest/tutorials/intro/inventory.html#Filter-Object>`_

platform ios and hostname 192.168.217.7::

    salt nornir-proxy-1  nr.inventory FO='{"platform": "ios", "hostname": "192.168.217.7"}'
    
location B1 or location B2:

    salt nornir-proxy-1  nr.inventory FO='[{"location": "B1"}, {"location": "B2"}]'
    
location B1 and platform ios or any host at location B2:

   salt nornir-proxy-1  nr.inventory FO='[{"location": "B1", "platform": "ios"}, {"location": "B2"}]' 
   
FB - Filter gloB
++++++++++++++++
   
Filter hosts by name using Glob Patterns - `fnmatchcase <https://docs.python.org/3.4/library/fnmatch.html#fnmatch.fnmatchcase>`_ method::

    salt nornir-proxy-1  nr.inventory FB="IOL*"

FG - Filter Group
+++++++++++++++++
   
Filter hosts by group returning all hosts that belongs to given group::

    salt nornir-proxy-1  nr.inventory FG="lab"
    
FP - Filter Prefix
++++++++++++++++++

Filter hosts by checking if hosts hostname is part of given IP Prefix::

    salt nornir-proxy-1  nr.inventory FP="192.168.217.0/29, 192.168.2.0/24"
    salt nornir-proxy-1  nr.inventory FP='["192.168.217.0/29", "192.168.2.0/24"]'
    
If hostname is IP will use it as is, if it is FQDN will attempt to resolve it to obtain IP address.

FL - Filter List
++++++++++++++++

Match only hosts with names in provided list::

    salt nornir-proxy-1  nr.inventory FL="IOL1, IOL2"
    salt nornir-proxy-1  nr.inventory FL='["IOL1", "IOL2"]'
    
jumphosts or bastions
---------------------

`nr.cli` function and `nr.cfg` with `plugin="netmiko"` can interract with devices
behind jumposts. 

Sample jumphost definition in host's data::

    hosts:
      LAB-R1:
        hostname: 192.168.1.10
        platform: ios
        password: user
        username: user
        data: 
          jumphost:
            hostname: 172.16.0.10
            port: 22
            password: admin
            username: admin

"""
from __future__ import absolute_import

# Import python stdlib 
import logging
from fnmatch import fnmatchcase

# Import third party libs
try:
    from nornir import InitNornir
    from nornir.core.deserializer.inventory import Inventory
    from nornir.plugins.tasks.networking import napalm_get
    from nornir.core.filter import F

    HAS_NORNIR = True
except ImportError:
    HAS_NORNIR = False


# -----------------------------------------------------------------------------
# proxy properties
# -----------------------------------------------------------------------------

__proxyenabled__ = ["nornir"]

# -----------------------------------------------------------------------------
# globals
# -----------------------------------------------------------------------------

__virtualname__ = "nornir"
log = logging.getLogger(__name__)
nornir_data = {"initialized": False}

# -----------------------------------------------------------------------------
# propery functions
# -----------------------------------------------------------------------------


def __virtual__():
    """
    Proxy module available only if nornir is installed.
    """
    if not HAS_NORNIR:
        return (
            False,
            "The nornir proxy module requires nornir library to be installed.",
        )
    return __virtualname__


# -----------------------------------------------------------------------------
# proxy functions
# -----------------------------------------------------------------------------


def init(opts):
    """
    Initiate nornir by calling InitNornir() 
    """
    nornir_data["nr"] = InitNornir(
        core={"num_workers": opts["proxy"].get("num_workers", 100)},
        logging={"enabled": False},
        inventory={
            "options": {
                "hosts": opts["pillar"]["hosts"],
                "groups": opts["pillar"].get("groups", {}),
                "defaults": opts["pillar"].get("defaults", {}),
            }
        }
    )
    nornir_data["initialized"] = True
    return True


def alive(opts):
    """
    Return the nornir status
    """
    return nornir_data["initialized"]


def ping():
    """
    Connection open successfully?
    """
    from nornir.plugins.tasks.networking import tcp_ping

    output = nornir_data["nr"].run(    
        task=tcp_ping,
        name="TCP Ping ports",
        ports=[22, 23]
    )
    return {host: res.result for host, res in output.items()} 


def initialized():
    """
    Nornir module finished initializing?
    """
    return nornir_data["initialized"]


def shutdown():
    """
    Closes connection with the device.
    """
    nornir_data["nr"].close_connections(on_good=True, on_failed=True)
    del(nornir_data["nr"])
    nornir_data["initialized"] = False
    return True


def grains():
    """
    Get grains from Hosts
    """
    # network_devices = nornir_data["nr"].filter(platfor="ios" |)
    # grains_data = network_devices.run(task=napalm_get, getters=["facts"])
    return {}


def grains_refresh():
    """
    Refresh grains
    """
    return grains()



# -----------------------------------------------------------------------------
# proxy module private functions
# -----------------------------------------------------------------------------


def _filter_FO(ret, filter_data):
    """Function to filter hosts using Filter Object
    """
    if isinstance(filter_data, dict):
        ret = ret.filter(F(**filter_data))
    elif isinstance(filter_data, list):
        ret = ret.filter(F(**filter_data[0]))
        for item in filter_data[1:]:
            filtered_hosts = nornir_data["nr"].filter(F(**item))
            ret.inventory.hosts.update(filtered_hosts.inventory.hosts)            
    return ret    


def _filter_FB(ret, pattern):
    """Function to filter hosts by name using glob patterns
    """
    return ret.filter(
        filter_func=lambda h: fnmatchcase(h.name, pattern)
    ) 


def _filter_FG(ret, group):
    """Function to filter hosts using Groups
    """    
    return ret.filter(
       filter_func=lambda h: h.has_parent_group(group)
    ) 


def _filter_FP(ret, prefix):
    """Function to filter hosts based on IP Prefix
    """
    return ret


def _filter_FL(ret, names_list):
    """Function to filter hosts names based on list of names
    """
    names_list = [i.strip() for i in names_list.split(",")] if isinstance(names_list, str) else names_list
    return ret.filter(
        filter_func=lambda h: h.name in names_list
    ) 


def _filters_dispatcher(kwargs):
    """Inventory filters dispatcher function
    """
    ret = nornir_data["nr"]
    if kwargs.get("FO"):
        ret = _filter_FO(ret, kwargs.pop("FO"))
    if kwargs.get("FB"):
        ret = _filter_FB(ret, kwargs.pop("FB"))
    if kwargs.get("FG"):
        ret = _filter_FG(ret, kwargs.pop("FG"))
    if kwargs.get("FP"):
        ret = _filter_FP(ret, kwargs.pop("FP"))
    if kwargs.get("FL"):
        ret = _filter_FL(ret, kwargs.pop("FL"))
    return ret


def _refresh(**kwargs):
    """
    Method to reinitiate nornir with latest pillar data
    """
    opts = {
        "pillar": __salt__['pillar.items'](), 
        "proxy": __opts__["proxy"]
    }
    init(opts)
    log.debug("Reinitiated Nornir with latest pillar data")
        
        
# -----------------------------------------------------------------------------
# callable functions
# -----------------------------------------------------------------------------
    

def inventory_data(**kwargs):
    """
    Return nornir inventory as a dictionary
    """
    # re-init Nornir
    _refresh()
    # filter hosts to return inventory for
    hosts = _filters_dispatcher(kwargs=kwargs)
    return Inventory.serialize(hosts.inventory).dict()
    
    
def run(task, *args, **kwargs):
    """
    Function to run Nornir tasks
    
    :param task: callable task function
    :param kwargs: arguments to pass on to run method
    """
    # re-init Nornir
    _refresh()
    # set dry_run argument
    nornir_data["nr"].data.dry_run = kwargs.get("dry_run", False)
    # Filter hosts to run tasks for. Do not unpack kwargs, e.g. **kwargs, as need 
    # to pop filter keys from it. This is required to unpack kwargs to run method 
    # without causing task function to choke on unsupported argument
    hosts = _filters_dispatcher(kwargs=kwargs)   
    # run tasks
    ret = hosts.run(
        task,
        *[i for i in args if not i.startswith("_")],
        **{k: v for k, v in kwargs.items() if not k.startswith("_")}
    )
    return ret
