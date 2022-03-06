import logging
import pprint
import json
import time
log = logging.getLogger(__name__)

try:
    import salt.config
    import salt.runner
    import salt.utils.event
    import salt.exceptions

    HAS_SALT = True
except:
    HAS_SALT = False
    raise SystemExit("SALT Nonrir Tests - failed importing SALT libraries")

if HAS_SALT:
    # initiate runner modules client to run 'salt-run xyz command' commands
    opts = salt.config.client_config("/etc/salt/master")
    event = salt.utils.event.get_event(
        "master", sock_dir=opts["sock_dir"], transport=opts["transport"], opts=opts
    )
    
    # initiate runner modules client to run 'salt "*" command' commands
    opts["quiet"] = True
    runner = salt.runner.RunnerClient(opts)

    
def test_nr_call_cli():
    ret = runner.cmd(
        fun="nr.call",
        full_return=True,
        arg=["cli", "show clock"],
        kwarg={"FB": "ceos[12]"},
    )
    # pprint.pprint(ret)
    assert ret["success"] == True
    assert isinstance(ret["return"]["ceos1"][0]["result"], str)
    assert isinstance(ret["return"]["ceos2"][0]["result"], str)
    
# test_nr_call_cli()


def test_nr_call_cfg():
    ret = runner.cmd(
        fun="nr.call",
        full_return=True,
        arg=["cfg", "logging host 1.2.3.4", "logging host 1.2.3.5"],
        kwarg={"plugin": "netmiko", "progress": False, "FB": "ceos[12]"},
    )
    # pprint.pprint(ret)
    assert ret["success"] == True
    assert ret["return"]["ceos1"][0]["failed"] == False
    assert ret["return"]["ceos2"][0]["failed"] == False
    assert isinstance(ret["return"]["ceos1"][0]["result"], str) 
    assert isinstance(ret["return"]["ceos2"][0]["result"], str) 
    
# test_nr_call_cfg()


def test_nr_call_cli_ret_struct_list():
    ret = runner.cmd(
        fun="nr.call",
        arg=["cli", "show clock"],
        kwarg={"FB": "ceos[12]", "ret_struct": "list"},
    )
    pprint.pprint(ret)
    for i in ret:
        assert i["name"] == "show clock"
        assert "Traceback" not in i["result"]
        assert "minion_id" in i
        assert "host" in i
        
def test_nr_call_cli_multiple_commands_ret_struct_dict():
    ret = runner.cmd(
        fun="nr.call",
        arg=["cli", "show clock", "show hostname"],
        kwarg={"FB": "ceos[12]", "ret_struct": "dictionary"},
    )
    pprint.pprint(ret)
    for hostname, results in ret.items():
        assert len(results) == 2
        for item in results:
            assert "Traceback" not in item["result"]
            assert "minion_id" in item
            assert item["name"] in ["show clock", "show hostname"]
            
def test_nr_call_cli_table_brief_nrp1_only():
    """
    This call should return results for nrp1 only, as this is the minion
    that manages ceos1 and 2.
    """
    ret = runner.cmd(
        fun="nr.call",
        arg=["cli", "show clock", "show hostname"],
        kwarg={"FB": "ceos[12]", "ret_struct": "dictionary", "table": "brief"},
    )
    pprint.pprint(ret)
    assert len(ret) == 1
    assert isinstance(ret["nrp1"], str)
    assert "Traceback" not in ret["nrp1"]
    
def test_nr_call_cli_non_existing_hosts():
    """
    This call should return results for nrp1 only, as this is the minion
    that manages ceos1 and 2.
    """
    ret = runner.cmd(
        fun="nr.call",
        arg=["cli", "show clock", "show hostname"],
        kwarg={"FB": "ceos-foo"},
    )
    pprint.pprint(ret)
    assert "CommandExecutionError: Hosts not found" in ret
    
def test_nr_call_cli_non_existing_minions():
    """
    This call should return results for nrp1 only, as this is the minion
    that manages ceos1 and 2.
    """
    ret = runner.cmd(
        fun="nr.call",
        arg=["cli", "show clock", "show hostname"],
        kwarg={"FB": "ceos*", "tgt": "foo", "tgt_type": "glob"}
    )
    pprint.pprint(ret)
    assert "CommandExecutionError: No minions matched" in ret