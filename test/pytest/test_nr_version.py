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


def test_nr_version_call():
    ret = client.cmd(
        tgt="nrp1", fun="nr.version", arg=[], kwarg={}, tgt_type="glob", timeout=60
    )
    assert "nrp1" in ret
    assert isinstance(ret["nrp1"], str), "Unexpected data type returned"
    assert "Traceback" not in ret["nrp1"], "nr.version returned error"
