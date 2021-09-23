proxy:
  proxytype: nornir
  multiprocessing: True

hosts:
  ceos1:
    hostname: 10.0.1.4
    platform: arista_eos
    groups: [lab, eos_params]
    data:
      location: "North West Hall DC1"

  ceos2:
    hostname: 10.0.1.5
    platform: arista_eos
    groups: [lab, eos_params]
    data:
      location: "East City Warehouse"
          
groups: 
  lab:
    username: nornir
    password: nornir
    data:
      ntp_servers: ["3.3.3.3", "3.3.3.4"]
      syslog_servers: ["1.2.3.4", "4.3.2.1"] 
  eos_params:
    connection_options:
      scrapli:
        platform: arista_eos
        extras:
          auth_strict_key: False
          ssh_config_file: False
      scrapli_netconf:
        port: 830
        extras:
          ssh_config_file: True
          auth_strict_key: False
          transport: paramiko
          transport_options: 
            netconf_force_pty: False
      napalm:
        platform: eos
        optional_args:
          transport: http
          port: 80  
      ncclient:
        port: 830
        extras:
          allow_agent: False
          hostkey_verify: False
      http:
        port: 80
        transport: http
          
nornir:
  actions:
    awr: 
      function: nr.cli
      args: ["wr"]
      kwargs: {"FO": {"platform": "arista_eos"}}
      description: "Save Arista devices configuration"
    configure_ntp:
      - function: nr.cfg
        args: ["ntp server 1.1.1.1"]
        kwargs: {"FB": "*", "plugin": "netmiko"}
      - function: nr.cfg
        args: ["ntp server 1.1.1.2"]
        kwargs: {"FB": "*", "plugin": "netmiko"}
      - function: nr.cli
        args: ["show run | inc ntp"]
        kwargs: {"FB": "*"}
    configure_logging:
      function: nr.cfg
      args: ["logging host 7.7.7.7"]
      kwargs: {"plugin": "netmiko"}
    # nr.learn aliases
    arp:
      function: nr.cli
      args: ["show ip arp"]
      description: "Learn ARP cache"  
    uptime:
      function: nr.cli
      args: ["show uptime"]
      description: "Learn uptime info"      
    facts:
      function: nr.cli
      args: ["show version"]
      kwargs: {"run_ttp": "salt://ttp/ceos_show_version.txt"}
      description: "Learn device facts"  
    interfaces:
      function: nr.cli
      args: ["show run"]
      kwargs: {"run_ttp": "salt://ttp/ceos_interface.txt", "enable": True}
      description: "Learn device interfaces"  