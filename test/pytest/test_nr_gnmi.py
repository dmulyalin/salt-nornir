"""
Make sure to have gnmi api enabled on ceos::

    management api gnmi
       transport grpc default
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
    ret = client.cmd(
        tgt="nrp1", fun="nr.gnmi", arg=["dir"], kwarg={}, tgt_type="glob", timeout=60
    )
    pprint.pprint(ret)
    assert ret == {'nrp1': {'ceos1': {'dir': ['capabilities',
                            'close',
                            'connect',
                            'delete',
                            'dir',
                            'get',
                            'help',
                            'replace',
                            'set',
                            'subscribe',
                            'update']},
          'ceos2': {'dir': ['capabilities',
                            'close',
                            'connect',
                            'delete',
                            'dir',
                            'get',
                            'help',
                            'replace',
                            'set',
                            'subscribe',
                            'update']}}}
    
# test_ncclient_dir_call()


def test_ncclient_help_call():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["help"], 
        kwarg={"method_name": "set"}, 
        tgt_type="glob", 
        timeout=60
    )
    # pprint.pprint(ret)
    assert isinstance(ret["nrp1"]["ceos1"]["help"], str)
    assert isinstance(ret["nrp1"]["ceos2"]["help"], str) 
    
# test_ncclient_help_call()


def test_gnmi_get_call_path_list():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["get"], 
        kwarg={"path": ["openconfig-interfaces:interfaces", "openconfig-network-instance:network-instances"]}, 
        tgt_type="glob", 
        timeout=60
    )
    # pprint.pprint(ret["nrp1"]["ceos1"]["get"]["notification"][1])
    assert len(ret["nrp1"]["ceos1"]["get"]["notification"]) == 2
    assert len(ret["nrp1"]["ceos2"]["get"]["notification"]) == 2
    assert "update" in ret["nrp1"]["ceos1"]["get"]["notification"][0]
    assert "update" in ret["nrp1"]["ceos2"]["get"]["notification"][0]
    assert "update" in ret["nrp1"]["ceos1"]["get"]["notification"][1]
    assert "update" in ret["nrp1"]["ceos2"]["get"]["notification"][1]
    
# test_ncclient_get_call_path_list()


def test_gnmi_get_call_path_string():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["get"], 
        kwarg={"path": "openconfig-interfaces:interfaces, openconfig-network-instance:network-instances"}, 
        tgt_type="glob", 
        timeout=60
    )
    # pprint.pprint(ret["nrp1"]["ceos1"]["get"]["notification"][1])
    assert len(ret["nrp1"]["ceos1"]["get"]["notification"]) == 2
    assert len(ret["nrp1"]["ceos2"]["get"]["notification"]) == 2
    assert "update" in ret["nrp1"]["ceos1"]["get"]["notification"][0]
    assert "update" in ret["nrp1"]["ceos2"]["get"]["notification"][0]
    assert "update" in ret["nrp1"]["ceos1"]["get"]["notification"][1]
    assert "update" in ret["nrp1"]["ceos2"]["get"]["notification"][1]
    
# test_ncclient_get_call_path_string()


def test_gnmi_get_call_path_as_arg():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["get", "openconfig-interfaces:interfaces", "openconfig-network-instance:network-instances"], 
        kwarg={}, 
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret["nrp1"]["ceos1"]["get"]["notification"][1])
    assert len(ret["nrp1"]["ceos1"]["get"]["notification"]) == 2
    assert len(ret["nrp1"]["ceos2"]["get"]["notification"]) == 2
    assert "update" in ret["nrp1"]["ceos1"]["get"]["notification"][0]
    assert "update" in ret["nrp1"]["ceos2"]["get"]["notification"][0]
    assert "update" in ret["nrp1"]["ceos1"]["get"]["notification"][1]
    assert "update" in ret["nrp1"]["ceos2"]["get"]["notification"][1]
    
# test_gnmi_get_call_path_as_arg()


def test_gnmi_set_call_update():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["set"], 
        kwarg={
            "update": [["openconfig-interfaces:interfaces/interface[name=Loopback100]/config", {"description": "MGMT Range xYz"}]],
            "FB": "ceos2"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret["nrp1"])
    assert ret["nrp1"] == {'ceos2': {'set': {'response': [{'op': 'UPDATE',
                                                           'path': 'interfaces/interface[name=Loopback100]/config'}]}}}
    
# test_ncclient_get_call_set_update()


def test_gnmi_set_call_replace():
    # create interface using set replace operation
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["set"], 
        kwarg={
            "replace": [["openconfig-interfaces:interfaces/interface[name=Loopback1234]/config", {"name": "Loopback1234", "description": "New"}]],
        },
        tgt_type="glob", 
        timeout=60
    )
    # delete interface to not interfere with other tests
    delete = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["set"], 
        kwarg={
            "delete": "openconfig-interfaces:interfaces/interface[name=Loopback1234]",
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret["nrp1"])
    assert ret["nrp1"] == {'ceos1': {'set': {'response': [{'op': 'REPLACE',
                                 'path': 'interfaces/interface[name=Loopback1234]/config'}]}},
 'ceos2': {'set': {'response': [{'op': 'REPLACE',
                                 'path': 'interfaces/interface[name=Loopback1234]/config'}]}}}
    
# test_gnmi_set_call_replace()


def test_gnmi_set_call_delete():
    # create inerface first
    client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["set"], 
        kwarg={
            "update": [["openconfig-interfaces:interfaces/interface[name=Loopback555]/config", {"name": "Loopback555"}]],
        },
        tgt_type="glob", 
        timeout=60
    )
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["set"], 
        kwarg={
            "delete": "openconfig-interfaces:interfaces/interface[name=Loopback555]",
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret["nrp1"])
    assert ret["nrp1"] == {'ceos1': {'set': {'response': [{'op': 'DELETE',
                                 'path': 'interfaces/interface[name=Loopback555]'}]}},
 'ceos2': {'set': {'response': [{'op': 'DELETE',
                                 'path': 'interfaces/interface[name=Loopback555]'}]}}}
    
# test_ncclient_get_call_set_delete()


def test_gnmi_subscribe_call_unsuppoted():
    # create inerface first
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["subscribe"], 
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret["nrp1"])
    assert "Unsupported" in ret["nrp1"]
    
# test_gnmi_subscribe_call_unsuppoted()


def test_gnmi_delete_call_args():
    # create inerface first
    client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["set"], 
        kwarg={
            "update": [["openconfig-interfaces:interfaces/interface[name=Loopback555]/config", {"name": "Loopback555"}]],
        },
        tgt_type="glob", 
        timeout=60
    )
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["delete", "openconfig-interfaces:interfaces/interface[name=Loopback555]"], 
        kwarg={},
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret["nrp1"])
    assert ret["nrp1"] == {'ceos1': {'delete': {'response': [{'op': 'DELETE',
                                 'path': 'interfaces/interface[name=Loopback555]'}]}},
 'ceos2': {'delete': {'response': [{'op': 'DELETE',
                                 'path': 'interfaces/interface[name=Loopback555]'}]}}}
    
# test_gnmi_delete_call_args()


def test_gnmi_delete_call_path_arg():
    # create inerface first
    client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["set"], 
        kwarg={
            "update": [["openconfig-interfaces:interfaces/interface[name=Loopback555]/config", {"name": "Loopback555"}]],
        },
        tgt_type="glob", 
        timeout=60
    )
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["delete"], 
        kwarg={
            "path": ["openconfig-interfaces:interfaces/interface[name=Loopback555]"]
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret["nrp1"])
    assert ret["nrp1"] == {'ceos1': {'delete': {'response': [{'op': 'DELETE',
                                 'path': 'interfaces/interface[name=Loopback555]'}]}},
 'ceos2': {'delete': {'response': [{'op': 'DELETE',
                                 'path': 'interfaces/interface[name=Loopback555]'}]}}}
    
# test_gnmi_delete_call_path_arg()


def test_gnmi_update_call():
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["update", "openconfig-interfaces:interfaces/interface[name=Loopback100]/config"], 
        kwarg={
            "description": "MGMT Range xYz",
            "FB": "ceos2"
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret["nrp1"])
    assert ret["nrp1"] == {'ceos2': {'update': {'response': [{'op': 'UPDATE',
                                                           'path': 'interfaces/interface[name=Loopback100]/config'}]}}}
    
# test_gnmi_update_call()


def test_gnmi_replace_call():
    # create interface using set replace operation
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["replace", "openconfig-interfaces:interfaces/interface[name=Loopback1234]/config"], 
        kwarg={
            "name": "Loopback1234", 
            "description": "New",
        },
        tgt_type="glob", 
        timeout=60
    )
    # delete interface to not interfere with other tests
    delete = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["set"], 
        kwarg={
            "delete": "openconfig-interfaces:interfaces/interface[name=Loopback1234]",
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret["nrp1"])
    assert ret["nrp1"] == {'ceos1': {'replace': {'response': [{'op': 'REPLACE',
                                 'path': 'interfaces/interface[name=Loopback1234]/config'}]}},
 'ceos2': {'replace': {'response': [{'op': 'REPLACE',
                                 'path': 'interfaces/interface[name=Loopback1234]/config'}]}}}
    
# test_gnmi_replace_call()


def test_gnmi_set_call_from_filename():
    # create interface using set replace operation
    ret = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["set"], 
        kwarg={
            "filename": "salt://gnmi/set_args_1.txt",
        },
        tgt_type="glob", 
        timeout=60
    )
    # delete interface to not interfere with other tests
    delete = client.cmd(
        tgt="nrp1", 
        fun="nr.gnmi", 
        arg=["set"], 
        kwarg={
            "delete": [
                "openconfig-interfaces:interfaces/interface[name=Loopback35]",
                "openconfig-interfaces:interfaces/interface[name=Loopback36]"
            ],
        },
        tgt_type="glob", 
        timeout=60
    )
    pprint.pprint(ret)
    assert ret == {'nrp1': {'ceos1': {'set': {'response': [{'op': 'DELETE',
                                          'path': 'interfaces/interface[name=Loopback35]'},
                                         {'op': 'DELETE',
                                          'path': 'interfaces/interface[name=Loopback36]'},
                                         {'op': 'REPLACE',
                                          'path': 'interfaces/interface[name=Loopback35]/config'},
                                         {'op': 'REPLACE',
                                          'path': 'interfaces/interface[name=Loopback36]/config'},
                                         {'op': 'UPDATE',
                                          'path': 'interfaces/interface[name=Loopback35]/config'},
                                         {'op': 'UPDATE',
                                          'path': 'interfaces/interface[name=Loopback36]/config'}]}},
          'ceos2': {'set': {'response': [{'op': 'DELETE',
                                          'path': 'interfaces/interface[name=Loopback35]'},
                                         {'op': 'DELETE',
                                          'path': 'interfaces/interface[name=Loopback36]'},
                                         {'op': 'REPLACE',
                                          'path': 'interfaces/interface[name=Loopback35]/config'},
                                         {'op': 'REPLACE',
                                          'path': 'interfaces/interface[name=Loopback36]/config'},
                                         {'op': 'UPDATE',
                                          'path': 'interfaces/interface[name=Loopback35]/config'},
                                         {'op': 'UPDATE',
                                          'path': 'interfaces/interface[name=Loopback36]/config'}]}}}}
# test_gnmi_set_call_from_filename()