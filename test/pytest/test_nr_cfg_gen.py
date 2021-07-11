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


def test_nr_cfg_gen_from_static_file():
    """
    Test configuration generation from file.

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                Rendered salt://templates/ntp_config.txt config:
                    ntp server 2.2.2.2
                    ntp server 2.2.2.3
            ceos2:
                ----------
                Rendered salt://templates/ntp_config.txt config:
                    ntp server 2.2.2.2
                    ntp server 2.2.2.3
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={"filename": "salt://templates/ntp_config.txt"},
        tgt_type="glob",
        timeout=60,
    )
    task_name = "salt_cfg_gen"
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert task_name in results
        assert isinstance(results[task_name], str)
        assert len(results[task_name]) > 0


def test_nr_cfg_gen_from_template_file():
    """
    Test configuration generation from template file.

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                Rendered salt://templates/ntp_config_template.txt config:

                    ntp server 3.3.3.3
                    ntp server 3.3.3.4
                    logging host 1.2.3.4
                    logging host 4.3.2.1
            ceos2:
                ----------
                Rendered salt://templates/ntp_config_template.txt config:

                    ntp server 3.3.3.3
                    ntp server 3.3.3.4
                    logging host 1.2.3.4
                    logging host 4.3.2.1
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={"filename": "salt://templates/ntp_config_template.txt"},
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert isinstance(results["salt_cfg_gen"], str)
        assert len(results["salt_cfg_gen"]) > 0
        assert "ntp" in results["salt_cfg_gen"] and "logging" in results["salt_cfg_gen"]


def test_nr_cfg_gen_from_static_file_per_host():
    """
    Test configuration generation from file per host.

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                Rendered salt://templates/per_host_cfg_snmp/{{ host.name }}.txt config:
                    snmp-server location "North West Hall DC1"
            ceos2:
                ----------
                Rendered salt://templates/per_host_cfg_snmp/{{ host.name }}.txt config:
                    snmp-server location "East City Warehouse"
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={"filename": "salt://templates/per_host_cfg_snmp/{{ host.name }}.txt"},
        tgt_type="glob",
        timeout=60,
    )
    task_name = "salt_cfg_gen"
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert task_name in results
        assert isinstance(results[task_name], str)
        assert len(results[task_name]) > 0
    assert "North" in ret["nrp1"]["ceos1"][task_name]
    assert "East" in ret["nrp1"]["ceos2"][task_name]


def test_nr_cfg_gen_from_template_file_per_host():
    """
    Test configuration generation from file per host.

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                Rendered salt://templates/per_host_cfg_snmp_template/{{ host.name }}.txt config:
                    snmp-server location North West Hall DC1
            ceos2:
                ----------
                Rendered salt://templates/per_host_cfg_snmp_template/{{ host.name }}.txt config:
                    snmp-server location Address East City Warehouse
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={
            "filename": "salt://templates/per_host_cfg_snmp_template/{{ host.name }}.txt"
        },
        tgt_type="glob",
        timeout=60,
    )
    task_name = "salt_cfg_gen"
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert task_name in results
        assert isinstance(results[task_name], str)
        assert len(results[task_name]) > 0
    assert "North" in ret["nrp1"]["ceos1"][task_name]
    assert "East" in ret["nrp1"]["ceos2"][task_name]
