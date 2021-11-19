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
    for host, results in ret.items():
        assert isinstance(results, str)
        assert "CommandExecutionError: Failed to get" in results


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