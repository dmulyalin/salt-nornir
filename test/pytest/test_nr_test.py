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
    This test should produce an error as tests must be a list of lists
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "tests": ["", "contains", "NTP"]
        },
        tgt_type="glob",
        timeout=60,
    )
    assert len(ret["nrp1"]) == 2
    for host_name, res in ret["nrp1"].items():
        assert "nornir-salt:TestsProcessor task_instance_completed error" in res
        assert "Traceback" in res["nornir-salt:TestsProcessor task_instance_completed error"]