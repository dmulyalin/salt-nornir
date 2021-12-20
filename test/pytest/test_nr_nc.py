"""
Make sure to have netconf api enabled on ceos:

    management api netconf
       transport ssh def
       no shutdown
"""
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
status = s.connect_ex((iosxe_sandbox_router, 830))
if status == 0:
    has_sandbox_iosxe_latest_1_metconf = True
else:
    has_sandbox_iosxe_latest_1_metconf = False
s.close()
skip_if_not_has_sandbox_iosxe_latest_1_netconf = pytest.mark.skipif(
    has_sandbox_iosxe_latest_1_metconf == False,
    reason="Has no connection to {} router".format(iosxe_sandbox_router),
)

# check if has access to always on sandbox IOSXR device
iosxr_sandbox_router = "sandbox-iosxr-1.cisco.com" 
s = socket.socket()
s.settimeout(5)
status = s.connect_ex((iosxr_sandbox_router, 830))
if status == 0:
    has_sandbox_iosxr_latest_1_metconf = True
    # enable netconf on the iosxr box
    client.cmd(
        tgt="nrp2",
        fun="nr.cfg",
        arg=[
            "netconf-yang agent",
            "netconf agent tty",
            "ssh server netconf vrf default",
        ],
        kwarg={"FB": "iosxr1", "plugin": "netmiko"},
        tgt_type="glob",
        timeout=60,
    )
else:
    has_sandbox_iosxr_latest_1_metconf = False
s.close()
skip_if_not_has_sandbox_iosxr_latest_1_netconf = pytest.mark.skipif(
    has_sandbox_iosxr_latest_1_metconf == False,
    reason="Has no connection to {} router".format(iosxr_sandbox_router),
)


# check if has access to always on sandbox NXOS device
nxos_sandbox_router = "sandbox-iosxe-latest-1.cisco.com" 
s = socket.socket()
s.settimeout(5)
status = s.connect_ex((nxos_sandbox_router, 830))
if status == 0:
    has_sandbox_nxos_latest_1_metconf = True
else:
    has_sandbox_nxos_latest_1_metconf = False
s.close()
skip_if_not_has_sandbox_nxos_latest_1_netconf = pytest.mark.skipif(
    has_sandbox_nxos_latest_1_metconf == False,
    reason="Has no connection to {} router".format(nxos_sandbox_router),
)

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
        assert "Traceback (most recent " not in data["dir"], "dir call returned error"


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
        assert (
            "Traceback (most recent " not in data["server_capabilities"]
        ), "server_capabilities call returned error"


def test_ncclient_get_config_call_with_filter_list_from_file():
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
        assert "Traceback" not in data["get_config"], "get_config returned error"


def test_ncclient_get_config_call_with_filter_with_ftype_from_file():
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
            "filter": "salt://rpc/get_config_filter_ietf_interfaces.xml",
            "ftype": "subtree",
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
        assert "Traceback" not in data["get_config"], "get_config returned error"


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
    # pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "edit_config" in data, "No 'edit_config' output from '{}'".format(
            host_name
        )
        assert isinstance(data["edit_config"], str)
        assert len(data["edit_config"]) > 0
        assert "ok" in data["edit_config"]
        assert (
            "Traceback (most recent " not in data["edit_config"]
        ), "edit_config call returned error"

# test_ncclient_edit_config_call()

def test_ncclient_transaction_edit_config_call():
    """
    Test edit_config method call

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                transaction:
                    <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="...">
                      <ok/>
                    </rpc-reply>
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["transaction"],
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
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "error" not in data["transaction"][-1]

# test_ncclient_transaction_edit_config_call()

def test_ncclient_netconf_transaction_target_candidate():
    """
    Ret should look like::

    {'nrp1': {'ceos1': {'transaction': [{'discard_changes': '<rpc-reply '
                                                            'xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" '
                                                            'message-id="110">\n'
                                                            '  <ok/>\n'
                                                            '</rpc-reply>\n'},
                                        {'edit_config': '<rpc-reply '
                                                        'xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" '
                                                        'message-id="111">\n'
                                                        '  <ok/>\n'
                                                        '</rpc-reply>\n'},
                                        {'commit': '<rpc-reply '
                                                   'xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" '
                                                   'message-id="112">\n'
                                                   '  <ok/>\n'
                                                   '</rpc-reply>\n'}]},
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["transaction"],
        kwarg={
            "target": "candidate",
            "config": "salt://rpc/edit_config_ietf_interfaces.xml",
            "plugin": "ncclient",
        },
        tgt_type="glob",
        timeout=120,
    )
    # pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "error" not in data["transaction"][-1]
        assert "discard_changes" in data["transaction"][0]
        assert "edit_config" in data["transaction"][1]
        assert "commit" in data["transaction"][2]
        
# test_ncclient_netconf_transaction_target_candidate()
        
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
                        Plugin function: transaction

                        Helper function to run this edit-config flow:
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["help"],
        kwarg={"method_name": "transaction"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "help" in data, "No 'help' output from '{}'".format(host_name)
        assert isinstance(data["help"], str)
        assert len(data["help"]) > 0
        assert (
            "Traceback (most recent call last)" not in data["help"]
        ), "Help output contains error"


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
        assert "Traceback (most recent " not in data["dir"], "dir call returned error"


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
                        Plugin function: transaction

                        Helper function to run this edit-config flow:
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["help"],
        kwarg={"method_name": "transaction", "plugin": "scrapli"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "help" in data, "No 'help' output from '{}'".format(host_name)
        assert isinstance(data["help"], str)
        assert len(data["help"]) > 0
        assert "Traceback (most recent " not in data["help"], "help call returned error"


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
        assert (
            "Traceback (most recent " not in data["server_capabilities"]
        ), "server_capabilities call returned error"


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
            "filter_": "salt://rpc/get_config_filter_ietf_interfaces.xml",
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
        assert (
            "Traceback (most recent " not in data["get_config"]
        ), "get_config call returned error"


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
        timeout=120,
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


def test_scrapli_netconf_transaction_target_running():
    """
    Test transaction edit_config method call

    ret should look like::

    {'nrp1': {'ceos1': {'transaction': [
                                        {'edit_config': '<rpc-reply '
                                                        'xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" '
                                                        'message-id="107">\n'
                                                        '  <ok/>\n'
                                                        '</rpc-reply>\n'}]},
              'ceos2': {'transaction': [
                                        {'edit_config': '<rpc-reply '
                                                        'xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" '
                                                        'message-id="107">\n'
                                                        '  <ok/>\n'
                                                        '</rpc-reply>\n'}]}}}
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["transaction"],
        kwarg={
            "target": "running",
            "config": "salt://rpc/edit_config_ietf_interfaces.xml",
            "plugin": "scrapli",
        },
        tgt_type="glob",
        timeout=120,
    )
    # pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "error" not in data["transaction"][-1]
        assert "edit_config" in data["transaction"][0]

# test_scrapli_netconf_transaction_target_running()


def test_scrapli_netconf_transaction_target_candidate():
    """
    Ret should look like::

    {'nrp1': {'ceos1': {'transaction': [{'discard_changes': '<rpc-reply '
                                                            'xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" '
                                                            'message-id="110">\n'
                                                            '  <ok/>\n'
                                                            '</rpc-reply>\n'},
                                        {'edit_config': '<rpc-reply '
                                                        'xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" '
                                                        'message-id="111">\n'
                                                        '  <ok/>\n'
                                                        '</rpc-reply>\n'},
                                        {'commit': '<rpc-reply '
                                                   'xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" '
                                                   'message-id="112">\n'
                                                   '  <ok/>\n'
                                                   '</rpc-reply>\n'}]},
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["transaction"],
        kwarg={
            "target": "candidate",
            "config": "salt://rpc/edit_config_ietf_interfaces.xml",
            "plugin": "scrapli",
        },
        tgt_type="glob",
        timeout=120,
    )
    # pprint.pprint(ret)
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "error" not in data["transaction"][-1]
        assert "discard_changes" in data["transaction"][0]
        assert "edit_config" in data["transaction"][1]
        assert "commit" in data["transaction"][2]
        
# test_scrapli_netconf_transaction_target_candidate()

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
            "filter_": "salt://rpc/get_config_rpc_ietf_interfaces.xml",
            "plugin": "scrapli",
        },
        tgt_type="glob",
        timeout=120,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"]) == 2
    for host_name, data in ret["nrp1"].items():
        assert "rpc" in data, "No 'rpc' output from '{}'".format(host_name)
        assert isinstance(data["rpc"], str)
        assert len(data["rpc"]) > 0
        assert "Traceback (most recent " not in data["rpc"], "RPC call returned error"


def test_ncclient_nr_nc_get_config_with_xpath_data_processor():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nc",
        arg=["get_config"],
        kwarg={
            "source": "running",
            "filter": ["subtree", "salt://rpc/get_config_filter_ietf_interfaces.xml"],
            "xpath": "//interfaces/interface/name",
            "plugin": "ncclient"
        },
        tgt_type="glob",
        timeout=120,
    )   
    pprint.pprint(ret)
    # should print
    # {'nrp1': {'ceos1': {'get_config': '<name>Ethernet1</name>\n'
    #                                   '        \n'
    #                                   '\n'
    #                                   '<name>Loopback2</name>\n'
    #                                   '        \n'
    #                                   '\n'
    #                                   '<name>Loopback3</name>\n'
    #                                   '        \n'
    #                                   '\n'
    #                                   '<name>Loopback1</name>\n'
    #                                   '        \n'},
    #           'ceos2': {'get_config': '<name>Ethernet1</name>\n'
    #                                   '        \n'
    #                                   '\n'
    #                                   '<name>Loopback102</name>\n'
    #                                   '        \n'
    #                                   '\n'
    #                                   '<name>Loopback101</name>\n'
    #                                   '        \n'
    #                                   '\n'
    #                                   '<name>Loopback100</name>\n'
    #                                   '        \n'}}}
    assert "<name>" in ret["nrp1"]["ceos1"]["get_config"]
    assert "Ethernet" in ret["nrp1"]["ceos1"]["get_config"]
    assert "Loopback" in ret["nrp1"]["ceos1"]["get_config"]
    assert "<name>" in ret["nrp1"]["ceos2"]["get_config"]
    assert "Ethernet" in ret["nrp1"]["ceos2"]["get_config"]
    assert "Loopback" in ret["nrp1"]["ceos2"]["get_config"]
    
# test_ncclient_nr_nc_get_config_with_xpath_data_processor()
  
@skip_if_not_has_sandbox_iosxe_latest_1_netconf
def test_ncclient_transaction_edit_config_running_iosxe_always_on():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.nc",
        arg=["transaction"],
        kwarg={
            "target": "running",
            "config": "salt://rpc/edit_config_iosxe_ietf_interface.xml",
            "FB": "csr1000v-1",
            "plugin": "ncclient",
        },
        tgt_type="glob",
        timeout=60,
    )
    for host_name, data in ret["nrp2"].items():
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "error" not in data["transaction"][-1]
        assert "edit_config" in data["transaction"][0]
        assert "validate" in data["transaction"][1]
        
# test_ncclient_transaction_edit_config_running_iosxe_always_on()

@skip_if_not_has_sandbox_iosxe_latest_1_netconf
def test_scrapli_transaction_edit_config_running_iosxe_always_on():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.nc",
        arg=["transaction"],
        kwarg={
            "target": "running",
            "config": "salt://rpc/edit_config_iosxe_ietf_interface.xml",
            "FB": "csr1000v-1",
            "plugin": "scrapli",
        },
        tgt_type="glob",
        timeout=60,
    )
    for host_name, data in ret["nrp2"].items():
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "error" not in data["transaction"][-1]
        assert "edit_config" in data["transaction"][0]
        assert "validate" in data["transaction"][1]
        
# test_scrapli_transaction_edit_config_running_iosxe_always_on()

@skip_if_not_has_sandbox_iosxr_latest_1_netconf
def test_ncclient_transaction_edit_config_iosxr_always_on():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.nc",
        arg=["transaction"],
        kwarg={
            "config": "salt://rpc/edit_config_iosxr_openconf_interface.xml",
            "FB": "iosxr1",
            "plugin": "ncclient",
        },
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    for host_name, data in ret["nrp2"].items():
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "discard_changes" in data["transaction"][0] and "<ok/>" in data["transaction"][0]["discard_changes"]
        assert "edit_config" in data["transaction"][1] and "<ok/>" in data["transaction"][1]["edit_config"]
        assert "validate" in data["transaction"][2] and "<ok/>" in data["transaction"][2]["validate"]
        assert "commit_confirmed" in data["transaction"][3] and "<ok/>" in data["transaction"][3]["commit_confirmed"]
        assert "commit" in data["transaction"][4] and "<ok/>" in data["transaction"][4]["commit"]
        
# test_ncclient_transaction_edit_config_iosxr_always_on()

@skip_if_not_has_sandbox_iosxr_latest_1_netconf
def test_ncclient_transaction_edit_config_invalid_iosxr_always_on():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.nc",
        arg=["transaction"],
        kwarg={
            "config": "salt://rpc/edit_config_iosxr_openconf_interface_invalid.xml",
            "FB": "iosxr1",
            "plugin": "ncclient",
        },
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    for host_name, data in ret["nrp2"].items():
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "discard_changes" in data["transaction"][0] and "<ok/>" in data["transaction"][0]["discard_changes"]
        assert "error" in data["transaction"][1] and "fatal" in data["transaction"][1]["error"]
        assert "discard_changes" in data["transaction"][2] and "<ok/>" in data["transaction"][2]["discard_changes"]
        
# test_ncclient_transaction_edit_config_invalid_iosxr_always_on() 

@skip_if_not_has_sandbox_iosxr_latest_1_netconf
def test_scrapli_transaction_edit_config_invalid_iosxr_always_on():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.nc",
        arg=["transaction"],
        kwarg={
            "config": "salt://rpc/edit_config_iosxr_openconf_interface_invalid.xml",
            "FB": "iosxr1",
            "plugin": "scrapli",
        },
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    for host_name, data in ret["nrp2"].items():
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "discard_changes" in data["transaction"][0] and "<ok/>" in data["transaction"][0]["discard_changes"]
        assert "error" in data["transaction"][1] and "fatal" in data["transaction"][1]["error"]
        assert "discard_changes" in data["transaction"][2] and "<ok/>" in data["transaction"][2]["discard_changes"]
        
# test_scrapli_transaction_edit_config_invalid_iosxr_always_on()

@skip_if_not_has_sandbox_iosxr_latest_1_netconf
def test_scrapli_transaction_edit_config_iosxr_always_on():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.nc",
        arg=["transaction"],
        kwarg={
            "config": "salt://rpc/edit_config_iosxr_openconf_interface.xml",
            "FB": "iosxr1",
            "plugin": "scrapli",
        },
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    for host_name, data in ret["nrp2"].items():
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "discard_changes" in data["transaction"][0] and "<ok/>" in data["transaction"][0]["discard_changes"]
        assert "edit_config" in data["transaction"][1] and "<ok/>" in data["transaction"][1]["edit_config"]
        assert "validate" in data["transaction"][2] and "<ok/>" in data["transaction"][2]["validate"]
        assert "commit" in data["transaction"][3] and "<ok/>" in data["transaction"][3]["commit"]
        
# test_scrapli_transaction_edit_config_iosxr_always_on()


@skip_if_not_has_sandbox_nxos_latest_1_netconf
def test_ncclient_transaction_edit_config_nxos_always_on():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.nc",
        arg=["transaction"],
        kwarg={
            "config": "salt://rpc/edit_config_nxos_openconf_interface.xml",
            "FB": "nxos1",
            "plugin": "ncclient",
            "confirmed": False, # confirmed does not work well with NXOS for some reason, consequetive commits by scrapli are failing
        },
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    for host_name, data in ret["nrp2"].items():
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "discard_changes" in data["transaction"][0] and "<ok/>" in data["transaction"][0]["discard_changes"]
        assert "edit_config" in data["transaction"][1] and "<ok/>" in data["transaction"][1]["edit_config"]
        assert "validate" in data["transaction"][2] and "<ok/>" in data["transaction"][2]["validate"]
        assert "commit" in data["transaction"][3] and "<ok/>" in data["transaction"][3]["commit"]
        
# test_ncclient_transaction_edit_config_nxos_always_on()


@skip_if_not_has_sandbox_nxos_latest_1_netconf
def test_scrapli_transaction_edit_config_nxos_always_on():
    ret = client.cmd(
        tgt="nrp2",
        fun="nr.nc",
        arg=["transaction"],
        kwarg={
            "config": "salt://rpc/edit_config_nxos_openconf_interface.xml",
            "FB": "nxos1",
            "plugin": "scrapli",
        },
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    for host_name, data in ret["nrp2"].items():
        assert "transaction" in data, "No 'transaction' output from '{}'".format(host_name)
        assert isinstance(data["transaction"], list)
        assert len(data["transaction"]) > 0
        assert "discard_changes" in data["transaction"][0] and "<ok/>" in data["transaction"][0]["discard_changes"]
        assert "edit_config" in data["transaction"][1] and "<ok/>" in data["transaction"][1]["edit_config"]
        assert "validate" in data["transaction"][2] and "<ok/>" in data["transaction"][2]["validate"]
        assert "commit" in data["transaction"][3] and "<ok/>" in data["transaction"][3]["commit"]
        
# test_scrapli_transaction_edit_config_nxos_always_on()