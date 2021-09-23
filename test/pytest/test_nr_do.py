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


def test_nr_do_call_to_single_step_in_pillar():
    ret = client.cmd(
        tgt="nrp1", fun="nr.do", arg=["awr"], kwarg={}, tgt_type="glob", timeout=60
    )
    assert ret["nrp1"]["failed"] == False
    assert "awr" in ret["nrp1"]["result"][0]
    assert isinstance(ret["nrp1"]["result"][0]["awr"], dict)


def test_nr_do_call_to_multiple_steps_in_pillar():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["configure_ntp", "awr"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    assert ret["nrp1"]["failed"] == False
    assert len(ret["nrp1"]["result"]) == 4
    assert "configure_ntp" in ret["nrp1"]["result"][0]
    assert "awr" in ret["nrp1"]["result"][-1]


def test_nr_do_call_to_single_step_in_filepath():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["configure_snmp"],
        kwarg={"filepath": "salt://actions/actions_file.txt"},
        tgt_type="glob",
        timeout=60,
    )
    assert ret["nrp1"]["failed"] == False
    assert len(ret["nrp1"]["result"]) == 2
    assert "configure_snmp" in ret["nrp1"]["result"][0]


def test_nr_do_call_to_multiple_steps_in_filepath():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["configure_snmp", "wr_"],
        kwarg={"filepath": "salt://actions/actions_file.txt"},
        tgt_type="glob",
        timeout=60,
    )
    assert ret["nrp1"]["failed"] == False
    assert len(ret["nrp1"]["result"]) == 3
    assert "configure_snmp" in ret["nrp1"]["result"][0]
    assert "wr_" in ret["nrp1"]["result"][-1]


def test_nr_do_call_to_non_existing_action():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["non_exists"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    assert ret["nrp1"]["failed"] == True
    assert "non_exists" in ret["nrp1"]["result"][0]
    assert isinstance(ret["nrp1"]["result"][0]["non_exists"], str)


def test_nr_do_call_to_non_existing_filepath():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["configure_snmp", "wr_"],
        kwarg={"filepath": "salt://non_exist.txt"},
        tgt_type="glob",
        timeout=60,
    )
    assert ret["nrp1"]["failed"] == True
    assert len(ret["nrp1"]["result"]) == 1
    assert "salt://non_exist.txt" in ret["nrp1"]["result"][0]


def test_nr_do_call_to_action_describe_from_filepath():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["configure_snmp"],
        kwarg={"filepath": "salt://actions/actions_file.txt", "describe": True},
        tgt_type="glob",
        timeout=60,
    )
    assert ret["nrp1"]["failed"] == False
    assert "configure_snmp" in ret["nrp1"]["result"][0]
    assert isinstance(ret["nrp1"]["result"][0]["configure_snmp"], list)


def test_nr_do_call_to_actions_describe_from_pillar():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["configure_ntp", "awr"],
        kwarg={"describe": True},
        tgt_type="glob",
        timeout=60,
    )
    assert ret["nrp1"]["failed"] == False
    assert "configure_ntp" in ret["nrp1"]["result"][0]
    assert "awr" in ret["nrp1"]["result"][1]


def test_nr_do_call_stop_on_error_true():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["configure_ntp_not_exist", "awr"],
        kwarg={"stop_on_error": True},
        tgt_type="glob",
        timeout=60,
    )
    assert ret["nrp1"]["failed"] == True
    assert len(ret["nrp1"]["result"]) == 1
    assert "configure_ntp_not_exist" in ret["nrp1"]["result"][0]
    assert isinstance(ret["nrp1"]["result"][0]["configure_ntp_not_exist"], str)


def test_nr_do_call_stop_on_error_false():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["configure_ntp_not_exist", "awr"],
        kwarg={"stop_on_error": False},
        tgt_type="glob",
        timeout=60,
    )
    assert ret["nrp1"]["failed"] == False
    assert len(ret["nrp1"]["result"]) == 2
    assert "configure_ntp_not_exist" in ret["nrp1"]["result"][0]
    assert isinstance(ret["nrp1"]["result"][0]["configure_ntp_not_exist"], str)
    assert "awr" in ret["nrp1"]["result"][1]


def test_nr_do_call_kwargs_combined():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["awr"],
        kwarg={"FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    assert ret["nrp1"]["failed"] == False
    assert len(ret["nrp1"]["result"][0]["awr"]) == 1
    assert "ceos1" in ret["nrp1"]["result"][0]["awr"]
