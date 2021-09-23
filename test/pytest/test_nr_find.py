import logging
import pprint
import pytest
import os
import time

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
    
def _learn_staff():
    return client.cmd(
        tgt="nrp1",
        fun="nr.learn",
        arg=["interfaces", "facts"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    
def test_nr_find_interfaces_all(): 
    # generate some data
    _clean_files()
    _learn_staff()

    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.find",
        arg=["interfaces"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
        
    # pprint.pprint(ret)
    
    assert isinstance(ret["nrp1"], str)
    assert len(ret["nrp1"].splitlines()) >=10
    assert ret["nrp1"].count("  ceos1   ") >= 4
    assert ret["nrp1"].count("  ceos2   ") >= 4
    
# test_nr_find_interfaces_all()


def test_nr_find_interfaces_and_facts_all():  
    # generate some data
    _clean_files()
    _learn_staff()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.find",
        arg=["interfaces", "facts"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
        
    pprint.pprint(ret)
    
    assert isinstance(ret["nrp1"], str), "Returned non string data"
    assert len(ret["nrp1"].splitlines()) >=12, "Not all data returned"
    assert ret["nrp1"].count(" interfaces ") >= 8, "Not all interfaces returned"
    assert ret["nrp1"].count(" facts ") == 2, "Not all facts returned"
    assert ret["nrp1"].count(" ceos1 ") == 5
    assert ret["nrp1"].count(" ceos2 ") == 5
    
# test_nr_find_interfaces_and_facts_all()


def test_nr_find_interfaces_and_facts_all_ceos1_only():    
    # generate some data
    _clean_files()
    _learn_staff()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.find",
        arg=["interfaces", "facts"],
        kwarg={"FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
        
    pprint.pprint(ret)
    
    assert isinstance(ret["nrp1"], str), "Returned non string data"
    assert len(ret["nrp1"].splitlines()) >=7, "Not all data returned"
    assert ret["nrp1"].count(" interfaces ") >= 4, "Not all interfaces returned"
    assert ret["nrp1"].count(" facts ") == 1, "Not all facts returned"
    assert ret["nrp1"].count(" ceos1 ") == 5
    assert ret["nrp1"].count(" ceos2 ") == 0
    
# test_nr_find_interfaces_and_facts_all_ceos1_only()


def test_nr_find_interfaces_and_facts_all_last_2():    
    # generate some data
    _clean_files()
    _learn_staff()
    _learn_staff()
    
    # check 
    ret_last_1 = client.cmd(
        tgt="nrp1",
        fun="nr.find",
        arg=["interfaces", "facts"],
        kwarg={"last": 1},
        tgt_type="glob",
        timeout=60,
    )

    ret_last_2 = client.cmd(
        tgt="nrp1",
        fun="nr.find",
        arg=["interfaces", "facts"],
        kwarg={"last": 2},
        tgt_type="glob",
        timeout=60,
    )
    
    # pprint.pprint(ret_last_1)
    # pprint.pprint(ret_last_2)
    
    assert ret_last_1 != ret_last_2, "Last 2 returned same data as last 1"

    assert isinstance(ret_last_1["nrp1"], str), "Last 1 returned non string data"
    assert len(ret_last_1["nrp1"].splitlines()) >=12, "Last 1 not all data returned"
    assert ret_last_1["nrp1"].count(" interfaces ") >= 8, "Last 1  Not all interfaces returned"
    assert ret_last_1["nrp1"].count(" facts ") == 2, "Last 1  Not all facts returned"
    assert ret_last_1["nrp1"].count(" ceos1 ") == 5
    assert ret_last_1["nrp1"].count(" ceos2 ") == 5

    
    assert isinstance(ret_last_2["nrp1"], str), "Last 1 returned non string data"
    assert len(ret_last_2["nrp1"].splitlines()) >=12, "Last 1 not all data returned"
    assert ret_last_2["nrp1"].count(" interfaces ") >= 8, "Last 1  Not all interfaces returned"
    assert ret_last_2["nrp1"].count(" facts ") == 2, "Last 1  Not all facts returned"
    assert ret_last_2["nrp1"].count(" ceos1 ") == 5
    assert ret_last_2["nrp1"].count(" ceos2 ") == 5
    
# test_nr_find_interfaces_and_facts_all_last_2()


def test_nr_find_interfaces_with_filter():    
    # generate some data
    _clean_files()
    _learn_staff()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.find",
        arg=["interfaces"],
        kwarg={"ip": "10.0*"},
        tgt_type="glob",
        timeout=60,
    )

    # pprint.pprint(ret)
               
    assert isinstance(ret["nrp1"], str)
    assert ret["nrp1"].count(" ceos1 ") == 1
    assert ret["nrp1"].count(" ceos2 ") == 1
    assert len(ret["nrp1"].splitlines()) >=4
    
# test_nr_find_interfaces_with_filter_glob()


def test_nr_find_interfaces_with_filter_glob_last_2():    
    # generate some data
    _clean_files()
    _learn_staff()
    _learn_staff()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.find",
        arg=["interfaces"],
        kwarg={"ip__glob": "10.0*", "last": 2},
        tgt_type="glob",
        timeout=60,
    )

    # pprint.pprint(ret)
               
    assert isinstance(ret["nrp1"], str)
    assert ret["nrp1"].count(" ceos1 ") == 1
    assert ret["nrp1"].count(" ceos2 ") == 1
    assert len(ret["nrp1"].splitlines()) >=4
    
# test_nr_find_interfaces_with_filter_glob_last_2()


def test_nr_find_interfaces_with_filter_and_headers():   
    # generate some data
    _clean_files()
    _learn_staff()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.find",
        arg=["interfaces"],
        kwarg={"ip__glob": "10.0*", "headers": "host, interface, ip"},
        tgt_type="glob",
        timeout=60,
    )

    # pprint.pprint(ret)
               
    assert isinstance(ret["nrp1"], str)
    assert ret["nrp1"].count("ceos1 ") == 1
    assert ret["nrp1"].count("ceos2 ") == 1
    assert len(ret["nrp1"].splitlines()) >=4
    assert "timestamp" not in ret["nrp1"]
    
# test_nr_find_interfaces_with_filter_and_headers()


def test_nr_find_interfaces_with_filter_and_table_is_false():   
    # generate some data
    _clean_files()
    _learn_staff()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.find",
        arg=["interfaces"],
        kwarg={"ip__glob": "10.0*", "table": False},
        tgt_type="glob",
        timeout=60,
    )

    pprint.pprint(ret)
               
    assert isinstance(ret["nrp1"], dict)
    assert len(ret["nrp1"]["ceos1"]["run_ttp"]) == 1
    assert len(ret["nrp1"]["ceos2"]["run_ttp"]) == 1
    
# test_nr_find_interfaces_with_filter_and_table_is_false()


def test_nr_find_interfaces_with_filter_non_existing_key():   
    # generate some data
    _clean_files()
    _learn_staff()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.find",
        arg=["interfaces"],
        kwarg={"ipv4__glob": "10.0*"},
        tgt_type="glob",
        timeout=60,
    )

    # pprint.pprint(ret)
               
    assert isinstance(ret["nrp1"], str)
    assert len(ret["nrp1"]) == 0
    assert len(ret["nrp1"]) == 0
    
# test_nr_find_interfaces_with_filter_non_existing_key()