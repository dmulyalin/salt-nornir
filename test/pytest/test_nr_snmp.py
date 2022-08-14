import logging
import pprint
import time
import pytest
import socket
import random

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
    
    
def test_nr_snmp_puresnmp_dir():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["dir"],
        kwarg={"plugin": "puresnmp"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "dir" in data, f"No 'dir' output from '{host_name}'"
        assert isinstance(data["dir"], list)
        assert all("Traceback" not in i for i in data["dir"])
        
 
def test_nr_snmp_puresnmp_help():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["help"],
        kwarg={"method_name": "set"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "help" in data, f"No 'help' output from '{host_name}'"
        assert isinstance(data["help"], str)
        assert "Traceback" not in data["help"]
        
def test_nr_snmp_puresnmp_get():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["get"],
        kwarg={
            "oid": "1.3.6.1.2.1.1.1.0", 
            "add_details": True,
            "plugin": "puresnmp"
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "get" in data, f"No snmp 'get' output from '{host_name}'"
        assert isinstance(data["get"]["result"], dict)
        assert "Traceback" not in data["get"]["result"]
        assert isinstance(data["get"]["result"]["1.3.6.1.2.1.1.1.0"], str)

    
def test_nr_snmp_puresnmp_multiget():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["multiget"],
        kwarg={
            "oids": ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.2.0"], 
            "add_details": True,
            "plugin": "puresnmp"
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "multiget" in data, f"No snmp 'multiget' output from '{host_name}'"
        assert isinstance(data["multiget"]["result"], dict)
        assert all(
            i in data["multiget"]["result"] 
            for i in ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.2.0"]
        )
        
        
def test_nr_snmp_puresnmp_bulkget():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["bulkget"],
        kwarg={
            "scalar_oids": ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.2.0"],
            "repeating_oids": ["1.3.6.1.2.1.3.1"],
            "plugin": "puresnmp"
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "bulkget" in data, f"No snmp 'bulkget' output from '{host_name}'"
        assert isinstance(data["bulkget"], dict)
        assert len(data["bulkget"]["scalars"]) > 0
        assert len(data["bulkget"]["listing"]) > 0
        
        
def test_nr_snmp_puresnmp_getnext():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["getnext"],
        kwarg={
            "oid": "1.3.6.1.2.1.1.1.0", 
            "add_details": True,
            "plugin": "puresnmp"
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "getnext" in data, f"No snmp 'getnext' output from '{host_name}'"
        assert isinstance(data["getnext"]["result"], dict)
        assert "1.3.6.1.2.1.1.1.0" not in data["getnext"]["result"]
        assert len(data["getnext"]["result"]) > 0
        
def test_nr_snmp_puresnmp_walk():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["walk"],
        kwarg={
            "oid": "1.3.6.1.2.1.1", 
            "plugin": "puresnmp"
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "walk" in data, f"No snmp 'walk' output from '{host_name}'"
        assert isinstance(data["walk"], dict)
        assert len(data["walk"]) > 0
        assert "1.3.6.1.2.1.1.1.0" in data["walk"]
        
        
def test_nr_snmp_puresnmp_multiwalk():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["multiwalk"],
        kwarg={
            "oids": ["1.3.6.1.2.1.1.1", "1.3.6.1.2.1.1.5"], 
            "plugin": "puresnmp"
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "multiwalk" in data, f"No snmp 'multiwalk' output from '{host_name}'"
        assert isinstance(data["multiwalk"], dict)
        assert len(data["multiwalk"]) > 0
        assert "1.3.6.1.2.1.1.1.0" in data["multiwalk"]
        assert "1.3.6.1.2.1.1.5.0" in data["multiwalk"]
        
        
def test_nr_snmp_puresnmp_bulkwalk():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["bulkwalk"],
        kwarg={
            "oids": ["1.3.6.1.2.1.1.1", "1.3.6.1.2.1.1.5"], 
            "plugin": "puresnmp",
            "bulk_size": 10
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "bulkwalk" in data, f"No snmp 'bulkwalk' output from '{host_name}'"
        assert isinstance(data["bulkwalk"], dict)
        assert len(data["bulkwalk"]) > 0
        assert "1.3.6.1.2.1.1.1.0" in data["bulkwalk"]
        assert "1.3.6.1.2.1.1.5.0" in data["bulkwalk"]
        
        
def test_nr_snmp_puresnmp_table():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["table"],
        kwarg={
            "oid": "1.3.6.1.2.1.2.2.1", 
            "plugin": "puresnmp",
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "table" in data, f"No snmp 'table' output from '{host_name}'"
        assert isinstance(data["table"], dict)
        assert len(data["table"]) > 0
        assert "1.3.6.1.2.1.2.2.1" in data["table"]
        assert len(data["table"]["1.3.6.1.2.1.2.2.1"]) > 2
        assert isinstance(data["table"]["1.3.6.1.2.1.2.2.1"], list)
        assert isinstance(data["table"]["1.3.6.1.2.1.2.2.1"][0], dict)
        
        
def test_nr_snmp_puresnmp_bulktable():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["bulktable"],
        kwarg={
            "oid": "1.3.6.1.2.1.2.2.1", 
            "plugin": "puresnmp",
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "bulktable" in data, f"No snmp 'bulktable' output from '{host_name}'"
        assert isinstance(data["bulktable"], dict)
        assert len(data["bulktable"]) > 0
        assert "1.3.6.1.2.1.2.2.1" in data["bulktable"]
        assert len(data["bulktable"]["1.3.6.1.2.1.2.2.1"]) > 2
        assert isinstance(data["bulktable"]["1.3.6.1.2.1.2.2.1"], dict)

        
def test_nr_snmp_puresnmp_set():
    rand_int = random.randint(1,10000)
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["set"],
        kwarg={
            "oid": "1.3.6.1.2.1.1.4.0", 
            "plugin": "puresnmp",
            "value": f"new contact value {rand_int}"
        },
        tgt_type="glob",
        timeout=60,
    )
    ret_get = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["get"],
        kwarg={
            "oid": "1.3.6.1.2.1.1.4.0", 
            "plugin": "puresnmp",
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    pprint.pprint(ret_get)
    # verify set operation
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "set" in data, f"No snmp 'set' output from '{host_name}'"
        assert isinstance(data["set"], dict)
        assert "1.3.6.1.2.1.1.4.0" in data["set"]
        assert str(rand_int) in data["set"]["1.3.6.1.2.1.1.4.0"]
    # verify value set using result of get operation
    for host_name, data in ret_get["nrp1"].items():
        assert str(rand_int) in data["get"]["1.3.6.1.2.1.1.4.0"], f"{rand_int} Value not present in get-ed contact config"
    
    
def test_nr_snmp_puresnmp_multiset():
    rand_int = random.randint(1,10000)
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["multiset"],
        kwarg={
            "mappings": {
                "1.3.6.1.2.1.1.4.0": f"new contact value {rand_int}",
                "1.3.6.1.2.1.1.6.0": f"new location {rand_int}",
            },
            "plugin": "puresnmp",
        },
        tgt_type="glob",
        timeout=60,
    )
    ret_get = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["multiget"],
        kwarg={
            "oids": ["1.3.6.1.2.1.1.4.0", "1.3.6.1.2.1.1.6.0"], 
            "plugin": "puresnmp",
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    pprint.pprint(ret_get)
    # verify set operation
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "multiset" in data, f"No snmp 'multiset' output from '{host_name}'"
        assert isinstance(data["multiset"], dict)
        assert str(rand_int) in data["multiset"]["1.3.6.1.2.1.1.4.0"]
        assert str(rand_int) in data["multiset"]["1.3.6.1.2.1.1.6.0"]
    # verify value set using result of get operation
    for host_name, data in ret_get["nrp1"].items():
        assert str(rand_int) in data["multiget"]["1.3.6.1.2.1.1.4.0"], f"{rand_int} Value not present in get-ed contact config"
        assert str(rand_int) in data["multiget"]["1.3.6.1.2.1.1.6.0"], f"{rand_int} Value not present in get-ed location config"
        
        
def test_nr_snmp_puresnmp_get_render():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["get"],
        kwarg={
            "oid": "{{ host.oid.get_os }}", 
            "add_details": True,
            "plugin": "puresnmp"
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "get" in data, f"No snmp 'get' output from '{host_name}'"
        assert isinstance(data["get"]["result"], dict)
        assert "Traceback" not in data["get"]["result"]
        assert isinstance(data["get"]["result"]["1.3.6.1.2.1.1.1.0"], str)
        
        
def test_nr_snmp_puresnmp_multiget_render():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.snmp",
        arg=["multiget"],
        kwarg={
            "oids": ["{{ host.oid.get_os }}", "{{ host.oid.get_hostname }}"], 
            "add_details": True,
            "plugin": "puresnmp"
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "multiget" in data, f"No snmp 'multiget' output from '{host_name}'"
        assert isinstance(data["multiget"]["result"], dict)
        assert all(
            i in data["multiget"]["result"] 
            for i in ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.5.0"]
        )