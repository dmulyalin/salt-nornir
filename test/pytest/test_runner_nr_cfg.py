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

    
# def test_nr_call_cli():
#     ret = runner.cmd(
#         fun="nr.call",
#         full_return=True,
#         arg=["cli", "show clock"],
#         kwarg={"FB": "ceos[12]"},
#     )
#     # pprint.pprint(ret)
#     assert ret["success"] == True
#     assert isinstance(ret["return"]["ceos1"]["show clock"], str)
#     assert isinstance(ret["return"]["ceos2"]["show clock"], str)
#     
# test_nr_call_cli()

def test_runner_nr_cfg_fromdir():
    ret = runner.cmd(
        fun="nr.cfg",
        arg=[],
        kwarg={
            "fromdir": "salt://templates/per_host_cfg_runner_cfg_test/",
            "plugin": "netmiko",
            "progress": False,
            "interactive": False,
            "FB": "ceos*"
        },
    )    
    pprint.pprint(ret)
    assert isinstance(ret, dict)
    assert len(ret) == 2
    for host_name, results in ret.items():
        assert len(results) == 1
        for result in results:
            assert "ceos" in result["result"]
            assert not result["exception"]
            assert result["failed"] == False
            assert "minion_id" in result
    
    
def test_runner_nr_cfg_fromdir_ret_struct_list():
    ret = runner.cmd(
        fun="nr.cfg",
        arg=[],
        kwarg={
            "fromdir": "salt://templates/per_host_cfg_runner_cfg_test/",
            "plugin": "netmiko",
            "progress": False,
            "interactive": False,
            "FB": "ceos*",
            "ret_struct": "list",
        },
    )    
    pprint.pprint(ret)
    assert isinstance(ret, list)
    assert len(ret) == 2
    for result in ret:
        assert "host" in result
        assert not result["exception"]
        assert result["failed"] == False
        assert "minion_id" in result
        
def test_runner_nr_cfg_fromdir_ret_struct_list_table():
    ret = runner.cmd(
        fun="nr.cfg",
        arg=[],
        kwarg={
            "fromdir": "salt://templates/per_host_cfg_runner_cfg_test/",
            "plugin": "netmiko",
            "progress": False,
            "interactive": False,
            "FB": "ceos*",
            "ret_struct": "list",
            "table": "brief",
            "tgt": "nrp1",
            "tgt_type": "glob",
        },
    )    
    pprint.pprint(ret)
    assert isinstance(ret, list)
    assert len(ret) == 1
    for result in ret:
        assert "Traceback" not in result
        assert isinstance(result, str)
        
        
def test_runner_nr_cfg_fromdir_ret_struct_dict_table():
    ret = runner.cmd(
        fun="nr.cfg",
        arg=[],
        kwarg={
            "fromdir": "salt://templates/per_host_cfg_runner_cfg_test/",
            "plugin": "netmiko",
            "progress": False,
            "interactive": False,
            "FB": "ceos*",
            "ret_struct": "dictionary",
            "table": "brief",
            "tgt": "nrp1",
            "tgt_type": "glob",
        },
    )    
    pprint.pprint(ret)
    assert isinstance(ret, dict)
    assert len(ret) == 1
    for result in ret.values():
        assert "Traceback" not in result
        assert isinstance(result, str)