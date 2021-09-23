import logging
import pprint
import json

log = logging.getLogger(__name__)

try:
    import salt.client
    import salt.config
    import salt.utils.event
    import salt.exceptions

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


def test_ttp_parser_template_loaded_from_master_nr_cli():
    """ DataProcessor parse_ttp function """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show version"],
        kwarg={
            "run_ttp": "salt://ttp/ceos_show_version.txt"
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert isinstance(ret["nrp1"]["ceos1"]["run_ttp"], list)
    assert isinstance(ret["nrp1"]["ceos2"]["run_ttp"], list)
    assert isinstance(ret["nrp1"]["ceos1"]["run_ttp"][0], dict)
    assert isinstance(ret["nrp1"]["ceos2"]["run_ttp"][0], dict)
    assert "tools_version" in ret["nrp1"]["ceos1"]["run_ttp"][0]
    assert "tools_version" in ret["nrp1"]["ceos2"]["run_ttp"][0]
    
# test_ttp_parser_template_loaded_from_master_nr_cli()


def test_ttp_parser_inline_template_nr_cli():
    """ DataProcessor parse_ttp function """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show version"],
        kwarg={
            "run_ttp": "Free memory: {{ total_memory}} kB"
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert isinstance(ret["nrp1"]["ceos1"]["run_ttp"], list)
    assert isinstance(ret["nrp1"]["ceos2"]["run_ttp"], list)
    assert isinstance(ret["nrp1"]["ceos1"]["run_ttp"][0], dict)
    assert isinstance(ret["nrp1"]["ceos2"]["run_ttp"][0], dict)
    assert "total_memory" in ret["nrp1"]["ceos1"]["run_ttp"][0]
    assert "total_memory" in ret["nrp1"]["ceos2"]["run_ttp"][0]
    
# test_ttp_parser_inline_template_nr_cli()