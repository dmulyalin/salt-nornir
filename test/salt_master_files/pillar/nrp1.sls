groups:
  eos_params:
    connection_options:
      ConnectionsPool:
        extras:
          max: 2
      http:
        extras:
          base_url: restconf/data
          headers:
            Accept: application/yang-data+json
            Content-Type: application/yang-data+json
          transport: https
          verify: false
        port: 6020
      napalm:
        extras:
          optional_args:
            port: 80
            transport: http
        platform: eos
      ncclient:
        extras:
          allow_agent: false
          hostkey_verify: false
        port: 830
      pygnmi:
        extras:
          insecure: true
        port: 6030
      scrapli:
        extras:
          auth_strict_key: false
          ssh_config_file: false
        platform: arista_eos
      scrapli_netconf:
        extras:
          auth_strict_key: false
          ssh_config_file: true
          transport: paramiko
          transport_options:
            netconf_force_pty: false
        port: 830
  lab:
    data:
      ntp_servers:
      - 3.3.3.3
      - 3.3.3.4
      syslog_servers:
      - 1.2.3.4
      - 4.3.2.1
    password: nornir
    username: nornir
hosts:
  ceos1:
    connection_options:
      pyats:
        extras:
          devices:
            ceos1:
              connections:
                default:
                  ip: 10.0.1.4
                  port: 22
                  protocol: ssh
                vty_1:
                  ip: 10.0.1.4
                  pool: 3
                  protocol: ssh
              credentials:
                default:
                  password: nornir
                  username: nornir
              os: eos
    data:
      location: North West Hall DC1
      syslog:
      - 1.1.1.1
      - 2.2.2.2
    groups:
    - lab
    - eos_params
    hostname: 10.0.1.4
    platform: arista_eos
  ceos2:
    connection_options:
      pyats:
        extras:
          devices:
            ceos2: {}
        platform: eos
    data:
      location: East City Warehouse
      syslog:
      - 1.1.1.2
      - 2.2.2.1
    groups:
    - lab
    - eos_params
    hostname: 10.0.1.5
    platform: arista_eos

nornir:
  actions:
    arp:
      args:
      - show ip arp
      description: Learn ARP cache
      function: nr.cli
    awr:
      args:
      - wr
      description: Save Arista devices configuration
      function: nr.cli
      kwargs:
        FO:
          platform: arista_eos
    configure_logging:
      args:
      - logging host 7.7.7.7
      function: nr.cfg
      kwargs:
        plugin: netmiko
    configure_ntp:
    - args:
      - ntp server 1.1.1.1
      function: nr.cfg
      kwargs:
        FB: '*'
        plugin: netmiko
    - args:
      - ntp server 1.1.1.2
      function: nr.cfg
      kwargs:
        FB: '*'
        plugin: netmiko
    - args:
      - show run | inc ntp
      function: nr.cli
      kwargs:
        FB: '*'
    facts:
      args:
      - show version
      description: Learn device facts
      function: nr.cli
      kwargs:
        run_ttp: salt://ttp/ceos_show_version.txt
    interfaces:
      args:
      - show run
      description: Learn device interfaces
      function: nr.cli
      kwargs:
        enable: true
        run_ttp: salt://ttp/ceos_interface.txt
    uptime:
      args:
      - show uptime
      description: Learn uptime info
      function: nr.cli
proxy:
  multiprocessing: true
  proxytype: nornir
defaults:
  data:
    credentials:
      deprecated_creds:
        username: cisco
        password: cisco
      local_account: 
        username: nornir
        password: nornir        