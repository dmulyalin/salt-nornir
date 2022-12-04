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
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    # last, run state for the second time to verify run-if statements
    # as it should be idempotent and stop after first pre-check step
    ret_2nd = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["nr_workflow_state_1"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    print("First run results:")
    pprint.pprint(ret_1st)
    print("Second run results:")
    pprint.pprint(ret_2nd)
    # verify first run
    for v in ret_1st["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 5
        # check steps content is correct
        assert "pre_check_if_logging_configured" in v["changes"]["details"][0]
        assert "save_configuration_before" in v["changes"]["details"][1]
        assert "apply_logging_config" in v["changes"]["details"][2]
        assert "post_check_if_logging_configured" in v["changes"]["details"][3]
        assert "save_configuration_after" in v["changes"]["details"][4]
        for host_name, steps in v["changes"]["summary"].items():
            assert len(steps) == 7  # check that did 7 steps including test tasks commands output
            assert (
                list(steps[1].values())[0] == "FAIL"
            )  # check that first step is failed as it was pre-check
            for step in steps[2:]:  # check that status of remaining steps is PASS
                step_name, step_status = list(step.items())[0]
                assert step_status == "PASS", "Host {}, {} step result not PASS".format(
                    host_name, step_name
                )
    # verify second run
    for v in ret_2nd["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 1
        # check steps content is correct
        assert "pre_check_if_logging_configured" in v["changes"]["details"][0]
        for host_name, steps in v["changes"]["summary"].items():
            assert len(steps) == 2  # check that did 1 step - 1st pre-check
            assert (
                list(steps[1].values())[0] == "PASS"
            )  # check that second step is PASSed as it was pre-check
            
# test_state_nr_workflow()

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
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    # last, run state for the second time to verify run-if statements
    # as it should be idempotent and stop after first pre-check step
    ret_2nd = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["nr_workflow_state_2"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    print("ret_1st: ")
    pprint.pprint(ret_1st)
    print("ret_2nd: ")
    pprint.pprint(ret_2nd)
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


def test_state_nr_workflow_run_if_fail_any():
    """ Test run_if_fail_any condition """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_run_if_fail_any"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    # verify run
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 6
        for host_name, steps in v["changes"]["summary"].items():
            assert steps[-1]["apply_ntp_config"] == "SKIP", "{} apply_ntp_config not skipped".format(host_name)
            assert steps[-2]["apply_logging_config"] == "PASS", "{} apply_ntp_config not passed".format(host_name)
            
# test_state_nr_workflow_ran_if_fail_any()
    
def test_state_nr_workflow_run_if_pass_any():
    """ Test run_if_pass_any condition """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_run_if_pass_any"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    # verify run
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 6
        for host_name, steps in v["changes"]["summary"].items():
            assert steps[-1]["apply_ntp_config"] == "SKIP", "{} apply_ntp_config not skipped".format(host_name)
            assert steps[-2]["apply_logging_config"] == "PASS", "{} apply_ntp_config not passed".format(host_name)

# test_state_nr_workflow_run_if_pass_any()

def test_state_nr_workflow_run_if_fail_all():
    """ Test run_if_fail_all condition """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_run_if_fail_all"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # ... expected result ...
    # 'summary': {'ceos1': [{'ceos1_will_fail': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'PASS'},
    #                       {'apply_ntp_config': 'SKIP'}],
    #             'ceos2': [{'ceos1_will_fail': 'PASS'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'SKIP'},
    #                       {'apply_ntp_config': 'SKIP'}]}},
    # verify run
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 6
        assert v["changes"]["summary"]["ceos1"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos1"][-2]["apply_logging_config"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos2"][-2]["apply_logging_config"] == "SKIP"        
            
# test_state_nr_workflow_run_if_fail_all()

def test_state_nr_workflow_run_if_pass_all():
    """ Test run_if_pass_all condition """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_run_if_pass_all"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # ... expected result ...
    # 'summary': {'ceos1': [{'ceos1_will_fail': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'SKIP'},
    #                       {'apply_ntp_config': 'SKIP'}],
    #             'ceos2': [{'ceos1_will_fail': 'PASS'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'PASS'},
    #                       {'apply_ntp_config': 'SKIP'}]}},
    # verify run
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 6
        assert v["changes"]["summary"]["ceos1"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos1"][-2]["apply_logging_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos2"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos2"][-2]["apply_logging_config"] == "PASS"  

# test_state_nr_workflow_run_if_pass_all()


def test_state_nr_workflow_run_if_fail_any_and_all():
    """ Test run_if_fail_all condition """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_run_if_fail_any_and_all"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # ... expected result ...
    # 'summary': {'ceos1': [{'ceos1_will_fail': 'FAIL'},
    #                       {'failed_step_1': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'PASS'},
    #                       {'apply_ntp_config': 'SKIP'}],
    #             'ceos2': [{'ceos1_will_fail': 'PASS'},
    #                       {'failed_step_1': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'SKIP'},
    #                       {'apply_ntp_config': 'SKIP'}]}},
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 7
        assert v["changes"]["summary"]["ceos1"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos1"][-2]["apply_logging_config"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos2"][-2]["apply_logging_config"] == "SKIP" 
        
# test_state_nr_workflow_run_if_fail_any_and_all()

def test_state_nr_workflow_run_if_pass_any_and_all():
    """ Test run_if_fail_all condition """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_run_if_pass_any_and_all"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # ... expected result ...
    # 'summary': {'ceos1': [{'ceos1_will_fail': 'FAIL'},
    #                       {'failed_step_1': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'SKIP'},
    #                       {'apply_ntp_config': 'SKIP'}],
    #             'ceos2': [{'ceos1_will_fail': 'PASS'},
    #                       {'failed_step_1': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'PASS'},
    #                       {'apply_ntp_config': 'SKIP'}]}},   
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 7
        assert v["changes"]["summary"]["ceos1"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos1"][-2]["apply_logging_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos2"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos2"][-2]["apply_logging_config"] == "PASS" 
        
# test_state_nr_workflow_run_if_pass_any_and_all()

def test_state_nr_workflow_run_if_fail_any_and_pass_all():
    """ Test run_if_fail_all condition """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_run_if_fail_any_and_pass_all"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # ... expected result ...
    # 'summary': {'ceos1': [{'ceos1_will_fail': 'FAIL'},
    #                       {'failed_step_1': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'PASS'},
    #                       {'apply_ntp_config': 'SKIP'}],
    #             'ceos2': [{'ceos1_will_fail': 'PASS'},
    #                       {'failed_step_1': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'SKIP'},
    #                       {'apply_ntp_config': 'SKIP'}]}},
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 7
        assert v["changes"]["summary"]["ceos1"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos1"][-2]["apply_logging_config"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos2"][-2]["apply_logging_config"] == "SKIP" 
        
# test_state_nr_workflow_run_if_fail_any_and_pass_all()
    
def test_state_nr_workflow_run_if_pass_any_and_fail_all():
    """ Test run_if_fail_all condition """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_run_if_pass_any_and_fail_all"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # ... expected result ...
    # 'summary': {'ceos1': [{'ceos1_will_fail': 'FAIL'},
    #                       {'failed_step_1': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'SKIP'},
    #                       {'apply_ntp_config': 'PASS'}],
    #             'ceos2': [{'ceos1_will_fail': 'PASS'},
    #                       {'failed_step_1': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'PASS'},
    #                       {'apply_ntp_config': 'SKIP'}]}},
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 7
        assert v["changes"]["summary"]["ceos1"][-1]["apply_ntp_config"] == "PASS"
        assert v["changes"]["summary"]["ceos1"][-2]["apply_logging_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos2"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos2"][-2]["apply_logging_config"] == "PASS" 
        
# test_state_nr_workflow_run_if_pass_any_and_fail_all()

def test_state_nr_workflow_run_if_all_conditions_combined():
    """ Test run_if_fail_all condition """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_run_if_all_conditions_combined"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # ... expected result ...
    # 'summary': {'ceos1': [{'ceos1_will_fail': 'FAIL'},
    #                       {'failed_step_1': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'PASS'},
    #                       {'apply_ntp_config': 'SKIP'}],
    #             'ceos2': [{'ceos1_will_fail': 'PASS'},
    #                       {'failed_step_1': 'FAIL'},
    #                       {'failed_step_2': 'FAIL'},
    #                       {'passed_step_1': 'PASS'},
    #                       {'passed_step_2': 'PASS'},
    #                       {'apply_logging_config': 'SKIP'},
    #                       {'apply_ntp_config': 'PASS'}]}},    
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 7
        assert v["changes"]["summary"]["ceos1"][-1]["apply_ntp_config"] == "SKIP"
        assert v["changes"]["summary"]["ceos1"][-2]["apply_logging_config"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][-1]["apply_ntp_config"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][-2]["apply_logging_config"] == "SKIP" 
        
# test_state_nr_workflow_run_if_all_conditions_combined()

def test_state_nr_workflow_no_run_if_conditions():
    """ Test run_if_fail_all condition """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_no_run_if_conditions"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # ... expected result ...
    # 'summary': {'ceos1': [{'apply_logging_config': 'PASS'},
    #                       {'apply_ntp_config': 'PASS'}],
    #             'ceos2': [{'apply_logging_config': 'PASS'},
    #                       {'apply_ntp_config': 'PASS'}]}},
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 2
        assert v["changes"]["summary"]["ceos1"][-1]["apply_ntp_config"] == "PASS"
        assert v["changes"]["summary"]["ceos1"][-2]["apply_logging_config"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][-1]["apply_ntp_config"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][-2]["apply_logging_config"] == "PASS"
        
# test_state_nr_workflow_no_run_if_conditions()

def test_state_nr_workflow_with_common_filter():
    """Set FL=ceos1 to run step agains one host only"""
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_with_common_filter"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # ... expected result ...
    # 'summary': {'ceos1': [{'apply_logging_config': 'PASS'},
    #                       {'apply_ntp_config': 'PASS'}]}},
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 2
        assert v["changes"]["summary"]["ceos1"][-1]["apply_ntp_config"] == "PASS"
        assert v["changes"]["summary"]["ceos1"][-2]["apply_logging_config"] == "PASS"
        assert "ceos2" not in v["changes"]["summary"]
        
# test_state_nr_workflow_with_common_filter()

def test_state_nr_workflow_with_nr_do_single_step():
    """ Runs steps that use nr.do with single item """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_with_nr_do_single_step"],
        kwarg={""},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # ... expected result ...
    # 'summary': {'ceos1': [{'apply_logging_config_nr_do': 'PASS'}],
    #             'ceos2': [{'apply_logging_config_nr_do': 'PASS'}]}}
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 1
        assert v["changes"]["summary"]["ceos1"][0]["apply_logging_config_nr_do"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][0]["apply_logging_config_nr_do"] == "PASS"
        
# test_state_nr_workflow_with_nr_do_single_step()

def test_state_nr_workflow_with_nr_do_multi_step():
    """ Runs steps that use nr.do with multiple items """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_with_nr_do_multi_step"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # ... expected result ...
    # 'summary': {'ceos1': [{'configure_ntp_nr_do': 'PASS'}],
    #             'ceos2': [{'configure_ntp_nr_do': 'PASS'}]}},
    for v in ret["nrp1"].values():
        assert v["result"] == True
        assert len(v["changes"]["details"]) == 1
        assert len(v["changes"]["details"][0]["configure_ntp_nr_do"]["result"]) == 3
        assert v["changes"]["summary"]["ceos1"][0]["configure_ntp_nr_do"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][0]["configure_ntp_nr_do"] == "PASS"
        
# test_state_nr_workflow_with_nr_do_multi_step()


def test_state_nr_workflow_hcache_usage():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_hcache_usage"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)    
    for v in ret["nrp1"].values():
        assert v["changes"]["summary"]["ceos1"][0]["get_interfaces"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][0]["get_interfaces"] == "PASS"
        assert v["changes"]["summary"]["ceos1"][1]["apply_mtu_config"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][1]["apply_mtu_config"] == "PASS"
        assert "mtu 9200" in v["changes"]["details"][1]["apply_mtu_config"]["ceos1"]["netmiko_send_config"]["result"]
        assert "mtu 9200" in v["changes"]["details"][1]["apply_mtu_config"]["ceos2"]["netmiko_send_config"]["result"]
        
    # verify inventory does not have ceched data
    inventory_data = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(inventory_data)
    assert "get_interfaces" not in inventory_data["nrp1"]["hosts"]["ceos1"]["data"]
    assert "get_interfaces" not in inventory_data["nrp1"]["hosts"]["ceos2"]["data"]
    assert "apply_mtu_config" not in inventory_data["nrp1"]["hosts"]["ceos1"]["data"]
    assert "apply_mtu_config" not in inventory_data["nrp1"]["hosts"]["ceos2"]["data"]
    
# test_state_nr_workflow_hcache_usage()


def test_state_nr_workflow_hcache_key_usage():
    # clean up hcache
    inventory_data = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_hcache"],
        tgt_type="glob",
        timeout=60,
    )
    # run workflow
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_hcache_key_usage"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)    
    for v in ret["nrp1"].values():
        assert v["changes"]["summary"]["ceos1"][0]["get_interfaces"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][0]["get_interfaces"] == "PASS"
        assert v["changes"]["summary"]["ceos1"][1]["apply_mtu_config"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][1]["apply_mtu_config"] == "PASS"
        assert "mtu 9200" in v["changes"]["details"][1]["apply_mtu_config"]["ceos1"]["netmiko_send_config"]["result"]
        assert "mtu 9200" in v["changes"]["details"][1]["apply_mtu_config"]["ceos2"]["netmiko_send_config"]["result"]
        
    # verify inventory contains ceched data after workflow completed
    inventory_data = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(inventory_data)
    assert "cache1234" in inventory_data["nrp1"]["hosts"]["ceos1"]["data"]
    assert "cache1234" in inventory_data["nrp1"]["hosts"]["ceos2"]["data"]
    assert "apply_mtu_config" not in inventory_data["nrp1"]["hosts"]["ceos1"]["data"]
    assert "apply_mtu_config" not in inventory_data["nrp1"]["hosts"]["ceos2"]["data"]
    
# test_state_nr_workflow_hcache_key_usage()


def test_state_nr_workflow_dcache_usage():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_dcache_usage"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)    
    for v in ret["nrp1"].values():
        assert v["changes"]["summary"]["ceos1"][0]["get_interfaces"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][0]["get_interfaces"] == "PASS"
        assert v["changes"]["summary"]["ceos1"][1]["apply_mtu_config"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][1]["apply_mtu_config"] == "PASS"
        assert "mtu 9200" in v["changes"]["details"][1]["apply_mtu_config"]["ceos1"]["netmiko_send_config"]["result"]
        assert "mtu 9200" in v["changes"]["details"][1]["apply_mtu_config"]["ceos2"]["netmiko_send_config"]["result"]
        
    # verify inventory does not have ceched data
    inventory_data = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(inventory_data)
    assert "get_interfaces" not in inventory_data["nrp1"]["defaults"]["data"]
    assert "apply_mtu_config" not in inventory_data["nrp1"]["defaults"]["data"]
    
# test_state_nr_workflow_dcache_usage()

def test_nr_cfg_syslog_and_ntp_state():
    """
    Run state similar to the one in docs use cases 
    that demonstrates how to use nr.task and nr.cfg state modules.
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["nr_cfg_syslog_and_ntp_state"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)     
    for v in ret["nrp1"].values():
        if v["__id__"] == "configure_logging":
            assert v["changes"]["ceos1"]["netmiko_send_config"]["changed"] == True
            assert v["changes"]["ceos1"]["netmiko_send_config"]["exception"] == None
            assert "logging host 1.1.1.1" in v["changes"]["ceos1"]["netmiko_send_config"]["result"]
            assert "logging host 2.2.2.2" in v["changes"]["ceos1"]["netmiko_send_config"]["result"]
            assert v["changes"]["ceos2"]["netmiko_send_config"]["changed"] == True
            assert v["changes"]["ceos2"]["netmiko_send_config"]["exception"] == None
            assert "logging host 1.1.1.2" in v["changes"]["ceos2"]["netmiko_send_config"]["result"]
            assert "logging host 2.2.2.1" in v["changes"]["ceos2"]["netmiko_send_config"]["result"]
        elif v["__id__"] == "configure_ntp":
            assert "nornir_netmiko.tasks.netmiko_send_config" in v["changes"]["ceos1"]
            assert "ntp server 7.7.7.7" in v["changes"]["ceos1"]["nornir_netmiko.tasks.netmiko_send_config"]
            assert "ntp server 7.7.7.8" in v["changes"]["ceos1"]["nornir_netmiko.tasks.netmiko_send_config"]
            assert "nornir_netmiko.tasks.netmiko_send_config" in v["changes"]["ceos2"]
            assert "ntp server 7.7.7.7" in v["changes"]["ceos2"]["nornir_netmiko.tasks.netmiko_send_config"]
            assert "ntp server 7.7.7.8" in v["changes"]["ceos2"]["nornir_netmiko.tasks.netmiko_send_config"]
        elif v["__id__"] == "save_configuration":
            assert "nornir_netmiko.tasks.netmiko_save_config" in v["changes"]["ceos1"]
            assert "nornir_netmiko.tasks.netmiko_save_config" in v["changes"]["ceos2"]
            
# test_nr_cfg_syslog_and_ntp_state()

def test_workflow_no_hosts_matched_by_filters_option():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["nr_workflow_state_3"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for v in ret["nrp1"].values():
        assert v["changes"] == {}
        assert v["result"] == False
        assert v["comment"]
        
# test_workflow_no_hosts_matched_by_filters_option()
    
@pytest.mark.modify_pillar_target("nrp1")
@pytest.mark.modify_pillar_pre_add({"nornir_filter_required": True})
@pytest.mark.modify_pillar_post_remove(["nornir_filter_required"])
def test_workflow_no_filters_but_filter_required(fixture_modify_proxy_pillar):
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_workflow_no_filters_but_filter_required"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for v in ret["nrp1"].values():
        assert v["changes"] == {}
        assert v["result"] == False
        assert "Traceback" in v["comment"] and "nornir_filter_required" in v["comment"]


def test_nr_workflow_hosts_failing_file_download():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_nr_workflow_hosts_failing_file_download"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)    
    for v in ret["nrp1"].values():
        assert v["changes"]["summary"]["ceos1"][0]["pre_cpre_check_config_gen"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][0]["pre_cpre_check_config_gen"] == "FAIL"
        assert v["changes"]["summary"]["ceos1"][1]["apply_config"] == "PASS"
        assert v["changes"]["summary"]["ceos2"][1]["apply_config"] == "SKIP"    
    
    
def test_nr_workflow_hosts_failing_file_download_single_host():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_nr_workflow_hosts_failing_file_download_single_host"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)    
    for v in ret["nrp1"].values():
        assert v["changes"]["summary"]["ceos2"][0]["pre_cpre_check_config_gen"] == "FAIL"
        assert v["changes"]["summary"]["ceos2"][1]["apply_config"] == "SKIP" 
        
        
def test_nr_workflow_sumtable_report():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_nr_workflow_sumtable_report"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)       
    for v in ret["nrp1"].values():
        assert isinstance(v["changes"]["summary"], str)
        assert "1  ceos1   PASS  SKIP  PASS  PASS  FAIL" in v["changes"]["summary"]
        assert "2  ceos2   PASS  PASS  PASS  PASS  FAIL" in v["changes"]["summary"]
        
 
def test_nr_workflow_sumtable_report_grid():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_nr_workflow_sumtable_report_grid"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)       
    for v in ret["nrp1"].values():
        assert isinstance(v["changes"]["summary"], str)
        assert "|  1 | ceos1  | PASS | SKIP | PASS | PASS | FAIL |" in v["changes"]["summary"]
        assert "|  2 | ceos2  | PASS | PASS | PASS | PASS | FAIL |" in v["changes"]["summary"]
        
        
def test_state_nr_workflow_common_kwargs():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_common_kwargs"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)       
    for v in ret["nrp1"].values():
        for item in v["changes"]["details"]:
            for k, v in item.items():
                assert k in ["show_current_time", "show_device_version"]
                assert isinstance(v, str)
                assert "Traceback" not in v
        
      
def test_state_nr_workflow_common_filters_fl_str():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_common_filters_fl_str"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)   
    for v in ret["nrp1"].values():
        for item in v["changes"]["details"]:
            for k, v in item.items():
                assert k == "show_current_time"
                assert "Clock source" in v["ceos1"]["show clock"]["result"]
                assert len(v) == 1, "matched more than 1 host"

    
def test_state_nr_workflow_common_filters_fo():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_common_filters_fo"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)   
    for v in ret["nrp1"].values():
        for item in v["changes"]["details"]:
            for k, v in item.items():
                assert k == "show_current_time"
                assert "Clock source" in v["ceos2"]["show clock"]["result"]
                assert len(v) == 1, "matched more than 1 host"
                
                
def test_state_nr_workflow_common_filters_fb():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.sls",
        arg=["test_state_nr_workflow_common_filters_fb"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)   
    for v in ret["nrp1"].values():
        for item in v["changes"]["details"]:
            for k, v in item.items():
                assert k == "pre_check_pull_config"
                assert "/interface" in v["ceos1"]["get_config"]["result"]
                assert "Traceback" not in v["ceos1"]["get_config"]["result"]
                assert len(v) == 1, "matched more than 1 host"
                
                
def test_state_nr_workflow_common_filters_fo_fb_fl_fakenos():
    """
    This test targets multiple proxy minons but Fx filters used to match
    fceos1 host only that is sits on nrp3
    """
    ret = client.cmd(
        tgt="nrp[13]",
        fun="state.sls",
        arg=["test_state_nr_workflow_common_filters_fo_fb_fl_fakenos"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)   
    for v in ret["nrp3"].values():
        for item in v["changes"]["details"]:
            for k, v in item.items():
                assert k == "show_current_time"
                assert "Clock source" in v["fceos1"]["show clock"]["result"]
                assert "Traceback" not in v["fceos1"]["show clock"]["result"]
                assert len(v) == 1, "matched more than 1 host"
                

def test_nr_workflow_with_other_modules():
    ret = client.cmd(
        tgt="nrp1",
        fun="state.apply",
        arg=["test_nr_workflow_with_other_modules"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)   
    for v in ret["nrp1"].values():
        assert v["result"] == True            
    
# def test_state_nr_workflow_some_steps_has_report_false():
#     """Some of the steps have report=False"""
#     pass
# 
# def test_state_nr_workflow_inline_test_step_to_dict_true():
#     """Test when having inline test defined with dictionary results"""
#     pass
# 
# 
# def test_state_nr_workflow_inline_test_step_to_dict_false():
#     """Test when having inline test defined with list results"""
#     pass
# 
# 
# def test_state_nr_workflow_with_nr_do_steps():
#     pass
# 
# 
# def test_state_nr_workflow_change_failed_rollback_step_triggered():
#     pass
# 