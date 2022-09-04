configuration:
  netbox:
    instances:
      prod_in_user_defined_config:
        token: 0123456789abcdef0123456789abcdef01234567
        url: http://192.168.64.200:8000/

defaults:
  data:
    credentials:
      deprecated_creds:
        password: cisco
        username: cisco
      local_account:
        password: nornir
        username: nornir
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
      netbox:
        extras:
          instances:
            dev:
              url: http://192.168.64.200:8000/
            dev_wrong:
              auth:
              - username
              - wrong
              url: http://192.168.64.200:8000/
            production:
              token: 0123456789abcdef0123456789abcdef01234567
              url: http://192.168.64.200:8000/
              default: True
        password: admin
        username: admin
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
      oid:
        get_hostname: 1.3.6.1.2.1.1.5.0
        get_os: 1.3.6.1.2.1.1.1.0
      syslog_servers:
      - 1.2.3.4
      - 4.3.2.1
    password: nornir
    username: nornir
hosts:
  ceos1:
    connection_options:
      puresnmp:
        extras:
          community: public
          version: v2c
        port: 161
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
      puresnmp:
        extras:
          auth:
            method: md5
            password: auth_pass
          priv:
            method: des
            password: priv_pass
          version: v3
        port: 161
        username: snmpv3_user
      pyats:
        extras:
          devices:
            ceos2: {}
        platform: eos
    data:
      location: East City Warehouse
      netbox_import_data:
        device_role:
          slug: router
        device_type:
          slug: arista-ceos
        site:
          slug: salt-nornir-lab
        status: active
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
