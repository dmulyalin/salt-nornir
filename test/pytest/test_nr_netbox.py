import logging
import pprint
import time
import pytest
import socket
import requests

from netbox_data import NB_URL, netbox_tasks_device_data_keys

log = logging.getLogger(__name__)

try:
    import salt.client

    from salt.exceptions import CommandExecutionError

    HAS_SALT = True
except:
    HAS_SALT = False
    raise SystemExit("SALT Nonrir Tests - failed importing SALT libraries")

if HAS_SALT:
    # initiate execution modules client to run 'salt xyz command' commands
    client = salt.client.LocalClient()
    opts = salt.config.client_config("/etc/salt/master")
    event = salt.utils.event.get_event(
        "master", sock_dir=opts["sock_dir"], transport=opts["transport"], opts=opts
    )
    
# check if Netbox endpoint reachable
netbox_url = NB_URL + "/api"
try:
    response = requests.get(netbox_url)
    has_netbox = response.status_code == 200
except Exception as e:
    has_netbox = False
skip_if_not_has_netbox = pytest.mark.skipif(
    has_netbox == False,
    reason=f"Has no connection to Netbox {netbox_url}",
)

def _clean_netbox_data(key="netbox"):
    # empty netbox inventory data for ceos1 host
    _ = client.cmd(
        tgt="nrp1", 
        fun="nr.nornir", 
        arg=["inventory", "update_host"], 
        kwarg={
            "name": "ceos1",
            "data": {key: {}}
        },
        tgt_type="glob", 
        timeout=60
    )
    

def test_netbox_dir():
    ret = client.cmd(
        tgt="nrp1", fun="nr.netbox", arg=["dir"], kwarg={}, tgt_type="glob", timeout=60
    )
    pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "dir" in data, "No 'dir' output from '{}'".format(host_name)
        assert isinstance(data["dir"], list)
        assert len(data["dir"]) > 0
        assert "Traceback (most recent " not in data["dir"], "dir call returned error"
        
@skip_if_not_has_netbox
def test_netbox_sync_from():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.netbox", 
        arg=["sync_from"], 
        kwarg={
            "add_details": True,
        },
        tgt_type="glob", 
        timeout=60
    )
    inventory = client.cmd(
        tgt="nrp1", 
        fun="nr.nornir", 
        arg=["inventory"], 
        kwarg={},
        tgt_type="glob", 
        timeout=60
    )
    _clean_netbox_data()
    pprint.pprint(ret)
    pprint.pprint(inventory)
    assert ret["nrp1"]["ceos1"]["sync_from"]["status"] == True
    assert ret["nrp1"]["ceos2"]["sync_from"]["status"] == False
    assert "netbox" in inventory["nrp1"]["hosts"]["ceos1"]["data"]
    assert inventory["nrp1"]["hosts"]["ceos1"]["data"]["netbox"] != {}
    assert "netbox" not in inventory["nrp1"]["hosts"]["ceos2"]["data"]
    
    
@skip_if_not_has_netbox
@pytest.mark.parametrize("via", ["production", "dev", "dev_wrong", "prod_in_user_defined_config"])
def test_netbox_sync_from_via(via):
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.netbox", 
        arg=["sync_from"], 
        kwarg={
            "add_details": True,
            "via": via
        },
        tgt_type="glob", 
        timeout=60
    )
    inventory = client.cmd(
        tgt="nrp1", 
        fun="nr.nornir", 
        arg=["inventory"], 
        kwarg={},
        tgt_type="glob", 
        timeout=60
    )
    _clean_netbox_data()
    pprint.pprint(ret)
    pprint.pprint(inventory)
    if via in ["production", "dev", "prod_in_user_defined_config"]:
        assert ret["nrp1"]["ceos1"]["sync_from"]["status"] == True
        assert ret["nrp1"]["ceos2"]["sync_from"]["status"] == False
        assert "netbox" in inventory["nrp1"]["hosts"]["ceos1"]["data"]
        assert inventory["nrp1"]["hosts"]["ceos1"]["data"]["netbox"] != {}
        assert "netbox" not in inventory["nrp1"]["hosts"]["ceos2"]["data"]
    elif via in ["dev_wrong"]:
        assert ret["nrp1"]["ceos1"]["sync_from"]["failed"] == True
        assert ret["nrp1"]["ceos2"]["sync_from"]["failed"] == True
        assert ret["nrp1"]["ceos1"]["sync_from"]["exception"]
        assert ret["nrp1"]["ceos2"]["sync_from"]["exception"]
        
        
@skip_if_not_has_netbox
def test_netbox_sync_from_with_data_key():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.netbox", 
        arg=["sync_from"], 
        kwarg={
            "add_details": True,
            "data_key": "netbox_data"
        },
        tgt_type="glob", 
        timeout=60
    )
    inventory = client.cmd(
        tgt="nrp1", 
        fun="nr.nornir", 
        arg=["inventory"], 
        kwarg={},
        tgt_type="glob", 
        timeout=60
    )
    _clean_netbox_data(key="netbox_data")
    pprint.pprint(ret)
    pprint.pprint(inventory)
    assert ret["nrp1"]["ceos1"]["sync_from"]["status"] == True
    assert ret["nrp1"]["ceos2"]["sync_from"]["status"] == False
    assert "netbox_data" in inventory["nrp1"]["hosts"]["ceos1"]["data"]
    assert inventory["nrp1"]["hosts"]["ceos1"]["data"]["netbox_data"] != {}
    assert "netbox_data" not in inventory["nrp1"]["hosts"]["ceos2"]["data"]
    
    
@skip_if_not_has_netbox
def test_netbox_sync_from_with_data_key_as_none():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.netbox", 
        arg=["sync_from"], 
        kwarg={
            "add_details": True,
            "data_key": None
        },
        tgt_type="glob", 
        timeout=60
    )
    inventory = client.cmd(
        tgt="nrp1", 
        fun="nr.nornir", 
        arg=["inventory"], 
        kwarg={},
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    pprint.pprint(inventory)
    assert ret["nrp1"]["ceos1"]["sync_from"]["status"] == True
    assert ret["nrp1"]["ceos2"]["sync_from"]["status"] == False
    for k in netbox_tasks_device_data_keys:
        assert k in inventory["nrp1"]["hosts"]["ceos1"]["data"], f"ceos1 has no key '{k}'"
    for k in netbox_tasks_device_data_keys:
        # skip because ceos2 data has location key in it
        if k in ["location"]:
            continue
        assert k not in inventory["nrp1"]["hosts"]["ceos2"]["data"], f"ceos2 has key '{k}'"
    
    
@skip_if_not_has_netbox
def test_netbox_query():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.netbox", 
        arg=["query"], 
        kwarg={
            "subject": "device",
            "filt": {"name": "ceos1"},
            "fields": ["name", "platform {name}", "primary_ip4 {address}", "status"],
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert ret["nrp1"][0]["name"] == "ceos1"
    assert ret["nrp1"][0]["status"] == "ACTIVE"
    assert ret["nrp1"][0]["platform"]["name"] == "Arista cEOS"
    
    
@skip_if_not_has_netbox
def test_netbox_get_interfaces():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_interfaces"], 
        kwarg={
            "add_ip": True,
            "add_inventory_items": True,
            "device_name": "fceos4"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    # check if inventory items added
    assert len(ret["nrp3"]["eth1"]["inventory_items"]) > 0, "No inventory items returned for fceos4 eth1 interface"
    assert all(k in ret["nrp3"]["eth1"]["inventory_items"][0] for k in ["name", "role", "manufacturer"])
    assert len(ret["nrp3"]["eth3"]["inventory_items"]) > 0, "No inventory items returned for fceos4 eth1 interface"
    assert all(k in ret["nrp3"]["eth3"]["inventory_items"][0] for k in ["name", "role", "manufacturer"])
    # check if ip addresses added
    assert len(ret["nrp3"]["loopback0"]["ip_addresses"]) > 0, "No ip addresses returned for fceos4 loopback0 interface"
    assert all(k in ret["nrp3"]["loopback0"]["ip_addresses"][0] for k in ["address", "role", "status"])

@skip_if_not_has_netbox
def test_netbox_get_connections():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_connections"], 
        kwarg={
            "device_name": "fceos4"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert len(ret["nrp3"]) > 0, "No connections returned for fceos4"
    assert all(k in ret["nrp3"] for k in ["ConsolePort1", "eth1", "eth2", "eth8"])
    assert all(k in ret["nrp3"]["eth8"] for k in ["status", "type", "tenant", "length"])