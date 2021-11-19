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
        kwarg={},
    )
    # pprint.pprint(ret)
    assert ret["success"] == True
    assert isinstance(ret["return"]["ceos1"]["show clock"], str)
    assert isinstance(ret["return"]["ceos2"]["show clock"], str)
    
# test_nr_call_cli()


def test_nr_call_cfg():
    ret = runner.cmd(
        fun="nr.call",
        full_return=True,
        arg=["cfg", "logging host 1.2.3.4", "logging host 1.2.3.5"],
        kwarg={"plugin": "netmiko", "show_progress": False},
    )
    # pprint.pprint(ret)
    assert ret["success"] == True
    assert ret["return"]["ceos1"]["netmiko_send_config"]["failed"] == False
    assert ret["return"]["ceos2"]["netmiko_send_config"]["failed"] == False
    assert isinstance(ret["return"]["ceos1"]["netmiko_send_config"]["result"], str) 
    assert isinstance(ret["return"]["ceos2"]["netmiko_send_config"]["result"], str) 
    
# test_nr_call_cfg()