import logging
import pprint
import pytest

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


def test_tping_call_with_no_args():
    ret = client.cmd(
        tgt="nrp1", fun="nr.tping", arg=[], kwarg={}, tgt_type="glob", timeout=60
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    task_name = "nornir_salt.plugins.tasks.tcp_ping"
    for host_name, data in ret["nrp1"].items():
        assert task_name in data, "No 'tping' output from '{}'".format(host_name)
        assert isinstance(data[task_name], dict)
        assert isinstance(data[task_name][22], bool)


def test_tping_call_with_unreachable_ports():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.tping",
        arg=[],
        kwarg={"ports": [777, 888]},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    task_name = "nornir_salt.plugins.tasks.tcp_ping"
    for host_name, data in ret["nrp1"].items():
        assert task_name in data, "No 'tping' output from '{}'".format(host_name)
        assert isinstance(data[task_name], dict)
        assert data[task_name][777] is False
        assert data[task_name][888] is False
