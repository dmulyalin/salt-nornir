import logging
import pprint
import json
import time
import os
import xml.etree.ElementTree as ET

log = logging.getLogger(__name__)

try:
    import salt.config
    import salt.runner
    import salt.utils.event
    import salt.exceptions

    HAS_SALT = True
except:
    HAS_SALT = False
    raise SystemExit("SALT Nonrir Tests - failed importing SALT libraries")

if HAS_SALT:
    # initiate runner modules client to run 'salt-run xyz command' commands
    opts = salt.config.client_config("/etc/salt/master")
    event = salt.utils.event.get_event(
        "master", sock_dir=opts["sock_dir"], transport=opts["transport"], opts=opts
    )
    
    # initiate runner modules client to run 'salt "*" command' commands
    opts["quiet"] = True
    runner = salt.runner.RunnerClient(opts)

    
def test_nr_diagram_IP():
    ret = runner.cmd(
        fun="nr.diagram",
        arg=["IP"],
        kwarg={
            "FB": "ceos[12]", 
            "outfile": "/tmp/pytest/test_nr_diagram_IP.graphml", 
            "tgt": "nrp1", 
            "tgt_type": "glob",
        },        
    )
    pprint.pprint(ret)
    with open("/tmp/pytest/test_nr_diagram_IP.graphml") as f:
        diagram_content = f.read()
        root = ET.fromstring(diagram_content)
        
    assert "/tmp/pytest/test_nr_diagram_IP.graphml" in ret and "saved" in ret
    assert "Traceback" not in diagram_content
    assert root and len(root) > 1
    
# test_nr_diagram_IP()


def test_nr_diagram_IP_from_file():
    # collect and save commands output to files
    commands_output = runner.cmd(
        fun="nr.call",
        arg=["cli", "show run", "show ip arp"],
        kwarg={
            "FB": "ceos[12]", 
            "tf": "ip_data",
            "tgt": "nrp1", 
            "tgt_type": "glob",
        },        
    )
    # build diagram out of files
    ret = runner.cmd(
        fun="nr.diagram",
        arg=["IP"],
        kwarg={
            "FB": "ceos[12]", 
            "outfile": 
            "/tmp/pytest/test_nr_diagram_IP_from_file.graphml", 
            "filegroup": "ip_data", 
            "last": 1,
            "tgt": "nrp1", 
            "tgt_type": "glob",
        },        
    )
    
    pprint.pprint(ret)
    with open("/tmp/pytest/test_nr_diagram_IP_from_file.graphml") as f:
        diagram_content = f.read()
        root = ET.fromstring(diagram_content)
        
    assert "/tmp/pytest/test_nr_diagram_IP_from_file.graphml" in ret and "saved" in ret
    assert "Traceback" not in diagram_content
    assert root and len(root) > 1
    
# test_nr_diagram_IP_from_file()


def test_nr_diagram_IP_save_data_true():
    ret = runner.cmd(
        fun="nr.diagram",
        arg=["IP"],
        kwarg={
            "FB": "ceos[12]", 
            "outfile": "/tmp/pytest/test_nr_diagram_IP_save_data_true.graphml", 
            "save_data": True, 
            "tgt": "nrp1", 
            "tgt_type": "glob",
        },        
    )
    
    pprint.pprint(ret)
    with open("/tmp/pytest/test_nr_diagram_IP_save_data_true.graphml") as f:
        diagram_content = f.read()
        root = ET.fromstring(diagram_content)
        
    assert "/tmp/pytest/test_nr_diagram_IP_save_data_true.graphml" in ret and "saved" in ret
    assert "Traceback" not in diagram_content
    assert root and len(root) > 1
    assert len([i for i in os.listdir("/tmp/pytest/") if i.startswith("IP_Data")]) > 0
                           
# test_nr_diagram_IP_save_data_true()


def test_nr_diagram_IP_save_data_path():
    ret = runner.cmd(
        fun="nr.diagram",
        arg=["IP"],
        kwarg={
            "FB": "ceos[12]", 
            "outfile": "/tmp/pytest/test_nr_diagram_IP_save_data_path.graphml", 
            "save_data": "/tmp/pytest/test_nr_diagram_IP_save_data_path/", 
            "tgt": "nrp1", 
            "tgt_type": "glob",
        },        
    )
    
    pprint.pprint(ret)
    with open("/tmp/pytest/test_nr_diagram_IP_save_data_path.graphml") as f:
        diagram_content = f.read()
        root = ET.fromstring(diagram_content)
        
    assert "/tmp/pytest/test_nr_diagram_IP_save_data_path.graphml" in ret and "saved" in ret
    assert "Traceback" not in diagram_content
    assert root and len(root) > 1
    assert "test_nr_diagram_IP_save_data_path" in os.listdir("/tmp/pytest/")
    assert "arista_eos" in os.listdir("/tmp/pytest/test_nr_diagram_IP_save_data_path/")
    assert "ceos1.txt" in os.listdir("/tmp/pytest/test_nr_diagram_IP_save_data_path/arista_eos/")
    assert "ceos2.txt" in os.listdir("/tmp/pytest/test_nr_diagram_IP_save_data_path/arista_eos/")

# test_nr_diagram_IP_save_data_path()


def test_nr_diagram_IP_fm_filter():
    ret = runner.cmd(
        fun="nr.diagram",
        arg=["IP"],
        kwarg={
            "FM": "arista*", 
            "outfile": "/tmp/pytest/test_nr_diagram_IP_fm_filter.graphml", 
            "tgt": "nrp1", 
            "tgt_type": "glob",
        },        
    )
    pprint.pprint(ret)
    with open("/tmp/pytest/test_nr_diagram_IP_fm_filter.graphml") as f:
        diagram_content = f.read()
        root = ET.fromstring(diagram_content)
        
    assert "/tmp/pytest/test_nr_diagram_IP_fm_filter.graphml" in ret and "saved" in ret
    assert "Traceback" not in diagram_content
    assert root and len(root) > 1