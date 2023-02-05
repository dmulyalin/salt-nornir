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
            "field": "device_list",
            "filters": {"name": "ceos1"},
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
    assert all(k in ret["nrp3"]["eth8"]["cable"] for k in ["status", "type", "tenant", "length"])
    assert ret["nrp3"]["eth2"]["breakout"] == True, "eth2 should indicate breakout cable"
    assert ret["nrp3"]["eth8"]["reachable"] == True, "eth8 reachable status should be True"
    assert ret["nrp3"]["eth7"]["remote_termination_type"] == "frontport", "eth7 should be connected to patch panel"
    assert ret["nrp3"]["eth101"]["remote_termination_type"] == "circuittermination"
    assert "circuit" in ret["nrp3"]["eth101"], "eth01 should have circuit data"
    
    
@skip_if_not_has_netbox
def test_netbox_get_connections_with_trace():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_connections"], 
        kwarg={
            "device_name": "fceos4",
            "trace": True
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert len(ret["nrp3"]) > 0, "No connections returned for fceos4"
    assert ret["nrp3"]["eth7"]["reachable"] == False, "eth7 reachable status should be False"
    assert len(ret["nrp3"]["eth7"]["cables"])== 3, "eth7 should have 3 cables"
    assert len(ret["nrp3"]["eth101"]["cables"]) == 2, "eth101 should have 2 cables"
    assert "PowerOutlet-1" in ret["nrp3"], "No power connections retrieved?"
    assert ret["nrp3"]["PowerOutlet-1"]["remote_termination_type"] == "powerport"
    
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
    
@skip_if_not_has_netbox
def test_netbox_query_string():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.netbox", 
        arg=["query"], 
        kwarg={
            "query_string": 'query{device_list(platform: "eos") {name}}'
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert isinstance(ret["nrp1"]["device_list"], list)
    assert len(ret["nrp1"]["device_list"]) > 0
    assert all("name" in i for i in ret["nrp1"]["device_list"])
    
@skip_if_not_has_netbox
def test_netbox_queries_dictionary_and_aliasing():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.netbox", 
        arg=["query"], 
        kwarg={
            "queries": {"devices": {"field": "device_list", "filters": {"platform": "eos"}, "fields": ["name"]}}
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert isinstance(ret["nrp1"]["devices"], list)
    assert len(ret["nrp1"]["devices"]) > 0
    assert all("name" in i for i in ret["nrp1"]["devices"])
    
@skip_if_not_has_netbox
def test_netbox_rest_using_args():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["rest", "get", "dcim/interfaces"], 
        kwarg={
            "params": {"device": "fceos4"}
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert isinstance(ret["nrp3"]["results"], list), "Non list data returned"
    assert all(i["device"]["name"] == "fceos4" for i in ret["nrp3"]["results"]), "Not all interfaces belong to fceos4"
    
@skip_if_not_has_netbox
def test_netbox_rest_using_kwargs():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["rest"], 
        kwarg={
            "params": {"device": "fceos4"},
            "method": "get",
            "api": "dcim/interfaces"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert isinstance(ret["nrp3"]["results"], list), "Non list data returned"
    assert all(i["device"]["name"] == "fceos4" for i in ret["nrp3"]["results"]), "Not all interfaces belong to fceos4"