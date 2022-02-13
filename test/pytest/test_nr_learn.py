import logging
import pprint
import pytest
import os

log = logging.getLogger(__name__)

try:
    import salt.client

    import salt.exceptions

    HAS_SALT = True
except:
    HAS_SALT = False
    raise SystemExit("SALT Nonrir Tests - failed importing SALT libraries")

if HAS_SALT:
    # initiate execution modules client to run 'salt xyz command' commands
    client = salt.client.LocalClient()

def _clean_files():
    _ = client.cmd(
        tgt="nrp1",
        fun="cmd.run",
        arg=["rm -f -r -d /var/salt-nornir/nrp1/files/*"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    
def _get_files():
    return client.cmd(
        tgt="nrp1",
        fun="cmd.run",
        arg=["ls -l /var/salt-nornir/nrp1/files/"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )

def test_nr_learn_using_nr_do_aliases():
    _clean_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.learn",
        arg=["interfaces", "facts"],
        kwarg={"tf_skip_failed": True},
        tgt_type="glob",
        timeout=60,
    )
    
    files = _get_files()
    
    # pprint.pprint(ret)
    # pprint.pprint(files)
    
    assert ret["nrp1"]["failed"] == False, "nr.do failed"
    assert "facts" in ret["nrp1"]["result"][1], "No facts collected"
    assert "interfaces" in ret["nrp1"]["result"][0], "No interfaces collected"
    assert files["nrp1"].count("facts__") >= 2, "Not all facts files stored"
    assert files["nrp1"].count("interfaces__") >= 2, "Not all interfaces files stored"
    
# test_nr_learn_using_nr_do_aliases()


def test_nr_learn_using_nr_do_aliases():
    _clean_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.learn",
        arg=["interfaces", "facts"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    
    files = _get_files()
    
    # pprint.pprint(ret)
    # pprint.pprint(files)
    
    assert ret["nrp1"]["failed"] == False, "nr.do failed"
    assert "facts" in ret["nrp1"]["result"][1], "No facts collected"
    assert "interfaces" in ret["nrp1"]["result"][0], "No interfaces collected"
    assert files["nrp1"].count("facts__") >= 2, "Not all facts files stored"
    assert files["nrp1"].count("interfaces__") >= 2, "Not all interfaces files stored"
    
# test_nr_learn_using_nr_do_aliases()


def test_nr_learn_using_nr_cli():
    _clean_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.learn",
        arg=["show version"],
        kwarg={"fun": "cli", "tf": "cli_show_version"},
        tgt_type="glob",
        timeout=60,
    )
    
    files = _get_files()
    
    # pprint.pprint(ret)
    # pprint.pprint(files)
    
    assert "show version" in ret["nrp1"]["ceos1"], "No show version output for ceos1"
    assert "show version" in ret["nrp1"]["ceos2"], "No show version output for ceos2"
    assert files["nrp1"].count("cli_show_version__") >= 2, "Not all files stored"
    
# test_nr_learn_using_nr_cli()


def test_nr_learn_using_nr_do_aliases_ceos1_only():
    _clean_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.learn",
        arg=["interfaces", "facts"],
        kwarg={"FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    
    files = _get_files()
    
    # pprint.pprint(ret)
    # pprint.pprint(files)
    
    assert ret["nrp1"]["failed"] == False, "nr.do failed"
    assert "facts" in ret["nrp1"]["result"][1], "No facts collected"
    assert "interfaces" in ret["nrp1"]["result"][0], "No interfaces collected"
    assert files["nrp1"].count("facts__") >= 1, "Not all facts files stored"
    assert files["nrp1"].count("interfaces__") >= 1, "Not all interfaces files stored"
    assert "ceos2" not in files["nrp1"], "Having extra output for ceos2"
    
# test_nr_learn_using_nr_do_aliases_ceos1_only()
