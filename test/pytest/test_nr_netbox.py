import logging
import pprint
import time
import pytest
import socket
import requests

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
    
# check if has access to always on sandbox IOSXR device
iosxr_sandbox_router = "sandbox-iosxr-1.cisco.com" 
s = socket.socket()
s.settimeout(5)
try:
    status = s.connect_ex((iosxr_sandbox_router, 830))
    has_sandbox_iosxr = True
except:
    log.exception("Failed to check iosxr_sandbox_router connection.")
    has_sandbox_iosxr = False
s.close()
skip_if_not_has_sandbox_iosxr = pytest.mark.skipif(
    has_sandbox_iosxr == False,
    reason="Has no connection to {} router".format(iosxr_sandbox_router),
)

# check if Netbox endpoint reachable
netbox_url = "http://192.168.64.200:8000/api"
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
    netbox_keys = [
        'airflow', 'asset_tag', 'cluster', 'comments', 'config_context', 'created', 'custom_fields',
        'device_type', 'display', 'face', 'id', 'last_updated', 'local_context_data', 'location',
        'name', 'parent_device', 'platform', 'position', 'primary_ip', 'primary_ip4', 'primary_ip6',
        'rack', 'serial', 'site', 'status', 'tags', 'tenant', 'url', 'vc_position', 'vc_priority',
        'virtual_chassis'
    ]
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
    assert all(k in inventory["nrp1"]["hosts"]["ceos1"]["data"] for k in netbox_keys)
    # any because ceos2 data has location key in it
    assert any(k not in inventory["nrp1"]["hosts"]["ceos2"]["data"] for k in netbox_keys)
    
