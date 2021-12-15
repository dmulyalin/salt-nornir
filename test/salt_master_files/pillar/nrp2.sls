proxy:
  proxytype: nornir
  multiprocessing: True

hosts:
  csr1000v-1:
    hostname: sandbox-iosxe-latest-1.cisco.com
    platform: cisco_ios
    username: developer
    password: C1sco12345
    port: 22
    connection_options:
      pyats:
        extras:
          devices:
            csr1000v-1:
              os: iosxe
              connections:
                default:
                  ip: 131.226.217.143
                  protocol: ssh
                  port: 22