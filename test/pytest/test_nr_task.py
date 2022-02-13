import logging
import pprint
import pytest
import socket

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

# check if has access to always on sandbox IOSXE device
iosxe_sandbox_router = "sandbox-iosxe-latest-1.cisco.com" 
s = socket.socket()
s.settimeout(5)
try:
    status = s.connect_ex((iosxe_sandbox_router, 830))
except:
    log.exception("Failed to check iosxe_sandbox_router connection.")
    status = 1
if status == 0:
    has_sandbox_iosxe_latest_1_metconf = True
else:
    has_sandbox_iosxe_latest_1_metconf = False
s.close()
skip_if_not_has_sandbox_iosxe_latest_1_netconf = pytest.mark.skipif(
    has_sandbox_iosxe_latest_1_metconf == False,
    reason="Has no connection to {} router".format(iosxe_sandbox_router),
)


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

    
def test_napalm_get_interfaces_with_jmespath():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={
            "plugin": "nornir_napalm.plugins.tasks.napalm_get",
            "getters": ["get_interfaces"],
            "jmespath": "get_interfaces.Ethernet1"
        },
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # should print:
    # {'nrp1': {'ceos1': {'nornir_napalm.plugins.tasks.napalm_get': {'description': 'Configured '
    #                                                                               'by '
    #                                                                               'NETCONF',
    #                                                                'is_enabled': True,
    #                                                                'is_up': True,
    #                                                                'last_flapped': 1633301427.8778741,
    #                                                                'mac_address': '02:42:0A:00:01:04',
    #                                                                'mtu': 1500,
    #                                                                'speed': 1000}},
    #           'ceos2': {'nornir_napalm.plugins.tasks.napalm_get': {'description': 'Configured '
    #                                                                               'by '
    #                                                                               'NETCONF',
    #                                                                'is_enabled': True,
    #                                                                'is_up': True,
    #                                                                'last_flapped': 1633277295.0623968,
    #                                                                'mac_address': '02:42:0A:00:01:05',
    #                                                                'mtu': 1500,
    #                                                                'speed': 1000}}}}
    assert "description" in ret["nrp1"]["ceos1"]["nornir_napalm.plugins.tasks.napalm_get"]
    assert "mac_address" in ret["nrp1"]["ceos1"]["nornir_napalm.plugins.tasks.napalm_get"]
    assert "mtu" in ret["nrp1"]["ceos1"]["nornir_napalm.plugins.tasks.napalm_get"]
    assert "description" in ret["nrp1"]["ceos2"]["nornir_napalm.plugins.tasks.napalm_get"]
    assert "mac_address" in ret["nrp1"]["ceos2"]["nornir_napalm.plugins.tasks.napalm_get"]
    assert "mtu" in ret["nrp1"]["ceos2"]["nornir_napalm.plugins.tasks.napalm_get"]
    
# test_napalm_get_interfaces_with_jmespath()

@skip_if_not_has_sandbox_iosxe_latest_1_netconf
def test_pyats_genie_api_ping_always_on_iosxe():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.task",
        kwarg={
            "plugin": "nornir_salt.plugins.tasks.pyats_genie_api",
            "FB": "csr1000v-1",
            "api": "ping",
            "address": "127.0.0.1",
            "timeout": 1,
            "count": 1
        },
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    # {'nrp2': {'csr1000v-1': {'pyats_genie_api': {'ping': {'address': '127.0.0.1',
    #                                                   'data_bytes': 100,
    #                                                   'repeat': 1,
    #                                                   'result_per_line': ['.'],
    #                                                   'statistics': {'received': 0,
    #                                                                  'send': 1,
    #                                                                  'success_rate_percent': 0.0},
    #                                                   'timeout_secs': 1}}}}}
    assert "ping" in ret["nrp2"]["csr1000v-1"]["pyats_genie_api"]
    assert ret["nrp2"]["csr1000v-1"]["pyats_genie_api"]["ping"]["address"] == "127.0.0.1"
    
# test_pyats_genie_api_ping_always_on_iosxe()