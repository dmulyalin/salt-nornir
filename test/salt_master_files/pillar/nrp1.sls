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
      napalm_huawei_vrp.huawei_vrp"ncclient:
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
      console:
        extras:
          redispatch:
            password: nornir
            platform: arista_eos
            username: nornir
        hostname: 10.0.1.4
        password: nornir
        port: 22
        username: nornir
      console2:
        extras:
          redispatch: true
        hostname: 10.0.1.4
      inband:
        hostname: 10.0.1.4
        port: 22
      inband_scrapli:
        extras:
          auth_strict_key: false
          ssh_config_file: false
        hostname: 10.0.1.4
        port: 22
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
      interfaces_test:
      - admin_status: is up
        description: Description
        line_status: line protocol is up
        mtu: IP MTU 9200
        name: Ethernet1
      - admin_status: is up
        description: Description
        line_status: line protocol is up
        mtu: IP MTU 65535
        name: Loopback1
      location: North West Hall DC1
      more_tests:
        suite123:
        - name: check ceos hostname
          pattern: FQDN
          task: show hostname
          test: contains
      software_version: cEOS
      syslog:
      - 1.1.1.1
      - 2.2.2.2
      tags:
      - core
      tests:
        suite1:
        - name: check ceos version
          pattern: 1.2.3
          task: show version
          test: contains
        - name: check local clock
          pattern: 'Clock source: local'
          task: show clock
          test: contains
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
      tags:
      - access
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
  cache_base_path: /var/salt-nornir/{proxy_id}/cache/
  multiprocessing: true
  proxytype: nornir
salt_nornir_netbox_pillar:
  host_add_netbox_data: salt_nornir_netbox_pillar_test
  hosts_filters:
  - name: ceos1
  use_hosts_filters: true
