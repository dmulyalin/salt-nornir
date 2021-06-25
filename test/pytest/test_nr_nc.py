"""
Make sure to have netconf apoi enabled on ceos:

    management api netconf
       transport ssh def
       no shutdown
"""
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


def test_ncclient_dir_call():
    """
    Test dir method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                dir:
                    - async_mode
                    - cancel_commit
                    - channel_id
                    - channel_name
                    - client_capabilities
                    - close_session
    """
    ret = client.cmd(
        tgt="nrp1", fun="nr.nc", arg=["dir"], kwarg={}, tgt_type="glob", timeout=60
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "dir" in data, "No 'dir' output from '{}'".format(host_name)
        assert isinstance(data["dir"], list)
        assert len(data["dir"]) > 0


def test_ncclient_connected_call():
    """
    Test connected method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                connected:
                    True
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["connected"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "connected" in data, "No 'connected' output from '{}'".format(host_name)
        assert isinstance(data["connected"], bool)


def test_ncclient_server_capabilities_call():
    """
    Test connected method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                server_capabilities:
                    - ...
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["server_capabilities"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert (
            "server_capabilities" in data
        ), "No 'server_capabilities' output from '{}'".format(host_name)
        assert isinstance(data["server_capabilities"], list)
        assert len(data["server_capabilities"]) > 0


def test_ncclient_get_config_call_with_filter_from_file():
    """
    Test get_config method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                get_config:
                    <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="...">
                      <data time-modified="2021-04-25T02:28:21.162756196Z">
                        <interfaces xmlns="http://openconfig.net/yang/interfaces">
                          <interface>
                            <name>Ethernet1</name>
                            ...
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["get_config"],
        kwarg={
            "filter": ["subtree", "salt://rpc/get_config_filter_ietf_interfaces.xml"],
            "source": "running",
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "get_config" in data, "No 'get_config' output from '{}'".format(
            host_name
        )
        assert isinstance(data["get_config"], str)
        assert len(data["get_config"]) > 0


def test_ncclient_edit_config_call():
    """
    Test edit_config method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                edit_config:
                    <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="...">
                      <ok/>
                    </rpc-reply>
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["edit_config"],
        kwarg={
            "target": "running",
            "config": "salt://rpc/edit_config_ietf_interfaces.xml",
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "edit_config" in data, "No 'edit_config' output from '{}'".format(
            host_name
        )
        assert isinstance(data["edit_config"], str)
        assert len(data["edit_config"]) > 0
        assert "ok" in data["edit_config"]


def test_ncclient_locked_edit_config_call():
    """
    Test edit_config method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                locked:
                    <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="...">
                      <ok/>
                    </rpc-reply>
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["locked"],
        kwarg={
            "target": "running",
            "config": "salt://rpc/edit_config_ietf_interfaces.xml",
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "locked" in data, "No 'locked' output from '{}'".format(host_name)
        assert isinstance(data["locked"], list)
        assert len(data["locked"]) > 0
        assert "error" not in data["locked"][-1]


def test_ncclient_help_call():
    """
    Test dir method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                help:

                        Module: nornir_salt
                        Task plugin: ncclient_call
                        Plugin function: locked

                        Helper function to run this edit-config flow:
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["help"],
        kwarg={"method_name": "locked"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "help" in data, "No 'help' output from '{}'".format(host_name)
        assert isinstance(data["help"], str)
        assert len(data["help"]) > 0


def test_scrapli_netconf_dir_call():
    """
    Test dir method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                dir:
                    - async_mode
                    - cancel_commit
                    - channel_id
                    - channel_name
                    - client_capabilities
                    - close_session
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["dir"],
        kwarg={"plugin": "scrapli"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "dir" in data, "No 'dir' output from '{}'".format(host_name)
        assert isinstance(data["dir"], list)
        assert len(data["dir"]) > 0


def test_scrapli_netconf_help_call():
    """
    Test dir method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                help:

                        Module: nornir_salt
                        Task plugin: scrapli_netconf_call
                        Plugin function: locked

                        Helper function to run this edit-config flow:
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["help"],
        kwarg={"method_name": "locked", "plugin": "scrapli"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "help" in data, "No 'help' output from '{}'".format(host_name)
        assert isinstance(data["help"], str)
        assert len(data["help"]) > 0


def test_scrapli_netconf_server_capabilities_call():
    """
    Test connected method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                server_capabilities:
                    - ...
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["server_capabilities"],
        kwarg={"plugin": "scrapli"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert (
            "server_capabilities" in data
        ), "No 'server_capabilities' output from '{}'".format(host_name)
        assert isinstance(data["server_capabilities"], list)
        assert len(data["server_capabilities"]) > 0


def test_scrapli_netconf_get_config_call_with_filter_from_file():
    """
    Test get_config method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                get_config:
                    <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="...">
                      <data time-modified="2021-04-25T02:28:21.162756196Z">
                        <interfaces xmlns="http://openconfig.net/yang/interfaces">
                          <interface>
                            <name>Ethernet1</name>
                            ...
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["get_config"],
        kwarg={
            "filters": "salt://rpc/get_config_filter_ietf_interfaces.xml",
            "source": "running",
            "plugin": "scrapli",
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "get_config" in data, "No 'get_config' output from '{}'".format(
            host_name
        )
        assert isinstance(data["get_config"], str)
        assert len(data["get_config"]) > 0


def test_scrapli_netconf_edit_config_call():
    """
    Test edit_config method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                edit_config:
                    <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="...">
                      <ok/>
                    </rpc-reply>
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["edit_config"],
        kwarg={
            "target": "running",
            "config": "salt://rpc/edit_config_ietf_interfaces.xml",
            "plugin": "scrapli",
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "edit_config" in data, "No 'edit_config' output from '{}'".format(
            host_name
        )
        assert isinstance(data["edit_config"], str)
        assert len(data["edit_config"]) > 0
        assert "ok" in data["edit_config"]


def test_scrapli_netconf_locked_edit_config_call():
    """
    Test locked edit_config method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                locked:
                    |_
                      ----------
                      lock:
                          <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="105">
                            <ok/>
                          </rpc-reply>
                    |_...
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["locked"],
        kwarg={
            "target": "running",
            "config": "salt://rpc/edit_config_ietf_interfaces.xml",
            "plugin": "scrapli",
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "locked" in data, "No 'locked' output from '{}'".format(host_name)
        assert isinstance(data["locked"], list)
        assert len(data["locked"]) > 0
        assert "error" not in data["locked"][-1]
        assert "lock" in data["locked"][0]
        assert "discard_changes" in data["locked"][1]
        assert "edit_config" in data["locked"][2]
        assert "validate" in data["locked"][3]
        assert "commit" in data["locked"][4]
        assert "unlock" in data["locked"][5]


def test_scrapli_netconf_rpc_call():
    """
    Test rpc method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                rpc:
                    <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="106">
                      <data time-modified="2021-05...
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["rpc"],
        kwarg={
            "data": "salt://rpc/get_config_rpc_ietf_interfaces.xml",
            "plugin": "scrapli",
        },
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "rpc" in data, "No 'rpc' output from '{}'".format(host_name)
        assert isinstance(data["rpc"], str)
        assert len(data["rpc"]) > 0
