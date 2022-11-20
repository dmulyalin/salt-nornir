import pynetbox
import re
import logging
import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


NB_URL = "http://192.168.75.200:8000/"
NB_USERNAME = "admin"
NB_PASSWORD = "admin"
NB_API_TOKEN = "0123456789abcdef0123456789abcdef01234567"
NB_SECRETSTORE_PRIVATE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAm8/rxs6hzp7mRIa7Uc5I3LBfkWihz5ue2jlFBapjFcTXC9J6
b9D/rVyjxw8wVlvnXzVvWicXakiq2zCrqDVt8QvleERw5Py2epRFPcqIeUMRY7Au
9PfYJlY5Lhj89pyrqUINr84AtSffXbkbRbCwS7mtV4Tmp0v5zlkm3W/Z7ImJDyQS
0UhlnlAKiaubPtqf+hweSPRmR2CtnIsBH4k6L2w89BPn8klGAm5Ir9MLZxR8tl3r
AWvKZc/jjNdPybQ/DXaZj+QBOTjuRqCFO2gTWmFnM0vziGD+54pJkT8bJxtJTlBk
hinNW1UNtWlKorZJymsEfZllAyW3m1k+RfoqgwIDAQABAoIBAAwq+qC19lDqe9US
KILE90+0vmHep/RMlOU537gHjGFg0+Jqd4FP8weY2nlrKD02RCVdSOrjbqKwNheT
/3PNaF6QrUTtI1vemGmONrISpQHDSRJd6ezbhhfIWALPlMG1jnpTXDpEfi2nhXwO
PqD8oWfogi75hAHAnyuMLsrQN1aPb9uhREglvlM05qBM2q3ZUpGGrduHyRMqLIo3
+4ow/h4bp3Zy7JDSJPitE9dWwegn0x1wbNSLPqBEo1L0a7A/P9bTcVODVKADHFeC
2+M8elSLfxbyEUikanrjqx9HAKgepDcsXp4atqmbPpIR/MA18Nh0f2VFd7zZvHCH
gInfDSECgYEAwIVPHrqpsVy15NK8o6WSbMBgJo1y949nrLgIsALllajIbUmIbnjp
ujS2lJpmerFcnP1lF9YgNMtRbwULxGQy80z9qUow7CyH/qWIsl3I88mzA3jj39gz
wu7pRzBtohEOkA5k1WL63y/8pBZ0QqHZCXPoci7mpV/UD6/5+QQIcRkCgYEAzzAK
YPXOTJF417lcQssAWeXwa0RgfUbdtSS1P7JFY/IX4MSJH3Oirsa2YIe9ImvNhNLn
tGidjtNAwGFkkndD3hrxk/0Jzye3BU6AMcxL6ZfK60JNQUU//Efz11Bn1cQnHf+Q
1YqOoR+Ln60iggqIkL/iUP5S3FVQl0y2jR3zX/sCgYEAqVcZJyBtjvLLlADBqPhE
eaAlcwPMcnETcltWWOvTYfbahTa+6N02SXGAf+nn5lgH7Jb+yx6vqYCFmq/Hj/HK
1zOLk9MMgVESNi0ItkvELJvn+E/nsMeNkBNx4gp5BKsYMiJXE1NC8/pTsUmG7e1K
6QOpHHagripCb6IMsLqZalECgYBskkkuDEFiQG0p5rmhSs3RTjyRiZBitcsizKyq
R1oziL7Yi0UsFSWwHvOdXCRRsFpPe1HuaU//c1agOalBU3xeHJJxsYz9YFt5TWzC
K8OwElpEtEbVqFticbYnI7x1+cdh4fXc4THi3ywEre7CZJCyAcuwE8YKLi8ASjPz
eTl7FwKBgACuUWblusPn6U3jBnifAybL3m3bhI5GcOUwSNSZ37bg/gmC3xWPaeiV
L3Xy+k/ETJENlgE9g6uHC4P3dZCg34d9hTJuJZ8+alme4s1GHVi0wRD4pjaRoZZg
mFFPZTv2Peg6HwHrFAGLr61fcerdVy7iXCaxbuGlwjVKdrEWA/AB
-----END RSA PRIVATE KEY-----
"""

def slugify(name):
    return re.sub('\W+','-', name.lower())

# list of netbox deice inventory keys to verify device data retrieved from Netbox
netbox_device_data_keys = [
    'airflow', 'asset_tag', 'config_context', 'custom_field_data',
    'device_type', 'last_updated', 'location', 'name', 'platform', 
    'position', 'primary_ip4', 'primary_ip6', 'rack', 'serial', 
    'site', 'status', 'tags', 'tenant',
]

netbox_tasks_device_data_keys = [
    'airflow', 'asset_tag', 'cluster', 'comments', 'config_context', 'created', 'custom_fields',
    'device_type', 'display', 'face', 'id', 'last_updated', 'local_context_data', 'location',
    'name', 'parent_device', 'platform', 'position', 'primary_ip', 'primary_ip4', 'primary_ip6',
    'rack', 'serial', 'site', 'status', 'tags', 'tenant', 'url', 'vc_position', 'vc_priority',
    'virtual_chassis'
]
    
regions = [
    {"name": "APAC"},
    {"name": "EMEA"},
]

tenants = [
    {"name": "SALTNORNIR"}
]

sites = [
    {
        "name": "SALTNORNIR-LAB", 
        "tenant": {"name": "SALTNORNIR"},
        "region": {"name": "APAC"}
    }
]

racks = [
    {"name": "R101", "site": {"name": "SALTNORNIR-LAB"}, "tenant": {"name": "SALTNORNIR"}},
    {"name": "R201", "site": {"name": "SALTNORNIR-LAB"}, "tenant": {"name": "SALTNORNIR"}},
    {"name": "R301", "site": {"name": "SALTNORNIR-LAB"}, "tenant": {"name": "SALTNORNIR"}},
]

manufacturers = [
    {"name": "FakeNOS"},
    {"name": "SaltNornir"},
    {"name": "SaltStack"},
    {"name": "Arista"},
    {"name": "Cisco"},
]

tags = [
    {"name": "nrp3"}
]

device_types = [
    {
        "model": "FakeNOS Arista cEOS",
        "manufacturer": {"name": "FakeNOS"},
    },
    {
        "model": "Salt-Nornir-Proxy-Minion",
        "manufacturer": {"name": "SaltStack"},
    },
    {
        "model": "KeyMaster",
        "manufacturer": {"name": "SaltNornir"},
    },
    {
        "model": "Arista cEOS",
        "manufacturer": {"name": "Arista"},
    },
]

device_roles = [
    {"name": "VirtualRouter", "color": "00ff00"}, # green
    {"name": "KeyMaster", "color": "ff0000"}, # red
    {"name": "ProxyMinion", "color": "0000ff"}, # blue
]

platforms = [
    {
        "name": "FakeNOS Arista cEOS",
        "manufacturer": {"name": "FakeNOS"},
        "napalm_driver": "arista_eos"
    },
    {
        "name": "Arista cEOS",
        "manufacturer": {"name": "Arista"},
        "napalm_driver": "arista_eos"
    },
    {
        "name": "Cisco IOS-XR",
        "napalm_driver": "cisco_xr"
    },    
]

ip_addresses = [
    {"address": "1.0.1.4/32"},
    {"address": "1.0.1.5/32"},
    {"address": "1.0.100.1/32"},
]
# add more ip addresses
ip_addresses.extend(
    [
        {"address": f"1.0.10.{i}/32"}
        for i in range(1, 11)
    ]
)

vlans = [
    {"name": f"VLAN_{i}", "vid": 100 + i}
    for i in range(1,6)
]

interfaces = [
    {"name": "loopback0", "device": {"name": "fceos4"}, "type": "virtual"},
    {"name": "loopback0", "device": {"name": "fceos5"}, "type": "virtual"},
    {"name": "Port-Channel1", "device": {"name": "fceos4"}, "type": "lag", "description": "Main uplink interface"},   
    {"name": "eth101", "device": {"name": "fceos4"}, "type": "1000base-t", "mtu": 1500, "mode": "tagged", "lag": {"name": "Port-Channel1"}},
    {"name": "eth102", "device": {"name": "fceos4"}, "type": "1000base-t", "mtu": 1500, "mode": "tagged", "lag": {"name": "Port-Channel1"}},
    {"name": "eth201", "device": {"name": "fceos4"}, "type": "1000base-t", "mode": "tagged", "tagged_vlans": [102,103,104,105], "untagged_vlan": 101},
]

inventory_items_roles = [
    {"name": "Transceiver", "slug": "transceiver", "color": "ff0000"}
]

inventory_items = [
    {"name": "SFP-1G-T", "device": {"name": "fceos4"}, "role": {"slug": "transceiver"}, "component_type": "dcim.interface", "component": {"name": "eth1"}},
    {"name": "SFP-1G-T", "device": {"name": "fceos4"}, "role": {"slug": "transceiver"}, "component_type": "dcim.interface", "component": {"name": "eth3"}}
]
     
# add more interfaces
interfaces.extend(
    [    
        {"name": f"eth{i}", "device": {"name": "fceos4"}, "type": "1000base-t", "mtu": 1500, "mode": "tagged", "description": f"Interface {i} description"}
        for i in range(1, 11)
    ]
)
interfaces.extend(
    [    
        {"name": f"eth{i}", "device": {"name": "fceos5"}, "type": "1000base-t", "mtu": 1500, "mode": "tagged", "description": f"Interface {i} description"}
        for i in range(1, 11)
    ]
)
# add sub-interfaces
interfaces.extend(
    [    
        {"name": f"eth{i}.1{i}", "device": {"name": "fceos4"}, "type": "virtual", 
         "mtu": 1500, "mode": "tagged", "parent": {"name": f"eth{i}"}, "description": f"Sub-Interface {i} description"}
        for i in range(1, 11)
    ]
)

console_server_ports = [
    {"name": "ConsoleServerPort1", "device": {"name": "fceos5"}},
    {"name": "ConsoleServerPort2", "device": {"name": "fceos5"}},
]

console_ports = [
    {"name": "ConsolePort1", "device": {"name": "fceos4"}},
    {"name": "ConsolePort2", "device": {"name": "fceos4"}},
]

vrfs = [
    {"name": "MGMT"},
    {"name": "CUST1-Flinch34"},
    {"name": "OOB_CTRL"},
    {"name": "Signalling"},
    {"name": "Voice"},
]

ip_adress_to_devices = [
    {
        "address": "1.0.1.4/32",
        "interface": "loopback0",
        "device": "fceos4",
        "role": "loopback",
        "primary_device_ip": True,
    },
    {
        "address": "1.0.1.5/32",
        "interface": "loopback0",
        "device": "fceos5",
        "role": "loopback",
        "primary_device_ip": True,
    },
    {"address": f"1.0.100.1/32", "interface": f"eth1.11", "device": "fceos4", "vrf": {"name": vrfs[1]["name"]}},
]
# associate IP addresses to subinterfaces
ip_adress_to_devices.extend(
    [
        {"address": f"1.0.10.{i}/32", "interface": f"eth{i}.1{i}", "device": "fceos4", "vrf": {"name": vrfs[min(i, 4)]["name"]}}
        for i in range(1, 11)
    ]
)

# create interface connections
# supported teminaton types - "dcim.consoleport", "dcim.interface", "dcim.consoleserverport" etc.
connections = [
    {
        "type": "cat6a",
        "a_terminations": [{"device": "fceos4", "interface": f"eth{i}", "termination_type": "dcim.interface"}],
        "b_terminations": [{"device": "fceos5", "interface": f"eth{i}", "termination_type": "dcim.interface"}],
        "status": "connected",
        "tenant": {"slug": "saltnornir"},
    }
    for i in range(1, 11)
]
# add console connections
connections.extend(
    [
        {
            "type": "cat6a",
            "a_terminations": [{"device": "fceos4", "interface": "ConsolePort1", "termination_type": "dcim.consoleport"}],
            "b_terminations": [{"device": "fceos5", "interface": "ConsoleServerPort1", "termination_type": "dcim.consoleserverport"}],
            "status": "connected",
            "tenant": {"slug": "saltnornir"},
        },
        {
            "type": "cat6a",
            "a_terminations": [{"device": "fceos4", "interface": "ConsolePort2", "termination_type": "dcim.consoleport"}],
            "b_terminations": [{"device": "fceos5", "interface": "ConsoleServerPort2", "termination_type": "dcim.consoleserverport"}],
            "status": "connected",
            "tenant": {"slug": "saltnornir"},
        },
    ]
)

devices = [
    {
        "name": "fceos4",
        "device_type": {"slug": slugify("FakeNOS Arista cEOS")},
        "device_role": {"name": "VirtualRouter"},
        "tenant": {"name": "SALTNORNIR"},
        "site": {"name": "SALTNORNIR-LAB"},
        "rack": {"name": "R101"},
        "position": 40,
        "face": "front",
        "serial": "FNS123451",
        "asset_tag": "UUID-123451",
        "tags": [{"name": "nrp3"}],
        "platform": {"name": "FakeNOS Arista cEOS"},
        "local_context_data": {
            "domain_name": "lab.io",
            "lo0_ip": "1.0.1.4",
            "syslog_servers": [
                "10.0.0.3",
                "10.0.0.4"
            ],
            "secrets": {
                "bgp": "nb://netbox_secretstore/keymaster-1/BGP/peers_pass",
                "secret1": "nb://netbox_secretstore/fceos4/SaltSecrets/secret1",
                "secret2": "nb://netbox_secretstore/SaltSecrets/secret2",
                "secret3": "nb://netbox_secretstore/secret3",
                "secret4": "nb://secret4",
            }
        }
    },
    {
        "name": "fceos5",
        "device_type": {"slug": slugify("FakeNOS Arista cEOS")},
        "device_role": {"name": "VirtualRouter"},
        "tenant": {"name": "SALTNORNIR"},
        "site": {"name": "SALTNORNIR-LAB"},
        "rack": {"name": "R201"},
        "position": 40,
        "face": "front",
        "platform": {"name": "FakeNOS Arista cEOS"},
        "local_context_data": {
            "nornir": {
                "platform": "arista_eos",
                "hostname": "10.0.1.10",
                "port": "6002",
                "username": "nb://netbox_secretstore/keymaster-1/SaltNornirCreds/username",
                "password": "nb://netbox_secretstore/keymaster-1/SaltNornirCreds/password",
            }
        }
    },
    {
        "name": "keymaster-1",
        "device_type": {"slug": slugify("KeyMaster")},
        "device_role": {"name": "KeyMaster"},
        "tenant": {"name": "SALTNORNIR"},
        "site": {"name": "SALTNORNIR-LAB"},
    },
    {
        "name": "nrp3",
        "device_type": {"slug": slugify("Salt-Nornir-Proxy-Minion")},
        "device_role": {"name": "ProxyMinion"},
        "tenant": {"name": "SALTNORNIR"},
        "site": {"name": "SALTNORNIR-LAB"},
        "local_context_data": {
            "proxy": {
                "proxy_always_alive": True
            },
            "hosts": {
                "fceos6": {
                    "hostname": "1.2.3.4",
                    "platform": "arista_eos",
                    "port": "22",
                    "username": "nb://netbox_secretstore/keymaster-1/SaltNornirCreds/username",
                    "password": "nb://netbox_secretstore/keymaster-1/SaltNornirCreds/password",
                    "data": {
                        "secrets": [
                            {"bgp": "nb://netbox_secretstore/keymaster-1/BGP/peers_pass"},
                            {"snmp": "nb://netbox_secretstore/keymaster-1/SNMP/community"},  
                            "nb://netbox_secretstore/keymaster-1/OSPF/hello_secret"
                        ]
                    }
                },
                "fceos7": {
                    "hostname": "1.2.3.5",
                    "platform": "arista_eos",
                    "port": "22",
                    "username": "nornir",
                    "password": "nornir",
                    "data": {
                        "bgp": {
                            "peers": [
                                {"bgp_peer_secret": "nb://netbox_secretstore/keymaster-1/BGP_PEERS/10.0.1.1"},
                                {"bgp_peer_secret": "nb://netbox_secretstore/keymaster-1/BGP_PEERS/10.0.1.2"},
                                {"bgp_peer_secret": "nb://netbox_secretstore/keymaster-1/BGP_PEERS/10.0.1.3"},
                            ]
                        }
                    }
                }
            },
            "foo": "bar",
            "nrp3_foobar_key": "nb://nrp3_foobar_key_secret",
            "nornir": {
                "actions": {
                    "foobar": {
                        "function": "nr.cli",
                        "args": ["show clock"],
                        "description": "test action"
                    }
                }
            }
        }
    },
    {
        "name": "ceos1",
        "device_type": {"slug": slugify("Arista cEOS")},
        "device_role": {"name": "VirtualRouter"},
        "tenant": {"name": "SALTNORNIR"},
        "site": {"name": "SALTNORNIR-LAB"},
        "rack": {"name": "R201"},
        "position": 41,
        "face": "front",
        "platform": {"name": "Arista cEOS"},
        "local_context_data": {
            "secrets_test": {
                "OSPF_KEY": "nb://netbox_secretstore/OSPF/hello_secret"
            },
            "nornir": {
                "hostname": "10.0.1.4",
            }
        }
    },
]

netbox_secretsotre_roles = [
    {"name": "SaltNornirCreds"},
    {"name": "SaltSecrets"},
    {"name": "BGP"},
    {"name": "SNMP"},
    {"name": "ISIS"},
    {"name": "OSPF"},
    {"name": "SSH"},
    {"name": "Credentials"},
    {"name": "BGP_PEERS"},
]

netbox_secretsotre_secrets = [
    {
        "name": "secret1",
        "role": {"name": "SaltSecrets"},
        "device": "fceos4",
        "plaintext": "secret1_value"
    },
    {
        "name": "secret2",
        "role": {"name": "SaltSecrets"},
        "device": "fceos4",
        "plaintext": "secret2_value"
    },
    {
        "name": "secret3",
        "role": {"name": "SaltSecrets"},
        "device": "fceos4",
        "plaintext": "secret3_value"
    },
    {
        "name": "secret4",
        "role": {"name": "SaltSecrets"},
        "device": "fceos4",
        "plaintext": "secret4_value"
    },
    {
        "name": "nrp3_foobar_key_secret",
        "role": {"name": "SaltSecrets"},
        "device": "nrp3",
        "plaintext": "nrp3_foobar_key_value"
    },
    {
        "name": "username",
        "role": {"name": "SaltNornirCreds"},
        "device": "keymaster-1",
        "plaintext": "nornir"
    },
    {
        "name": "password",
        "role": {"name": "SaltNornirCreds"},
        "device": "keymaster-1",
        "plaintext": "nornir"
    },
    {
        "name": "username",
        "role": {"name": "SaltNornirCreds"},
        "device": "fceos4",
        "plaintext": "nornir"
    },
    {
        "name": "password",
        "role": {"name": "SaltNornirCreds"},
        "device": "fceos4",
        "plaintext": "nornir"
    },
    {
        "name": "peers_pass",
        "role": {"name": "BGP"},
        "device": "keymaster-1",
        "plaintext": "123456bgppeer"
    },
    {
        "name": "community",
        "role": {"name": "SNMP"},
        "device": "keymaster-1",
        "plaintext": "qwerty123456"
    },   
    {
        "name": "admin_user",
        "role": {"name": "Credentials"},
        "device": "keymaster-1",
        "plaintext": "Nornir123"
    },   
    {
        "name": "10.0.1.1",
        "role": {"name": "BGP_PEERS"},
        "device": "keymaster-1",
        "plaintext": "BGPSecret1"
    },    
    {
        "name": "10.0.1.2",
        "role": {"name": "BGP_PEERS"},
        "device": "keymaster-1",
        "plaintext": "BGPSecret2"
    },    
    {
        "name": "10.0.1.3",
        "role": {"name": "BGP_PEERS"},
        "device": "keymaster-1",
        "plaintext": "BGPSecret3"
    },    
    {
        "name": "hello_secret",
        "role": {"name": "OSPF"},
        "device": "keymaster-1",
        "plaintext": "q1w2e3r45t5y"
    },  
]


def _netbox_secretstore_get_session_key():
    """
    Function to retrieve netbox_secretstore session key
    """
    url = NB_URL + "/api/plugins/netbox_secretstore/get-session-key/"
    token = "Token " + NB_API_TOKEN
    # send request to netbox
    req = requests.post(
        url, 
        headers={
            "authorization": token
        }, 
        json={
            "private_key": NB_SECRETSTORE_PRIVATE_KEY.strip(),
            "preserve_key": True,
        }
    )
    if req.status_code == 200:
        log.info("netbox_data obtained netbox-secretsore session key")   
        return req.json()["session_key"]
    else:
        raise RuntimeError(
            f"netbox_data failed to get netbox_secretstore session-key, "
            f"status-code '{req.status_code}', reason '{req.reason}', response "
            f"content '{req.text}'" 
        )
                
def create_regions():
    log.info("netbox_data: creating regions")
    for region in regions:
        region.setdefault("slug", slugify(region["name"]))
        try:
            nb.dcim.regions.create(**region)
        except Exception as e:
            log.error(f"netbox_data: creating region '{region}' error '{e}'")
            
def ceate_tenants():
    log.info("netbox_data: creating tenants")
    for tenant in tenants:
        tenant.setdefault("slug", slugify(tenant["name"]))
        try:
            nb.tenancy.tenants.create(**tenant)
        except Exception as e:
            log.error(f"netbox_data: creating tenant '{tenant}' error '{e}'")    
    
def create_sites():
    log.info("netbox_data: creating sites")
    for site in sites:
        site.setdefault("slug", slugify(site["name"]))
        try:
            nb.dcim.sites.create(**site)
        except Exception as e:
            log.error(f"netbox_data: creating site '{site}' error '{e}'")        

def create_racks():
    log.info("netbox_data: creating racks")
    for rack in racks:
        rack.setdefault("slug", slugify(rack["name"]))
        try:
            nb.dcim.racks.create(**rack)
        except Exception as e:
            log.error(f"netbox_data: creating rack '{rack}' error '{e}'")  
            
def create_manufacturers():
    log.info("netbox_data: creating manufacturers")
    for manufacturer in manufacturers:
        manufacturer.setdefault("slug", slugify(manufacturer["name"]))
        try:
            nb.dcim.manufacturers.create(**manufacturer)
        except Exception as e:
            log.error(f"netbox_data: creating manufacturer '{manufacturer}' error '{e}'") 

def create_tags():
    log.info("netbox_data: creating tags")
    for tag in tags:
        tag.setdefault("slug", slugify(tag["name"]))
        try:
            nb.extras.tags.create(**tag)
        except Exception as e:
            log.error(f"netbox_data: creating tag '{tag}' error '{e}'") 

def create_platforms():
    log.info("netbox_data: creating platforms")
    for platform in platforms:
        platform.setdefault("slug", slugify(platform["name"]))
        try:
            nb.dcim.platforms.create(**platform)
        except Exception as e:
            log.error(f"netbox_data: creating platform '{platform}' error '{e}'") 

def create_device_types():
    log.info("netbox_data: creating device types")
    for device_type in device_types:
        device_type.setdefault("slug", slugify(device_type["model"]))
        try:
            nb.dcim.device_types.create(**device_type)
        except Exception as e:
            log.error(f"netbox_data: creating device type '{device_type}' error '{e}'") 
            
def create_device_roles():
    log.info("netbox_data: creating device roles")
    for device_role in device_roles:
        device_role.setdefault("slug", slugify(device_role["name"]))
        try:
            nb.dcim.device_roles.create(**device_role)
        except Exception as e:
            log.error(f"netbox_data: creating device role '{device_role}' error '{e}'") 
            
def create_ip_addresses():
    log.info("netbox_data: creating ip addresses")
    for ip_address in ip_addresses:
        try:
            nb.ipam.ip_addresses.create(**ip_address)
        except Exception as e:
            log.error(f"netbox_data: creating ip address '{ip_address}' error '{e}'") 

def create_vrfs():
    log.info("netbox_data: creating vrfs")
    for vrf in vrfs:
        try:
            nb.ipam.vrfs.create(**vrf)
        except Exception as e:
            log.error(f"netbox_data: creating vrf '{vrf}' error '{e}'") 
            
def create_vlans():
    log.info("netbox_data: creating vlans")
    for vlan in vlans:
        try:
            nb.ipam.vlans.create(**vlan)
        except Exception as e:
            log.error(f"netbox_data: creating vlan '{vlan}' error '{e}'") 
            
def create_interfaces():
    log.info("netbox_data: creating interfaces")
    # create parent interfaces
    for interface in interfaces:
        # skip child interfaces
        if "parent" in interface:
            continue        
        try:
            if "tagged_vlans" in interface:
                for index, vid in enumerate(interface["tagged_vlans"]):
                    nb_vlan = nb.ipam.vlans.get(vid=str(vid))
                    interface["tagged_vlans"][index] = nb_vlan.id
            if "untagged_vlan" in interface:
                nb_vlan = nb.ipam.vlans.get(vid=str(interface["untagged_vlan"]))
                interface["untagged_vlan"] = nb_vlan.id
            nb.dcim.interfaces.create(**interface)
        except Exception as e:
            log.error(f"netbox_data: creating interface '{interface}' error '{e}'") 
    # create child interfaces
    log.info("netbox_data: creating child interfaces")
    for interface in interfaces:
        # skip non child interfaces
        if "parent" not in interface:
            continue  
        try:
            nb_parent_intf = nb.dcim.interfaces.get(name=interface["parent"]["name"], device=interface["device"]["name"])
            interface["parent"] = nb_parent_intf.id
            nb.dcim.interfaces.create(**interface)
        except Exception as e:
            log.error(f"netbox_data: creating interface '{interface}' error '{e}'") 
        
def create_console_server_ports():
    log.info("netbox_data: creating console server ports")
    for port in console_server_ports:    
        try:
            nb.dcim.console_server_ports.create(**port)
        except Exception as e:
            log.error(f"netbox_data: creating console server port '{port}' error '{e}'") 

def create_console_ports():
    log.info("netbox_data: creating console ports")
    for port in console_ports:    
        try:
            nb.dcim.console_ports.create(**port)
        except Exception as e:
            log.error(f"netbox_data: creating console port '{port}' error '{e}'") 
            
def create_devices():
    log.info("netbox_data: creating devices")
    for device in devices:
        device.setdefault("slug", slugify(device["name"]))
        try:
            nb.dcim.devices.create(**device)
        except Exception as e:
            log.error(f"netbox_data: creating device '{device}' error '{e}'") 

def associate_ip_adress_to_devices():
    """Function to associate IP adresses to device intefaces and to associate vrfs to interfaces and ip adresses"""
    log.info("netbox_data: associating primary ip adresses to devices")
    for i in ip_adress_to_devices:
        device = nb.dcim.devices.get(name=i["device"])
        interface = nb.dcim.interfaces.get(name=i["interface"], device=i["device"])
        ip = nb.ipam.ip_addresses.get(address=i["address"])
        ip.assigned_object_id = interface.id
        ip.assigned_object_type = "dcim.interface"
        if i.get("vrf"):
            vrf = nb.ipam.vrfs.get(name=i["vrf"]["name"])
            ip.vrf = vrf.id
            interface.vrf = vrf.id
            interface.save()
        ip.save()
        if i.get("primary_device_ip"):
            device.primary_ip4 = ip.id
            device.save()
            
# {
#     "type": "cat6a",
#     "a_terminations": [{"device": "fceos4", "interface": f"eth{i}", "termination_type": "dcim.interface"}],
#     "b_terminations": [{"device": "fceos5", "interface": f"eth{i}", "termination_type": "dcim.interface"}],
#     "status": "active",
#     "tenant": {"slug": "saltnornir"},
# }
def create_connections():
    log.info("netbox_data: creatig connections")
    for connection in connections:
        
        a_termination_type = connection["a_terminations"][0]["termination_type"]
        if a_termination_type == "dcim.interface":
            nb_interface_a = nb.dcim.interfaces.get(
                device=connection["a_terminations"][0]["device"],
                name=connection["a_terminations"][0]["interface"],
            )
        elif a_termination_type == "dcim.consoleport":
            nb_interface_a = nb.dcim.console_ports.get(
                device=connection["a_terminations"][0]["device"],
                name=connection["a_terminations"][0]["interface"],
            )
        elif a_termination_type == "dcim.consoleserverport":
            nb_interface_a = nb.dcim.console_server_ports.get(
                device=connection["a_terminations"][0]["device"],
                name=connection["a_terminations"][0]["interface"],
            )
        else:
            raise ValueError(f"Unsupported a_termination_type '{a_termination_type}'")

        b_termination_type = connection["b_terminations"][0]["termination_type"]
        if b_termination_type == "dcim.interface":
            nb_interface_b = nb.dcim.interfaces.get(
                device=connection["b_terminations"][0]["device"],
                name=connection["b_terminations"][0]["interface"],
            )
        elif b_termination_type == "dcim.consoleport":
            nb_interface_b = nb.dcim.console_ports.get(
                device=connection["b_terminations"][0]["device"],
                name=connection["b_terminations"][0]["interface"],
            )
        elif b_termination_type == "dcim.consoleserverport":
            nb_interface_b = nb.dcim.console_server_ports.get(
                device=connection["b_terminations"][0]["device"],
                name=connection["b_terminations"][0]["interface"],
            )
        else:
            raise ValueError(f"Unsupported b_termination_type '{b_termination_type}'")
            
        connection["a_terminations"] = [{
            "object_type": connection["a_terminations"][0]["termination_type"],
            "object_id": nb_interface_a.id
        }]
        connection["b_terminations"] = [{
            "object_type": connection["b_terminations"][0]["termination_type"],
            "object_id": nb_interface_b.id
        }]
        nb.dcim.cables.create(**connection)
        
        
def create_netbox_secretsotre_roles():
    log.info("netbox_data: creating netbox_secretstore secret roles")
    session_key = _netbox_secretstore_get_session_key()
    url = NB_URL + "/api/plugins/netbox_secretstore/secret-roles/"
    token = "Token " + NB_API_TOKEN
    for role in netbox_secretsotre_roles:
        role.setdefault("slug", slugify(role["name"]))
        # send request to netbox
        req = requests.post(
            url, 
            headers={
                "X-Session-Key": session_key,
                "authorization": token
            }, 
            json=role
        )
        if req.status_code != 201:
            log.error(
                f"netbox_data failed to create netbox_secretstore secret role '{role}', "
                f"status-code '{req.status_code}', reason '{req.reason}', response "
                f"content '{req.text}'" 
            )
    
def create_netbox_secretsotre_secrets():
    log.info("netbox_data: creating netbox_secretstore secrets")
    session_key = _netbox_secretstore_get_session_key()
    url = NB_URL + "/api/plugins/netbox_secretstore/secrets/"
    token = "Token " + NB_API_TOKEN
    for secret in netbox_secretsotre_secrets:
        device = nb.dcim.devices.get(name=secret.pop("device"))
        secret["assigned_object_id"] = device.id
        secret["assigned_object_type"] = "dcim.device"
        # send request to netbox
        req = requests.post(
            url, 
            headers={
                "X-Session-Key": session_key,
                "authorization": token
            }, 
            json=secret
        )
        if req.status_code != 201:
            log.error(
                f"netbox_data failed to create netbox_secretstore secret '{secret}', "
                f"status-code '{req.status_code}', reason '{req.reason}', response "
                f"content '{req.text}'" 
            )        

def create_inventory_items_roles():
    log.info("netbox_data: creating inventory items roles")
    for role in inventory_items_roles:
        try:
            nb.dcim.inventory_item_roles.create(**role)
        except Exception as e:
            log.error(f"netbox_data: creating inventory item role '{role}' error '{e}'") 
        
    
def create_inventory_items():
    log.info("netbox_data: creating inventory items")
    for item in inventory_items:
        component = item.pop("component")
        interface = nb.dcim.interfaces.get(
            device=item["device"]["name"],
            name=component["name"],
        )
        try:
            nb.dcim.inventory_items.create(
                **item,
                component_id=interface.id
            )
        except Exception as e:
            log.error(f"netbox_data: creating inventory item '{item}' error '{e}'") 
            
def delete_netbox_secretstore_secrets():
    log.info("netbox_data: deleting netbox_secretstore secrets")
    session_key = _netbox_secretstore_get_session_key()
    url = NB_URL + "/api/plugins/netbox_secretstore/secrets/"
    token = "Token " + NB_API_TOKEN
    req = requests.get(
        url, 
        headers={
            "X-Session-Key": session_key,
            "authorization": token
        },
        json={}
    )
    if req.status_code != 200:
        raise SystemExit(
            f"netbox_data failed to retrieve netbox_secretstore secrets, "
            f"status-code '{req.status_code}', reason '{req.reason}', response "
            f"content '{req.text}'" 
        ) 
    # delete secrets one by one
    for secret in req.json()["results"]:
        req = requests.delete(
            url + f"/{secret['id']}", 
            headers={
                "X-Session-Key": session_key,
                "authorization": token
            },
            json={}
        )
        if req.status_code != 204:
            log.error(
                f"netbox_data failed to delete netbox_secretstore secret '{secret}', "
                f"status-code '{req.status_code}', reason '{req.reason}', response "
                f"content '{req.text}'" 
            )         
    
def delete_netbox_secretsotre_roles():
    log.info("netbox_data: deleting netbox_secretstore secret roles")
    session_key = _netbox_secretstore_get_session_key()
    url = NB_URL + "/api/plugins/netbox_secretstore/secret-roles/"
    token = "Token " + NB_API_TOKEN
    # get existing roles
    req = requests.get(
        url, 
        headers={
            "X-Session-Key": session_key,
            "authorization": token
        },
        json={}
    )
    if req.status_code != 200:
        log.error(
            f"netbox_data failed to get netbox_secretstore secret roles, "
            f"status-code '{req.status_code}', reason '{req.reason}', response "
            f"content '{req.text}'" 
        )
    # delete roles
    req = requests.delete(
        url, 
        headers={
            "X-Session-Key": session_key,
            "authorization": token
        },
        json=[{"id": i["id"]} for i in req.json()["results"]]
    )
    if req.status_code != 204:
        log.error(
            f"netbox_data failed to delete netbox_secretstore secret roles, "
            f"status-code '{req.status_code}', reason '{req.reason}', response "
            f"content '{req.text}'" 
        )
            
def delete_devices():
    log.info("netbox_data: deleting devices")
    for device in devices:
        try:
            nb_device = nb.dcim.devices.get(name=device["name"])
            if nb_device:
                nb_device.delete()
        except Exception as e:
            log.error(f"netbox_data: creating device '{device}' error '{e}'")     
    
def delete_ip_addresses():
    log.info("netbox_data: deleting ip addresses")
    for ip_address in ip_addresses:
        try:
            ip = nb.ipam.ip_addresses.filter(address=ip_address["address"])
            for ip in ip:
                ip.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting ip address '{ip_address}' error '{e}'") 
            
def delete_vrfs():
    log.info("netbox_data: deleting vrfs")
    for vrf in vrfs:
        try:
            vrf_nb = nb.ipam.vrfs.get(name=vrf["name"])
            if vrf_nb:
                vrf_nb.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting vrf '{vrf}' error '{e}'") 
 
def delete_vlans():
    log.info("netbox_data: deleting vlans")
    for vlan in vlans:
        try:
            vlan_nb = nb.ipam.vlans.get(name=vlan["name"])
            if vlan_nb:
                vlan_nb.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting vlan '{vlan}' error '{e}'") 
            
def delete_device_roles():
    log.info("netbox_data: delete device roles")
    for device_role in device_roles:
        try:
            nb_device_role = nb.dcim.device_roles.get(name=device_role["name"])
            if nb_device_role:
                nb_device_role.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting device role '{device_role}' error '{e}'") 
            
def delete_device_types():
    log.info("netbox_data: deleting device types")
    for device_type in device_types:
        try:
            nb_device_type = nb.dcim.device_types.get(
                model=device_type["model"],
                manufacturer=slugify(device_type["manufacturer"]["name"])
            )
            if nb_device_type:
                nb_device_type.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting device type '{device_type}' error '{e}'") 

def delete_platforms():
    log.info("netbox_data: deleting platforms")
    for platform in platforms:
        try:
            nb_platform = nb.dcim.platforms.get(name=platform["name"])
            if nb_platform:
                nb_platform.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting platform '{platform}' error '{e}'") 

def delete_manufacturers():
    log.info("netbox_data: deleting manufacturers")
    for manufacturer in manufacturers:
        try:
            nb_manufacturer = nb.dcim.manufacturers.get(name=manufacturer["name"])
            if nb_manufacturer:
                nb_manufacturer.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting manufacturer '{manufacturer}' error '{e}'") 
            
def delete_tags():
    log.info("netbox_data: deleting tags")
    for tag in tags:
        try:
            nb_tag = nb.extras.tags.get(name=tag["name"])
            if nb_tag:
                nb_tag.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting tag '{tag}' error '{e}'") 

def delete_racks():
    log.info("netbox_data: deleting racks")
    for rack in racks:
        try:
            nb_rack = nb.dcim.racks.get(name=rack["name"])
            if nb_rack:
                nb_rack.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting racks '{rack}' error '{e}'")  
            
def delete_regions():
    log.info("netbox_data: deleting regions")
    for region in regions:
        try:
            nb_region = nb.dcim.regions.get(name=region["name"])
            if nb_region:
                nb_region.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting region '{region}' error '{e}'")
            
def delete_tenants():
    log.info("netbox_data: deleting tenants")
    for tenant in tenants:
        try:
            nb_tenant = nb.tenancy.tenants.get(name=tenant["name"])
            if nb_tenant:
                nb_tenant.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting tenant '{tenant}' error '{e}'")    
    
def delete_connections():
    log.info("netbox_data: deleting all connections")
    try:
        nb_connections = nb.dcim.cables.all()
        for i in nb_connections:
            i.delete()
    except Exception as e:
        log.error(f"netbox_data: deleting all connections error '{e}'")    
        
def delete_sites():
    log.info("netbox_data: deleting sites")
    for site in sites:
        try:
            nb_site = nb.dcim.sites.get(name=site["name"])
            if nb_site:
                nb_site.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting site '{site}' error '{e}'")   
            
def delete_inventory_items_roles():
    log.info("netbox_data: deleting inventory items roles")
    for role in inventory_items_roles:
        try:
            nb_role = nb.dcim.inventory_item_roles.get(name=role["name"])
            nb_role.delete()
        except Exception as e:
            log.error(f"netbox_data: deleting inventory item role '{role}' error '{e}'")     
    
def clean_up_netbox():
    delete_netbox_secretstore_secrets()
    delete_netbox_secretsotre_roles()
    delete_devices()
    delete_ip_addresses()
    delete_vrfs()
    delete_vlans()
    delete_device_roles()
    delete_device_types()
    delete_platforms()
    delete_manufacturers()
    delete_tags()
    delete_racks()
    delete_sites()
    delete_regions()
    delete_connections()
    delete_tenants()
    delete_inventory_items_roles()
    
def populate_netbox():
    create_regions()
    ceate_tenants()
    create_sites()
    create_racks()
    create_manufacturers()
    create_device_types()
    create_device_roles()
    create_platforms()
    create_vrfs()
    create_ip_addresses()
    create_tags()
    create_devices()
    create_vlans()
    create_interfaces()
    create_inventory_items_roles()
    create_inventory_items()
    create_console_server_ports()
    create_console_ports()
    associate_ip_adress_to_devices()
    create_connections()
    create_netbox_secretsotre_roles()
    create_netbox_secretsotre_secrets()
    
    
if __name__ == "__main__":
    try:
        nb = pynetbox.api(url=NB_URL, token=NB_API_TOKEN)
        # request status to verify that Netbox is reachable,
        # raises ConnectionError if Netbox is not reachable
        _ = nb.status()
        globals()["nb"] = nb
    except Exception as e:
        log.exception(
            f"netbox_data failed to instantiate pynetbox.api object, "
            f"Netbox url '{url}', token ends with '..{token[-6:]}', error '{e}'"
        )
    
    todo = input("""Select what to do with Netbox:
1 - cleanup
2 - populate
3 - cleanup first, next populate
[1,2,3]: """)
    if todo == "1":
        clean_up_netbox()
    elif todo == "2":
        populate_netbox()
    elif todo == "3":
        clean_up_netbox()
        populate_netbox()
