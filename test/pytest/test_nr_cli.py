import logging
import pprint
import time
import pytest
import socket

log = logging.getLogger(__name__)

try:
    import salt.client

    from salt.exceptions import CommandExecutionError

    HAS_SALT = True
except:
    HAS_SALT = False
    raise SystemExit("SALT Nonrir Tests - failed importing SALT libraries")

if HAS_SALT:
    # initiate execution modules client to run 'salt xyz command' commands
    client = salt.client.LocalClient()
    opts = salt.config.client_config("/etc/salt/master")
    event = salt.utils.event.get_event(
        "master", sock_dir=opts["sock_dir"], transport=opts["transport"], opts=opts
    )
    
# check if has access to always on sandbox devices
sandbox_router = "sandbox-iosxe-latest-1.cisco.com"
try:
    s = socket.socket()
    s.settimeout(5)
    s.connect((sandbox_router, 22))
    has_sandbox_iosxe_latest_1_ssh = True
except:
    has_sandbox_iosxe_latest_1_ssh = False
    
skip_if_not_has_sandbox_iosxe_latest_1_ssh = pytest.mark.skipif(
    has_sandbox_iosxe_latest_1_ssh == False,
    reason="Has no connection to {} router".format(sandbox_router),
)

def test_nr_cli_brief():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={},
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


def test_nr_cli_FB_one_host():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 1
    for host_name, data in ret["nrp1"].items():
        assert "show clock" in data, "No 'show clock' output from '{}'".format(
            host_name
        )
        assert isinstance(data["show clock"], str)


def test_nr_cli_details():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"add_details": True},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "show clock" in data, "No 'show clock' output from '{}'".format(
            host_name
        )
        assert isinstance(data["show clock"], dict)
        assert "result" in data["show clock"]
        assert "diff" in data["show clock"]
        assert "exception" in data["show clock"]
        assert "failed" in data["show clock"]
        assert isinstance(data["show clock"]["result"], str)


def test_nr_cli_plugin_netmiko():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko"},
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


def test_nr_cli_plugin_scrapli():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "scrapli"},
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


def test_nr_cli_match():
    """
    nr.cli call should return something like this::

        nrp1:
            ----------
            ceos1:
                ----------
                show version:
                    Uptime: 0 weeks, 0 days, 0 hours and 5 minutes
            ceos2:
                ----------
                show version:
                    Uptime: 0 weeks, 0 days, 0 hours and 5 minutes
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show version"],
        kwarg={"match": "Uptime"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "show version" in data, "No 'show version' output from '{}'".format(
            host_name
        )
        assert isinstance(data["show version"], str)
        assert len(data["show version"].splitlines()) == 1


def test_nr_cli_match_with_before():
    """
    nr.cli call should return something like this::

        nrp1:
            ----------
            ceos1:
                ----------
                show version:
                    --
                    Kernel version: 3.10.0-862.el7.x86_64

                    Uptime: 0 weeks, 0 days, 0 hours and 8 minutes
            ceos2:
                ----------
                show version:
                    --
                    Kernel version: 3.10.0-862.el7.x86_64

                    Uptime: 0 weeks, 0 days, 0 hours and 8 minutes
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show version"],
        kwarg={"match": "Uptime", "before": 2},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "show version" in data, "No 'show version' output from '{}'".format(
            host_name
        )
        assert isinstance(data["show version"], str)
        assert (
            len(data["show version"].splitlines()) == 4
        ), "Not 4 lines fron '{}' show version output: '{}'".format(host_name, data)


def test_nr_cli_plugin_netmiko_with_kwargs():
    """
    Shoulkd return something like this::

        nrp1:
            ----------
            ceos1:
                ----------
                show clock:
                    12345
                    Timezone: UTC
                    Clock source: local
                    ceos1>
            ceos2:
                ----------
                show clock:
                    12345
                    Timezone: UTC
                    Clock source: local
                    ceos2>
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko", "strip_prompt": False},
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
        assert (
            ">" in data["show clock"] or "#" in data["show clock"]
        ), "No prompt in 'show clock' output from '{}'".format(host_name)


def test_nr_cli_plugin_netmiko_with_enable():
    """
    By Default cEOS is not in enable/privileged mode, and prompt ends with
    "...>" character, using enable-True we can verify that modee changed properly.

    Shoulkd return something like this::

        nrp1:
            ----------
            ceos1:
                ----------
                show clock:
                    12345
                    Timezone: UTC
                    Clock source: local
                    ceos1#
            ceos2:
                ----------
                show clock:
                    12345
                    Timezone: UTC
                    Clock source: local
                    ceos2#
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko", "enable": True, "strip_prompt": False},
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
        assert (
            "#" in data["show clock"]
        ), "No prompt in 'show clock' output from '{}'".format(host_name)


def test_nr_cli_netmiko_use_ps():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"use_ps": True},
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


def test_nr_cli_netmiko_from_file():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=[],
        kwarg={"filename": "salt://cli/show_cmd_1.txt"},
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
        assert (
            "Clock source: local" in data["show clock"]
        ), "Unexpected 'show clock' output from '{}'".format(host_name)

        assert (
            "show ip int brief" in data
        ), "No 'show ip int brief output from '{}'".format(host_name)
        assert isinstance(data["show ip int brief"], str)
        assert (
            "IP Address" in data["show ip int brief"]
        ), "Unexpected 'show ip int brief' output from '{}'".format(host_name)


def test_nr_cli_scrapli_from_file():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=[],
        kwarg={"filename": "salt://cli/show_cmd_1.txt", "plugin": "scrapli"},
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
        assert (
            "Clock source: local" in data["show clock"]
        ), "Unexpected 'show clock' output from '{}'".format(host_name)

        assert (
            "show ip int brief" in data
        ), "No 'show ip int brief output from '{}'".format(host_name)
        assert isinstance(data["show ip int brief"], str)
        assert (
            "IP Address" in data["show ip int brief"]
        ), "Unexpected 'show ip int brief' output from '{}'".format(host_name)


def test_nr_cli_netmiko_from_file_use_ps():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=[],
        kwarg={"filename": "salt://cli/show_cmd_1.txt", "use_ps": True},
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
        assert (
            "Clock source: local" in data["show clock"]
        ), "Unexpected 'show clock' output from '{}'".format(host_name)

        assert (
            "show ip int brief" in data
        ), "No 'show ip int brief output from '{}'".format(host_name)
        assert isinstance(data["show ip int brief"], str)
        assert (
            "IP Address" in data["show ip int brief"]
        ), "Unexpected 'show ip int brief' output from '{}'".format(host_name)


def test_nr_cli_netmiko_with_commands_render():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["ping {{ host.name }}"],
        kwarg={"render": "commands"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2, "Not all hosts returned results"

    assert "ping ceos1" in ret["nrp1"]["ceos1"], "No ping results for ceos1"
    assert "ping ceos2" in ret["nrp1"]["ceos2"], "No ping results for ceos2"

    assert (
        "ping statistics" in ret["nrp1"]["ceos1"]["ping ceos1"]
    ), "Unexpected ping output from ceos1"
    assert (
        "ping statistics" in ret["nrp1"]["ceos2"]["ping ceos2"]
    ), "Unexpected ping output from ceos2"


def test_nr_cli_netmiko_from_file_use_ps_multiline():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=[],
        kwarg={
            "filename": "salt://cli/use_ps_multiline_command.txt",
            "use_ps": True,
            "split_lines": False,
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2, "Not all hosts returned results"

    for host_name, data in ret["nrp1"].items():
        assert "enable" in data, "{} - Task name not returned or malformed".format(
            host_name
        )

        assert "enable" in data["enable"], "{} - no 'enable' command".format(host_name)
        assert "conf t" in data["enable"], "{} - no 'conf t' command".format(host_name)
        assert (
            "do show ip int brief" in data["enable"]
        ), "{} - no 'do show ip int brief' command".format(host_name)
        assert "exit" in data["enable"], "{} - no 'exit' command".format(host_name)

    
def test_nr_cli_netmiko_run_ttp_from_string():
    template = """
<input name="version">
commands = ["show version"]
</input>

<input name="interfaces">
commands = ["show run"]
</input>

<group name="facts" input="version">
Architecture: {{ arch }}
cEOS tools version: {{ tools_version }}
</group>
  
<group name="interf" input="interfaces">
interface {{ interface }}
   ip address {{ ip }}/{{ mask }}
</group>
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko", "run_ttp": template, "enable": True},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert ret == {'nrp1': {'ceos1': {'run_ttp': [{'facts': {'arch': 'i686',
                                           'tools_version': '1.1'}},
                                {'interf': [{'interface': 'Ethernet1',
                                             'ip': '10.0.1.4',
                                             'mask': '24'},
                                            {'interface': 'Loopback1',
                                             'ip': '1.1.1.1',
                                             'mask': '24'},
                                            {'interface': 'Loopback2',
                                             'ip': '2.2.2.2',
                                             'mask': '24'},
                                            {'interface': 'Loopback3',
                                             'ip': '1.2.3.4',
                                             'mask': '24'}]}]},
          'ceos2': {'run_ttp': [{'facts': {'arch': 'i686',
                                           'tools_version': '1.1'}},
                                {'interf': [{'interface': 'Ethernet1',
                                             'ip': '10.0.1.5',
                                             'mask': '24'},
                                            {'interface': 'Loopback100',
                                             'ip': '100.12.3.4',
                                             'mask': '22'},
                                            {'interface': 'Loopback101',
                                             'ip': '1.101.2.2',
                                             'mask': '32'},
                                            {'interface': 'Loopback102',
                                             'ip': '5.5.5.5',
                                             'mask': '24'}]}]}}}
    
# test_nr_cli_netmiko_run_ttp_from_string()


def test_nr_cli_netmiko_run_ttp_download_from_salt_master():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=[],
        kwarg={"run_ttp": "salt://ttp/run_ttp_test_1.txt", "enable": True},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert ret == {'nrp1': {'ceos1': {'run_ttp': [{'facts': {'arch': 'i686',
                                           'tools_version': '1.1'}},
                                {'interf': [{'interface': 'Ethernet1',
                                             'ip': '10.0.1.4',
                                             'mask': '24'},
                                            {'interface': 'Loopback1',
                                             'ip': '1.1.1.1',
                                             'mask': '24'},
                                            {'interface': 'Loopback2',
                                             'ip': '2.2.2.2',
                                             'mask': '24'},
                                            {'interface': 'Loopback3',
                                             'ip': '1.2.3.4',
                                             'mask': '24'}]}]},
          'ceos2': {'run_ttp': [{'facts': {'arch': 'i686',
                                           'tools_version': '1.1'}},
                                {'interf': [{'interface': 'Ethernet1',
                                             'ip': '10.0.1.5',
                                             'mask': '24'},
                                            {'interface': 'Loopback100',
                                             'ip': '100.12.3.4',
                                             'mask': '22'},
                                            {'interface': 'Loopback101',
                                             'ip': '1.101.2.2',
                                             'mask': '32'},
                                            {'interface': 'Loopback102',
                                             'ip': '5.5.5.5',
                                             'mask': '24'}]}]}}}
    
# test_nr_cli_netmiko_run_ttp_download_from_salt_master()


def test_nr_cli_netmiko_empty_commands():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock", "\n", " ", "", "show version"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    assert len(ret["nrp1"]["ceos1"]) == 2
    assert "show clock" in ret["nrp1"]["ceos1"]
    assert "show version" in ret["nrp1"]["ceos1"]
    assert len(ret["nrp1"]["ceos2"]) == 2
    assert "show clock" in ret["nrp1"]["ceos2"]
    assert "show version" in ret["nrp1"]["ceos2"]
    
# test_nr_cli_netmiko_empty_commands()


def test_nr_cli_netmiko_empty_commands_use_ps():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock", "\n", " ", "", "show version"],
        kwarg={"use_ps": True},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    assert len(ret["nrp1"]["ceos1"]) == 2
    assert "show clock" in ret["nrp1"]["ceos1"]
    assert "show version" in ret["nrp1"]["ceos1"]
    assert len(ret["nrp1"]["ceos2"]) == 2
    assert "show clock" in ret["nrp1"]["ceos2"]
    assert "show version" in ret["nrp1"]["ceos2"]
    
# test_nr_cli_netmiko_empty_commands_use_ps()


def test_nr_cli_scrapli_empty_commands():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock", "\n", " ", "", "show version"],
        kwarg={"plugin": "scrapli"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    assert len(ret["nrp1"]["ceos1"]) == 2
    assert "show clock" in ret["nrp1"]["ceos1"]
    assert "show version" in ret["nrp1"]["ceos1"]
    assert len(ret["nrp1"]["ceos2"]) == 2
    assert "show clock" in ret["nrp1"]["ceos2"]
    assert "show version" in ret["nrp1"]["ceos2"]
    
# test_nr_cli_scrapli_empty_commands()


def test_nr_cli_with_iplkp():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show ip int brief"],
        kwarg={"iplkp": "salt://lookup/ip.txt"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "ceos1:Eth1" in ret["nrp1"]["ceos1"]["show ip int brief"]
    assert "ceos2:Eth1" in ret["nrp1"]["ceos2"]["show ip int brief"]
    
# test_cli_with_iplkp()


def test_nr_cli_br_netmiko():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show hostname _br_"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "show hostname" in ret["nrp1"]["ceos1"]
    assert "show hostname" in ret["nrp1"]["ceos2"]
    assert len(ret["nrp1"]["ceos1"]["show hostname"].splitlines()) == 2
    assert len(ret["nrp1"]["ceos2"]["show hostname"].splitlines()) == 2
    
# test_nr_cli_br_netmiko()


def test_nr_cli_br_scrapli():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["_br_ show hostname"],
        kwarg={"plugin": "scrapli"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "show hostname" in ret["nrp1"]["ceos1"]
    assert "show hostname" in ret["nrp1"]["ceos2"]
    assert len(ret["nrp1"]["ceos1"]["show hostname"].splitlines()) == 2
    assert len(ret["nrp1"]["ceos2"]["show hostname"].splitlines()) == 2
    
# test_nr_cli_br_scrapli()


def test_nr_cli_br_netmiko_use_ps():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show hostname _br_"],
        kwarg={"use_ps": True},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "show hostname" in ret["nrp1"]["ceos1"]
    assert "show hostname" in ret["nrp1"]["ceos2"]
    assert len(ret["nrp1"]["ceos1"]["show hostname"].splitlines()) == 2
    assert len(ret["nrp1"]["ceos2"]["show hostname"].splitlines()) == 2
    
# test_nr_cli_br_netmiko_use_ps()


def test_nr_cli_napalm_plugin():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show hostname", "show clock"],
        kwarg={"plugin": "napalm"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "show clock" in ret["nrp1"]["ceos1"]
    assert "show clock" in ret["nrp1"]["ceos2"]
    assert "show hostname" in ret["nrp1"]["ceos1"]
    assert "show hostname" in ret["nrp1"]["ceos2"]
    
# test_nr_cli_napalm_plugin()


def test_nr_cli_napalm_plugin_with_interval():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show hostname", "show clock"],
        kwarg={"plugin": "napalm", "interval": 1},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "show clock" in ret["nrp1"]["ceos1"]
    assert "show clock" in ret["nrp1"]["ceos2"]
    assert "show hostname" in ret["nrp1"]["ceos1"]
    assert "show hostname" in ret["nrp1"]["ceos2"]
    
# test_nr_cli_napalm_plugin_with_interval()


def test_nr_cli_napalm_plugin_with_new_line_char():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show hostname _br_", "show clock _br_"],
        kwarg={"plugin": "napalm", "interval": 1},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "show clock" in ret["nrp1"]["ceos1"]
    assert "show clock" in ret["nrp1"]["ceos2"]
    assert "show hostname" in ret["nrp1"]["ceos1"]
    assert "show hostname" in ret["nrp1"]["ceos2"]
    
# test_nr_cli_napalm_plugin_with_new_line_char()

def test_nr_cli_napalm_plugin_filename():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=[],
        kwarg={"filename": "salt://cli/show_cmd_2.txt", "plugin": "napalm"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():

        assert "show clock" in data, "No 'show clock' output from '{}'".format(
            host_name
        )
        assert isinstance(data["show clock"], str)
        assert (
            "Clock source: local" in data["show clock"]
        ), "Unexpected 'show clock' output from '{}'".format(host_name)

        assert (
            "show ip interface brief" in data
        ), "No 'show ip interface brief output from '{}'".format(host_name)
        assert isinstance(data["show ip interface brief"], str)
        assert (
            "IP Address" in data["show ip interface brief"]
        ), "Unexpected 'show ip interface brief' output from '{}'".format(host_name)
        
# test_nr_cli_napalm_plugin_filename()


def test_nr_cli_napalm_plugin_render_command():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["ping {{ host.name }}"],
        kwarg={"plugin": "napalm"},
        tgt_type="glob",
        timeout=60,
    )
    assert "PING ceos1" in ret["nrp1"]["ceos1"]["ping ceos1"] 
    assert "PING ceos2" in ret["nrp1"]["ceos2"]["ping ceos2"]
    
# test_nr_cli_napalm_plugin_render_command()
        
    
def test_nr_cli_netmiko_plugin_render_command():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["ping {{ host.name }}"],
        kwarg={"plugin": "netmiko"},
        tgt_type="glob",
        timeout=60,
    )
    assert "PING ceos1" in ret["nrp1"]["ceos1"]["ping ceos1"] 
    assert "PING ceos2" in ret["nrp1"]["ceos2"]["ping ceos2"]
    
# test_nr_cli_netmiko_plugin_render_command()


def test_nr_cli_scrapli_plugin_render_command():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["ping {{ host.name }}"],
        kwarg={"plugin": "scrapli"},
        tgt_type="glob",
        timeout=60,
    )
    assert "PING ceos1" in ret["nrp1"]["ceos1"]["ping ceos1"] 
    assert "PING ceos2" in ret["nrp1"]["ceos2"]["ping ceos2"]
    
# test_nr_cli_scrapli_plugin_render_command()


def test_nr_cli_pyats_plugin_render_command():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["ping {{ host.name }}"],
        kwarg={"plugin": "pyats"},
        tgt_type="glob",
        timeout=60,
    )
    assert "PING ceos1" in ret["nrp1"]["ceos1"]["ping ceos1"] 
    assert "PING ceos2" in ret["nrp1"]["ceos2"]["ping ceos2"]
    
# test_nr_cli_pyats_plugin_render_command()

def test_nr_cli_pyats_plugin():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show hostname", "show clock"],
        kwarg={"plugin": "pyats"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "show clock" in ret["nrp1"]["ceos1"]
    assert "show clock" in ret["nrp1"]["ceos2"]
    assert "show hostname" in ret["nrp1"]["ceos1"]
    assert "show hostname" in ret["nrp1"]["ceos2"]
    
# test_nr_cli_pyats_plugin()


def test_nr_cli_pyats_plugin_with_interval():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show hostname", "show clock"],
        kwarg={"plugin": "pyats", "interval": 1},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "show clock" in ret["nrp1"]["ceos1"]
    assert "show clock" in ret["nrp1"]["ceos2"]
    assert "show hostname" in ret["nrp1"]["ceos1"]
    assert "show hostname" in ret["nrp1"]["ceos2"]
    
# test_nr_cli_pyats_plugin_with_interval()


def test_nr_cli_pyats_plugin_with_new_line_char():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show hostname _br_", "show clock _br_"],
        kwarg={"plugin": "pyats", "interval": 1},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "show clock" in ret["nrp1"]["ceos1"]
    assert "show clock" in ret["nrp1"]["ceos2"]
    assert "show hostname" in ret["nrp1"]["ceos1"]
    assert "show hostname" in ret["nrp1"]["ceos2"]
    
# test_nr_cli_pyats_plugin_with_new_line_char()

def test_nr_cli_pyats_plugin_filename():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=[],
        kwarg={"filename": "salt://cli/show_cmd_2.txt", "plugin": "pyats"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():

        assert "show clock" in data, "No 'show clock' output from '{}'".format(
            host_name
        )
        assert isinstance(data["show clock"], str)
        assert (
            "Clock source: local" in data["show clock"]
        ), "Unexpected 'show clock' output from '{}'".format(host_name)

        assert (
            "show ip interface brief" in data
        ), "No 'show ip interface brief output from '{}'".format(host_name)
        assert isinstance(data["show ip interface brief"], str)
        assert (
            "IP Address" in data["show ip interface brief"]
        ), "Unexpected 'show ip interface brief' output from '{}'".format(host_name)
        
# test_nr_cli_pyats_plugin_filename()


def test_nr_cli_pyats_plugin_via_pool():
    """
    This test measures time for task to complete, it should take less than 6 seconds
    to finish if all good.
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=[
            "enable", "enable", "enable",
            "ping 8.8.8.8 interval 1 timeout 1", 
            "ping 1.2.3.4 interval 1 timeout 1", 
            "ping 4.4.8.8 interval 1 timeout 1",
        ],
        kwarg={"plugin": "pyats", "via": "vty_1", "FB": "ceos1", "event_progress": True},
        tgt_type="glob",
        timeout=60,
    )    
    
    event_start = event.get_event(
        tag="nornir-proxy/.+/nrp1/ceos1/task/started/nornir_salt.plugins.tasks.pyats_send_commands", match_type="regex", wait=10,
    )
    event_end = event.get_event(
        tag="nornir-proxy/.+/nrp1/ceos1/task/completed/nornir_salt.plugins.tasks.pyats_send_commands", match_type="regex", wait=20,
    )

    start_time = time.strptime(event_start["_stamp"].split(".")[0], "%Y-%m-%dT%H:%M:%S") 
    end_time = time.strptime(event_end["_stamp"].split(".")[0], "%Y-%m-%dT%H:%M:%S")
    elapsed = time.mktime(end_time) - time.mktime(start_time)
    
    assert elapsed < 10, "Took more then 10seconds to finish commands"
    assert "ping 8.8.8.8 interval 1 timeout 1" in ret["nrp1"]["ceos1"]
    assert "ping 1.2.3.4 interval 1 timeout 1" in ret["nrp1"]["ceos1"]
    assert "ping 4.4.8.8 interval 1 timeout 1" in ret["nrp1"]["ceos1"]

# test_nr_cli_pyats_plugin_via_pool()


def test_nr_cli_pyats_plugin_via_default():
    """
    This test measures time for task to complete, it should take more than 6 seconds
    to finish if all good.
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=[
            "enable", "enable", "enable",
            "ping 8.8.8.8 interval 1 timeout 1", 
            "ping 1.2.3.4 interval 1 timeout 1", 
            "ping 4.4.8.8 interval 1 timeout 1",
        ],
        kwarg={"plugin": "pyats", "via": "default", "FB": "ceos1", "event_progress": True},
        tgt_type="glob",
        timeout=60,
    )    
    
    event_start = event.get_event(
        tag="nornir-proxy/.+/nrp1/ceos1/task/started/nornir_salt.plugins.tasks.pyats_send_commands", match_type="regex", wait=10,
    )
    event_end = event.get_event(
        tag="nornir-proxy/.+/nrp1/ceos1/task/completed/nornir_salt.plugins.tasks.pyats_send_commands", match_type="regex", wait=20,
    )

    start_time = time.strptime(event_start["_stamp"].split(".")[0], "%Y-%m-%dT%H:%M:%S") 
    end_time = time.strptime(event_end["_stamp"].split(".")[0], "%Y-%m-%dT%H:%M:%S")
    elapsed = time.mktime(end_time) - time.mktime(start_time)
    
    assert 20 > elapsed > 10, "Took less then 10s or mote then 20s to finish commands"
    assert "ping 8.8.8.8 interval 1 timeout 1" in ret["nrp1"]["ceos1"]
    assert "ping 1.2.3.4 interval 1 timeout 1" in ret["nrp1"]["ceos1"]
    assert "ping 4.4.8.8 interval 1 timeout 1" in ret["nrp1"]["ceos1"]

# test_nr_cli_pyats_plugin_via_default()


def test_nr_cli_pyats_plugin_parse_eos_fail():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock", "show version"],
        kwarg={"plugin": "pyats", "parse": True},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "Could not find parser" in ret["nrp1"]["ceos1"]["show clock"]
    assert "Could not find parser" in ret["nrp1"]["ceos1"]["show version"]
    assert "Could not find parser" in ret["nrp1"]["ceos2"]["show clock"]
    assert "Could not find parser" in ret["nrp1"]["ceos2"]["show version"]
    
# test_nr_cli_pyats_plugin_parse_eos_fail()

@skip_if_not_has_sandbox_iosxe_latest_1_ssh
def test_nr_cli_pyats_plugin_parse_nrp2_iosxe():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.cli",
        arg=["show clock", "show version"],
        kwarg={"plugin": "pyats", "parse": True, "add_details": True, "FC": "csr"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert isinstance(ret["nrp2"]["csr1000v-1"]["show clock"]["result"], dict)
    assert isinstance(ret["nrp2"]["csr1000v-1"]["show version"]["result"], dict)
    assert ret["nrp2"]["csr1000v-1"]["show clock"]["failed"] == False
    assert ret["nrp2"]["csr1000v-1"]["show version"]["failed"] == False
    
# test_nr_cli_pyats_plugin_parse_nrp2_iosxe()