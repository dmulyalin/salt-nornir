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


def test_all_stats_call():
    ret = client.cmd(
        tgt="nrp1", fun="nr.stats", arg=[], kwarg={}, tgt_type="glob", timeout=60
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"].keys()) > 5


def test_single_stat_call():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.stats",
        arg=[],
        kwarg={"stat": "main_process_pid"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"].keys()) == 1
