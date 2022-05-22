import logging
import pprint
import pytest
import yaml
import time

from utils import fixture_modify_proxy_pillar

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

    
def test_state_nr_cfg_and_nr_task():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.apply",
        arg=["nr_cfg_syslog_and_ntp_state"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for v in ret["nrp1"].values():
        assert v["result"] == True, "State result is not True"
        assert len(v["changes"]) == 2, "Not all hosts return results"
        for host_name, host_res in v["changes"].items():
            for task_name, task_res in host_res.items():
                if isinstance(task_res, str):
                    assert "Traceback" not in task_res, f"{host_name} task {task_name} result has traceback"
                else:
                    assert task_res["failed"] == False, f"{host_name} has failed task {task_name}"
                    assert "Traceback" not in task_res["result"], f"{host_name} task {task_name} result has traceback"