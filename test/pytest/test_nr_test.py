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

def test_nr_test_inline_contains():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "contains", "Clock source: local"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for item in ret["nrp1"]:
        assert item["result"] == "PASS"
        assert item["criteria"] == "Clock source: local"
        assert item["test"] == "contains"
        assert "name" in item


def test_nr_test_inline_contains_tabulate():
    """Check tabulate formatting, need to have tabulate installed"""
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "contains", "Clock source: local"],
        kwarg={"table": True},
        tgt_type="glob",
        timeout=60,
    )
    assert isinstance(ret["nrp1"], str)
    assert ret["nrp1"].count("PASS") == 2


# def test_nr_test_inline_contains_to_dict_add_details_false_with_test_name():
#     """ this test case became irrelevant once moved to per-test item execution """
#     ret = client.cmd(
#         tgt="nrp1",
#         fun="nr.test",
#         arg=["show clock", "contains", "Clock source: local"],
#         kwarg={
#             "add_details": False,
#             "name": "check_1",
#             "to_dict": True
#         },
#         tgt_type="glob",
#         timeout=60
#     )
#     assert len(ret["nrp1"]) == 2
#     for k, v in ret["nrp1"].items():
#         assert v["check_1"] == "PASS"


def test_nr_test_inline_contains_using_kwargs():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "commands": "show clock",
            "test": "contains",
            "pattern": "Clock source: local",
        },
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for item in ret["nrp1"]:
        assert item["result"] == "PASS"
        assert item["criteria"] == "Clock source: local"
        assert item["test"] == "contains"
        assert "name" in item


def test_nr_test_failed_only():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show ntp associations", "contains", "1.1.1.11"],
        kwarg={"failed_only": True},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 1
    for item in ret["nrp1"]:
        assert item["result"] == "FAIL"
        assert item["host"] == "ceos2"
        assert item["success"] == False
        assert item["criteria"] == "1.1.1.11"
        assert item["test"] == "contains"


def test_nr_test_suite():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={"suite": "salt://tests/test_suite_1.txt"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 4
    for index, item in enumerate(ret["nrp1"]):
        if item["host"] == "ceos1":
            if item["task"] == "show version":
                assert item["result"] == "PASS"
                assert item["criteria"] == "cEOS"
            elif item["task"] == "show run | inc ntp":
                assert item["result"] == "PASS"
        elif item["host"] == "ceos2":
            if item["task"] == "show version":
                assert item["result"] == "PASS"
                assert item["criteria"] == "cEOS"
            elif item["task"] == "show run | inc ntp":
                assert item["result"] == "FAIL"
                assert item["criteria"] == "1.1.1.11"


def test_nr_test_contains_lines_pattern_from_file():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show ntp associations", "contains_lines"],
        kwarg={"pattern": "salt://tests/pattern_ntp_cfg_lines.txt"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for item in ret["nrp1"]:
        assert item["test"] == "contains_lines"
        if item["host"] == "ceos1":
            assert item["result"] == "PASS"
        elif item["host"] == "ceos2":
            assert item["result"] == "FAIL"


def test_nr_test_suite_with_subset_list():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_1.txt",
            "subset": ["check ceos version"],
        },
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for index, item in enumerate(ret["nrp1"]):
        assert item["result"] == "PASS"
        assert item["criteria"] == "cEOS"
        assert item["task"] == "show version"


def test_nr_test_suite_with_subset_str():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_1.txt",
            "subset": "check ceos version",
        },
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for index, item in enumerate(ret["nrp1"]):
        assert item["result"] == "PASS"
        assert item["criteria"] == "cEOS"
        assert item["task"] == "show version"


def test_nr_test_suite_with_subset_glob():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={"suite": "salt://tests/test_suite_1.txt", "subset": "check ceos *"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for index, item in enumerate(ret["nrp1"]):
        assert item["result"] == "PASS"
        assert item["criteria"] == "cEOS"
        assert item["task"] == "show version"


def test_nr_test_contains_plugin_scrapli():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "contains", "Clock source: local"],
        kwarg={"plugin": "scrapli"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for item in ret["nrp1"]:
        assert item["result"] == "PASS"
        assert item["criteria"] == "Clock source: local"
        assert item["test"] == "contains"


def test_nr_test_suite_non_existing_file():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={"suite": "salt://tests/test_suite_not_exists.txt"},
        tgt_type="glob",
        timeout=60,
    )
    assert isinstance(ret["nrp1"], str)
    assert "ERROR" in ret["nrp1"]


def test_nr_test_function_file_custom_function():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "custom"],
        kwarg={"function_file": "salt://tests/cust_fun_1.py"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for item in ret["nrp1"]:
        assert item["result"] == "FAIL"
        assert item["criteria"] == ""
        assert item["test"] == "custom"


def test_nr_test_function_file_custom_function_use_all_tasks():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "function_file": "salt://tests/cust_fun_2.py",
            "use_all_tasks": True,
            "test": "custom",
            "commands": ["show clock", "show ip int brief"],
        },
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 4
    for item in ret["nrp1"]:
        assert item["result"] == "FAIL"
        assert item["criteria"] == ""
        assert item["test"] == "custom"


def test_nr_test_function_file_custom_function_use_list_of_tasks():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "function_file": "salt://tests/cust_fun_3.py",
            "test": "custom",
            "commands": ["show clock", "show ip int brief"],
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert len(ret["nrp1"]) == 4
    for item in ret["nrp1"]:
        assert item["result"] == "FAIL"
        assert item["criteria"] == ""
        assert item["test"] == "custom"
        assert item["exception"] in [
            "NTP not synced cust fun 3",
            "10. IP not configured",
        ]


def test_nr_test_suite_with_custom_functions():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={"suite": "salt://tests/test_suite_2.txt"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert len(ret["nrp1"]) == 10
    for item in ret["nrp1"]:
        if item["name"] == "test_cust_fun_1":
            assert item["result"] == "FAIL"
            assert item["exception"] == "NTP not synced"
        elif item["name"] == "test_cust_fun_2":
            assert item["result"] == "FAIL"
            assert item["exception"] == "NTP not synced"
        elif item["name"] == "test_cust_fun_3":
            assert item["result"] == "FAIL"
            assert item["exception"] in [
                "NTP not synced cust fun 3",
                "10. IP not configured",
            ]


def test_nr_test_function_file_return_empty_list():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "custom"],
        kwarg={"function_file": "salt://tests/cust_fun_4.py"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for item in ret["nrp1"]:
        assert item["result"] == "PASS"
        assert item["test"] == "custom"
        assert item["success"] == True


def test_nr_test_function_file_return_empty_dict():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "custom"],
        kwarg={"function_file": "salt://tests/cust_fun_5.py"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for item in ret["nrp1"]:
        assert item["result"] == "PASS"
        assert item["test"] == "custom"
        assert item["success"] == True


def test_nr_test_function_file_return_none():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "custom"],
        kwarg={"function_file": "salt://tests/cust_fun_6.py"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for item in ret["nrp1"]:
        assert item["result"] == "PASS"
        assert item["test"] == "custom"
        assert item["success"] == True


def test_nr_test_function_file_return_false():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "custom"],
        kwarg={"function_file": "salt://tests/cust_fun_7.py"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for item in ret["nrp1"]:
        assert item["result"] == "FAIL"
        assert item["test"] == "custom"
        assert item["success"] == False


def test_nr_test_function_file_return_true():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "custom"],
        kwarg={"function_file": "salt://tests/cust_fun_8.py"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for item in ret["nrp1"]:
        assert item["result"] == "PASS"
        assert item["test"] == "custom"
        assert item["success"] == True


def test_nr_test_suite_with_cli_params():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={"suite": "salt://tests/test_suite_3.txt"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 3
    for item in ret["nrp1"]:
        if item["name"] == "check ceos version":
            assert item["result"] == "PASS"
        elif item["name"] == "check NTP config":
            assert item["result"] == "FAIL"
            assert item["host"] == "ceos2"


def test_nr_test_inline_contains_with_FB_filter():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "contains", "Clock source: local"],
        kwarg={"FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 1
    for item in ret["nrp1"]:
        assert item["result"] == "PASS"
        assert item["criteria"] == "Clock source: local"
        assert item["test"] == "contains"
        assert item["host"] == "ceos1"
        assert "name" in item


def test_nr_test_inline_contains_with_render():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["ping {{ host.name }}", "contains", "packet loss"],
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for item in ret["nrp1"]:
        assert item["result"] == "PASS"

def test_nr_test_inline_contains_failure():
    """
    This test should produce an error as tests must be a list of strings
    that can render to list of dictionaries.
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "tests": ["foo", "contains", "NTP"]
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "Traceback (most recent call last)" in ret["nrp1"]
    assert "ValidationError" in ret["nrp1"]

        
def test_nr_test_dump():
    import random
    
    dump_filename = "test_nr_test_dump_{}".format(random.randint(1,10000))
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_1.txt", 
            "dump": dump_filename
        },
        tgt_type="glob",
        timeout=60,
    )
    salt_nornir_files = client.cmd(
        tgt="nrp1",
        fun="cmd.run",
        arg=["ls -l /var/salt-nornir/nrp1/files/"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(salt_nornir_files)
    assert dump_filename in salt_nornir_files["nrp1"]
    
# test_nr_test_dump()

def test_nr_test_sortby_and_reverse():

    ret_sortby_host = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_1.txt", "table": "brief",
            "sortby": "host"
        },
        tgt_type="glob",
        timeout=60,
    )
    ret_sortby_host_reverse = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_1.txt", "table": "brief",
            "sortby": "host",
            "reverse": True
        },
        tgt_type="glob",
        timeout=60,
    )
    print(ret_sortby_host["nrp1"])    
    print(ret_sortby_host_reverse["nrp1"])
    
    assert "0 | ceos1" in ret_sortby_host["nrp1"] and "1 | ceos1" in ret_sortby_host["nrp1"]
    assert "0 | ceos2" in ret_sortby_host_reverse["nrp1"] and "1 | ceos2" in ret_sortby_host_reverse["nrp1"]
    
# test_nr_test_sortby_and_reverse()


def test_nr_test_eval_tests():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        kwarg={
            "suite": "salt://tests/test_suite_4.txt",
            "FB": "ceos1",
        },
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(ret)
    assert ret["nrp1"][0]["exception"] == "wrong version"
    assert ret["nrp1"][1]["exception"] == "AssertionError"
    assert ret["nrp1"][2]["exception"] == "assert failed"
    assert ret["nrp1"][3]["exception"] == "Wrong version"
    assert ret["nrp1"][4]["exception"] == "Wrong version"    
    
# test_nr_test_eval_tests()


def test_nr_test_with_run_ttp():
    """
    Verify that when "task: run_ttp", run_ttp string not send as a command to device 
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        kwarg={
            "suite": "salt://tests/test_with_run_ttp.txt",
            "remove_tasks": False,
        },
        tgt_type="glob",
        timeout=60,
    )    
    # pprint.pprint(ret)
    for item in ret["nrp1"]:
        if item["name"] == "run_ttp":
            assert not isinstance(item["result"], str), "Having task run_ttp with string result: {}".format(item)
            
# test_nr_test_with_run_ttp()


# def test_nr_test_wait_timeout():
#     ret = client.cmd(
#         tgt="nrp1",
#         fun="nr.test",
#         kwarg={
#             "suite": "salt://tests/test_nr_test_wait_timeout.txt",
#         },
#         tgt_type="glob",
#         timeout=60,
#     )    
#     # pprint.pprint(ret)
#     for i in ret["nrp1"]:
#         if i["name"] == "Check if has 1.1.1.1/32 route":
#             assert i["success"] == False
#             assert i["failed"] == True
#             assert "wait timeout expired" in i["exception"] and "test run attempts" in i["exception"]
#         elif i["name"] == "Check if has correct version":
#             assert i["success"] == True
#             assert i["failed"] == False
#             assert i["exception"] == None
            
# test_nr_test_wait_timeout()


def test_nr_test_function_file_custom_function_add_host():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "custom"],
        kwarg={"function_file": "salt://tests/cust_fun_with_add_host.py", "add_host": True},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for i in ret["nrp1"]:
        assert "host_name" in i, "Seems that host name not added to results"
        
# test_nr_test_function_file_custom_function_add_host()

def test_nr_test_all_tasks_failed():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={
            "plugin": "nornir_salt.plugins.tasks.nr_test",
            "excpt": True,
            "tests": [["nornir_salt.plugins.tasks.nr_test", "contains", "foobar"]]
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "Traceback" in ret["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.nr_test"]
    assert "Traceback" in ret["nrp1"]["ceos2"]["nornir_salt.plugins.tasks.nr_test"]
                                               
def test_nr_test_test_has_empty_command_to_test():
    """
    Expect TestsProcessor to skip test that has empty task/command
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        kwarg={
            "tests": [["show clock", "contains", "local", "test1"], ["", "contains", "bar", "test2"]],
            "add_details": True,
        },
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(ret)
    assert len(ret["nrp1"]["ceos1"]) == 1
    assert len(ret["nrp1"]["ceos2"]) == 1
    assert ret["nrp1"]["ceos1"]["test1"]["result"] == "PASS"
    assert ret["nrp1"]["ceos2"]["test1"]["result"] == "PASS"
    
def test_nr_test_validate_suite():
    """Test to run test suite with wrong test name"""
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_validation.txt"
        },
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(ret)
    assert "ValidationError" in ret["nrp1"]
    
def test_nr_test_jinja2_template_suite():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_template.j2",
            "FB": "ceos1"
        },
        tgt_type="glob",
        timeout=60,
    ) 
    pprint.pprint(ret)
    assert len(ret["nrp1"]) == 3, "Expected 3 test items to return"
    assert all([i["result"] == "PASS" for i in ret["nrp1"]])
    assert len([i for i in ret["nrp1"] if i["name"] == "check ceos version"]) == 1, "expected one show version check tests"
    assert len(
        [i for i in ret["nrp1"] if "check interface" in i["name"] and i["host"] == "ceos1"]
    ) == 2, "expected two ceos1 interface check tests"
    
def test_nr_test_jinja2_template_suite_rendering_fail():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_template.j2",
            "FB": "ceos2"
        },
        tgt_type="glob",
        timeout=60,
    ) 
    pprint.pprint(ret)
    assert "Traceback" in ret["nrp1"]
    assert "ERROR" in ret["nrp1"]
    assert "rendering failed for 'ceos2'" in ret["nrp1"]
    
    
def test_nr_test_suite_in_host_data():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "{{ host.tests.suite1 }}",
            "FB": "ceos1"
        },
        tgt_type="glob",
        timeout=60,
    ) 
    pprint.pprint(ret)
    assert ret == {'nrp1': [{'changed': False,
           'connection_retry': 0,
           'criteria': '1.2.3',
           'diff': '',
           'exception': 'Pattern not in output',
           'failed': True,
           'host': 'ceos1',
           'name': 'check ceos version',
           'result': 'FAIL',
           'success': False,
           'task': 'show version',
           'task_retry': 0,
           'test': 'contains'},
          {'changed': False,
           'connection_retry': 0,
           'criteria': 'Clock source: local',
           'diff': '',
           'exception': None,
           'failed': False,
           'host': 'ceos1',
           'name': 'check local clock',
           'result': 'PASS',
           'success': True,
           'task': 'show clock',
           'task_retry': 0,
           'test': 'contains'}]}
    
def test_nr_test_suite_list_of_dict():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": [{"task": "show clock", "test": "contains", "pattern": "NTP", "name": "Test NTP"}],
            "FB": "ceos1"
        },
        tgt_type="glob",
        timeout=60,
    ) 
    pprint.pprint(ret)    
    assert ret == {'nrp1': [{'changed': False,
           'connection_retry': 0,
           'criteria': 'NTP',
           'diff': '',
           'exception': 'Pattern not in output',
           'failed': True,
           'host': 'ceos1',
           'name': 'Test NTP',
           'result': 'FAIL',
           'success': False,
           'task': 'show clock',
           'task_retry': 0,
           'test': 'contains'}]}


def test_nr_test_using_tests_host_data():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "tests": ["tests.suite1", "more_tests.suite123"],
            "FB": "ceos*",
            "strict": False
        },
        tgt_type="glob",
        timeout=60,
    ) 
    pprint.pprint(ret)   
    assert ret == {'nrp1': [{'changed': False,
           'connection_retry': 0,
           'criteria': '1.2.3',
           'diff': '',
           'exception': 'Pattern not in output',
           'failed': True,
           'host': 'ceos1',
           'name': 'check ceos version',
           'result': 'FAIL',
           'success': False,
           'task': 'show version',
           'task_retry': 0,
           'test': 'contains'},
          {'changed': False,
           'connection_retry': 0,
           'criteria': 'Clock source: local',
           'diff': '',
           'exception': None,
           'failed': False,
           'host': 'ceos1',
           'name': 'check local clock',
           'result': 'PASS',
           'success': True,
           'task': 'show clock',
           'task_retry': 0,
           'test': 'contains'},
          {'changed': False,
           'connection_retry': 0,
           'criteria': 'FQDN',
           'diff': '',
           'exception': None,
           'failed': False,
           'host': 'ceos1',
           'name': 'check ceos hostname',
           'result': 'PASS',
           'success': True,
           'task': 'show hostname',
           'task_retry': 0,
           'test': 'contains'}]}
    
def test_nr_test_using_tests_host_data_strict():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "tests": ["tests.suite1", "more_tests.suite123"],
            "FB": "ceos*",
            "strict": True
        },
        tgt_type="glob",
        timeout=60,
    ) 
    pprint.pprint(ret)  
    assert ret == {'nrp1': "ERROR: 'ceos2' no tests found for 'tests.suite1'"}

    
def test_nr_test_jinja2_template_suite_with_worker():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_template.j2",
            "FB": "ceos1",
            "worker": 3
        },
        tgt_type="glob",
        timeout=60,
    ) 
    pprint.pprint(ret)
    assert len(ret["nrp1"]) == 3, "Expected 3 test items to return"
    assert all([i["result"] == "PASS" for i in ret["nrp1"]])
    assert len([i for i in ret["nrp1"] if i["name"] == "check ceos version"]) == 1, "expected one show version check tests"
    assert len(
        [i for i in ret["nrp1"] if "check interface" in i["name"] and i["host"] == "ceos1"]
    ) == 2, "expected two ceos1 interface check tests"
    

def test_nr_test_inline_test_with_worker():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "contains", "local"],
        kwarg={
            "FB": "ceos1",
            "worker": 3
        },
        tgt_type="glob",
        timeout=60,
    ) 
    pprint.pprint(ret)
    assert ret == {'nrp1': [{'FB': 'ceos1',
           'changed': False,
           'connection_retry': 0,
           'criteria': 'local',
           'diff': '',
           'exception': None,
           'failed': False,
           'host': 'ceos1',
           'name': 'show clock contains local..',
           'result': 'PASS',
           'success': True,
           'task': 'show clock',
           'task_retry': 0,
           'test': 'contains'}]}
    
    
def test_nr_test_jinja2_template_suite_with_worker_unsupported_value():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_template.j2",
            "FB": "ceos1",
            "worker": "all"
        },
        tgt_type="glob",
        timeout=60,
    ) 
    pprint.pprint(ret)
    assert "Traceback" in ret["nrp1"]
    
    
def test_nr_test_jinja2_template_suite_with_job_data():
    ret_fail = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_template_with_job_data.j2",
            "FB": "ceos1",
            "job_data": {
                "expected_value": "foobar"
            }
        },
        tgt_type="glob",
        timeout=60,
    ) 
    ret_pass = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=[],
        kwarg={
            "suite": "salt://tests/test_suite_template_with_job_data.j2",
            "FB": "ceos1",
            "job_data": {
                "expected_value": "Clock source: local"
            }
        },
        tgt_type="glob",
        timeout=60,
    ) 
    pprint.pprint(ret_fail)
    pprint.pprint(ret_pass)
    assert ret_fail == {'nrp1': [{'changed': False,
           'connection_retry': 0,
           'criteria': 'foobar',
           'diff': '',
           'exception': 'Pattern not in output',
           'failed': True,
           'host': 'ceos1',
           'name': 'test ntp',
           'result': 'FAIL',
           'success': False,
           'task': 'show clock',
           'task_retry': 0,
           'test': 'contains'}]}
    assert ret_pass == {'nrp1': [{'changed': False,
           'connection_retry': 0,
           'criteria': 'Clock source: local',
           'diff': '',
           'exception': None,
           'failed': False,
           'host': 'ceos1',
           'name': 'test ntp',
           'result': 'PASS',
           'success': True,
           'task': 'show clock',
           'task_retry': 0,
           'test': 'contains'}]}

    
def test_nr_test_inline_testwith_job_data():
    ret_fail = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "contains", "Clock source: {{ job_data.expected_value }}"],
        kwarg={
            "FB": "ceos1",
            "job_data": {
                "expected_value": "foobar"
            }
        },
        tgt_type="glob",
        timeout=60,
    ) 
    ret_pass = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        arg=["show clock", "contains", "Clock source: {{ job_data.expected_value }}"],
        kwarg={
            "FB": "ceos1",
            "job_data": {
                "expected_value": "local"
            }
        },
        tgt_type="glob",
        timeout=60,
    ) 
    pprint.pprint(ret_fail)
    pprint.pprint(ret_pass)
    assert ret_fail == {'nrp1': [{'FB': 'ceos1',
           'changed': False,
           'connection_retry': 0,
           'criteria': 'Clock source: foobar',
           'diff': '',
           'exception': 'Pattern not in output',
           'failed': True,
           'host': 'ceos1',
           'name': 'show clock contains Clock sou..',
           'result': 'FAIL',
           'success': False,
           'task': 'show clock',
           'task_retry': 0,
           'test': 'contains'}]}
    assert ret_pass == {'nrp1': [{'FB': 'ceos1',
           'changed': False,
           'connection_retry': 0,
           'criteria': 'Clock source: local',
           'diff': '',
           'exception': None,
           'failed': False,
           'host': 'ceos1',
           'name': 'show clock contains Clock sou..',
           'result': 'PASS',
           'success': True,
           'task': 'show clock',
           'task_retry': 0,
           'test': 'contains'}]}
    
def test_nr_test_suite_with_nr_exec_functions():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.test",
        kwarg={
            "FB": "ceos1",
            "suite": "salt://tests/test_suite_with_nr_exec_functions.txt"
        },
        tgt_type="glob",
        timeout=60,
    )     
    pprint.pprint(ret)
    assert all(i["result"] == "PASS" for i in ret["nrp1"])
    assert ret["nrp1"][0]["task"] == "nornir_napalm.plugins.tasks.napalm_get"
    assert ret["nrp1"][1]["task"] == "nornir_salt.plugins.tasks.tcp_ping"
    