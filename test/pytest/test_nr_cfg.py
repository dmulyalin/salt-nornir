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

# list of workds that should ne be in good results
INVALID = ["Traceback", "Invalid input"]

def test_nr_cfg_inline_commands_plugin_netmiko():
    """
    This test pushes inline config commands to hosts.

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                netmiko_send_config:
                    ----------
                    changed:
                        True
                    diff:
                    exception:
                        None
                    failed:
                        False
                    result:
                        configure terminal
                        ceos1(config)#ntp server 1.1.1.1
                        ntp server 1.1.1.2
                        ceos1(config)#ntp server 1.1.1.2
                        ceos1(config)#end
                        ceos1#
            ceos2:
                ----------
                netmiko_send_config:
                    ----------
                    changed:
                        True
                    diff:
                    exception:
                        None
                    failed:
                        False
                    result:
                        configure terminal
                        ceos2(config)#ntp server 1.1.1.1
                        ntp server 1.1.1.2
                        ceos2(config)#ntp server 1.1.1.2
                        ceos2(config)#end
                        ceos2#
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=["ntp server 1.1.1.1", "ntp server 1.1.1.2"],
        kwarg={"plugin": "netmiko"},
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["netmiko_send_config"]["changed"] is True
        assert results["netmiko_send_config"]["exception"] is None
        assert results["netmiko_send_config"]["failed"] is False
        assert isinstance(results["netmiko_send_config"]["result"], str)
        assert len(results["netmiko_send_config"]["result"]) > 0
        assert all(i not in results["netmiko_send_config"]["result"] for i in INVALID)

        
def test_nr_cfg_commands_argument_string_plugin_netmiko():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={"plugin": "netmiko", "commands": "ntp server 1.1.1.1"},
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["netmiko_send_config"]["changed"] is True
        assert results["netmiko_send_config"]["exception"] is None
        assert results["netmiko_send_config"]["failed"] is False
        assert isinstance(results["netmiko_send_config"]["result"], str)
        assert len(results["netmiko_send_config"]["result"]) > 0
        assert all(i not in results["netmiko_send_config"]["result"] for i in INVALID)
        
        
def test_nr_cfg_commands_argument_list_plugin_netmiko():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={"plugin": "netmiko", "commands": ["ntp server 1.1.1.1", "ntp server 1.1.1.2"]},
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["netmiko_send_config"]["changed"] is True
        assert results["netmiko_send_config"]["exception"] is None
        assert results["netmiko_send_config"]["failed"] is False
        assert isinstance(results["netmiko_send_config"]["result"], str)
        assert len(results["netmiko_send_config"]["result"]) > 0
        assert all(i not in results["netmiko_send_config"]["result"] for i in INVALID)
               
               
def test_nr_cfg_multiline_commands_string_plugin_netmiko():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=["ntp server 1.1.1.1\nntp server 1.1.1.2"],
        kwarg={"plugin": "netmiko"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["netmiko_send_config"]["changed"] is True
        assert results["netmiko_send_config"]["exception"] is None
        assert results["netmiko_send_config"]["failed"] is False
        assert isinstance(results["netmiko_send_config"]["result"], str)
        assert len(results["netmiko_send_config"]["result"]) > 0
        assert all(i not in results["netmiko_send_config"]["result"] for i in INVALID)
        

def test_nr_cfg_escaped_multiline_commands_string_plugin_netmiko():
    """
    Multiline cmmand string has \\n escaped \n in it
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=["interface Lo1", "description test\\nstring"],
        kwarg={"plugin": "netmiko", "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["netmiko_send_config"]["changed"] is True
        assert results["netmiko_send_config"]["exception"] is None
        assert results["netmiko_send_config"]["failed"] is False
        assert isinstance(results["netmiko_send_config"]["result"], str)
        assert len(results["netmiko_send_config"]["result"]) > 0
        assert all(i not in results["netmiko_send_config"]["result"] for i in INVALID)
        
        
def test_nr_cfg_from_file_plugin_netmiko():
    """
    This test pushes static config from same file to all hosts

    ret should be::

        nrp1:
            ----------
            ceos1:
                ----------
                netmiko_send_config:
                    ----------
                    changed:
                        True
                    diff:
                    exception:
                        None
                    failed:
                        False
                    result:
                        configure terminal
                        ceos1(config)#ntp server 2.2.2.2
                        ceos1(config)#ntp server 2.2.2.3
                        ceos1(config)#end
                        ceos1#
            ceos2:
                ----------
                netmiko_send_config:
                    ----------
                    changed:
                        True
                    diff:
                    exception:
                        None
                    failed:
                        False
                    result:
                        configure terminal
                        ceos2(config)#ntp server 2.2.2.2
                        ceos2(config)#ntp server 2.2.2.3
                        ceos2(config)#end
                        ceos2#
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={"plugin": "netmiko", "filename": "salt://templates/ntp_config.txt"},
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["netmiko_send_config"]["changed"] is True
        assert results["netmiko_send_config"]["exception"] is None
        assert results["netmiko_send_config"]["failed"] is False
        assert isinstance(results["netmiko_send_config"]["result"], str)
        assert len(results["netmiko_send_config"]["result"]) > 0
        assert all(i not in results["netmiko_send_config"]["result"] for i in INVALID)


def test_nr_cfg_from_file_template_plugin_netmiko():
    """
        This test generates config using Nornir inventory

        ret should look like::

    nrp1:
        ----------
        ceos1:
            ----------
            netmiko_send_config:
                ----------
                changed:
                    True
                diff:
                exception:
                    None
                failed:
                    False
                result:
                    configure terminal
                    ceos1(config)#
                    ceos1(config)#ntp server 3.3.3.3
                    ceos1(config)#
                    ceos1(config)#ntp server 3.3.3.4

                    ceos1(config)#
                    ceos1(config)#
                    ceos1(config)#
                    ceos1(config)#logging host 1.2.3.4
                    ceos1(config)#
                    ceos1(config)#logging host 4.3.2.1
                    ceos1(config)#end
                    ceos1#
        ceos2:
            ----------
            netmiko_send_config:
                ----------
                changed:
                    True
                diff:
                exception:
                    None
                failed:
                    False
                result:
                    configure terminal
                    ceos2(config)#
                    ceos2(config)#ntp server 3.3.3.3
                    ceos2(config)#
                    ceos2(config)#ntp server 3.3.3.4

                    ceos2(config)#
                    ceos2(config)#
                    ceos2(config)#
                    ceos2(config)#logging host 1.2.3.4
                    ceos2(config)#
                    ceos2(config)#logging host 4.3.2.1
                    ceos2(config)#end
                    ceos2#
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "plugin": "netmiko",
            "filename": "salt://templates/ntp_config_template.txt",
        },
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["netmiko_send_config"]["changed"] is True
        assert results["netmiko_send_config"]["exception"] is None
        assert results["netmiko_send_config"]["failed"] is False
        assert isinstance(results["netmiko_send_config"]["result"], str)
        assert len(results["netmiko_send_config"]["result"]) > 0


def test_nr_cfg_from_file_per_host_plugin_netmiko():
    """
    To test per-device static config push

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                netmiko_send_config:
                    ----------
                    changed:
                        True
                    diff:
                    exception:
                        None
                    failed:
                        False
                    result:
                        configure terminal
                        ceos1(config)#snmp-server location "North West Hall DC1"
                        ceos1(config)#end
                        ceos1#
            ceos2:
                ----------
                netmiko_send_config:
                    ----------
                    changed:
                        True
                    diff:
                    exception:
                        None
                    failed:
                        False
                    result:
                        configure terminal
                        ceos2(config)#snmp-server location "East City Warehouse"
                        ceos2(config)#end
                        ceos2#
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "plugin": "netmiko",
            "filename": "salt://templates/per_host_cfg_snmp/{{ host.name }}.txt",
        },
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["netmiko_send_config"]["changed"] is True
        assert results["netmiko_send_config"]["exception"] is None
        assert results["netmiko_send_config"]["failed"] is False
        assert isinstance(results["netmiko_send_config"]["result"], str)
        assert len(results["netmiko_send_config"]["result"]) > 0
    # check result contains correct config
    assert (
        "North West Hall DC1" in ret["nrp1"]["ceos1"]["netmiko_send_config"]["result"]
    )
    assert (
        "East City Warehouse" in ret["nrp1"]["ceos2"]["netmiko_send_config"]["result"]
    )


def test_nr_cfg_from_file_per_host_template_plugin_netmiko():
    """
    Push per host templated config

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                netmiko_send_config:
                    ----------
                    changed:
                        True
                    diff:
                    exception:
                        None
                    failed:
                        False
                    result:
                        configure terminal
                        ceos1(config)#snmp-server location North West Hall DC1
                        ceos1(config)#end
                        ceos1#
            ceos2:
                ----------
                netmiko_send_config:
                    ----------
                    changed:
                        True
                    diff:
                    exception:
                        None
                    failed:
                        False
                    result:
                        configure terminal
                        ceos2(config)#snmp-server location Address East City Warehouse
                        ceos2(config)#end
                        ceos2#
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "plugin": "netmiko",
            "filename": "salt://templates/per_host_cfg_snmp_template/{{ host.name }}.txt",
        },
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["netmiko_send_config"]["changed"] is True
        assert results["netmiko_send_config"]["exception"] is None
        assert results["netmiko_send_config"]["failed"] is False
        assert isinstance(results["netmiko_send_config"]["result"], str)
        assert len(results["netmiko_send_config"]["result"]) > 0
    # check result contains correct config
    assert (
        "North West Hall DC1" in ret["nrp1"]["ceos1"]["netmiko_send_config"]["result"]
    )
    assert (
        "East City Warehouse" in ret["nrp1"]["ceos2"]["netmiko_send_config"]["result"]
    )


def test_nr_cfg_from_non_existing_file_fail():
    """
    To test per-device static config push FAILURE DUE TO NON-EXISTING FILE
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "plugin": "netmiko",
            "filename": "salt://templates/per_host_cfg_snmp/{{ host.name }}_non_exist.txt",
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert ret["nrp1"]["ceos1"]["netmiko_send_config"]["failed"] == True
    assert ret["nrp1"]["ceos2"]["netmiko_send_config"]["failed"] == True   
    assert "Traceback" in ret["nrp1"]["ceos1"]["netmiko_send_config"]["exception"]
    assert "Traceback" in ret["nrp1"]["ceos2"]["netmiko_send_config"]["exception"] 

def test_nr_cfg_inline_commands_plugin_scrapli():
    """
    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                scrapli_send_config:
                    ----------
                    changed:
                        True
                    diff:
                    exception:
                        None
                    failed:
                        False
                    result:
                        ntp server 1.1.1.1
                        ntp server 1.1.1.2
            ceos2:
                ----------
                scrapli_send_config:
                    ----------
                    changed:
                        True
                    diff:
                    exception:
                        None
                    failed:
                        False
                    result:
                        ntp server 1.1.1.1
                        ntp server 1.1.1.2
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=["ntp server 1.1.1.1", "ntp server 1.1.1.2"],
        kwarg={"plugin": "scrapli"},
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert results["scrapli_send_config"]["changed"] is True
        assert results["scrapli_send_config"]["exception"] is None
        assert results["scrapli_send_config"]["failed"] is False
        assert isinstance(results["scrapli_send_config"]["result"], str)
        assert len(results["scrapli_send_config"]["result"]) > 0


def test_nr_cfg_multiline_commands_string_plugin_scrapli():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=["interface Lo1", "description test\\nstring"],
        kwarg={"plugin": "scrapli", "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for host, results in ret["nrp1"].items():
        assert results["scrapli_send_config"]["changed"] is True
        assert results["scrapli_send_config"]["exception"] is None
        assert results["scrapli_send_config"]["failed"] is False
        assert isinstance(results["scrapli_send_config"]["result"], str)
        assert len(results["scrapli_send_config"]["result"]) > 0
        assert all(i not in results["scrapli_send_config"]["result"] for i in INVALID)
        
        
def test_nr_cfg_escaped_multiline_commands_string_plugin_scrapli():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=["ntp server 1.1.1.1\nntp server 1.1.1.2"],
        kwarg={"plugin": "scrapli"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for host, results in ret["nrp1"].items():
        assert results["scrapli_send_config"]["changed"] is True
        assert results["scrapli_send_config"]["exception"] is None
        assert results["scrapli_send_config"]["failed"] is False
        assert isinstance(results["scrapli_send_config"]["result"], str)
        assert len(results["scrapli_send_config"]["result"]) > 0
        assert all(i not in results["scrapli_send_config"]["result"] for i in INVALID)
        
        
def test_nr_cfg_inline_commands_plugin_napalm():
    """
    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                napalm_configure:
                    ----------
                    changed:
                        True
                    diff:
                        @@ -13,9 +13,6 @@
                         agent LicenseManager shutdown
                         !
                         hostname ceos1
                        -!
                        -ntp server 1.1.1.1
                        -ntp server 1.1.1.2
                         !
                         spanning-tree mode mstp
                         !
                    exception:
                        None
                    failed:
                        False
                    result:
                        None
            ceos2:
                ----------
                napalm_configure:
                    ----------
                    changed:
                        True
                    diff:
                        @@ -13,9 +13,6 @@
                         agent LicenseManager shutdown
                         !
                         hostname ceos2
                        -!
                        -ntp server 1.1.1.1
                        -ntp server 1.1.1.2
                         !
                         spanning-tree mode mstp
                         !
                    exception:
                        None
                    failed:
                        False
                    result:
                        None
    """
    # delete config first
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=["no ntp server 1.1.1.1", "no ntp server 1.1.1.2"],
        kwarg={"plugin": "napalm"},
        tgt_type="glob",
        timeout=60,
    )
    # apply it again
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=["ntp server 1.1.1.1", "ntp server 1.1.1.2"],
        kwarg={"plugin": "napalm"},
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert results["napalm_configure"]["changed"] is True
        assert results["napalm_configure"]["exception"] is None
        assert results["napalm_configure"]["failed"] is False
        assert isinstance(results["napalm_configure"]["diff"], str)
        assert len(results["napalm_configure"]["diff"]) > 0


def test_nr_cfg_plugin_netmiko_command_batch_1():
    config = ["logging host 1.2.3.4", "logging host 1.2.3.5", "logging host 1.2.3.6"]
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=config,
        kwarg={"plugin": "netmiko", "batch": 1},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for cmd in config:
        assert cmd in ret["nrp1"]["ceos1"]["netmiko_send_config"]["result"], "Command not sent to ceos1 '{}'".format(cmd)
        assert cmd in ret["nrp1"]["ceos2"]["netmiko_send_config"]["result"], "Command not sent to ceos2 '{}'".format(cmd)
        
# test_nr_cfg_plugin_netmiko_command_batch_1()


def test_nr_cfg_plugin_netmiko_command_batch_invalid():
    config = ["logging host 1.2.3.4", "logging host 1.2.3.5", "logging host 1.2.3.6"]
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=config,
        kwarg={"plugin": "netmiko", "batch": -100},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for cmd in config:
        assert cmd in ret["nrp1"]["ceos1"]["netmiko_send_config"]["result"], "Command not sent to ceos1 '{}'".format(cmd)
        assert cmd in ret["nrp1"]["ceos2"]["netmiko_send_config"]["result"], "Command not sent to ceos2 '{}'".format(cmd)
        
# test_nr_cfg_plugin_netmiko_command_batch_1()


def test_nr_cfg_plugin_netmiko_command_batch_2():
    config = ["logging host 1.2.3.4", "logging host 1.2.3.5", "logging host 1.2.3.6"]
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=config,
        kwarg={"plugin": "netmiko", "batch": 2},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for cmd in config:
        assert cmd in ret["nrp1"]["ceos1"]["netmiko_send_config"]["result"], "Command not sent to ceos1 '{}'".format(cmd)
        assert cmd in ret["nrp1"]["ceos2"]["netmiko_send_config"]["result"], "Command not sent to ceos2 '{}'".format(cmd)
        
# test_nr_cfg_plugin_netmiko_command_batch_1()





















def test_nr_cfg_inline_commands_plugin_pyats():
    """
    This test pushes inline config commands to hosts.
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=["ntp server 1.1.1.1", "ntp server 1.1.1.2"],
        kwarg={"plugin": "pyats"},
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["pyats_send_config"]["changed"] is True
        assert results["pyats_send_config"]["exception"] is None
        assert results["pyats_send_config"]["failed"] is False
        assert isinstance(results["pyats_send_config"]["result"], str)
        assert len(results["pyats_send_config"]["result"]) > 0


def test_nr_cfg_from_file_plugin_pyats():
    """
    This test pushes static config from same file to all hosts
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={"plugin": "pyats", "filename": "salt://templates/ntp_config.txt"},
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["pyats_send_config"]["changed"] is True
        assert results["pyats_send_config"]["exception"] is None
        assert results["pyats_send_config"]["failed"] is False
        assert isinstance(results["pyats_send_config"]["result"], str)
        assert len(results["pyats_send_config"]["result"]) > 0


def test_nr_cfg_from_file_template_plugin_pyats():
    """
    This test generates config using Nornir inventory
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "plugin": "pyats",
            "filename": "salt://templates/ntp_config_template.txt",
        },
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["pyats_send_config"]["changed"] is True
        assert results["pyats_send_config"]["exception"] is None
        assert results["pyats_send_config"]["failed"] is False
        assert isinstance(results["pyats_send_config"]["result"], str)
        assert len(results["pyats_send_config"]["result"]) > 0


def test_nr_cfg_from_file_per_host_plugin_pyats():
    """
    To test per-device static config push
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "plugin": "pyats",
            "filename": "salt://templates/per_host_cfg_snmp/{{ host.name }}.txt",
        },
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["pyats_send_config"]["changed"] is True
        assert results["pyats_send_config"]["exception"] is None
        assert results["pyats_send_config"]["failed"] is False
        assert isinstance(results["pyats_send_config"]["result"], str)
        assert len(results["pyats_send_config"]["result"]) > 0
    # check result contains correct config
    assert (
        "North West Hall DC1" in ret["nrp1"]["ceos1"]["pyats_send_config"]["result"]
    )
    assert (
        "East City Warehouse" in ret["nrp1"]["ceos2"]["pyats_send_config"]["result"]
    )


def test_nr_cfg_from_file_per_host_template_plugin_pyats():
    """
    Push per host templated config
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "plugin": "pyats",
            "filename": "salt://templates/per_host_cfg_snmp_template/{{ host.name }}.txt",
        },
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert results["pyats_send_config"]["changed"] is True
        assert results["pyats_send_config"]["exception"] is None
        assert results["pyats_send_config"]["failed"] is False
        assert isinstance(results["pyats_send_config"]["result"], str)
        assert len(results["pyats_send_config"]["result"]) > 0
    # check result contains correct config
    assert (
        "North West Hall DC1" in ret["nrp1"]["ceos1"]["pyats_send_config"]["result"]
    )
    assert (
        "East City Warehouse" in ret["nrp1"]["ceos2"]["pyats_send_config"]["result"]
    )


def test_nr_cfg_from_non_existing_file_fail_pyats():
    """
    To test per-device static config push FAILURE DUE TO NON-EXISTING FILE
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "plugin": "pyats",
            "filename": "salt://templates/per_host_cfg_snmp/{{ host.name }}_non_exist.txt",
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert ret["nrp1"]["ceos1"]["pyats_send_config"]["failed"] == True
    assert ret["nrp1"]["ceos2"]["pyats_send_config"]["failed"] == True   
    assert "Traceback" in ret["nrp1"]["ceos1"]["pyats_send_config"]["exception"]
    assert "Traceback" in ret["nrp1"]["ceos2"]["pyats_send_config"]["exception"] 
        
        
def test_nr_cfg_plugin_pyats_command_batch():
    config = ["logging host 1.2.3.4", "logging host 1.2.3.5", "logging host 1.2.3.6"]
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=config,
        kwarg={"plugin": "pyats", "bulk": True, "bulk_chunk_lines": 1},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for cmd in config:
        assert cmd in ret["nrp1"]["ceos1"]["pyats_send_config"]["result"], "Command not sent to ceos1 '{}'".format(cmd)
        assert cmd in ret["nrp1"]["ceos2"]["pyats_send_config"]["result"], "Command not sent to ceos2 '{}'".format(cmd)
        
        
def test_nr_cfg_template_using_context_argument():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "plugin": "netmiko", 
            "filename": "salt://templates/test_context_argument.txt",
            "context": {
                "log_host": "9.9.9.9", 
                "ntp_server": "4.3.2.1",
            }
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert ret["nrp1"]["ceos1"]["netmiko_send_config"]["failed"] == False
    assert "logging host 9.9.9.9" in ret["nrp1"]["ceos1"]["netmiko_send_config"]["result"]
    assert "ntp server 4.3.2.1" in ret["nrp1"]["ceos1"]["netmiko_send_config"]["result"]
    assert ret["nrp1"]["ceos2"]["netmiko_send_config"]["failed"] == False
    assert "logging host 9.9.9.9" in ret["nrp1"]["ceos2"]["netmiko_send_config"]["result"]
    assert "ntp server 4.3.2.1" in ret["nrp1"]["ceos2"]["netmiko_send_config"]["result"]
    
# test_nr_cfg_template_using_context_argument()
    
    
def test_inline_config_template_string_netmiko():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "config": "snmp-server location {{ host.location }}",
            "plugin": "netmiko"
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "snmp-server location North" in ret["nrp1"]["ceos1"]["netmiko_send_config"]["result"]
    assert "snmp-server location East" in ret["nrp1"]["ceos2"]["netmiko_send_config"]["result"]
    assert ret["nrp1"]["ceos1"]["netmiko_send_config"]["failed"] == False
    assert ret["nrp1"]["ceos2"]["netmiko_send_config"]["failed"] == False
    assert ret["nrp1"]["ceos1"]["netmiko_send_config"]["changed"] == True
    assert ret["nrp1"]["ceos2"]["netmiko_send_config"]["changed"] == True
    
    
def test_inline_config_template_string_napalm():
    ret_del = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "config": "no snmp-server location {{ host.location }}",
            "plugin": "netmiko"
        },
        tgt_type="glob",
        timeout=60,
    )
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "config": "snmp-server location {{ host.location }}",
            "plugin": "napalm"
        },
        tgt_type="glob",
        timeout=60,
    )
    print("Deleted config using netmiko:")
    pprint.pprint(ret_del)
    print("Applied config using NAPALAM:")
    pprint.pprint(ret)
    assert "snmp-server location North" in ret["nrp1"]["ceos1"]["napalm_configure"]["diff"]
    assert "snmp-server location East" in ret["nrp1"]["ceos2"]["napalm_configure"]["diff"]
    assert ret["nrp1"]["ceos1"]["napalm_configure"]["failed"] == False
    assert ret["nrp1"]["ceos2"]["napalm_configure"]["failed"] == False
    assert ret["nrp1"]["ceos1"]["napalm_configure"]["changed"] == True
    assert ret["nrp1"]["ceos2"]["napalm_configure"]["changed"] == True

def test_inline_config_template_string_scrapli():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "config": "snmp-server location {{ host.location }}",
            "plugin": "scrapli"
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "snmp-server location North" in ret["nrp1"]["ceos1"]["scrapli_send_config"]["result"]
    assert "snmp-server location East" in ret["nrp1"]["ceos2"]["scrapli_send_config"]["result"]
    assert ret["nrp1"]["ceos1"]["scrapli_send_config"]["failed"] == False
    assert ret["nrp1"]["ceos2"]["scrapli_send_config"]["failed"] == False
    assert ret["nrp1"]["ceos1"]["scrapli_send_config"]["changed"] == True
    assert ret["nrp1"]["ceos2"]["scrapli_send_config"]["changed"] == True

def test_inline_config_template_string_pyats():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "config": "snmp-server location {{ host.location }}",
            "plugin": "pyats"
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "snmp-server location North" in ret["nrp1"]["ceos1"]["pyats_send_config"]["result"]
    assert "snmp-server location East" in ret["nrp1"]["ceos2"]["pyats_send_config"]["result"]
    assert ret["nrp1"]["ceos1"]["pyats_send_config"]["failed"] == False
    assert ret["nrp1"]["ceos2"]["pyats_send_config"]["failed"] == False
    assert ret["nrp1"]["ceos1"]["pyats_send_config"]["changed"] == True
    assert ret["nrp1"]["ceos2"]["pyats_send_config"]["changed"] == True
    
def test_inline_config_dict_netmiko():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "config": {
                "ceos1": "snmp-server location {{ host.location }}",
                "ceos2": "snmp-server location {{ host.location }}"
            },
            "plugin": "netmiko",
            "FL": ["ceos1", "ceos2"]
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "snmp-server location North" in ret["nrp1"]["ceos1"]["netmiko_send_config"]["result"]
    assert "snmp-server location East" in ret["nrp1"]["ceos2"]["netmiko_send_config"]["result"]
    assert ret["nrp1"]["ceos1"]["netmiko_send_config"]["failed"] == False
    assert ret["nrp1"]["ceos2"]["netmiko_send_config"]["failed"] == False
    assert ret["nrp1"]["ceos1"]["netmiko_send_config"]["changed"] == True
    assert ret["nrp1"]["ceos2"]["netmiko_send_config"]["changed"] == True

def test_inline_config_dict_netmiko_host_missing_fail():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg",
        arg=[],
        kwarg={
            "config": {
                "ceos1": "snmp-server location {{ host.location }}",
            },
            "plugin": "netmiko",
            "FL": ["ceos1", "ceos2"]
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "snmp-server location North" in ret["nrp1"]["ceos1"]["netmiko_send_config"]["result"]
    assert "Traceback" in ret["nrp1"]["ceos2"]["netmiko_send_config"]["result"]
    assert ret["nrp1"]["ceos1"]["netmiko_send_config"]["failed"] == False
    assert ret["nrp1"]["ceos2"]["netmiko_send_config"]["failed"] == True
    assert ret["nrp1"]["ceos1"]["netmiko_send_config"]["changed"] == True
    assert ret["nrp1"]["ceos2"]["netmiko_send_config"]["changed"] == False