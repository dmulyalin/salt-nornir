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


def test_nr_network_resolve_dns_failed():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.network",
        arg=["resolve_dns"],
        kwarg={"run_task_retry": 0},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert ret["nrp1"]["ceos1"]["resolve_dns"] == []
    assert ret["nrp1"]["ceos2"]["resolve_dns"] == []
    
    
def test_nr_network_resolve_dns_failed_exception_added():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.network",
        arg=["resolve_dns"],
        kwarg={"add_details": True, "run_task_retry": 0},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert ret["nrp1"]["ceos1"]["resolve_dns"]["result"] == []
    assert ret["nrp1"]["ceos2"]["resolve_dns"]["result"] == []
    assert ret["nrp1"]["ceos1"]["resolve_dns"]["failed"] == True
    assert ret["nrp1"]["ceos2"]["resolve_dns"]["failed"] == True
    assert ret["nrp1"]["ceos1"]["resolve_dns"]["exception"]
    assert ret["nrp1"]["ceos2"]["resolve_dns"]["exception"]
    
    
def test_nr_network_resolve_dns_use_host_name():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.network",
        arg=["resolve_dns"],
        kwarg={"use_host_name": True},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert len(ret["nrp1"]["ceos1"]["resolve_dns"]) > 0
    assert len(ret["nrp1"]["ceos2"]["resolve_dns"]) > 0
    
    
def test_nr_network_resolve_dns():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.network",
        arg=["resolve_dns"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert len(ret["nrp2"]["csr1000v-1"]["resolve_dns"]) > 0
    assert len(ret["nrp2"]["iosxr1"]["resolve_dns"]) > 0
    assert len(ret["nrp2"]["nxos1"]["resolve_dns"]) > 0
    
    
def test_nr_network_resolve_dns_ipv6_failed():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.network",
        arg=["resolve_dns"],
        kwarg={"ipv6": True, "add_details": True, "run_task_retry": 0},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert len(ret["nrp2"]["csr1000v-1"]["resolve_dns"]["result"]) > 0
    assert len(ret["nrp2"]["iosxr1"]["resolve_dns"]["result"]) > 0
    assert len(ret["nrp2"]["nxos1"]["resolve_dns"]["result"]) > 0

    assert ret["nrp2"]["csr1000v-1"]["resolve_dns"]["exception"]
    assert ret["nrp2"]["iosxr1"]["resolve_dns"]["exception"]
    assert ret["nrp2"]["nxos1"]["resolve_dns"]["exception"]

    assert ret["nrp2"]["csr1000v-1"]["resolve_dns"]["failed"] == True
    assert ret["nrp2"]["iosxr1"]["resolve_dns"]["failed"] == True
    assert ret["nrp2"]["nxos1"]["resolve_dns"]["failed"] == True
    

def test_nr_network_resolve_dns_custom_servers():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.network",
        arg=["resolve_dns"],
        kwarg={"servers": ["8.8.8.8"]},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert len(ret["nrp2"]["csr1000v-1"]["resolve_dns"]) > 0
    assert len(ret["nrp2"]["iosxr1"]["resolve_dns"]) > 0
    assert len(ret["nrp2"]["nxos1"]["resolve_dns"]) > 0
    
    
def test_nr_network_resolve_dns_custom_servers_timeout():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.network",
        arg=["resolve_dns"],
        kwarg={"servers": ["127.1.2.3"], "add_details": True, "run_task_retry": 0},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert len(ret["nrp2"]["csr1000v-1"]["resolve_dns"]["result"]) == 0
    assert len(ret["nrp2"]["iosxr1"]["resolve_dns"]["result"]) == 0
    assert len(ret["nrp2"]["nxos1"]["resolve_dns"]["result"]) == 0

    assert ret["nrp2"]["csr1000v-1"]["resolve_dns"]["exception"]
    assert ret["nrp2"]["iosxr1"]["resolve_dns"]["exception"]
    assert ret["nrp2"]["nxos1"]["resolve_dns"]["exception"]

    assert ret["nrp2"]["csr1000v-1"]["resolve_dns"]["failed"] == True
    assert ret["nrp2"]["iosxr1"]["resolve_dns"]["failed"] == True
    assert ret["nrp2"]["nxos1"]["resolve_dns"]["failed"] == True