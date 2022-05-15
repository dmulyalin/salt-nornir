"""
Make sure to have RESTCONF api enabled on ceos:

    management api http-commands
       protocol http
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


def test_http_get_call_absolute_url():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.http", 
        arg=["get"], 
        kwarg={"url": "http://10.0.1.4", "FB": "ceos1"}, 
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert isinstance(ret["nrp1"]["ceos1"]["get"], str)
    assert len(ret["nrp1"]["ceos1"]["get"]) > 500
    
# test_http_get_call()


def test_http_pydantic_model_wrong_method():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.http", 
        arg=[], 
        kwarg={"url": "http://10.0.1.4", "FB": "ceos1", "method": "gett"}, 
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert "ValidationError" in ret["nrp1"]
    
def test_http_pydantic_model_wrong_method_arg():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.http", 
        arg=["gett"], 
        kwarg={"url": "http://10.0.1.4", "FB": "ceos1"}, 
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert "ValidationError" in ret["nrp1"]