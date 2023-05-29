"""
Nornir Netbox Pillar Module
===========================

SaltStack external pillar module to source Salt-Nornir proxy minion
pillar and Nornir inventory data from Netbox.

SaltStack pillar module name - ``salt_nornir_netbox``

Foreword
++++++++

Salt-Nornir Netbox Pillar attempts to be as efficient as possible and
uses Netbox read-only GraphQL API because of that. However, the more data
sourced from Netbox the longer it takes to process it and more memory
it will occupy. Moreover, Netbox infrastructure need to be scaled to match
Salt-Nornir requirements capable of processing appropriate number of
incoming requests.

Be mindful that pillar retrieval happens from Salt-Master only,
retrieved data pushed to proxy minions. Netbox capable of supplying
significant amount of data, Salt-Master resources should be sized
appropriately to process it in a timely fashion.

Salt-Nornir Proxy Minion uses Nornir workers internally, each worker is an
instance of Nornir with its own dedicated inventory. As a result, an
independent copy of pillar data retrieved from Netbox used by each Nornir
worker. This can raise memory utilization concerns and should be kept an eye on.

It is always good to test this pillar to get an understanding of resources 
usage in scaled-out deployments.

.. warning:: Salt-Nornir Netbox Pillar imposes hard timeout of 50 seconds to
  retrieve data from Netbox for each of the methods. This is done due to hard 
  timeout of 60 seconds that SaltStack imposes on pillar data composing by master.

Dependencies
++++++++++++

Salt-Nornir Netbox Pillar module uses Netbox read-only GraphQL API, as
a result GraphQL API need to be enabled for this pillar module to work.
In other words, Netbox configuration ``GRAPHQL_ENABLED`` parameter should
be set to ``True``.

Salt-Nornir Netbox Pillar module uses Netbox REST API for secrets
retrieval, as a result REST API need to be enabled if secrets fetched
from Netbox.

Supported Netbox Versions
+++++++++++++++++++++++++

+---------+------------------+
| Netbox  | Salt-Nornir      |
+=========+==================+
| 3.3     | 0.17, 0.18       |
+---------+------------------+
| 3.4     | 0.19             |
+---------+------------------+

Configuration Parameters
++++++++++++++++++++++++

Sample external pillar Salt Master configuration::

    ext_pillar:
      - salt_nornir_netbox:
          url: 'http://192.168.115.129:8000'
          token: '837494d786ff420c97af9cd76d3e7f1115a913b4'
          ssl_verify: True
          use_minion_id_device: True
          use_minion_id_tag: True
          use_hosts_filters: True
          use_pillar: True
          host_primary_ip: ip4,
          host_add_netbox_data: True
          host_add_interfaces: True
          host_add_interfaces_ip: True
          host_add_interfaces_inventory_items: True
          host_add_connections: True
          data_retrieval_timeout: 120
          data_retrieval_num_workers: 10
          secrets:
            resolve_secrets: True
            fetch_username: True
            fetch_password: True
            secret_device: keymaster
            secret_name_map: 
              password: username
            plugins:
              netbox_secrets:
                private_key: /etc/salt/netbox_secrets_private.key

If ``use_pillar`` is True, salt_nornir_netbox additional configuration can be
defined in proxy minion pillar under ``salt_nornir_netbox_pillar`` key::

    salt_nornir_netbox_pillar:
      url: 'http://192.168.115.129:8000'
      token: '837494d786ff420c97af9cd76d3e7f1115a913b4'
      host_add_interfaces: "nb_interfaces"
      hosts_filters:
        - name__ic: "ceos"
        - location__nic: "south"
          tag: "mytag"
          role: "core"
      secrets:
        resolve_secrets: True
        fetch_username: True
        fetch_password: True
        secret_device: nrp1
        secret_name_map: 
          password: username
        plugins:
          netbox_secrets:
            private_key: /etc/salt/netbox_secrets_private.key

Pillar configuration updates Master's configuration and takes precedence.
Configuration **not** merged recursively, instead, pillar top key values
override Master's configuration.

Base Configuration Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``url`` - example: ``http://192.168.115.129:8000``; Netbox URL value, mandatory to define 
  parameter
* ``token`` - Netbox API Token, mandatory to define parameter
* ``ssl_verify`` - default: ``True``; Configure SSL verification, disabled if set to ``False``   
* ``use_minion_id_device`` - default: ``False``; If True, configuration context data of 
  device with name equal to proxy minion-id merged with proxy minion pillar
* ``use_minion_id_tag`` - default: ``False``; If True, Netbox devices that have tag assigned 
  with value equal to proxy minion-id included into pillar data
* ``use_hosts_filters`` - default: ``False``; If True, devices matched by ``hosts_filters`` 
  processed and included into pillar data, filters processed in sequence, devices matched 
  by at least one filter added into proxy minion pillar. Filters nomenclature available at 
  Netbox `documentation <https://demo.netbox.dev/static/docs/rest-api/filtering/>`_
* ``use_pillar`` - default: ``False``; If True, Master's ext_pillar ``salt_nornir_netbox`` 
  configuration augmented with pillar ``salt_nornir_netbox_pillar`` configuration
* ``host_add_netbox_data`` - default: ``False``, supported values: ``True``, ``False`` or
  string e.g. ``netbox_data``; If True, Netbox device data merged with Nornir host's data, 
  if ``host_add_netbox_data`` is a string, Netbox device data saved into Nornir host's 
  data under key with ``host_add_netbox_data`` value
* ``host_add_interfaces`` - default: ``False``, supported values: ``True``, ``False`` or
  string e.g. ``interfaces``; If True, Netbox device's interfaces data added into Nornir 
  host's data under ``interfaces`` key. If ``host_add_interfaces`` is a string, interfaces 
  data added into Nornir host's data under key with ``host_add_interfaces`` value
* ``host_add_connections`` - default: ``False``, supported values: ``True``, ``False`` or
  string e.g. ``nb_connections``; If True, Netbox device's interface and console connections 
  data added into Nornir host's data under ``conections`` key. If ``host_add_connections``
  is a string, connections data added into Nornir host's data under key with 
  ``host_add_connections`` value
* ``host_primary_ip`` - default: ``None``, supported values: ``ip4``, ``ip6`` or ``None``;
  Control which primary IP to use as host's hostname
* ``hosts_filters`` - default: N/A, example: ``"name__ic": "ceos1"``; List of dictionaries 
  where each dictionary contains filtering parameters to filter Netbox devices, Netbox 
  devices that matched, processed further and included into pillar data
* ``secrets`` - Secrets Configuration Parameters indicating how to retrieve secrets values 
  from Netbox
* ``data_retrieval_timeout`` - default: ``50``; Python concurrent futures ``as_completed`` 
  function timeout to impose hard limit on time to retrieve data from Netbox 
* ``data_retrieval_num_workers`` - default: ``10``; Number of multi-threading workers to run 
  to retrive data from Netbox

Secrets Configuration Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``resolve_secrets`` - default: ``True``; If True, attempts to resolve secrets values 
  defined using URL like strings
* ``fetch_username`` - default: ``True``; If True, attempts to retrieve host's username 
  from Netbox secrets plugins, raises error if fails to do so, removing host from pillar 
  data.
* ``fetch_password`` - default: ``True``; If True, attempts to retrieve host's password 
  from Netbox secrets plugins, raises error if fails to do so, removing host from pillar 
  data.
* ``secret_device`` - default: N/A, example: ``keymaster-1``; Name of netbox device to 
  retrieve secrets from by default
* ``secret_name_map`` - default: N/A, example: ``password: username``; List of dictionaries 
  keyed by secret key names with values of the of the inventory data key name to assign 
  secret name to
* ``plugins`` - Netbox Secrets Plugins Configuration Parameters, supported values: 
  ``netbox_secrets``
   
netbox_secrets Secrets Plugin Configuration Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``private_key`` - default: N/A, example: ``/etc/salt/nb_secrets.key``
  OS Path to file with netbox_secrets RSA Private Key content

Sourcing Data from Netbox
+++++++++++++++++++++++++

``salt_nornir_netbox`` external pillar retrieves data from Netbox using several
methods. **By default none of the methods turned on**. All of the methods can be
used separately or simultaneously, if used simultaneously processing follows
order below.

Pillar data automatically sourced from Netbox on proxy-minion process startup or
restart, to source data on demand use ``nr.nornir refresh`` command::

    salt nrp1 nr.nornir refresh

**Method-1** If ``use_minion_id_device`` is True, configuration context data of
device with name equal to proxy minion id merged into proxy minion pillar.

Sample Netbox device configuration context data that contains Salt-Nornir
proxy minion pillar data::

    proxy:
      proxy_always_alive: true
    hosts:
      fceos6:
        data:
          secrets:
          - bgp: nb://netbox_secrets/keymaster-1/BGP/peers_pass
          - snmp: nb://netbox_secrets/keymaster-1/SNMP/community
          - nb://netbox_secrets/keymaster-1/OSPF/hello_secret
        hostname: 1.2.3.4
        password: nb://netbox_secrets/keymaster-1/SaltNornirCreds/password
        platform: arista_eos
        port: '22'
        username: nb://netbox_secrets/keymaster-1/SaltNornirCreds/username
    nornir:
      actions:
        foobar:
          args:
          - show clock
          description: test action
          function: nr.cli
    nrp3_secret_key: nb://nrp3_key_secret

Above data recursively merged with Salt-Nornir Proxy Minion pillar by SaltStack pillar system.

**Method-2** If ``use_minion_id_tag`` set to True, devices that have tag attached with value set
equal to minion-id retrieved from Netbox and processed to merge their data into
proxy minion pillar Salt-Nornir hosts

**Method-3** If ``use_hosts_filters`` is True, devices queried from Netbox using filters from
``salt_nornir_netbox.hosts_filters`` list and processed to merge their data into proxy
minion pillar Salt-Nornir hosts. If ``use_pillar`` set to True, Proxy Minion
pillar can be used to define filters list under ``salt_nornir_netbox_pillar.hosts_filters``
key

.. warning:: To be able to merge hosts filters in a pillar from multiple sls files make sure to 
    set ``pillar_source_merging_strategy: recurse`` and ``pillar_merge_lists: True`` in master
    configuration file

Netbox Device Processing
++++++++++++++++++++++++

Nornir host's parameters sourced from Netbox device's configuration context
``nornir`` section. Sample device configuration context ``nornir`` section
in YAML format::

    nornir:
      name: lsr21-foc771
      platform: cisco_xr
      hostname: 1.2.3.4
      port: 22
      groups: ["lab", "def_creds"]
      username: admin1234
      password: "nb://netbox_secrets/password"
      connection_options:
        napalm:
          platform: iosxr
        scrapli:
          platform: cisco_iosxr
        puresnmp:
          port: 161
          extras:
            version: v2c
            community: "nb://netbox_secrets/keymaster/snmp/community"
        ncclient:
          username: "nb://netbox_secrets/netconf-creds/username"
          password: "nb://netbox_secrets/netconf-creds/password"
          port: 830
          extras:
            hostkey_verify: False
            device_params:
              name: iosxr
      data:
        inventory_id: FCF483551

Above data processed and included into Salt-Nornir host's inventory
following these rules:

1. Device configuration context ``nornir`` section merged with Nornir host's inventory
2. If ``name`` defined under Netbox device's configuration context ``nornir`` section it
   is used as a Nornir host's inventory name key, otherwise device name used
3. If ``platform`` not defined in Netbox device's configuration context ``nornir`` section,
   platform value set equal to the value of device's platform NAPALM Driver. If Netbox
   device has no platform associated and no platform given in configuration context ``nornir``
   section, warning message logged statring with version 0.19.0 instead of raising KeyError
4. If ``hostname`` parameter not defined in Netbox device's configuration context ``nornir``
   section, ``hostname`` value set equal to device primary IPv4 address if ``host_primary_ip``
   is set to ``ip4`` or not configured at all, if primary IPv4 address is not defined, primary 
   IPv6 address used if ``host_primary_ip`` is set to ``ip6`` or not configured at all, if 
   no primary IPv6 address defined, device name is used as a ``hostname`` in assumption that 
   device name is a valid FQDN
5. If ``host_add_netbox_data`` is a string, Netbox device data saved into Nornir host's data
   using ``host_add_netbox_data`` value as a key. For example, if value of ``host_add_netbox_data``
   is `netbox_data`, Netbox device data saved into Nornir host's data under `netbox_data` key.
   If ``host_add_netbox_data value`` is True, Netbox device data merged with Nornir host's
   data parameters

.. warning:: device is skipped if ``salt_nornir_netbox`` fails to identify its ``platform``

Sample device data sourced from Netbox, ``host_add_netbox_data`` key name equal to
``netbox`` string in this example::

    hosts:
      ceos1:
        data:
          netbox:
            airflow: FRONT_TO_REAR
            asset_tag: UUID-123451
            config_context:
              domain_name: lab.io
              lo0_ip: 1.0.1.4
              secrets:
                bgp: 123456bgppeer
                secret1: secret1_value
                secret2: secret2_value
                secret3: secret3_value
                secret4: secret4_value
              syslog_servers:
              - 10.0.0.3
              - 10.0.0.4
            custom_field_data:
              sr_mpls_sid: 4578
            device_role:
              name: VirtualRouter
            device_type:
              model: FakeNOS Arista cEOS
            last_updated: '2022-10-01T04:43:03.890510+00:00'
            location:
              name: Cage-77
            name: fceos4
            platform:
              name: FakeNOS Arista cEOS
              napalm_driver: arista_eos
            position: '40.0'
            primary_ip4:
              address: 1.0.1.4/32
            primary_ip6:
              address: fb71::32/128
            rack:
              name: R101
            serial: FNS123451
            site:
              name: SALTNORNIR-LAB
            status: ACTIVE
            tags:
            - name: nrp3
            tenant:
              name: SALTNORNIR

Sourcing Secrets from Netbox
++++++++++++++++++++++++++++

salt_nornir_netbox supports `netbox_secrets <https://github.com/Onemind-Services-LLC/netbox-secrets/>`_
secrets plugin. ``netbox_secrets`` should be installed and
configured as a Netbox plugin. RSA private key need to be generated for
the user which token is used to work with Netbox, private key need
to be uploaded to Master and configured in Master's ext_pillar::

    ext_pillar:
      - salt_nornir_netbox:
          token: '837494d786ff420c97af9cd76d3e7f1115a913b4'
          secrets:
            resolve_secrets: True
            fetch_username: True
            fetch_password: True
            secret_device: keymaster
            secret_name_map: 
              password: username
            plugins:
              netbox_secrets:
                private_key: /etc/salt/netbox_secrets_private.key
                
.. note:: netbox_secrets supported starting with Salt-Nornir version 0.19.0

Alternatively, secrets plugins configuration can be defined in Salt-Nornir
Proxy Minion pillar if Master's ext_pillar configuration has ``use_pillar``
set to True.

Any of inventory keys can use value of URL string in one of the formats:

1. ``nb://<secre-plugin-name>/<device-name>/<secret-role>/<secret-name>`` -
   fully qualified path to particular key, can be used to source
   secrets from any devices, secrets plugins or secrets roles
2. ``nb://<secre-plugin-name>/<secret-role>/<secret-name>`` - ``device-name``
   assumed to be equal to the value of ``secrets.secret_device``
   parameter if it is given, otherwise Netbox device name is used as such
3. ``nb://<secre-plugin-name>/<secret-name>`` - same rule applied for
   ``device-name`` as in case 2, but secret searched ignoring ``secret-role``
   and if secret with given name defined under multiple roles, the first
   one returned by Netbox is used as a secret value.
4. ``nb://<secret-name>`` - salt_nornir_netbox attempts to search for
   given ``secret-name``across all plugins and secret roles, uses same
   rule for ``device-name`` as in case 2

.. note:: `secret-role` refers to secret role name, but starting with version 
  0.18.1 `secret-role` can refer to secret role slug as well
    
salt_nornir_netbox recursively iterates over entire data sourced from Netbox
and attempts to resolve keys using specified secrets URLs.

For example, if this is how secrets defined in Netbox:

.. image:: ./_images/netbox_secrets.png

And sample configuration context data of Netbox device with name``fceos4`` is::

    secrets:
      bgp: nb://netbox_secrets/keymaster-1/BGP/peers_pass
      secret1: nb://netbox_secrets/fceos4/SaltSecrets/secret1
      secret2: nb://netbox_secrets/SaltSecrets/secret2
      secret3: nb://netbox_secrets/secret3
      secret4: nb://secret4

Above secrets would be resolved to this::

    secrets:
      bgp: 123456bgppeer        <--- resolves to key id 187
      secret1: secret1_value    <--- resolves to key id 178
      secret2: secret2_value    <--- resolves to key id 179
      secret3: secret3_value    <--- resolves to key id 180
      secret4: secret4_value    <--- resolves to key id 181

salt_nornir_netbox iterates over all key's values and resolves
them accordingly.

Starting with version ``0.17.0`` ``secret_name_map`` dictionary parameter
added to allow the use of secret name values in Nornir inventory, mapping
secret names to keys as specified by ``secret_name_map`` dictionary.

For example, given this secrets:

.. image:: ./_images/netbox_secrets_with_usernames.png

With this master's pillar secrets configuration::

    ext_pillar:
      - salt_nornir_netbox:
          token: '837494d786ff420c97af9cd76d3e7f1115a913b4'
          secrets:
            secret_name_map:
              password: username
              bgp_peer_secret: peer_ip
            plugins:
              netbox_secrets:
                private_key: /etc/salt/netbox_secrets_private.key

This Nornir inventory data for ``fceos`` devices::

    hosts:
      fceos6:
        password: "nb://netbox_secrets/Credentials/admin_user"
      fceos7:
        data:
          bgp:
            peers:
              - bgp_peer_secret: "nb://netbox_secrets/BGP_PEERS/10.0.1.1"
              - bgp_peer_secret: "nb://netbox_secrets/BGP_PEERS/10.0.1.2"
              - bgp_peer_secret: "nb://netbox_secrets/BGP_PEERS/10.0.1.3"

Would be resolved to this final Nornir Inventory data::

    hosts:
      fceos6:
        password: Nornir123
        username: admin_user
      fceos7:
        data:
          bgp:
            peers:
              - bgp_peer_secret: BGPSecret1
                peer_ip: 10.0.1.1
              - bgp_peer_secret: BGPSecret2
                peer_ip: 10.0.1.2
              - bgp_peer_secret: BGPSecret3
                peer_ip: 10.0.1.3

In example above, for ``fceos6`` username and password values are encoded in
same secret entry, this mapping::

    secrets:
      secret_name_map:
        password: username

Tells Salt-Nornir Netbox Pillar to assign ``password``'s secret name value
to ``username`` key in Nornir inventory at the same level.

For ``fceos7``, this configuration::

    secrets:
      secret_name_map:
        bgp_peer_secret: peer_ip

Tells Salt-Nornir Netbox Pillar to assign ``bgp_peer_secret``'s secret name
value to ``peer_ip`` key in Nornir inventory at the same level.

That approach allows to simplify secrets management making it easier to map
secrets to other entities in Nornir inventory.

Sourcing Interfaces and IP addresses data
+++++++++++++++++++++++++++++++++++++++++

Salt-Nornir Netbox Pillar can source device's interface data from Netbox if
``host_add_interfaces`` parameter given. Interfaces added to device's data
under key with the name equal to ``host_add_interfaces`` parameter value, by
default it is set to ``interfaces``.

Interfaces combined into a dictionary keyed by device interface names.

Sample device interfaces data retrieved from Netbox::

    hosts:
      ceos1:
        data:
          interfaces:
            Port-Channel1:
              bridge: null
              bridge_interfaces: []
              child_interfaces: []
              custom_fields: {}
              description: Main uplink interface
              enabled: true
              ip_addresses: []
              last_updated: '2022-09-19T18:47:28.425655+00:00'
              mac_address: null
              member_interfaces:
              - name: eth101
              - name: eth102
              mode: null
              mtu: null
              parent: null
              tagged_vlans: []
              tags: []
              untagged_vlan: null
              vrf: null
              wwn: null
            eth1:
              bridge: null
              bridge_interfaces: []
              child_interfaces:
              - name: eth1.11
              custom_fields: {}
              description: Interface 1 description
              enabled: true
              ip_addresses: []
              last_updated: '2022-09-19T18:47:29.519124+00:00'
              mac_address: null
              member_interfaces: []
              mode: TAGGED
              mtu: 1500
              parent: null
              tagged_vlans: []
              tags: []
              untagged_vlan: null
              vrf: null
              wwn: null
            eth1.11:
              bridge: null
              bridge_interfaces: []
              child_interfaces: []
              custom_fields: {}
              description: Sub-Interface 1 description
              enabled: true
              last_updated: '2022-09-19T18:47:38.603688+00:00'
              mac_address: null
              member_interfaces: []
              mode: TAGGED
              mtu: 1500
              parent:
                name: eth1
              tagged_vlans: []
              tags: []
              untagged_vlan: null
              vrf:
                name: CUST1-Flinch34
              wwn: null
            eth201:
              bridge: null
              bridge_interfaces: []
              child_interfaces: []
              custom_fields: {}
              description: ''
              enabled: true
              ip_addresses: []
              last_updated: '2022-09-19T18:47:29.284530+00:00'
              mac_address: null
              member_interfaces: []
              mode: TAGGED
              mtu: null
              parent: null
              tagged_vlans:
              - name: VLAN_2
                vid: 102
              - name: VLAN_3
                vid: 103
              - name: VLAN_4
                vid: 104
              - name: VLAN_5
                vid: 105
              tags: []
              untagged_vlan:
                name: VLAN_1
                vid: 101
              vrf: null
              wwn: null

If ``host_add_interfaces_ip`` parameter set to True, interface IP addresses
retrieved from Netbox as well.

If ``host_add_interfaces_inventory_items`` parameter set to True, interface
inventory items retrieved from Netbox too.

Interface IP addresses combined into a list and added under ``ip_addresses``
key in interface data::

    hosts:
      ceos1:
        data:
          interfaces:
            eth1.11:
              ip_addresses:
                - address: 1.0.1.4/32
                  custom_fields: {}
                  description: ''
                  dns_name: ''
                  last_updated: '2022-09-19T18:47:36.818058+00:00'
                  role: null
                  status: ACTIVE
                  tags: []
                  tenant: null
                - address: fb71::32/128
                  custom_fields: {}
                  description: ''
                  dns_name: ''
                  last_updated: '2022-10-01T04:43:03.873277+00:00'
                  role: LOOPBACK
                  status: ACTIVE
                  tags: []
                  tenant: null
              inventory_items:
                - asset_tag: null
                  custom_fields: {}
                  description: ''
                  label: ''
                  manufacturer:
                    name: Cisco
                  name: SFP-1G-T
                  part_id: ''
                  role:
                    name: Transceiver
                  serial: ''
                  tags: []

Sourcing Connections Data
+++++++++++++++++++++++++

If parameter ``host_add_connections`` given, Salt-Nornir Netbox pillar
can fetch device interfaces connection details from Netbox and add them to
device's data under key equal to ``host_add_connections`` parameter value, by
default it is set to ``connections``.

Connections retrieved for device interfaces and console ports and combined
into a dictionary keyed by device interface names.

Sample device connections data retrieved from Netbox::

  hosts:
    fceos4:
      connection_options: {}
      data:
        connections:
          ConsolePort1:
            breakout: false
            cable:
              custom_fields: {}
              label: ''
              last_updated: '2022-12-30T06:21:48.819037+00:00'
              length: null
              length_unit: null
              status: CONNECTED
              tags: []
              tenant:
                name: SALTNORNIR
              type: CAT6A
            reachable: true
            remote_device: fceos5
            remote_interface: ConsoleServerPort1
            remote_termination_type: consoleserverport
            termination_type: consoleport
          PowerOutlet-1:
            breakout: false
            cable:
              custom_fields: {}
              label: ''
              last_updated: '2022-12-30T06:21:49.048937+00:00'
              length: null
              length_unit: null
              status: CONNECTED
              tags: []
              tenant:
                name: SALTNORNIR
              type: POWER
            reachable: true
            remote_device: fceos5
            remote_interface: PowerPort-1
            remote_termination_type: powerport
            termination_type: poweroutlet
          eth1:
            breakout: true
            cable:
              custom_fields: {}
              label: ''
              last_updated: '2022-12-30T06:21:47.258167+00:00'
              length: null
              length_unit: null
              status: CONNECTED
              tags: []
              tenant:
                name: SALTNORNIR
              type: CAT6A
            reachable: true
            remote_device: fceos5
            remote_interface:
            - eth1
            - eth10
            remote_termination_type: interface
            termination_type: interface
          eth101:
            cable:
              custom_fields: {}
              label: ''
              last_updated: '2022-12-30T06:21:52.925936+00:00'
              length: null
              length_unit: null
              status: CONNECTED
              tags: []
              tenant: null
              type: SMF
            circuit:
              cid: CID1
              commit_rate: null
              custom_fields: {}
              description: ''
              provider:
                name: Provider1
              status: ACTIVE
              tags: []
            reachable: true
            remote_termination_type: circuittermination
            termination_type: interface

Reference
+++++++++

.. autofunction:: salt_nornir.pillar.salt_nornir_netbox.ext_pillar
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._process_device
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._resolve_secrets
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._resolve_secret
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._fetch_device_secrets
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._host_add_interfaces
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._host_add_connections
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._netbox_secrets_get_session_key
"""
import logging
import requests
import json
from threading import RLock
from concurrent.futures import as_completed, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from salt_nornir.netbox_utils import nb_graphql, get_interfaces, get_connections

log = logging.getLogger(__name__)

__virtualname__ = "salt_nornir_netbox"

RUNTIME_VARS = {"devices_done": set(), "secrets": {}}
RUNTIME_VARS_LOCK = RLock()


def __virtual__():
    return __virtualname__


def _netbox_secrets_get_session_key(params, device_name):
    """
    Function to retrieve netbox_secrets session key
    """
    # if salt_jobs_results provided, extract Netbox params from it
    if params.get("ssl_verify") == False:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    with RUNTIME_VARS_LOCK:
        if "nb_secretstore_session_key" not in RUNTIME_VARS:
            url = f"{params['url']}/api/plugins/secrets/get-session-key/"
            token = "Token " + params["token"]
            # read private key content from file
            key_file = params["secrets"]["plugins"]["netbox_secrets"]["private_key"]
            with open(key_file, encoding="utf-8") as kf:
                private_key = kf.read().strip()
            # send request to netbox
            req = requests.post(
                url,
                headers={"authorization": token},
                json={
                    "private_key": private_key,
                    "preserve_key": True,
                },
                verify=params.get("ssl_verify", True),
            )
            if req.status_code == 200:
                RUNTIME_VARS["nb_secrets_session_key"] = req.json()["session_key"]
                log.debug(
                    f"salt_nornir_netbox fetched and saved netbox-secrets session "
                    f"key in RUNTIME_VARS while processing '{device_name}'"
                )
            else:
                raise RuntimeError(
                    f"salt_nornir_netbox failed to get netbox_secrets session-key, "
                    f"status-code '{req.status_code}', reason '{req.reason}', response "
                    f"content '{req.text}'"
                )

    log.debug(
        f"salt_nornir_netbox retrieved netbox-secrets session key "
        f"for '{device_name}' processing"
    )

    return RUNTIME_VARS["nb_secrets_session_key"]


def _fetch_device_secrets(device_name, params):
    """
    Function to retrieve all secret values for given device from all
    configured Netbox secret plugins, cache it RUNTIME_VARS and return
    secrets dictionary.

    :param device_name: string, name of device to retrieve secrets for
    :param params: dictionary with salt_nornir_netbox parameters
    """
    # if salt_jobs_results provided, extract Netbox params from it
    if params.get("ssl_verify") == False:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    # check if secret plugins configured
    if not params.get("secrets", {}).get("plugins"):
        raise RuntimeError(
            f"Failed to retrieve '{device_name}' device secrets - "
            f"no secrets plugins configured."
        )
    # retrieve device secrets
    for plugin_name in params["secrets"]["plugins"].keys():
        if RUNTIME_VARS["secrets"].get(device_name, {}).get(plugin_name):
            return RUNTIME_VARS["secrets"][device_name]
        elif plugin_name == "netbox_secrets":
            url = f"{params['url']}/api/plugins/secrets/secrets/"
            token = "Token " + params["token"]
            session_key = _netbox_secrets_get_session_key(params, device_name)
            # fetch device id using Netbox GraphQL API
            nb_device = nb_graphql(
                field="device_list",
                filters={"name": device_name},
                fields=["id"],
                params=params,
            )
            # retrieve all device secrets
            req = requests.get(
                url,
                headers={
                    "X-Session-Key": session_key,
                    "authorization": token,
                },
                params={
                    "assigned_object_type": "dcim.device",
                    "assigned_object_id": nb_device[0]["id"],
                },
                verify=params.get("ssl_verify", True),
            )
            if req.status_code == 200:
                with RUNTIME_VARS_LOCK:
                    RUNTIME_VARS["secrets"].setdefault(device_name, {})
                    RUNTIME_VARS["secrets"][device_name][plugin_name] = [
                        {
                            "role": i["role"]["name"],
                            "role_slug": i["role"]["slug"],
                            "name": i["name"],
                            "value": i["plaintext"],
                        }
                        for i in req.json()["results"]
                    ]
            else:
                raise RuntimeError(
                    f"salt_nornir_netbox failed to retrieve '{device_name}' device secrets "
                    f"from '{req.url}', status-code '{req.status_code}', reason '{req.reason}', "
                    f"response content '{req.text}'"
                )

    log.debug(f"salt_nornir_netbox retrieved '{device_name}' device secrets")

    return RUNTIME_VARS["secrets"][device_name]


def _resolve_secret(device_name, secret_path, params, strict=False):
    """
    Function to retrieve netbox_secrets secret value at secret_path.

    :param device_name: string, name of device to retrieve secret for
    :param secret_path: string, path to the secret in one of the supported formats
    :param params: dictionary with salt_nornir_netbox parameters
    :param strict: bool, if True raise KeyError if no secret found, return None otherwise
    :return: secret value and secret name or (None, None) if fail to resolve

    Supported secret key path formats:

    - ``nb://<plugin-name>/<device-name>/<secret-role>/<secret-name>``
    - ``nb://<plugin-name>/<secret-role>/<secret-name>``
    - ``nb://<plugin-name>/<secret-name>``
    - ``nb://<secret-name>``
    """
    # retrieve secret plugin, device, role and name from secret_path
    path_items = [i.strip() for i in secret_path.split("/") if i.strip()]
    # 'nb:', '<plugin-name>', '<device-name>', '<secret-role>', '<secret-name>'
    secret_plugin, secret_device, secret_role, secret_name = None, None, None, None
    # handle nb://<plugin-name>/<device-name>/<secret-role>/<secret-name> case
    if len(path_items) == 5:
        secret_plugin = path_items[1]
        secret_device = path_items[2]
        secret_role = path_items[3]
        secret_name = path_items[4]
    # handle nb://<plugin-name>/<secret-role>/<secret-name> case
    elif len(path_items) == 4:
        secret_plugin = path_items[1]
        secret_role = path_items[2]
        secret_name = path_items[3]
    # handle nb://<plugin-name>/<secret-name> case
    elif len(path_items) == 3:
        secret_plugin = path_items[1]
        secret_name = path_items[2]
    # handle nb://<secret-name> case
    elif len(path_items) == 2:
        secret_name = path_items[1]
    # get all secrets dictionary for given secret device
    secret_device_name = (
        secret_device or params["secrets"].get("secret_device") or device_name
    )
    device_secrets = _fetch_device_secrets(secret_device_name, params)
    # find secret
    for plugin_name, secrets in device_secrets.items():
        if secret_plugin and plugin_name != secret_plugin:
            continue
        for secret in secrets:
            # check secret role if its given
            if secret_role and (
                secret_role != secret["role"]
                and secret_role  # check role name
                != secret["role_slug"]  # check role slug
            ):
                continue
            if secret_name == secret["name"]:
                log.debug(
                    f"salt_nornir_netbox fetched secret '{secret_path}' for '{device_name}', "
                    f"secret_device '{secret_device_name}', secrets plugin '{plugin_name}'"
                )
                return secret["value"], secret_name
    else:
        message = (
            f"salt_nornir_netbox failed to fetch '{secret_path}' secret for "
            f"'{device_name}' device using '{secret_device_name}' as a secret_device "
            f"in any of Netbox secrets plugins data"
        )
        if strict:
            raise KeyError(message)
        else:
            log.debug(message)
        return None, None


def _secret_name_map(key: str, params: dict, data: dict, secret_name: str):
    """
    Helper function to add secret name in host's inventory.

    :param key: name of the key to map secret name for
    :param params: netbox secrets plugins configuration parameters
    :param data: host inventory data
    :param secret_name: name of the secret retrieved from netbox
    """
    if key in params["secrets"].get("secret_name_map", {}):
        secret_name_map_key = params["secrets"]["secret_name_map"][key]
        data[secret_name_map_key] = secret_name


def _resolve_secrets(data, device_name, params):
    """
    Recursive function to iterate over data dictionary and resolve secrets using
    Netbox secret plugins, retrieving secrets for given device by device_name.
    Designed so to add capability to process data for one device, while retrieving
    keys from other device to simplify secrets management on Netbox side - all keys
    can be recorded under single, master device, instead of individual devices.

    :param device_name: string, name of device to retrieve secret for
    :param data: dictionary, containing key with values to be resolved
    :param params: salt_nornir_netbox configuration parameters
    """
    if isinstance(data, dict):
        # run against list of keys, as we may add new
        # keys to data using secret_name_map dictionary
        for k in list(data.keys()):
            # resolve key if its value is "nb://.." like string
            if isinstance(data[k], str) and data[k].startswith("nb://"):
                secret_value, secret_name = _resolve_secret(
                    device_name, data[k], params
                )
                _secret_name_map(k, params, data, secret_name)
                data[k] = secret_value
            # run recursion otherwise
            else:
                data[k] = _resolve_secrets(data[k], device_name, params)
    elif isinstance(data, list):
        for index, i in enumerate(data):
            # resolve list item if its an "nb://.." like string
            if isinstance(i, str) and i.startswith("nb://"):
                secret_value, secret_name = _resolve_secret(device_name, i, params)
                data[index] = secret_value
            # run recursion otherwise
            else:
                data[index] = _resolve_secrets(i, device_name, params)
    return data


def _host_add_interfaces(device, host, params):
    """
    Function to retrieve interface and ip addresses data and add it
    into Nornir host's inventory.

    :param device: device data dictionary
    :param host: Nornir host inventory dictionary
    :param params: dictionary with salt_nornir_netbox parameters
    """
    host_add_interfaces = params["host_add_interfaces"]

    interfaces = get_interfaces(
        hosts=[device["name"]],
        params=params,
        add_ip=params.get("host_add_interfaces_ip", False),
        add_inventory_items=params.get("host_add_interfaces_inventory_items", False),
        cache=False,
    )

    # save data into Nornir host's inventory
    dk = host_add_interfaces if isinstance(host_add_interfaces, str) else "interfaces"
    host.setdefault("data", {})
    host["data"][dk] = interfaces[device["name"]]


def _host_add_connections(device, host, params):
    """
    Function to add interfaces and console ports connections details
    to Nornir host data.

    :param device: device data dictionary
    :param host: Nornir host inventory dictionary
    :param params: dictionary with salt_nornir_netbox parameters
    """
    host_add_connections = params["host_add_connections"]

    cables = get_connections(hosts=[device["name"]], params=params, cache=False)

    # save data into Nornir host's inventory
    dk = (
        host_add_connections if isinstance(host_add_connections, str) else "connections"
    )
    host.setdefault("data", {})
    host["data"][dk] = cables[device["name"]]


def _process_device(device, inventory, params):
    """
    Helper function to extract data to form Nornir host entry out
    of Netbox device entry.

    :param device: Netbox device data dictionary
    :param inventory: Nornir inventory dictionary to update with host details
    :param params: salt_nornir_netbox configuration parameters dictionary
    """
    # check if device have not been done already
    device["custom_field_data"] = json.loads(device["custom_field_data"])
    nornir_data = device["config_context"].pop("nornir", {})
    name = nornir_data.get("name", device["name"])
    if name in RUNTIME_VARS["devices_done"]:
        return
    host_add_netbox_data = params.get("host_add_netbox_data", False)
    host_add_interfaces = params.get("host_add_interfaces", False)
    host_add_connections = params.get("host_add_connections", False)
    host_primary_ip = params.get("host_primary_ip", None)
    resolve_secrets = params.get("secrets", {}).get("resolve_secrets", False)
    fetch_username = params.get("secrets", {}).get("fetch_username", False)
    fetch_password = params.get("secrets", {}).get("fetch_password", False)
    # form Nornir host inventory dictionary
    host = inventory["hosts"].pop(name, {})
    host.update(nornir_data)
    # add platform if not provided in device config context
    if not host.get("platform"):
        if device["platform"]:
            host["platform"] = device["platform"]["napalm_driver"]
        else:
            log.warning(f"salt_nornir_netbox no platform found for '{name}' device")
    # add hostname if not provided in config context
    if not host.get("hostname"):
        if device["primary_ip4"] and host_primary_ip in ["ip4", None]:
            host["hostname"] = device["primary_ip4"]["address"].split("/")[0]
        elif device["primary_ip6"] and host_primary_ip in ["ip6", None]:
            host["hostname"] = device["primary_ip6"]["address"].split("/")[0]
        else:
            host["hostname"] = name
    # save device data under host data
    if host_add_netbox_data:
        # transform tags dictionaries to lists
        device["tags"] = [t["name"] for t in device["tags"]]
        device["site"]["tags"] = [t["name"] for t in device["site"]["tags"]]
        if isinstance(host_add_netbox_data, str) and host_add_netbox_data.strip():
            host.setdefault("data", {})
            host["data"].setdefault(host_add_netbox_data, {})
            host["data"][host_add_netbox_data].update(device)
        elif host_add_netbox_data is True:
            host.setdefault("data", {})
            host["data"].update(device)
    # retrieve interfaces data
    if host_add_interfaces:
        _host_add_interfaces(device, host, params)
    # retrieve device connections
    if host_add_connections:
        _host_add_connections(device, host, params)
    # retrieve device secrets
    if fetch_username and host.get("username", "nb://username").startswith("nb://"):
        host["username"], secret_name = _resolve_secret(
            name, host.get("username", "nb://username"), params, strict=True
        )
        _secret_name_map("username", params, host, secret_name)
    if fetch_password and host.get("password", "nb://password").startswith("nb://"):
        host["password"], secret_name = _resolve_secret(
            name, host.get("password", "nb://password"), params, strict=True
        )
        _secret_name_map("password", params, host, secret_name)
    if resolve_secrets:
        _resolve_secrets(host, name, params)
    # save host to Nornir inventory
    inventory["hosts"][name] = host
    # add device as processed
    with RUNTIME_VARS_LOCK:
        RUNTIME_VARS["devices_done"].add(name)


def _process_devices_in_threads(num_workers, timeout, devices, inventory, params):
    """
    Helper function to run threads to retrieve data from Netbox

    :param device: device dictionary
    :param inventory: Nornir inventory dictionary to update with host details
    :param params: salt_nornir_netbox configuration parameters dictionary
    """
    devices_done = []
    futures = []
    with ThreadPoolExecutor(num_workers) as pool:
        # start threads
        futures = {
            pool.submit(_process_device, device, inventory, params): device["name"]
            for device in devices
        }
        # wait for threads to complete its work
        try:
            for future in as_completed(futures, timeout=timeout):
                device_name = futures[future]
                devices_done.append(device_name)
                # check if experienced an error, log it accordingly
                if future.exception():
                    try:
                        raise future.exception()
                    except Exception as e:
                        log.exception(
                            f"salt_nornir_netbox ThreadPoolExecutor error "
                            f"processing device '{device_name}': {e}"
                        )
                else:
                    log.info(
                        f"salt_nornir_netbox ThreadPoolExecutor finished "
                        f"processing device '{device_name}'"
                    )
        except FuturesTimeoutError:
            devices_not_done = ", ".join(
                [
                    device_name
                    for device_name in futures.values()
                    if device_name not in devices_done
                ]
            )
            raise TimeoutError(
                f"salt_nornir_netbox ThreadPoolExecutor {timeout}s timeout expired, "
                f"devices not completed - {devices_not_done}"
            )


def ext_pillar(minion_id, pillar, *args, **kwargs):
    """
    Salt Nornir Netbox External Pillar

    :param minion_id: proxy minion id
    :param pillar: proxy minion pillar data
    :param args: list of any additional argument
    :param kwargs: dictionary of any additional argument

    External pillar automatically called on proxy minion startup, to refresh pillar
    data on demand call command on Salt-Master::

        salt nrp1 nr.nornir refresh
    """
    try:
        ret = {}

        # check proxy minion pillar type is "nornir", skip otherwise
        if not pillar.get("proxy", {}).get("proxytype") == "nornir":
            return ret

        # check if need to merge kwargs with proxy minion pillar
        if kwargs.get("use_pillar", False):
            params = {**kwargs, **pillar.get("salt_nornir_netbox_pillar", {})}
        else:
            params = kwargs

        use_minion_id_device = params.get("use_minion_id_device", False)
        use_minion_id_tag = params.get("use_minion_id_tag", False)
        use_hosts_filters = params.get("use_hosts_filters", False)
        data_retrieval_num_workers = params.get("data_retrieval_num_workers", 10)
        data_retrieval_timeout = params.get("data_retrieval_timeout", 10)

        device_fields = [
            "name",
            "last_updated",
            "custom_field_data",
            "tags {name}",
            "device_type {model}",
            "device_role {name}",
            "config_context",
            "tenant {name}",
            "platform {name napalm_driver}",
            "serial",
            "asset_tag",
            "site {name tags{name}}",
            "location {name}",
            "rack {name}",
            "status",
            "primary_ip4 {address}",
            "primary_ip6 {address}",
            "airflow",
            "position",
        ]

        try:
            # request dummy device to verify that Netbox GraphQL API is reachable
            _ = nb_graphql(
                field="device_list",
                filters={"name": "__dummy__"},
                fields=["id"],
                params=params,
                raise_for_status=True,
            )
        except Exception as e:
            log.exception(
                f"salt_nornir_netbox failed to query GarphQL API, Netbox URL "
                f"'{params['url']}', token ends with '..{params['token'][-6:]}'"
            )
            return ret

        # source proxy minion pillar from config context
        if use_minion_id_device is True:
            minion_nb = nb_graphql(
                field="device_list",
                filters={"name": minion_id},
                fields=["config_context"],
                params=params,
            )
            if not minion_nb:
                log.warning(
                    f"salt_nornir_netbox no device with name "
                    f"'{minion_id}' found in netbox"
                )
            else:
                ret.update(dict(minion_nb[0]["config_context"]))
                try:
                    _resolve_secrets(ret, minion_id, params)
                except Exception as e:
                    log.exception(
                        f"salt_nornir_netbox error while resolving secrets for "
                        f"'{minion_id}' config context data: {e}"
                    )
                # retrieve all hosts details
                host_names = list(ret.get("hosts", {}))
                devices_by_minion_id = nb_graphql(
                    field="device_list",
                    filters={"name": host_names},
                    fields=device_fields,
                    params=params,
                )
                # process hosts
                try:
                    _process_devices_in_threads(
                        num_workers=data_retrieval_num_workers,
                        timeout=data_retrieval_timeout,
                        devices=devices_by_minion_id,
                        inventory=ret,
                        params=params,
                    )
                except Exception as e:
                    log.exception(
                        f"salt_nornir_netbox error while processing device '{host_name}' "
                        f"from '{minion_id}' config context data: {e}"
                    )

        # source devices list using tag value equal to minion id
        if use_minion_id_tag is True:
            ret.setdefault("hosts", {})
            devices_by_tag = nb_graphql(
                field="device_list",
                filters={"tag": minion_id},
                fields=device_fields,
                params=params,
            )
            try:
                _process_devices_in_threads(
                    num_workers=data_retrieval_num_workers,
                    timeout=data_retrieval_timeout,
                    devices=devices_by_tag,
                    inventory=ret,
                    params=params,
                )
            except Exception as e:
                log.exception(
                    f"salt_nornir_netbox error while retrieving devices by "
                    f"tag '{minion_id}': {e}"
                )

        # retrieve devices using hosts filters
        if use_hosts_filters and params.get("hosts_filters"):
            ret.setdefault("hosts", {})
            # form queries dictionary out of filters
            queries = {
                f"devices_by_filter_{index}": {
                    "field": "device_list",
                    "filters": filter_item,
                    "fields": device_fields,
                }
                for index, filter_item in enumerate(params["hosts_filters"])
            }
            # send queries
            devices_query_result = nb_graphql(queries=queries, params=params)
            # unpack devices into a list
            devices_by_filter, devices_added = [], set()
            for devices in devices_query_result.values():
                for device in devices:
                    if device["name"] not in devices_added:
                        devices_by_filter.append(device)
                        devices_added.add(device["name"])
            log.debug(
                f"salt_nornir_netbox retrieved devices by host filters for "
                f"'{minion_id}': '{', '.join(devices_added)}', processing"
            )
            # process devices
            try:
                _process_devices_in_threads(
                    num_workers=data_retrieval_num_workers,
                    timeout=data_retrieval_timeout,
                    devices=devices_by_filter,
                    inventory=ret,
                    params=params,
                )
            except Exception as e:
                log.exception(
                    f"salt_nornir_netbox '{minion_id}' error while retrieving devices "
                    f"by hosts filter: {e}"
                )

        return ret
    except Exception as e:
        log.exception(f"salt_nornir_netbox '{minion_id}' error: {e}")
        return {}
