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
            "hosts": ["fceos4"]
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    # check if inventory items added
    assert len(ret["nrp3"]["fceos4"]["eth1"]["inventory_items"]) > 0, "No inventory items returned for fceos4 eth1 interface"
    assert all(k in ret["nrp3"]["fceos4"]["eth1"]["inventory_items"][0] for k in ["name", "role", "manufacturer"])
    assert len(ret["nrp3"]["fceos4"]["eth3"]["inventory_items"]) > 0, "No inventory items returned for fceos4 eth1 interface"
    assert all(k in ret["nrp3"]["fceos4"]["eth3"]["inventory_items"][0] for k in ["name", "role", "manufacturer"])
    # check if ip addresses added
    assert len(ret["nrp3"]["fceos4"]["loopback0"]["ip_addresses"]) > 0, "No ip addresses returned for fceos4 loopback0 interface"
    assert all(k in ret["nrp3"]["fceos4"]["loopback0"]["ip_addresses"][0] for k in ["address", "role", "status"])
    
    
@skip_if_not_has_netbox
def test_netbox_get_interfaces_cache_false():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_interfaces"], 
        kwarg={
            "add_ip": True,
            "add_inventory_items": True,
            "hosts": ["fceos4"],
            "cache": False
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    # check if inventory items added
    assert len(ret["nrp3"]["fceos4"]["eth1"]["inventory_items"]) > 0, "No inventory items returned for fceos4 eth1 interface"
    assert all(k in ret["nrp3"]["fceos4"]["eth1"]["inventory_items"][0] for k in ["name", "role", "manufacturer"])
    assert len(ret["nrp3"]["fceos4"]["eth3"]["inventory_items"]) > 0, "No inventory items returned for fceos4 eth1 interface"
    assert all(k in ret["nrp3"]["fceos4"]["eth3"]["inventory_items"][0] for k in ["name", "role", "manufacturer"])
    # check if ip addresses added
    assert len(ret["nrp3"]["fceos4"]["loopback0"]["ip_addresses"]) > 0, "No ip addresses returned for fceos4 loopback0 interface"
    assert all(k in ret["nrp3"]["fceos4"]["loopback0"]["ip_addresses"][0] for k in ["address", "role", "status"])


@skip_if_not_has_netbox
def test_netbox_get_interfaces_cache_refresh():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_interfaces"], 
        kwarg={
            "add_ip": True,
            "add_inventory_items": True,
            "hosts": ["fceos4"],
            "cache": "refresh"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    # check if inventory items added
    assert len(ret["nrp3"]["fceos4"]["eth1"]["inventory_items"]) > 0, "No inventory items returned for fceos4 eth1 interface"
    assert all(k in ret["nrp3"]["fceos4"]["eth1"]["inventory_items"][0] for k in ["name", "role", "manufacturer"])
    assert len(ret["nrp3"]["fceos4"]["eth3"]["inventory_items"]) > 0, "No inventory items returned for fceos4 eth1 interface"
    assert all(k in ret["nrp3"]["fceos4"]["eth3"]["inventory_items"][0] for k in ["name", "role", "manufacturer"])
    # check if ip addresses added
    assert len(ret["nrp3"]["fceos4"]["loopback0"]["ip_addresses"]) > 0, "No ip addresses returned for fceos4 loopback0 interface"
    assert all(k in ret["nrp3"]["fceos4"]["loopback0"]["ip_addresses"][0] for k in ["address", "role", "status"])
    
@skip_if_not_has_netbox
def test_netbox_get_interfaces_fb_filter():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_interfaces"], 
        kwarg={
            "add_ip": True,
            "add_inventory_items": True,
            "FB": "fceos4"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    # check if inventory items added
    assert len(ret["nrp3"]["fceos4"]["eth1"]["inventory_items"]) > 0, "No inventory items returned for fceos4 eth1 interface"
    assert all(k in ret["nrp3"]["fceos4"]["eth1"]["inventory_items"][0] for k in ["name", "role", "manufacturer"])
    assert len(ret["nrp3"]["fceos4"]["eth3"]["inventory_items"]) > 0, "No inventory items returned for fceos4 eth1 interface"
    assert all(k in ret["nrp3"]["fceos4"]["eth3"]["inventory_items"][0] for k in ["name", "role", "manufacturer"])
    # check if ip addresses added
    assert len(ret["nrp3"]["fceos4"]["loopback0"]["ip_addresses"]) > 0, "No ip addresses returned for fceos4 loopback0 interface"
    assert all(k in ret["nrp3"]["fceos4"]["loopback0"]["ip_addresses"][0] for k in ["address", "role", "status"])
    
    
@skip_if_not_has_netbox
def test_netbox_get_connections():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_connections"], 
        kwarg={
            "hosts": ["fceos4"]
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert len(ret["nrp3"]["fceos4"]) > 0, "No connections returned for fceos4"
    assert all(k in ret["nrp3"]["fceos4"] for k in ["ConsolePort1", "eth1", "eth2", "eth8"])
    assert all(k in ret["nrp3"]["fceos4"]["eth8"]["cable"] for k in ["status", "type", "tenant", "length"])
    assert ret["nrp3"]["fceos4"]["eth2"]["breakout"] == True, "eth2 should indicate breakout cable"
    assert ret["nrp3"]["fceos4"]["eth8"]["reachable"] == True, "eth8 reachable status should be True"
    assert ret["nrp3"]["fceos4"]["eth7"]["remote_termination_type"] == "frontport", "eth7 should be connected to patch panel"
    assert ret["nrp3"]["fceos4"]["eth101"]["remote_termination_type"] == "circuittermination"
    assert "circuit" in ret["nrp3"]["fceos4"]["eth101"], "eth01 should have circuit data"
    

@skip_if_not_has_netbox
def test_netbox_get_connections_cache_false():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_connections"], 
        kwarg={
            "hosts": ["fceos4"],
            "cache": False
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert len(ret["nrp3"]["fceos4"]) > 0, "No connections returned for fceos4"
    assert all(k in ret["nrp3"]["fceos4"] for k in ["ConsolePort1", "eth1", "eth2", "eth8"])
    assert all(k in ret["nrp3"]["fceos4"]["eth8"]["cable"] for k in ["status", "type", "tenant", "length"])
    assert ret["nrp3"]["fceos4"]["eth2"]["breakout"] == True, "eth2 should indicate breakout cable"
    assert ret["nrp3"]["fceos4"]["eth8"]["reachable"] == True, "eth8 reachable status should be True"
    assert ret["nrp3"]["fceos4"]["eth7"]["remote_termination_type"] == "frontport", "eth7 should be connected to patch panel"
    assert ret["nrp3"]["fceos4"]["eth101"]["remote_termination_type"] == "circuittermination"
    assert "circuit" in ret["nrp3"]["fceos4"]["eth101"], "eth01 should have circuit data"
    
    
@skip_if_not_has_netbox
def test_netbox_get_connections_cache_refresh():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_connections"], 
        kwarg={
            "hosts": ["fceos4"],
            "cache": "refresh"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert len(ret["nrp3"]["fceos4"]) > 0, "No connections returned for fceos4"
    assert all(k in ret["nrp3"]["fceos4"] for k in ["ConsolePort1", "eth1", "eth2", "eth8"])
    assert all(k in ret["nrp3"]["fceos4"]["eth8"]["cable"] for k in ["status", "type", "tenant", "length"])
    assert ret["nrp3"]["fceos4"]["eth2"]["breakout"] == True, "eth2 should indicate breakout cable"
    assert ret["nrp3"]["fceos4"]["eth8"]["reachable"] == True, "eth8 reachable status should be True"
    assert ret["nrp3"]["fceos4"]["eth7"]["remote_termination_type"] == "frontport", "eth7 should be connected to patch panel"
    assert ret["nrp3"]["fceos4"]["eth101"]["remote_termination_type"] == "circuittermination"
    assert "circuit" in ret["nrp3"]["fceos4"]["eth101"], "eth01 should have circuit data"
    
    
@skip_if_not_has_netbox
def test_netbox_get_connections_fb_filter():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_connections"], 
        kwarg={
            "FB": "fceos4"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert len(ret["nrp3"]["fceos4"]) > 0, "No connections returned for fceos4"
    assert all(k in ret["nrp3"]["fceos4"] for k in ["ConsolePort1", "eth1", "eth2", "eth8"])
    assert all(k in ret["nrp3"]["fceos4"]["eth8"]["cable"] for k in ["status", "type", "tenant", "length"])
    assert ret["nrp3"]["fceos4"]["eth2"]["breakout"] == True, "eth2 should indicate breakout cable"
    assert ret["nrp3"]["fceos4"]["eth8"]["reachable"] == True, "eth8 reachable status should be True"
    assert ret["nrp3"]["fceos4"]["eth7"]["remote_termination_type"] == "frontport", "eth7 should be connected to patch panel"
    assert ret["nrp3"]["fceos4"]["eth101"]["remote_termination_type"] == "circuittermination"
    assert "circuit" in ret["nrp3"]["fceos4"]["eth101"], "eth01 should have circuit data"
    
    
@skip_if_not_has_netbox
def test_netbox_get_connections_with_trace():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_connections"], 
        kwarg={
            "hosts": ["fceos4"],
            "trace": True
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert len(ret["nrp3"]["fceos4"]) > 0, "No connections returned for fceos4"
    assert ret["nrp3"]["fceos4"]["eth7"]["reachable"] == False, "eth7 reachable status should be False"
    assert len(ret["nrp3"]["fceos4"]["eth7"]["cables"])== 3, "eth7 should have 3 cables"
    assert len(ret["nrp3"]["fceos4"]["eth101"]["cables"]) == 2, "eth101 should have 2 cables"
    assert "PowerOutlet-1" in ret["nrp3"]["fceos4"], "No power connections retrieved?"
    assert ret["nrp3"]["fceos4"]["PowerOutlet-1"]["remote_termination_type"] == "powerport"
    
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
            "query_string": 'query{device_list(name__ic: "ceos1") {name}}'
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
            "queries": {"devices": {"field": "device_list", "filters": {"name__ic": "eos"}, "fields": ["name"]}}
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
    
    
@skip_if_not_has_netbox
def test_netbox_get_interfaces_sync():
    update_ceos = client.cmd(
        tgt="nrp1", 
        fun="nr.nornir", 
        arg=["inventory", "update_host"], 
        kwarg={
            "data": {
                "interfaces": []
            },
            "name": "ceos1",
        },
        tgt_type="glob", 
        timeout=60
    )
    print("Deleted ceos interfaces data:")
    pprint.pprint(update_ceos)
    sync_ret = client.cmd(
        tgt="nrp1", 
        fun="nr.netbox", 
        arg=["get_interfaces"], 
        kwarg={
            "sync": True,
            "hosts": ["ceos1"]
        },
        tgt_type="glob", 
        timeout=60
    )
    print("Updated ceos interfaces:")
    pprint.pprint(sync_ret)
    updated_inventory = client.cmd(
        tgt="nrp1", 
        fun="nr.nornir", 
        arg=["inventory"], 
        kwarg={"FB": "ceos1"},
        tgt_type="glob", 
        timeout=60
    )
    print("Ceos inventory:")
    pprint.pprint(updated_inventory)
    
    assert sync_ret["nrp1"]["nornir-worker-1"] == [{"ceos1": True}]
    assert sync_ret["nrp1"]["nornir-worker-2"] == [{"ceos1": True}]    
    assert sync_ret["nrp1"]["nornir-worker-3"] == [{"ceos1": True}]    
    assert "loopback0" in updated_inventory["nrp1"]["hosts"]["ceos1"]["data"]["interfaces"]    
    
    
@skip_if_not_has_netbox
def test_netbox_get_connections_sync():
    update_ceos = client.cmd(
        tgt="nrp3", 
        fun="nr.nornir", 
        arg=["inventory", "update_host"], 
        kwarg={
            "data": {
                "connections": []
            },
            "name": "fceos4",
        },
        tgt_type="glob", 
        timeout=60
    )
    print("Deleted fceos interfaces data:")
    pprint.pprint(update_ceos)
    sync_ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_connections"], 
        kwarg={
            "sync": True,
            "hosts": ["fceos4"]
        },
        tgt_type="glob", 
        timeout=60
    )
    print("Updated ceos interfaces:")
    pprint.pprint(sync_ret)
    updated_inventory = client.cmd(
        tgt="nrp3", 
        fun="nr.nornir", 
        arg=["inventory"], 
        kwarg={"FB": "fceos4"},
        tgt_type="glob", 
        timeout=60
    )
    print("Ceos inventory:")
    pprint.pprint(updated_inventory)

    assert sync_ret["nrp3"]["nornir-worker-1"] == [{"fceos4": True}]
    assert sync_ret["nrp3"]["nornir-worker-2"] == [{"fceos4": True}]    
    assert sync_ret["nrp3"]["nornir-worker-3"] == [{"fceos4": True}]    
    assert "ConsolePort1" in updated_inventory["nrp3"]["hosts"]["fceos4"]["data"]["connections"]
    assert "eth1" in updated_inventory["nrp3"]["hosts"]["fceos4"]["data"]["connections"] 
    

def test_netbox_get_circuits():
    circuits_fields = [
        "comments",
        "commit_rate",
        "custom_fields",
        "description",
        "interface",
        "is_active",
        "provider",
        "provider_account",
        "remote_device",
        "remote_interface",
        "status",
        "subinterfaces",
        "tags",
        "tenant",
        "type",
    ]
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_circuits"], 
        kwarg={
            "hosts": ["fceos4"]
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    # check circuits data
    assert all(k in ret["nrp3"]["fceos4"] for k in ["CID1", "CID2", "CID3"])
    # CID1 is direct between devices 
    assert all(k in ret["nrp3"]["fceos4"]["CID1"] for k in circuits_fields)
    assert "name" in ret["nrp3"]["fceos4"]["CID1"]["interface"]
    # CID2 is via patchpanels with child interfaces
    assert "eth11.123" in ret["nrp3"]["fceos4"]["CID2"]["subinterfaces"]
    assert "peer_ip" in ret["nrp3"]["fceos4"]["CID2"]["subinterfaces"]["eth11.123"]["ip_addresses"][0], "subinterface peer_ip is missing"
    assert "peer_ip" in ret["nrp3"]["fceos4"]["CID2"]["interface"]["ip_addresses"][0], "interface peer_ip is missing"
    # CID3 goes to provider network
    assert "provider_network" in ret["nrp3"]["fceos4"]["CID3"]
    assert "remote_device" not in ret["nrp3"]["fceos4"]["CID3"]
    
    
def test_netbox_get_circuits_sync_true():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.netbox", 
        arg=["get_circuits"], 
        kwarg={
            "hosts": ["fceos4"],
            "sync": True
        },
        tgt_type="glob", 
        timeout=60
    )
    inventory_data = client.cmd(
        tgt="nrp3", 
        fun="nr.nornir", 
        arg=["inventory"], 
        kwarg={
            "FB": "fceos4",
        },
        tgt_type="glob", 
        timeout=60
    )
    print("get circuits with sync true")
    pprint.pprint(ret)
    print("fceos4 inventory")
    pprint.pprint(inventory_data)
    
    assert ret == {'nrp3': {'nornir-worker-1': [{'fceos4': True}],
                            'nornir-worker-2': [{'fceos4': True}],
                            'nornir-worker-3': [{'fceos4': True}]}}
    assert all(k in inventory_data["nrp3"]["hosts"]["fceos4"]["data"]["circuits"] for k in ["CID1", "CID2", "CID3"])