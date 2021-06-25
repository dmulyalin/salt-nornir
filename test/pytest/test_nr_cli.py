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
        kwarg={"plugin": "netmiko", "netmiko_kwargs": {"strip_prompt": False}},
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
        kwarg={
            "plugin": "netmiko",
            "enable": True,
            "netmiko_kwargs": {"strip_prompt": False},
        },
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
