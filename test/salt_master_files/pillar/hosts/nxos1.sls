hosts:
  nxos1:
    hostname: sandbox-nxos-1.cisco.com
    platform: nxos_ssh
    username: admin
    password: "Admin_1234!"
    port: 22
    connection_options:
      ncclient:
        port: 830
        extras:
          allow_agent: False
          hostkey_verify: False
          device_params:
            name: nexus
      scrapli_netconf:
        port: 830
        extras:
          ssh_config_file: True
          auth_strict_key: False
          transport_options: 
            netconf_force_pty: False            
      pyats:
        extras:
          devices:
            nxos1:
              os: nxos
              connections:
                default:
                  arguments:
                    learn_hostname: true
                  ip: sandbox-nxos-1.cisco.com
                  protocol: ssh
                  port: 22      