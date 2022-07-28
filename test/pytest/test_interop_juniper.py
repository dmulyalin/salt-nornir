"""
Set of Juniper Interoperability test cases.

Device under test must have test username created with correct pasword:

    set system login user nornir class super-user
    set system login user nornir authentication plain-text-password    
    New password: nornir123
    Retype new password: nornir123
    
Alternative update below inventory data with test device credentials.
    
For NETCONF tests to work make sure have NETCONF enabled over SSH on port 830:

    set system services netconf ssh
"""
import logging
import pprint
import pytest
import yaml
import random

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

test_proxy_id = "nrp2"
junos_test_device_params = """
name: vSRX-1
hostname: 192.168.1.220
username: nornir
password: nornir123
platform: juniper
port: 22
connection_options:
  ncclient:
     extras:
        device_params:
           name: junos
        allow_agent: false
        hostkey_verify: false
        look_for_keys: false
        timeout: 10
  scrapli_netconf:
    port: 830
    extras:
      transport: paramiko
      ssh_config_file: True
      auth_strict_key: False
  scrapli:
    platform: juniper_junos
    port: 22
    extras:
      transport: system
      auth_strict_key: false
      ssh_config_file: false
  napalm:
    platform: junos
    extras:
      optional_args:
        auto_probe: 0
        config_private: False
data: {}
groups: []
"""


def add_juniper_hosts():
    # add hosts using docker vm as a jumphost
    print(f"Adding juniper host to {test_proxy_id}")
    ret_add_juniper_box = client.cmd(
        tgt=test_proxy_id,
        fun="nr.nornir",
        arg=["inventory", "create_host"],
        kwarg=yaml.safe_load(junos_test_device_params),
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(ret_add_juniper_box)

def enable_netconf():
    ret = client.cmd(
        tgt=test_proxy_id,
        fun="nr.cfg",
        arg=["set system services netconf ssh"],
        kwarg={"FM": "*jun*", "plugin": "netmiko"},
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(ret)
    
add_juniper_hosts()
enable_netconf()

class TestJunosNrCli:        
    def test_cli_command(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.cli",
            arg=["show version"],
            kwarg={"add_details": True, "FM": "*jun*"},
            tgt_type="glob",
            timeout=60,
        )
        pprint.pprint(ret)
        assert ret[test_proxy_id] not in [{}, [], None]
        for host_name, data in ret[test_proxy_id].items():
            assert "show version" in data, f"No 'show version' output from '{host_name}'"
            assert isinstance(data["show version"], dict)
            assert "result" in data["show version"]
            assert "diff" in data["show version"]
            assert data["show version"]["exception"] == None
            assert data["show version"]["failed"] is False
            assert isinstance(data["show version"]["result"], str)   
            assert "Traceback" not in data["show version"]["result"]
            
            
class TestJunosNrCfg:      
    def test_netmiko_config_inline(self):
        pass
    
    def test_netmiko_config_commit_confirmed(self):
        pass
        
class TestJunosNrNc:        
    def test_ncclient_dir_call(self):
        ret = client.cmd(
            tgt=test_proxy_id, 
            fun="nr.nc", 
            arg=["dir"], 
            kwarg={"FM": "*jun*"}, 
            tgt_type="glob", 
            timeout=60
        )
        for host_name, data in ret[test_proxy_id].items():
            assert "dir" in data, "No 'dir' output from '{}'".format(host_name)
            assert isinstance(data["dir"], list)
            assert len(data["dir"]) > 0
            assert "Traceback (most recent " not in data["dir"], "dir call returned error"
    
    def test_ncclient_connected_call(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["connected"],
            kwarg={"FM": "*jun*"},
            tgt_type="glob",
            timeout=60,
        )
        for host_name, data in ret[test_proxy_id].items():
            assert "connected" in data, "No 'connected' output from '{}'".format(host_name)
            assert isinstance(data["connected"], bool)
    
    def test_ncclient_server_capabilities_call(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["server_capabilities"],
            kwarg={"FM": "*jun*"},
            tgt_type="glob",
            timeout=60,
        )
        for host_name, data in ret[test_proxy_id].items():
            assert (
                "server_capabilities" in data
            ), "No 'server_capabilities' output from '{}'".format(host_name)
            assert isinstance(data["server_capabilities"], list)
            assert len(data["server_capabilities"]) > 0
            assert (
                "Traceback (most recent " not in data["server_capabilities"]
            ), "server_capabilities call returned error"
    
    def test_ncclient_get_config_call_with_filter_list_subtree(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "FM": "*jun*",
                "filter": [
                    "subtree", 
                    "<configuration><interfaces><interface/></interfaces></configuration>"
                ],
                "source": "running",
            },
            tgt_type="glob",
            timeout=60,
        )    
        pprint.pprint(ret)
        for host_name, data in ret[test_proxy_id].items():
            assert (
                "get_config" in data
            ), "No 'get_config' output from '{}'".format(host_name)
            assert isinstance(data["get_config"], str)
            assert (
                "Traceback (most recent " not in data["get_config"]
            ), "get_config call returned error"
            assert all(k in data["get_config"] for k in ["rpc-reply", "configuration", "<interfaces>", "<interface>"])
            
    def test_ncclient_get_config_call_with_filter_with_ftype(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "FM": "*jun*",
                "filter": "<configuration><interfaces><interface/></interfaces></configuration>",
                "ftype": "subtree", 
                "source": "running",
            },
            tgt_type="glob",
            timeout=60,
        )    
        pprint.pprint(ret)
        for host_name, data in ret[test_proxy_id].items():
            assert (
                "get_config" in data
            ), "No 'get_config' output from '{}'".format(host_name)
            assert isinstance(data["get_config"], str)
            assert (
                "Traceback (most recent " not in data["get_config"]
            ), "get_config call returned error"
            assert all(k in data["get_config"] for k in ["rpc-reply", "configuration", "<interfaces>", "<interface>"])
            
    
    def test_ncclient_edit_config_call(self):
        rand_id = random.randint(0, 10000)
        payload = """
          <config>
            <configuration>
              <interfaces>
                <interface>
                  <name>lo0</name>
                  <description>Created by NETCONF {}</description>
                </interface>
              </interfaces>
            </configuration>
          </config>
        """.format(rand_id)
        # edit configuration
        edit_ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["edit_config"],
            kwarg={
                "target": "candidate",
                "config": payload,
                "FM": "*jun*",
            },
            tgt_type="glob",
            timeout=60,
        )
        # commit edited configuration
        comit_ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["commit"],
            kwarg={"FM": "*jun*"},
            tgt_type="glob",
            timeout=60,
        )
        # get config to verify description updated
        lo0_config = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "FM": "*jun*",
                "filter": "<configuration><interfaces><interface/></interfaces></configuration>",
                "ftype": "subtree", 
                "source": "running",
            },
            tgt_type="glob",
            timeout=60,
        )       
        print("edit config return:")
        pprint.pprint(edit_ret)
        print("commit config return:")
        pprint.pprint(comit_ret)
        print("get config return:")
        pprint.pprint(lo0_config)
        # check edit config return
        for host_name, data in edit_ret[test_proxy_id].items():
            assert (
                "edit_config" in data
            ), "No 'edit_config' output from '{}'".format(host_name)
            assert isinstance(data["edit_config"], str)
            assert (
                "Traceback (most recent " not in data["edit_config"]
            ), "edit_config call returned error"
            assert all(k in data["edit_config"] for k in ["rpc-reply", "<ok/>"])  
        # check commit config return
        for host_name, data in comit_ret[test_proxy_id].items():
            assert (
                "commit" in data
            ), "No 'commit' output from '{}'".format(host_name)
            assert isinstance(data["commit"], str)
            assert (
                "Traceback (most recent " not in data["commit"]
            ), "commit call returned error"
            assert all(k in data["commit"] for k in ["rpc-reply", "<ok/>"])    
        # check get config return
        for host_name, data in lo0_config[test_proxy_id].items():
            assert str(rand_id) in data["get_config"], f"lo0 description was not updated with rand int {rand_id}"

    def test_ncclient_transaction_call(self):
        rand_id = random.randint(0, 10000)
        payload = """
          <config>
            <configuration>
              <interfaces>
                <interface>
                  <name>lo0</name>
                  <description>Created by NETCONF {}</description>
                </interface>
              </interfaces>
            </configuration>
          </config>
        """.format(rand_id)
        # edit configuration
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["transaction"],
            kwarg={
                "config": payload,
                "FM": "*jun*",
            },
            tgt_type="glob",
            timeout=60,
        )        
        # get config to verify description updated
        lo0_config = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "FM": "*jun*",
                "filter": "<configuration><interfaces><interface/></interfaces></configuration>",
                "ftype": "subtree", 
                "source": "running",
            },
            tgt_type="glob",
            timeout=60,
        )     
        print("Transaction call return:")
        pprint.pprint(ret)
        print("get config return:")
        pprint.pprint(lo0_config)
        # check transaction results
        for host_name, data in ret[test_proxy_id].items():
            assert "<ok/>" in data["transaction"][0]["discard_changes"]
            assert "<ok/>" in data["transaction"][1]["edit_config"]
            assert "<ok/>" in data["transaction"][2]["validate"]
            assert "<ok/>" in data["transaction"][3]["commit_confirmed"]
            assert "<ok/>" in data["transaction"][4]["commit"]
        # check get config return
        for host_name, data in lo0_config[test_proxy_id].items():
            assert str(rand_id) in data["get_config"], f"lo0 description was not updated with rand int {rand_id}"        
        
    def test_ncclient_transaction_load_configuration_set(self):
        rand_id = random.randint(0, 10000)
        payload = 'set interfaces lo0 description "Configured over NETCONF {}"'.format(rand_id)
        # edit configuration
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["transaction"],
            kwarg={
                "config": payload,
                "FM": "*jun*",
                "edit_rpc": "load_configuration",
                "edit_arg": {
                    "action": "set",
                }
            },
            tgt_type="glob",
            timeout=60,
        )
        # get config to verify description updated
        lo0_config = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "FM": "*jun*",
                "filter": "<configuration><interfaces><interface/></interfaces></configuration>",
                "ftype": "subtree", 
                "source": "running",
            },
            tgt_type="glob",
            timeout=60,
        )  
        print("Transaction call return:")
        pprint.pprint(ret)
        print("get config return:")
        pprint.pprint(lo0_config)
        # check transaction results
        for host_name, data in ret[test_proxy_id].items():
            assert "<ok/>" in data["transaction"][0]["discard_changes"]
            assert "<ok/>" in data["transaction"][1]["load_configuration"]
            assert "<ok/>" in data["transaction"][2]["validate"]
            assert "<ok/>" in data["transaction"][3]["commit_confirmed"]
            assert "<ok/>" in data["transaction"][4]["commit"]
        # check get config return
        for host_name, data in lo0_config[test_proxy_id].items():
            assert str(rand_id) in data["get_config"], f"lo0 description was not updated with rand int {rand_id}"     
            

    def test_ncclient_transaction_load_configuration_set_with_comment(self):
        rand_id = random.randint(0, 10000)
        payload = 'set interfaces lo0 description "Configured over NETCONF {}"'.format(rand_id)
        # edit configuration
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["transaction"],
            kwarg={
                "config": payload,
                "FM": "*jun*",
                "edit_rpc": "load_configuration",
                "edit_arg": {
                    "action": "set",
                },
                "target": "candidate",
                "confirmed": True,
                "confirm_delay": 120,
                "commit_final_delay": 5,
                "commit_arg": {"comment": f"Test comment {rand_id}"}
            },
            tgt_type="glob",
            timeout=60,
        )
        # get config to verify description updated
        lo0_config = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "FM": "*jun*",
                "filter": "<configuration><interfaces><interface/></interfaces></configuration>",
                "ftype": "subtree", 
                "source": "running",
            },
            tgt_type="glob",
            timeout=60,
        )  
        # get commits history to verify comment
        commits_history = client.cmd(
            tgt=test_proxy_id,
            fun="nr.cli",
            arg=["show system commit"],
            kwarg={
                "FM": "*jun*",
            },
            tgt_type="glob",
            timeout=60,
        )  
        print("Transaction call return:")
        pprint.pprint(ret)
        print("get config return:")
        pprint.pprint(lo0_config)
        print("commits history:")
        pprint.pprint(commits_history, width=150)
        # check transaction results
        for host_name, data in ret[test_proxy_id].items():
            assert "<ok/>" in data["transaction"][0]["discard_changes"]
            assert "<ok/>" in data["transaction"][1]["load_configuration"]
            assert "<ok/>" in data["transaction"][2]["validate"]
            assert "<ok/>" in data["transaction"][3]["commit_confirmed"]
            assert "<ok/>" in data["transaction"][4]["commit"]
        # check get config return
        for host_name, data in lo0_config[test_proxy_id].items():
            assert str(rand_id) in data["get_config"], f"lo0 description was not updated with rand int {rand_id}"  
        # check if comment present in commit history
        for host_name, data in commits_history[test_proxy_id].items():
            assert str(rand_id) in data["show system commit"], f"random integer '{rand_id}' not found in commit history"
            
            
    def test_ncclient_netconf_rpc_call(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["rpc"],
            kwarg={
                "rpc": "<get-system-uptime-information/>",
                "FM": "*jun*",
            },
            tgt_type="glob",
            timeout=60,
        )   
        pprint.pprint(ret)
        for host_name, data in ret[test_proxy_id].items():
            assert all(k in data["rpc"] for k in ["<up-time", "<rpc-reply", "<uptime-information>"])
            

    def test_scrapli_netconf_dir_call(self):
        ret = client.cmd(
            tgt=test_proxy_id, 
            fun="nr.nc", 
            arg=["dir"], 
            kwarg={"FM": "*jun*", "plugin": "scrapli"}, 
            tgt_type="glob", 
            timeout=60
        )
        for host_name, data in ret[test_proxy_id].items():
            assert "dir" in data, "No 'dir' output from '{}'".format(host_name)
            assert isinstance(data["dir"], list)
            assert len(data["dir"]) > 0
            assert "Traceback (most recent " not in data["dir"], "dir call returned error"
    
    def test_scrapli_netconf_server_capabilities_call(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["server_capabilities"],
            kwarg={"FM": "*jun*", "plugin": "scrapli"},
            tgt_type="glob",
            timeout=60,
        )
        for host_name, data in ret[test_proxy_id].items():
            assert (
                "server_capabilities" in data
            ), "No 'server_capabilities' output from '{}'".format(host_name)
            assert isinstance(data["server_capabilities"], list)
            assert len(data["server_capabilities"]) > 0
            assert (
                "Traceback (most recent " not in data["server_capabilities"]
            ), "server_capabilities call returned error"
    
    def test_scrapli_netconf_get_config_call_with_filter(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "filter_": "<configuration><interfaces><interface/></interfaces></configuration>",
                "source": "running",
                "plugin": "scrapli",
                "FM": "*jun*",
            },
            tgt_type="glob",
            timeout=60,
        )
        pprint.pprint(ret)
        for host_name, data in ret[test_proxy_id].items():
            assert (
                "get_config" in data
            ), "No 'get_config' output from '{}'".format(host_name)
            assert isinstance(data["get_config"], str)
            assert (
                "Traceback (most recent " not in data["get_config"]
            ), "get_config call returned error"
            assert all(k in data["get_config"] for k in ["rpc-reply", "configuration", "<interfaces>", "<interface>"])
            
    def test_scrapli_netconf_edit_config_call(self):
        rand_id = random.randint(0, 10000)
        payload = """
          <config>
            <configuration>
              <interfaces>
                <interface>
                  <name>lo0</name>
                  <description>Created by NETCONF {}</description>
                </interface>
              </interfaces>
            </configuration>
          </config>
        """.format(rand_id)
        # edit configuration
        edit_ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["edit_config"],
            kwarg={
                "target": "candidate",
                "config": payload,
                "FM": "*jun*",
                "plugin": "scrapli",
            },
            tgt_type="glob",
            timeout=60,
        )
        # commit edited configuration
        comit_ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["commit"],
            kwarg={"FM": "*jun*", "plugin": "scrapli"},
            tgt_type="glob",
            timeout=60,
        )
        # get config to verify description updated
        lo0_config = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "FM": "*jun*",
                "filter_": "<configuration><interfaces><interface/></interfaces></configuration>",
                "source": "running",
                "plugin": "scrapli",
            },
            tgt_type="glob",
            timeout=60,
        )       
        print("edit config return:")
        pprint.pprint(edit_ret)
        print("commit config return:")
        pprint.pprint(comit_ret)
        print("get config return:")
        pprint.pprint(lo0_config)
        # check edit config return
        for host_name, data in edit_ret[test_proxy_id].items():
            assert (
                "edit_config" in data
            ), "No 'edit_config' output from '{}'".format(host_name)
            assert isinstance(data["edit_config"], str)
            assert (
                "Traceback (most recent " not in data["edit_config"]
            ), "edit_config call returned error"
            assert all(k in data["edit_config"] for k in ["rpc-reply", "<ok/>"])  
        # check commit config return
        for host_name, data in comit_ret[test_proxy_id].items():
            assert (
                "commit" in data
            ), "No 'commit' output from '{}'".format(host_name)
            assert isinstance(data["commit"], str)
            assert (
                "Traceback (most recent " not in data["commit"]
            ), "commit call returned error"
            assert all(k in data["commit"] for k in ["rpc-reply", "<ok/>"])    
        # check get config return
        for host_name, data in lo0_config[test_proxy_id].items():
            assert str(rand_id) in data["get_config"], f"lo0 description was not updated with rand int {rand_id}"

    def test_scrapli_netconf_transaction_call(self):
        rand_id = random.randint(0, 10000)
        payload = """
          <config>
            <configuration>
              <interfaces>
                <interface>
                  <name>lo0</name>
                  <description>Created by NETCONF {}</description>
                </interface>
              </interfaces>
            </configuration>
          </config>
        """.format(rand_id)
        # edit configuration
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["transaction"],
            kwarg={
                "config": payload,
                "FM": "*jun*",
                "plugin": "scrapli",
            },
            tgt_type="glob",
            timeout=60,
        )        
        # get config to verify description updated
        lo0_config = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "FM": "*jun*",
                "filter_": "<configuration><interfaces><interface/></interfaces></configuration>",
                "source": "running",
                "plugin": "scrapli",
            },
            tgt_type="glob",
            timeout=60,
        )     
        print("Transaction call return:")
        pprint.pprint(ret)
        print("get config return:")
        pprint.pprint(lo0_config)
        # check transaction results
        for host_name, data in ret[test_proxy_id].items():
            assert "<ok/>" in data["transaction"][0]["discard_changes"]
            assert "<ok/>" in data["transaction"][1]["edit_config"]
            assert "<ok/>" in data["transaction"][2]["validate"]
            assert "<ok/>" in data["transaction"][3]["commit"]
        # check get config return
        for host_name, data in lo0_config[test_proxy_id].items():
            assert str(rand_id) in data["get_config"], f"lo0 description was not updated with rand int {rand_id}"   
            
    def test_scrapli_netconf_rpc_call(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["rpc"],
            kwarg={
                "filter_": "<get-system-uptime-information/>",
                "FM": "*jun*",
                "plugin": "scrapli",
            },
            tgt_type="glob",
            timeout=60,
        )   
        pprint.pprint(ret)
        for host_name, data in ret[test_proxy_id].items():
            assert all(k in data["rpc"] for k in ["<up-time", "<rpc-reply", "<uptime-information>"])
    
    