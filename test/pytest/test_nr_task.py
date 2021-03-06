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


def test_task_call_netmiko_send_command_brief():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=["nornir_netmiko.tasks.netmiko_send_command"],
        kwarg={"command_string": "show clock"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert (
            "nornir_netmiko.tasks.netmiko_send_command" in data
        ), "No 'show clock' output from '{}'".format(host_name)
        assert isinstance(data["nornir_netmiko.tasks.netmiko_send_command"], str)


def test_task_call_netmiko_send_command_details():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=["nornir_netmiko.tasks.netmiko_send_command"],
        kwarg={"command_string": "show clock", "add_details": True},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert (
            "nornir_netmiko.tasks.netmiko_send_command" in data
        ), "No 'show clock' output from '{}'".format(host_name)
        assert isinstance(data["nornir_netmiko.tasks.netmiko_send_command"], dict)
        assert "result" in data["nornir_netmiko.tasks.netmiko_send_command"]
        assert "diff" in data["nornir_netmiko.tasks.netmiko_send_command"]
        assert "exception" in data["nornir_netmiko.tasks.netmiko_send_command"]
        assert "failed" in data["nornir_netmiko.tasks.netmiko_send_command"]
        assert isinstance(
            data["nornir_netmiko.tasks.netmiko_send_command"]["result"], str
        )


def test_custom_task_call():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=["salt://tasks/custom_send_commands.py"],
        kwarg={"commands": ["show clock"]},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "show clock" in data, "No 'show clock' output from '{}'".format(
            host_name
        )
        assert isinstance(data["show clock"], str)


def test_custom_task_call_fail():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=["salt://tasks/does_not_exists.py"],
        kwarg={"commands": ["show clock"]},
        tgt_type="glob",
        timeout=60,
    )
    assert (
        "salt.exceptions.CommandExecutionError" in ret["nrp1"]
        and "failed download task function file" in ret["nrp1"]
    )
