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

def test_netbox_dir():
    ret = client.cmd(
        tgt="nrp1", fun="nr.netbox", arg=["dir"], kwarg={}, tgt_type="glob", timeout=60
    )
    pprint.pprint(ret)
    assert isinstance(ret["nrp1"], list)
    assert len(ret["nrp1"]) > 0
    
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
    
@skip_if_not_has_netbox
def test_netbox_parse_config():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["parse_config"], 
        kwarg={
            "FB": "iosxr1"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert isinstance(ret["nrp3"]["iosxr1"]["run_ttp"]["netbox_data"], dict), "Unexpected parsing results"
    assert ret["nrp3"]["iosxr1"]["run_ttp"]["netbox_data"], "Empty parsing results"
    
@skip_if_not_has_netbox
def test_netbox_update_config_context():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["update_config_context"], 
        kwarg={
            "FB": "iosxr1"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert "Configuration Context data updated" in ret["nrp3"]["iosxr1"]
    
@skip_if_not_has_netbox
def test_netbox_update_config_context_no_device_in_netbox():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.netbox", 
        arg=["update_config_context"], 
        kwarg={
            "FB": "ceos2"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert "ERROR" in ret["nrp1"]["ceos2"] and "device not found" in ret["nrp1"]["ceos2"]
    
@skip_if_not_has_netbox
def test_netbox_update_vrf():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["update_vrf"], 
        kwarg={
            "FB": "iosxr1"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert all(
        i in ret["nrp3"] 
        for i in [
            "Hosts processed", "Created RT", "Updated RT", 
            "Created VRF", "Updated VRF"
        ]
    )