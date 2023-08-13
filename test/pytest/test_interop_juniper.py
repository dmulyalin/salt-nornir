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
import socket 

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
JUNOS_DEVICE_IP = "192.168.1.220"
junos_test_device_params = f"""
name: vSRX-1
hostname: {JUNOS_DEVICE_IP}
username: nornir
password: nornir123
platform: juniper
port: 22
connection_options:
  ncclient:
     extras:
        device_params:
           name: junos
        raise_mode: all
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
data: {{}}
groups: []
"""

 
junos_test_device_params_creds_retry = f"""
name: vSRX-1-creds-retry
hostname: {JUNOS_DEVICE_IP}
platform: juniper
connection_options:
  napalm:
    platform: junos
    username: nornir-wrong
    extras:
      optional_args:
        key_file: /root/.ssh/id_rsa
        auto_probe: 0
        config_private: False
data: 
  credentials:
     ssh_key_auth:
        username: "nornir-ssh-key"
     local_account:
        username: "nornir"
        password: "nornir123"  
        extras:
          optional_args:
            key_file: False
"""

# check if junos endpoint reachable
s = socket.socket()
s.settimeout(5)
try:
    status = s.connect_ex((JUNOS_DEVICE_IP, 22))
except:
    log.exception("Failed to check junos connection.")
    status = 1
if status == 0:
    has_junos_device = True
else:
    has_junos_device = False
s.close()
skip_if_not_junos_device = pytest.mark.skipif(
    has_junos_device == False,
    reason="Has no connection to {} juniper device".format(JUNOS_DEVICE_IP),
)


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
    print(f"Added juniper host to {test_proxy_id}")
    pprint.pprint(ret_add_juniper_box)
    ret_add_juniper_box_2nd = client.cmd(
        tgt=test_proxy_id,
        fun="nr.nornir",
        arg=["inventory", "create_host"],
        kwarg=yaml.safe_load(junos_test_device_params_creds_retry),
        tgt_type="glob",
        timeout=60,
    )    
    print(f"Added second juniper host to {test_proxy_id}")
    pprint.pprint(ret_add_juniper_box_2nd)

    
def enable_netconf():
    ret = client.cmd(
        tgt=test_proxy_id,
        fun="nr.cfg",
        arg=["set system services netconf ssh"],
        kwarg={"FB": "vSRX-1", "plugin": "netmiko"},
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(ret)
    
if has_junos_device:
    add_juniper_hosts()
    enable_netconf()

@skip_if_not_junos_device
class TestJunosNrCli:        
    def test_cli_command_netmiko(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.cli",
            arg=["show version"],
            kwarg={"add_details": True, "FB": "vSRX-1"},
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

    def test_cli_command_napalm(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.cli",
            arg=["show version"],
            kwarg={"add_details": True, "FB": "vSRX-1", "plugin": "napalm"},
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
            
    def test_cli_configure_use_ps_multiline(self):
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.cli",
            arg=["salt://templates/juniper_jinja_multiline_test.j2"],
            kwarg={"add_details": True, "FB": "vSRX-1", "use_ps": True, "split_lines": False},
            tgt_type="glob",
            timeout=60,
        )
        pprint.pprint(ret)
        assert ret[test_proxy_id] not in [{}, [], None]
        for host_name, data in ret[test_proxy_id].items():        
            assert "unknown command" not in data["configure"]["result"]
            assert r"test\nbanner\nstring\n" in data["configure"]["result"]

    def test_cli_command_napalm_run_creds_retry(self):
        """
        This test uses junos_test_device_params_creds_retry inventory and iterates over
        ssh key auth first using "nornir-wrong" username, next using "nornir-ssh-key" and
        at last using username "nornir" and password with key auth disabled.
        """
        ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.cli",
            arg=["show version"],
            kwarg={
                "FB": "vSRX-1-creds-retry", 
                "plugin": "napalm",
                "run_creds_retry": ["ssh_key_auth", "local_account"],
                "add_details": True
            },
            tgt_type="glob",
            timeout=60,
        )
        pprint.pprint(ret)
        for host_name, data in ret[test_proxy_id].items():
            assert "show version" in data, f"No 'show version' output from '{host_name}'"
            assert isinstance(data["show version"], dict)
            assert "result" in data["show version"]
            assert "diff" in data["show version"]
            assert data["show version"]["exception"] == None
            assert data["show version"]["failed"] is False
            assert isinstance(data["show version"]["result"], str)   
            assert "Traceback" not in data["show version"]["result"]
            
        
@skip_if_not_junos_device
class TestJunosNrCfg:      
    def test_netmiko_config_inline_multiline(self):
        rand_id = random.randint(0, 10000)
        ret_cfg = client.cmd(
            tgt=test_proxy_id,
            fun="nr.cfg",
            arg=[f'set system login message "test\\n\\string\\n{rand_id}"'],
            kwarg={"FB": "vSRX-1", "plugin": "netmiko"},
            tgt_type="glob",
            timeout=60,
        )
        ret_cli = client.cmd(
            tgt=test_proxy_id,
            fun="nr.cli",
            arg=['show configuration system login message'],
            kwarg={"FB": "vSRX-1"},
            tgt_type="glob",
            timeout=60,
        )
        print("ret_cfg: ")
        pprint.pprint(ret_cfg)
        print("ret_cli: ")
        pprint.pprint(ret_cli)
        # check configuration command results
        assert ret_cfg[test_proxy_id] not in [{}, [], None]
        for host_name, data in ret_cfg[test_proxy_id].items():
            assert data["netmiko_send_config"]["exception"] == None
            assert data["netmiko_send_config"]["failed"] is False
            assert str(rand_id) in data["netmiko_send_config"]["result"]
        # check show command contain random int
        for host_name, data in ret_cli[test_proxy_id].items():
            assert str(rand_id) in data["show configuration system login message"]
    
    def test_netmiko_config_commit_confirmed(self):
        pass
        
@skip_if_not_junos_device
class TestJunosNrNc:        
    def test_ncclient_dir_call(self):
        ret = client.cmd(
            tgt=test_proxy_id, 
            fun="nr.nc", 
            arg=["dir"], 
            kwarg={"FB": "vSRX-1"}, 
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
            kwarg={"FB": "vSRX-1"},
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
            kwarg={"FB": "vSRX-1"},
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
            },
            tgt_type="glob",
            timeout=60,
        )
        # commit edited configuration
        comit_ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["commit"],
            kwarg={"FB": "vSRX-1"},
            tgt_type="glob",
            timeout=60,
        )
        # get config to verify description updated
        lo0_config = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "FB": "vSRX-1",
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

    def test_ncclient_edit_config_call(self):
        rand_id = random.randint(0, 10000)
        payload = """
<config>
    <configuration>
        <system>
            <login>
                <message>test\nbanner\nstring\nnew{}</message>
            </login>
        </system>
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
                "FB": "vSRX-1",
            },
            tgt_type="glob",
            timeout=60,
        )
        # commit edited configuration
        comit_ret = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["commit"],
            kwarg={"FB": "vSRX-1"},
            tgt_type="glob",
            timeout=60,
        )
        # get config to verify description updated
        lo0_config = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "FB": "vSRX-1",
                "filter": "<configuration><system><login><message/></login></system></configuration>",
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
            assert str(rand_id) in data["get_config"], f"Login message was not updated with rand int {rand_id}"        
        
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
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
            kwarg={"FB": "vSRX-1", "plugin": "scrapli"}, 
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
            kwarg={"FB": "vSRX-1", "plugin": "scrapli"},
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
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
            kwarg={"FB": "vSRX-1", "plugin": "scrapli"},
            tgt_type="glob",
            timeout=60,
        )
        # get config to verify description updated
        lo0_config = client.cmd(
            tgt=test_proxy_id,
            fun="nr.nc",
            arg=["get_config"],
            kwarg={
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
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
                "FB": "vSRX-1",
                "plugin": "scrapli",
            },
            tgt_type="glob",
            timeout=60,
        )   
        pprint.pprint(ret)
        for host_name, data in ret[test_proxy_id].items():
            assert all(k in data["rpc"] for k in ["<up-time", "<rpc-reply", "<uptime-information>"])
    
    