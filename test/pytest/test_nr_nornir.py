import logging
import pprint

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


def test_nr_inventory_call():
    ret = client.cmd(
        tgt="nrp1", fun="nr.nornir", arg=["inventory"], kwarg={}, tgt_type="glob", timeout=60
    )
    assert (
        "nrp1" in ret
        and "defaults" in ret["nrp1"]
        and "groups" in ret["nrp1"]
        and "hosts" in ret["nrp1"]
        and len(ret["nrp1"]["hosts"]) == 2
    )


def test_nr_inventory_call_FB():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={"FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    assert (
        "nrp1" in ret
        and "defaults" in ret["nrp1"]
        and "groups" in ret["nrp1"]
        and "hosts" in ret["nrp1"]
        and len(ret["nrp1"]["hosts"]) == 1
    )


def test_nr_inventory_call_FL_no_match():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={"FL": ["dummy"]},
        tgt_type="glob",
        timeout=60,
    )
    assert (
        "nrp1" in ret
        and "defaults" in ret["nrp1"]
        and "groups" in ret["nrp1"]
        and "hosts" in ret["nrp1"]
        and len(ret["nrp1"]["hosts"]) == 0
    )

def test_nr_version_call():
    ret = client.cmd(
        tgt="nrp1", fun="nr.nornir", arg=["version"], kwarg={}, tgt_type="glob", timeout=60
    )
    assert "nrp1" in ret
    assert isinstance(ret["nrp1"], str), "Unexpected data type returned"
    assert "Traceback" not in ret["nrp1"], "nr.version returned error"
    
def test_all_stats_call():
    ret = client.cmd(
        tgt="nrp1", fun="nr.nornir", arg=["stats"], kwarg={}, tgt_type="glob", timeout=60
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"].keys()) > 5


def test_single_stat_call():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["stats"],
        kwarg={"stat": "main_process_pid"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"].keys()) == 1

    
def test_connections_list():
    # close connections
    client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        tgt_type="glob",
        timeout=60,
    )    
    # run some cli commands
    client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko"},
        tgt_type="glob",
        timeout=60,
    )
    # list active connections
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert len(ret["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.connections"]) == 1
    assert ret["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.connections"][0]["connection_name"] == "netmiko"
    assert len(ret["nrp1"]["ceos2"]["nornir_salt.plugins.tasks.connections"]) == 1
    assert ret["nrp1"]["ceos2"]["nornir_salt.plugins.tasks.connections"][0]["connection_name"] == "netmiko"
    
# test_connections_list()


def test_disconnect():
    # run some cli commands
    client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko"},
        tgt_type="glob",
        timeout=60,
    )
    # close connections
    client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        tgt_type="glob",
        timeout=60,
    )   
    # list active connections
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert len(ret["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.connections"]) == 0
    assert len(ret["nrp1"]["ceos2"]["nornir_salt.plugins.tasks.connections"]) == 0
    
# test_disconnect()


def test_disconnect_by_name():
    # close connections
    client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        tgt_type="glob",
        timeout=60,
    ) 
    # run some cli commands
    client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko"},
        tgt_type="glob",
        timeout=60,
    )
    client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "scrapli"},
        tgt_type="glob",
        timeout=60,
    )
    # list active connections
    ret_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        tgt_type="glob",
        timeout=60,
    )
    conn_count_before_ceos1 = len(ret_before["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.connections"])
    conn_count_before_ceos2 = len(ret_before["nrp1"]["ceos2"]["nornir_salt.plugins.tasks.connections"])
    # close connections
    client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={"conn_name": "scrapli", "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )   
    # list active connections
    ret_after = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    conn_count_after_ceos1 = len(ret_after["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.connections"])
    conn_count_after_ceos2 = len(ret_after["nrp1"]["ceos2"]["nornir_salt.plugins.tasks.connections"])
    
    assert conn_count_before_ceos1 == 2 and conn_count_after_ceos1 == 1
    assert conn_count_before_ceos2 == 2 and conn_count_after_ceos2 ==2
    assert ret_after["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.connections"][0]["connection_name"] == "netmiko"
    
# test_disconnect_by_name()