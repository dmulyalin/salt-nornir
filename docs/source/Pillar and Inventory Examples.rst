Pillar and Inventory Examples
#############################

This section contains samples that could serve as a starting point to construct pillar for
Nornir Proxy Minion on salt-master machine.

.. contents:: :local:

Arista cEOS
===========

Below inventory can be used with Arista cEOS and contains parameters for these connection plugins:

- Netmiko - uses SSH and platform ``arista_eos`` under base arguments definition
- NAPALM - uses Arista eAPI over HTTP port 80 and platform ``eos`` as specified in eos_params group's ``connection_options``
- Ncclient - as specified in eos_params group's ``connection_options`` uses port 830 with default device type
- PyATS - for ceos1 has multiple connections defined, including a pool of 3 connections for ``vty_1`` connection.
  For ceos2 parameters sourced from base arguments.
- HTTP - uses port 6020 over HTTPS as specified in eos_params group's ``connection_options``
- Scrapli - uses SSH without verifying the keys, platform ``arista_eos`` as specified in eos_params group's ``connection_options``
- Scrapli-Netconf - uses SSH paramiko transport with port 830 as specified in eos_params group's ``connection_options``
- PyGNMI - uses port 6030 allowing insecure connection as specified in eos_params group's ``connection_options``

.. code-block:: yaml

    proxy:
      proxytype: nornir
      multiprocessing: True

    hosts:
      ceos1:
        hostname: 10.0.1.4
        platform: arista_eos
        groups: [creds, eos_params]
        connection_options:
          pyats:
            extras:
              devices:
                ceos1:
                  os: eos
                  credentials:
                    default:
                      username: nornir
                      password: nornir
                  connections:
                    default:
                      protocol: ssh
                      ip: 10.0.1.4
                      port: 22
                    vty_1:
                      protocol: ssh
                      ip: 10.0.1.4
                      pool: 3

      ceos2:
        hostname: 10.0.1.5
        platform: arista_eos
        groups: [creds, eos_params]
        connection_options:
          pyats:
            platform: eos
            extras:
              devices:
                ceos2: {}

    groups:
      creds:
        username: nornir
        password: nornir
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
                # refer to https://github.com/saltstack/salt/issues/59962 for details
                # on why need netconf_force_pty False
                netconf_force_pty: False
          napalm:
            platform: eos
            extras:
              optional_args:
                transport: http
                port: 80
          ncclient:
            port: 830
            extras:
              allow_agent: False
              hostkey_verify: False
          http:
            port: 6020
            extras:
              transport: https
              verify: False
              base_url: "restconf/data"
              headers:
                Content-Type: "application/yang-data+json"
                Accept: "application/yang-data+json"
          pygnmi:
            port: 6030
            extras:
              insecure: True

Cisco IOS-XE
============

Below inventory can be used with Cisco IOSXE based devices and contains parameters for these connection plugins:

- Netmiko - uses SSH and platform ``cisco_ios`` under base arguments definition
- PyATS - uses ``iosxe`` platform with SSH protocol on port 22 as specified in ``connection_options``
- HTTP - uses HTTPS transport on port 443 with base url "restconf/data" as specified in ``connection_options``
- Ncclient - uses port 830 with platform name ``iosxe`` as specified in ``connection_options``
- Scrapli-Netconf - uses port 830 with paramiko transport as specified in ``connection_options``
- NAPALM - uses SSH and platform ``ios`` as specified in ``connection_options``
- Scrapli - uses SSH and platform ``cisco_iosxe`` without verifying SSH keys as specified in ``connection_options``

.. code-block:: yaml

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
          napalm:
            platform: ios
          scrapli:
            platform: cisco_iosxe
            extras:
              auth_strict_key: False
              ssh_config_file: False
          http:
            port: 443
            extras:
              transport: https
              verify: False
              base_url: "restconf/data"
              headers:
                Content-Type: "application/yang-data+json"
                Accept: "application/yang-data+json"
          ncclient:
            port: 830
            extras:
              allow_agent: False
              hostkey_verify: False
              device_params:
                name: iosxe
          scrapli_netconf:
            port: 830
            extras:
              transport: paramiko
              ssh_config_file: True
              auth_strict_key: False
              transport_options:
                netconf_force_pty: False

Cisco IOSXR
===========

Below inventory can be used with Cisco IOSXR based devices and contains parameters for these connection plugins:

- Netmiko - uses SSH and platform ``cisco_xr`` under base arguments definition
- Ncclient - uses port 830 with platform name ``iosxr`` as specified in ``connection_options``
- Scrapli-Netconf - uses port 830 as specified in ``connection_options``
- NAPALM - uses SSH and platform ``iosxr`` as specified in ``connection_options``
- Scrapli - uses SSH and platform ``cisco_iosxr`` without verifying SSH keys as specified in ``connection_options``
- PyATS - uses ``iosxr`` platform with SSH protocol on port 22 as specified in ``connection_options``

.. code-block:: yaml

    proxy:
      proxytype: nornir
      multiprocessing: True

    hosts:
      iosxr1:
        hostname: sandbox-iosxr-1.cisco.com
        platform: cisco_xr
        username: admin
        password: "C1sco12345"
        port: 22
        connection_options:
          pyats:
            extras:
              devices:
                iosxr1:
                  os: iosxr
                  connections:
                    default:
                      ip: 131.226.217.150
                      protocol: ssh
                      port: 22
          napalm:
            platform: iosxr
          scrapli:
            platform: cisco_iosxr
            extras:
              auth_strict_key: False
              ssh_config_file: False
          ncclient:
            port: 830
            extras:
              allow_agent: False
              hostkey_verify: False
              device_params:
                name: iosxr
          scrapli_netconf:
            port: 830
            extras:
              ssh_config_file: True
              auth_strict_key: False
              transport_options:
                netconf_force_pty: False

Cisco NXOS
===========

Below inventory can be used with Cisco NXOS based devices and contains parameters for these connection plugins:

- Netmiko - uses SSH and platform ``nxos_ssh`` under base arguments definition
- Ncclient - uses port 830 with platform name ``nexus`` as specified in ``connection_options``
- Scrapli-Netconf - uses port 830 as specified in ``connection_options``
- NAPALM - uses SSH and platform ``nxos_ssh`` as specified in ``connection_options``
- Scrapli - uses SSH and platform ``cisco_nxos`` without verifying SSH keys as specified in ``connection_options``
- PyATS - uses ``nxos`` platform with SSH protocol on port 22 as specified in ``connection_options``

.. code-block:: yaml

    proxy:
      proxytype: nornir
      multiprocessing: True

    hosts:
      sandbox-nxos-1.cisco:
        hostname: sandbox-nxos-1.cisco.com
        platform: nxos_ssh
        username: admin
        password: "Admin_1234!"
        port: 22
        connection_options:
          pyats:
            extras:
              devices:
                sandbox-nxos-1.cisco:
                  os: nxos
                  connections:
                    default:
                      ip: 131.226.217.151
                      protocol: ssh
                      port: 22
          napalm:
            platform: nxos_ssh
          scrapli:
            platform: cisco_nxos
            extras:
              auth_strict_key: False
              ssh_config_file: False
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

Juniper Junos
=============

Below inventory can be used with Juniper Junos based devices (tested with vMX) and contains parameters
for these connection plugins:

- Netmiko - uses SSH and platform ``juniper_junos`` under base arguments definition
- Ncclient - uses port 830 with platform name ``junos`` as specified in ``connection_options.extras.device_params``
- Scrapli-Netconf - uses port 830 platform ``juniper_junos`` as specified in ``connection_options``
- Scrapli - uses SSH and platform ``juniper_junos`` without verifying SSH keys as specified in ``connection_options``
- NAPALM - uses platform ``junos`` as specified in ``connection_options`` with additional Junos driver parameters in ``connection_options.extras.optional_args``

.. code-block:: yaml

    proxy:
      proxytype: nornir

    hosts:
      vmx1:
        hostname: 192.168.217.150
        platform: juniper_junos
        username: nornir
        password: nornir
        connection_options:
          ncclient:
            port: 830
            extras:
              hostkey_verify: false
              device_params:
                name: junos
          scrapli_netconf:
            port: 830
            extras:
              transport: system # or paramiko, ssh2
              ssh_config_file: True
              auth_strict_key: False
          scrapli:
            platform: juniper_junos
            port: 22
            extras:
              transport: system # or asyncssh, ssh2, paramiko
              auth_strict_key: false
              ssh_config_file: false
          napalm:
            platform: junos
            extras:
              optional_args:
                auto_probe: 0
                config_private: False
