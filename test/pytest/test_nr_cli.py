import logging
import pprint

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
   description {{ description | re(".*") }}
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
                                {'interf': [{'description': 'Configured by '
                                                            'NETCONF',
                                             'interface': 'Ethernet1',
                                             'ip': '10.0.1.4',
                                             'mask': '24'},
                                            {'interface': 'Loopback1',
                                             'ip': '1.1.1.1',
                                             'mask': '24'},
                                            {'description': 'Lopback2 for '
                                                            'Customer 27123',
                                             'interface': 'Loopback2',
                                             'ip': '2.2.2.2',
                                             'mask': '24'},
                                            {'description': 'Customer #56924 '
                                                            'service',
                                             'interface': 'Loopback3',
                                             'ip': '1.2.3.4',
                                             'mask': '24'}]}]},
          'ceos2': {'run_ttp': [{'facts': {'arch': 'i686',
                                           'tools_version': '1.1'}},
                                {'interf': [{'description': 'Configured by '
                                                            'NETCONF',
                                             'interface': 'Ethernet1',
                                             'ip': '10.0.1.5',
                                             'mask': '24'},
                                            {'description': 'MGMT Range xYz',
                                             'interface': 'Loopback100',
                                             'ip': '100.12.3.4',
                                             'mask': '22'},
                                            {'description': 'NTU workstation '
                                                            'service',
                                             'interface': 'Loopback101',
                                             'ip': '1.101.2.2',
                                             'mask': '32'},
                                            {'description': 'Customer ID '
                                                            '67123A5',
                                             'interface': 'Loopback102',
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
                                {'interf': [{'description': 'Configured by '
                                                            'NETCONF',
                                             'interface': 'Ethernet1',
                                             'ip': '10.0.1.4',
                                             'mask': '24'},
                                            {'interface': 'Loopback1',
                                             'ip': '1.1.1.1',
                                             'mask': '24'},
                                            {'description': 'Lopback2 for '
                                                            'Customer 27123',
                                             'interface': 'Loopback2',
                                             'ip': '2.2.2.2',
                                             'mask': '24'},
                                            {'description': 'Customer #56924 '
                                                            'service',
                                             'interface': 'Loopback3',
                                             'ip': '1.2.3.4',
                                             'mask': '24'}]}]},
          'ceos2': {'run_ttp': [{'facts': {'arch': 'i686',
                                           'tools_version': '1.1'}},
                                {'interf': [{'description': 'Configured by '
                                                            'NETCONF',
                                             'interface': 'Ethernet1',
                                             'ip': '10.0.1.5',
                                             'mask': '24'},
                                            {'description': 'MGMT Range xYz',
                                             'interface': 'Loopback100',
                                             'ip': '100.12.3.4',
                                             'mask': '22'},
                                            {'description': 'NTU workstation '
                                                            'service',
                                             'interface': 'Loopback101',
                                             'ip': '1.101.2.2',
                                             'mask': '32'},
                                            {'description': 'Customer ID '
                                                            '67123A5',
                                             'interface': 'Loopback102',
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