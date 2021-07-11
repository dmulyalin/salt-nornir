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


def test_state_nr_workflow():
    """
    Tests workflow of configuring logging server
    with pre-checks, change, post checks and rollback groups
    """
    # first delete configuration
    ret_0 = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=["no logging host 5.5.5.5"],
        kwarg={"plugin": "netmiko"},
        tgt_type="glob",
        timeout=60,
    )
    # second run state for the first time
    ret_1st = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["nr_workflow_state_1"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # last, run state for the second time to verify run-if statements
    # as it should be idempotent and stop after first pre-check step
    ret_2nd = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["nr_workflow_state_1"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # verify first run
    for v in ret_1st["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 6
        for host_name, steps in v["changes"]["summary"].items():
            assert len(steps) == 5  # check that did 5 steps
            assert (
                list(steps[0].values())[0] == "FAIL"
            )  # check that first step is failed as it was pre-check
            for step in steps[1:]:  # check that status of remaining steps is PASS
                step_name, step_status = list(step.items())[0]
                assert step_status == "PASS", "Host {}, {} step result not PASS".format(
                    host_name, step_name
                )
    # verify second run
    for v in ret_2nd["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 6
        for host_name, steps in v["changes"]["summary"].items():
            assert len(steps) == 1  # check that did 1 step - 1st pre-check
            assert (
                list(steps[0].values())[0] == "PASS"
            )  # check that first step is PASSed as it was pre-check


def test_state_nr_workflow_report_all():
    """
    Tests workflow of configuring logging server
    with pre-checks, change, post checks and rollback groups.
    In addition workflow option report_all=True
    """
    # first delete configuration
    ret_0 = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=["no logging host 5.5.5.5"],
        kwarg={"plugin": "netmiko"},
        tgt_type="glob",
        timeout=60,
    )
    # second run state for the first time
    ret_1st = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["nr_workflow_state_2"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # last, run state for the second time to verify run-if statements
    # as it should be idempotent and stop after first pre-check step
    ret_2nd = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["nr_workflow_state_2"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # verify first run
    for v in ret_1st["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 6
        for host_name, steps in v["changes"]["summary"].items():
            assert len(steps) == 6  # check that have 6 steps due to report_all=True
            assert (
                list(steps[0].values())[0] == "FAIL"
            )  # check that first step is failed as it was pre-check
            for step in steps[1:]:  # check that status of remaining steps is PASS
                step_name, step_status = list(step.items())[0]
                assert step_status in [
                    "PASS",
                    "SKIP",
                ], "Host {}, {} step result not PASS/SKIP".format(host_name, step_name)
    # verify second run
    for v in ret_2nd["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 6
        for host_name, steps in v["changes"]["summary"].items():
            assert len(steps) == 6  # check that have 6 steps due to report_all=True
            for step in steps:  # check that status of remaining steps is PASS
                step_name, step_status = list(step.items())[0]
                assert step_status in [
                    "PASS",
                    "SKIP",
                ], "Host {}, {} step result not PASS/SKIP".format(host_name, step_name)


def test_state_nr_workflow_some_steps_has_report_false():
    """Some of the steps have report=False"""
    pass


def test_state_nr_workflow_with_common_filter():
    """Set FL=ceos1 to run step agains one host only"""
    pass


def test_state_nr_workflow_inline_test_step_to_dict_true():
    """Test when having inline test defined with dictionary results"""
    pass


def test_state_nr_workflow_inline_test_step_to_dict_false():
    """Test when having inline test defined with list results"""
    pass


def test_state_nr_workflow_with_nr_do_steps():
    pass


def test_state_nr_workflow_change_failed_rollback_step_triggered():
    pass
