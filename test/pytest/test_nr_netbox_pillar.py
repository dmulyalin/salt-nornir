import logging
import pprint
import time
import pytest
import socket
import requests

from netbox_data import NB_URL, netbox_device_data_keys

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
    opts = salt.config.client_config("/etc/salt/master")
    event = salt.utils.event.get_event(
        "master", sock_dir=opts["sock_dir"], transport=opts["transport"], opts=opts
    )
    
# check if Netbox endpoint reachable
netbox_url = NB_URL + "/api"
try:
    response = requests.get(netbox_url)
    has_netbox = response.status_code == 200
except Exception as e:
    has_netbox = False
skip_if_not_has_netbox = pytest.mark.skipif(
    has_netbox == False,
    reason=f"Has no connection to Netbox {netbox_url}",
)

def _refresh_nornir():
    ret = client.cmd(
        tgt="nrp3", 
        fun="nr.nornir", 
        arg=["refresh"], 
    )    
    
@skip_if_not_has_netbox
class TestProxyNRP3:  
    
    @pytest.fixture(scope="class", autouse=True)
    def nrp3_inventory(self):        
        ret = client.cmd(
            tgt="nrp3", 
            fun="nr.nornir", 
            arg=["refresh"], 
        )  
        for i in range(3):
            time.sleep(10)
            ret = client.cmd(
                tgt="nrp3", 
                fun="nr.nornir", 
                arg=["inventory"], 
                kwarg={}
            )
            if ret["nrp3"] and "Traceback (most recent call last)" not in str(ret["nrp3"]):
                pprint.pprint(ret)
                return ret
        else:
            raise RuntimeError(f"Failed to retrieve nrp3 inventory: {ret}")

    @pytest.fixture(scope="class", autouse=True)
    def pillar_data(self):   
        pillar_data = client.cmd(
            tgt="nrp3", 
            fun="pillar.items", 
        )  
        print("nrp3 pillar data: ")
        pprint.pprint(pillar_data)
        return pillar_data
        
    def test_match_by_use_minion_id_tag(self, nrp3_inventory):
        """
        In Netbox device fceos4 tagget with tag nrp3, as a result data
        from Netbox for fceos4 should be include in inventory 
        """            
        assert "fceos4" in nrp3_inventory["nrp3"]["hosts"], "fceos4 not part of inventory, should be matched by 'nrp3' tag"

    def test_match_by_use_hosts_filters(self, nrp3_inventory):  
        """
        nrp3 proxy pillar contains this filter:
        
            hosts: 
              - name__ic: "fceos5"
        
        this is to verify that fceos5 fetched from netbox using above "name is contains" filter
        """
        # verify secretes fetched for the host
        assert "fceos5" in nrp3_inventory["nrp3"]["hosts"], "fceos5 not part of inventory, should be matched by hosts filters"
        
    def test_host_add_netbox_data(self, nrp3_inventory):
        """
        nrp3 pillar has host_add_netbox_data set to "netbox", this test is
        to verify netbox device data added to Nornir data.
        """            
        assert all(k in nrp3_inventory["nrp3"]["hosts"]["fceos4"]["data"]["netbox"] for k in netbox_device_data_keys) 
        assert all(k in nrp3_inventory["nrp3"]["hosts"]["fceos5"]["data"]["netbox"] for k in netbox_device_data_keys) 
        
    def test_fetch_username_password(self, nrp3_inventory):    
        """
        fceos4 has username and password secrets created in netbox-secretstore, 
        and nrp3 has fet_username and fetch_password set to True, this test is to
        verify that username and password fetched from netbox secretstore.
        """
        # verify secretes fetched for the host
        assert nrp3_inventory["nrp3"]["hosts"]["fceos4"]["username"] is not None, "fceos4 username not fetched"
        assert nrp3_inventory["nrp3"]["hosts"]["fceos4"]["password"] is not None, "fceos4 password not fetched"

    def test_use_minion_id_tag_host_resolve_secrets(self, nrp3_inventory):    
        """
        fceos4 matched by nrp3 tag and has these secrets define in inventory:
            data:
              secrets:
                bgp: nb://netbox_secretstore/keymaster-1/BGP/peers_pass
                secret1: nb://netbox_secretstore/fceos1/SaltSecrets/secret1
                secret2: nb://netbox_secretstore/SaltSecrets/secret2
                secret3: nb://netbox_secretstore/secret3
                secret4: nb://secret4
                
        this test is to verify above secrets resolved
        """
        secrets = nrp3_inventory["nrp3"]["hosts"]["fceos4"]["data"]["netbox"]["local_context_data"]["secrets"]
        assert secrets["bgp"] == "123456bgppeer", "fceos4 bgp secret is wrong"
        assert secrets["secret1"] == "secret1_value", "fceos4 secret1 secret is wrong"
        assert secrets["secret2"] == "secret2_value", "fceos4 secret2 secret is wrong"
        assert secrets["secret3"] == "secret3_value", "fceos4 secret3 secret is wrong"
        assert secrets["secret4"] == "secret4_value", "fceos4 secret4 secret is wrong"

    def test_hostname_from_primary_ip4(self, nrp3_inventory):    
        """
        fceos4 has primary_ip4 assigned to it, this test to verify
        that IP used as a hostname
        """
        # verify secretes fetched for the host
        fce04_hostname = nrp3_inventory["nrp3"]["hosts"]["fceos4"]["hostname"]
        assert fce04_hostname == "1.0.1.4", f"fceos4 hostname '{fce04_hostname}' - is not equal to primary_ip4 1.0.1.4"

    def test_device_config_context_nornir_data(self, nrp3_inventory):  
        """
        nrp3 pillar includes fceos5 device using hosts filters, fceos5
        device has nornir section defined in config context data:
        
            nornir:
              hostname: 10.0.1.10
              platform: arista_eos
              port: '6002'
              
        this test is to verify above data is included into fceos5 nornir inventory
        """
        assert nrp3_inventory["nrp3"]["hosts"]["fceos5"]["hostname"] == "10.0.1.10", (
            "fceos5 has no hostname from config context data"
        )
        assert nrp3_inventory["nrp3"]["hosts"]["fceos5"]["platform"] == "arista_eos", (
            "fceos5 has no platform from config context data"
        )        
        assert nrp3_inventory["nrp3"]["hosts"]["fceos5"]["port"] == "6002", (
            "fceos5 has no port from config context data"
        )
        
    def test_fetch_creds_from_another_device(self, nrp3_inventory):  
        """
        nrp3 pillar includes fceos5 device using hosts filters, fceos5
        device in return has username and password defined using this config
        context data:
        
            nornir:
              password: nb://netbox_secretstore/keymaster-1/SaltNornirCreds/password
              username: nb://netbox_secretstore/keymaster-1/SaltNornirCreds/username
              
        this test is to verify above data is resolved to actual secrets
        """
        assert nrp3_inventory["nrp3"]["hosts"]["fceos5"]["username"] == "nornir", "fceos5 username not resolved using keymaster"
        assert nrp3_inventory["nrp3"]["hosts"]["fceos5"]["password"] == "nornir", "fceos5 password not resolved using keymaster"
    
    def test_use_minion_id_device(self, pillar_data):  
        """
        Verify Netbox device nrp3 config context data merged with 
        nrp3 proxy minion pillar
        """
        assert pillar_data["nrp3"]["foo"] == "bar", "nrp3 pillar missing 'foo: bar'"
        assert pillar_data["nrp3"]["proxy"]["multiprocessing"] == True
        assert pillar_data["nrp3"]["proxy"]["proxytype"] == "nornir"
        assert pillar_data["nrp3"]["proxy"]["proxy_always_alive"] == True, "nrp3 pillar missing 'proxy_always_alive'"
        assert "foobar" in pillar_data["nrp3"]["nornir"]["actions"], "nrp3 pillar missing 'foobar' nornir action"
        
    def test_use_minion_id_device_secrets_resolved(self, pillar_data):  
        """
        nrp3 device config context in Netbox used to merge with nrp3 proxy minon pillar,
        several secrets should be resolved for that pillar data.
        """
        assert pillar_data["nrp3"]["nrp3_foobar_key"] == "nrp3_foobar_key_value", (
            "nrp3 config context nrp3_foobar_key secret not resolved"
        )

    def test_use_minion_id_device_hosts_merged(self, nrp3_inventory):  
        """
        nrp3 device config context in Netbox used to merge with nrp3 proxy minon pillar,
        """
        assert len(nrp3_inventory["nrp3"]["hosts"]) > 0, "nrp3 pillar missing all 'hosts'"
        assert nrp3_inventory["nrp3"]["hosts"]["fceos6"]["hostname"] == "1.2.3.4", "nrp3 fceos6 missing hostname"
        assert all(k in nrp3_inventory["nrp3"]["hosts"] for k in ["fceos1", "fceos2", "fceos4", "fceos5", "fceos6"])
        
    def test_use_minion_id_device_hosts_secrets_resolved(self, nrp3_inventory):  
        """
        nrp3 device config context in Netbox used to merge with nrp3 proxy minon pillar,
        adding new fceos6 host, several secrets should be resolved for that host.
        """    
        secrets = nrp3_inventory["nrp3"]["hosts"]["fceos6"]["data"]["secrets"]
        assert nrp3_inventory["nrp3"]["hosts"]["fceos6"]["username"] == "nornir", "fceos6 username secret is missing"
        assert nrp3_inventory["nrp3"]["hosts"]["fceos6"]["password"] == "nornir", "fceos6 password secret is missing"
        assert secrets[0]["bgp"] == "123456bgppeer", "fceos6 bgp secret is missing"
        assert secrets[1]["snmp"] == "qwerty123456", "fceos6 snmp secret is missing"
        assert secrets[2] == "q1w2e3r45t5y", "fceos6 third secret is missing"

    def test_host_platform_value(self, nrp3_inventory):  
        """
        fceos4 Nornir host platrorm value should resolve to "arista_eos"
        using NAPALM driver string value from "FakeNOS Arista cEOS" platform
        """            
        assert nrp3_inventory["nrp3"]["hosts"]["fceos4"]["platform"] == "arista_eos", (
            "fceos4 platform is wrong, should be arista_eos"
        )
        
@skip_if_not_has_netbox
class TestProxyNRP1:  
    
    @pytest.fixture(scope="class", autouse=True)
    def nrp1_inventory(self):        
        ret = client.cmd(
            tgt="nrp1", 
            fun="nr.nornir", 
            arg=["refresh"], 
        )  
        for i in range(3):
            time.sleep(10)
            ret = client.cmd(
                tgt="nrp1", 
                fun="nr.nornir", 
                arg=["inventory"], 
                kwarg={}
            )
            if ret["nrp1"] and "Traceback (most recent call last)" not in str(ret["nrp1"]):
                pprint.pprint(ret)
                return ret
        else:
            raise RuntimeError(f"Failed to retrieve nrp3 inventory: {ret}")
        
    def test_host_add_netbox_data(self, nrp1_inventory):
        """
        Netbox has ceos1 device defined, nrp1 pillar has this config:
        
            salt_nornir_netbox_pillar:
              host_add_netbox_data: salt_nornir_netbox_pillar_test
              use_hosts_filters: True
              hosts_filters: 
                - name: "ceos1"
                
        this is to verify ceos1 has "salt_nornir_netbox_pillar_test" data
        key with netbox inventory data.
        """            
        assert "salt_nornir_netbox_pillar_test" in nrp1_inventory["nrp1"]["hosts"]["ceos1"]["data"], (
            "ceos1 does not have 'salt_nornir_netbox_pillar_test' key in inventory data"
        )
        assert all(
            k in nrp1_inventory["nrp1"]["hosts"]["ceos1"]["data"]["salt_nornir_netbox_pillar_test"]
            for k in netbox_device_data_keys
        ), "ceos1 'salt_nornir_netbox_pillar_test' missing some Netbox keys"
        
    def test_resolve_secrets(self, nrp1_inventory):
        """
        ceos1 in netbox has thos config context data:
        
            secrets_test:
              OSPF_KEY: nb://netbox_secretstore/OSPF/hello_secret
              
        and nrp1 has this configuration:
        
            salt_nornir_netbox_pillar:
              host_add_netbox_data: salt_nornir_netbox_pillar_test
              use_hosts_filters: True
              hosts_filters: 
                - name: "ceos1"
                
        combine with this master config:
        
            ext_pillar:
              - salt_nornir_netbox:
                  ...
                  secrets:
                    resolve_secrets: True
                    secret_device: keymaster-1
                    plugins:
                      netbox_secretstore:
                        private_key: /etc/salt/netbox_secretstore_private.key
                        
        Should result in "nb://netbox_secretstore/OSPF/hello_secret" being 
        resolved to secret value of "keymastr-1/OSPF/hello_secret" secret
        """
        cfg_ctxt = nrp1_inventory["nrp1"]["hosts"]["ceos1"]["data"]["salt_nornir_netbox_pillar_test"]["config_context"]
        assert cfg_ctxt["secrets_test"]["OSPF_KEY"] == "q1w2e3r45t5y", "ceos1 OSPF hello_secret not resolved"