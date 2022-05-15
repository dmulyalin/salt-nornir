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
    
def _generate_files():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"tf": "clock", "tf_skip_failed": True},
        tgt_type="glob",
        timeout=60,
    )
    res = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["interfaces", "uptime"],
        kwarg={"tf": True, "tf_skip_failed": True},
        tgt_type="glob",
        timeout=60,
    ) 

def test_nr_diff_file_diff_last_2_3_ceos1():
    _clean_files()
    _generate_files()
    _generate_files()
    _generate_files()
    
    # check 
    ret_1_2 = client.cmd(
        tgt="nrp1",
        fun="nr.diff",
        arg=["interfaces", "clock"],
        kwarg={"last": [1, 2], "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    ret_2_3 = client.cmd(
        tgt="nrp1",
        fun="nr.diff",
        arg=["interfaces", "clock"],
        kwarg={"last": [2, 3], "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret_1_2)
    # pprint.pprint(ret_2_3)
    
    assert ret_1_2["nrp1"]["ceos1"]["interfaces"] == True
    assert "/clock__" in ret_1_2["nrp1"]["ceos1"]["clock"]
    assert ret_2_3["nrp1"]["ceos1"]["interfaces"] == True
    assert "/clock__" in ret_2_3["nrp1"]["ceos1"]["clock"]
    assert ret_1_2["nrp1"]["ceos1"]["clock"] != ret_2_3["nrp1"]["ceos1"]["clock"]
    
# test_nr_diff_file_diff_last_2_3_ceos1()


def test_nr_diff_diff_processor_last_1_ceos1():
    _clean_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.diff",
        arg=["interfaces", "uptime"],
        kwarg={"last": 1, "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    
    assert ret["nrp1"]["failed"] == False
    assert ret["nrp1"]["result"][0]["interfaces"]["ceos1"]["run_ttp"] == True
    assert "/uptime__" in ret["nrp1"]["result"][1]["uptime"]["ceos1"]["show uptime"] 
    
# test_nr_diff_diff_processor_last_1_ceos1()

def test_nr_diff_diff_processor_no_last_keyword_ceos1():
    _clean_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.diff",
        arg=["interfaces", "uptime"],
        kwarg={"FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    
    assert ret["nrp1"]["failed"] == False
    assert ret["nrp1"]["result"][0]["interfaces"]["ceos1"]["run_ttp"] == True
    assert "/uptime__" in ret["nrp1"]["result"][1]["uptime"]["ceos1"]["show uptime"] 