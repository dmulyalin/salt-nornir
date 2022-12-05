"""
Nornir Netbox Pillar Module
===========================

SaltStack external pillar module to source Salt-Nornir proxy minion
pillar and Nornir inventory data from Netbox.

SaltStack pillar module name - ``salt_nornir_netbox``

Foreword
++++++++

Salt-Nornir Netbox Pillar strives to be as efficient as possible and
uses Netbox read-only GraphQL API because of that. However, the more data
sourced from Netbox the longer it takes to process it and more memory
it will occupy. Moreover, Netbox infrastructure need to be scaled to match
Salt-Nornir requirements capable of processing appropriate number of
incoming requests.

Keep in mind that pillar retrieval happens from Salt-Master only, with
retrieved data pushed to proxy minions for their use. Given Netbox can
supply significant amount of data, Salt-Master resources should be sized
appropriately to process it in a timely fashion.

Salt-Nornir Proxy uses Nornir workers internally, each worker is an
instance of Nornir with its own dedicated inventory. As a result, an
independent copy of pillar data retrieved from Netbox used by each Nornir
worker. This can raise memory utilization concerns and should be kept an eye on.

It is always good to test this pillar functionality to get an understanding
of how much resources required before using it in scaled-out deployments.

Dependencies
++++++++++++

Salt-Nornir Netbox Pillar module uses Netbox read-only GraphQL API, as
a result GraphQL API need to be enabled for this pillar module to work.
In other words, Netbox configuration ``GRAPHQL_ENABLED`` parameter should
be set to ``True``.

Salt-Nornir Netbox Pillar module uses Netbox REST API for secrets
retrieval, as a result REST API need to be enabled if secrets fetched
from Netbox.

Configuration Parameters
++++++++++++++++++++++++

Sample external pillar Salt Master configuration::

    ext_pillar:
      - salt_nornir_netbox:
          url: 'http://192.168.115.129:8000'
          token: '837494d786ff420c97af9cd76d3e7f1115a913b4'
          use_minion_id_device: True
          use_minion_id_tag: True
          use_hosts_filters: True
          use_pillar: True
          host_add_netbox_data: True
          host_add_interfaces: True
          host_add_interfaces_ip: True
          host_add_interfaces_inventory_items: True
          host_add_connections: True
          secrets:
            resolve_secrets: True
            fetch_username: True
            fetch_password: True
            secret_device: keymaster
            secret_name_map: username
            plugins:
              netbox_secretstore:
                url_override: netbox_secretstore
                private_key: /etc/salt/netbox_secretstore_private.key


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
        secret_name_map: username
        plugins:
          netbox_secretstore:
            url_override: netbox_secretstore
            private_key: /etc/salt/netbox_secretstore_private.key

Pillar configuration updates Master's configuration and takes precedence.
Configuration **not** merged recursively, instead, pillar top key values
override Master's configuration.

.. warning:: Salt-Nornir Netbox pillar module strives to optimize interaction with
    Netbox improving efficiency of data retrieval. However, the more data fetched
    from Netbox the longer it takes to process it.

.. list-table:: Configuration Parameters
   :widths: 10 10 20 60
   :header-rows: 1

   * - Name
     - Default
     - Example
     - Description
   * - ``url``
     - N/A
     - 'http://192.168.115.129:8000'
     - Netbox URL
   * - ``token``
     - N/A
     - N/A
     - Netbox API Token
   * - ``use_minion_id_device``
     - False
     - True or False
     - | If True, configuration context data of device with name
       | equal to proxy minion-id merged with proxy minion pillar
   * - ``use_minion_id_tag``
     - False
     - True or False
     - | If True, Netbox devices that have tag assigned with value equal
       | to proxy minion-id included into pillar data
   * - ``use_hosts_filters``
     - False
     - True or False
     - | If True, devices matched by ``hosts_filters`` processed
       | and included into pillar data
   * - ``use_pillar``
     - False
     - True or False
     - | If True, Master's ext_pillar ``salt_nornir_netbox`` configuration
       | augmented with pillar ``salt_nornir_netbox_pillar`` configuration
   * - ``host_add_netbox_data``
     - False
     - | True, False or
       | String e.g. ``netbox_data``
     - | If True, Netbox device data merged with Nornir host's data, if
       | ``host_add_netbox_data`` is a string, Netbox device data saved into
       | Nornir host's data under key with ``host_add_netbox_data`` value
   * - ``host_add_interfaces``
     - False
     - | True, False or
       | String e.g. ``interfaces``
     - | If True, Netbox device's interfaces data added into Nornir host's data
       | under ``interfaces`` key. If ``host_add_interfaces`` is a string,
       | interfaces data added into Nornir host's data under key with
       | ``host_add_interfaces`` value
   * - ``host_add_connections``
     - False
     - | True, False or
       | String e.g. ``nb_connections``
     - | If True, Netbox device's interface and console connections data added
       | into Nornir host's data under ``conections`` key. If ``host_add_connections``
       | is a string, connections data added into Nornir host's data under key with
       | ``host_add_connections`` value
   * - ``hosts_filters``
     - None
     - "name__ic": "ceos1"
     - | List of dictionaries where each dictionary contains filtering
       | parameters to filter Netbox devices, Netbox devices that
       | matched, processed further and included into pillar data
   * - ``secrets``
     - N/A
     - N/A
     - | Secrets Configuration Parameters indicating how to retrieve
       | secrets values from Netbox

``url`` and ``token`` are mandatory parameters. ``salt_nornir_netbox.hosts_filters``
nomenclature available at Netbox
`documentation <https://demo.netbox.dev/static/docs/rest-api/filtering/>`_.
Filters processed in sequence, devices matched by at least one filter added into
proxy minion pillar.

.. list-table:: Secrets Configuration Parameters
   :widths: 10 10 20 60
   :header-rows: 1

   * - Name
     - Default
     - Example
     - Description
   * - ``resolve_secrets``
     - True
     - True or False
     - | If True, attempts to resolve secrets values defined using
       | URL like strings
   * - ``fetch_username``
     - True
     - True or False
     - | If True, attempts to retrieve host's username from Netbox
       | secrets plugins, raises error if fails to do so, removing
       | host from pillar data.
   * - ``fetch_password``
     - True
     - True or False
     - | If True, attempts to retrieve host's password from Netbox
       | secrets plugins, raises error if fails to do so, removing
       | host from pillar data.
   * - ``secret_device``
     - N/A
     - keymaster
     - Name of netbox device to retrieve secrets from by default
   * - ``secret_name_map``
     - N/A
     - username
     - Name of the inventory data key to assign secret name to
   * - ``plugins``
     - N/A
     - N/A
     - Netbox Secrets Plugins Configuration Parameters

.. list-table:: netbox_secretstore Secrets Plugin Configuration Parameters
   :widths: 10 10 20 60
   :header-rows: 1

   * - Parameter
     - Default
     - Example
     - Description
   * - ``private_key``
     - N/A
     - "/etc/salt/nb_secretstore.key"
     - OS Path to file with netbox_secretstore RSA Private Key content
   * - ``url_override``
     - ``netbox_secretstore``
     - ``netbox_secretstore_fork``
     - Used to customize plugin URL "{netbox_url}/api/plugins/{url_override}/secrets/"

Sourcing Data from Netbox
+++++++++++++++++++++++++

salt_nornir_netbox external pillar retrieves data from Netbox using several
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
          - bgp: nb://netbox_secretstore/keymaster-1/BGP/peers_pass
          - snmp: nb://netbox_secretstore/keymaster-1/SNMP/community
          - nb://netbox_secretstore/keymaster-1/OSPF/hello_secret
        hostname: 1.2.3.4
        password: nb://netbox_secretstore/keymaster-1/SaltNornirCreds/password
        platform: arista_eos
        port: '22'
        username: nb://netbox_secretstore/keymaster-1/SaltNornirCreds/username
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
      password: "nb://netbox_secretstore/password"
      connection_options:
        napalm:
          platform: iosxr
        scrapli:
          platform: cisco_iosxr
        puresnmp:
          port: 161
          extras:
            version: v2c
            community: "nb://netbox_secretstore/keymaster/snmp/community"
        ncclient:
          username: "nb://netbox_secretstore/netconf-creds/username"
          password: "nb://netbox_secretstore/netconf-creds/password"
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
   section, KeyError raised and device excluded from pillar data
4. If ``hostname`` parameter not defined in Netbox device's configuration context ``nornir`` s
   action, ``hostname`` value set equal to device primary IPv4 address, if primary IPv4
   address is not defined, primary IPv6 address used, if no primary IPv6 address defined,
   device name is used as a ``hostname`` in assumption that device name is a valid FQDN
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

salt_nornir_netbox supports
`netbox_secretstore <https://github.com/DanSheps/netbox-secretstore>`_
plugin to source secrets. netbox_secretstore should be installed and
configured as a Netbox plugin. RSA private key need to be generated for
the user which token is used to work with Netbox, private key need
to be uploaded to Master and configured in Master's ext_pillar::

    ext_pillar:
      - salt_nornir_netbox:
          token: '837494d786ff420c97af9cd76d3e7f1115a913b4'
          use_pillar: False
          secrets:
            resolve_secrets: True
            fetch_username: True
            fetch_password: True
            secret_device: keymaster
            secret_name_map: username
            plugins:
              netbox_secretstore:
                private_key: /etc/salt/netbox_secretstore_private.key

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

salt_nornir_netbox recursively iterates over entire data sourced from Netbox
and attempts to resolve keys using specified secrets URLs.

For example, if this is how secrets defined in Netbox:

.. image:: ./_images/netbox_secrets.png

And sample configuration context data of Netbox device with name``fceos4`` is::

    secrets:
      bgp: nb://netbox_secretstore/keymaster-1/BGP/peers_pass
      secret1: nb://netbox_secretstore/fceos4/SaltSecrets/secret1
      secret2: nb://netbox_secretstore/SaltSecrets/secret2
      secret3: nb://netbox_secretstore/secret3
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
              netbox_secretstore:
                private_key: /etc/salt/netbox_secretstore_private.key

This Nornir inventory data for ``fceos`` devices::

    hosts:
      fceos6:
        password: "nb://netbox_secretstore/Credentials/admin_user"
      fceos7:
        data:
          bgp:
            peers:
              - bgp_peer_secret: "nb://netbox_secretstore/BGP_PEERS/10.0.1.1"
              - bgp_peer_secret: "nb://netbox_secretstore/BGP_PEERS/10.0.1.2"
              - bgp_peer_secret: "nb://netbox_secretstore/BGP_PEERS/10.0.1.3"

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

Sample device interfaces connections data retrieved from Netbox::

    hosts:
      ceos1:
        data:
          connections:
            ConsolePort1:
              custom_fields: {}
              label: ''
              last_updated: '2022-09-19T18:47:52.533889+00:00'
              length: null
              length_unit: null
              remote_device: fceos5
              remote_interface: ConsoleServerPort1
              status: CONNECTED
              tags: []
              tenant:
                name: SALTNORNIR
              type: CAT6A
            eth1:
              custom_fields: {}
              label: ''
              last_updated: '2022-09-19T18:47:48.091871+00:00'
              length: null
              length_unit: null
              remote_device: fceos5
              remote_interface: eth1
              status: CONNECTED
              tags: []
              tenant:
                name: SALTNORNIR
              type: CAT6A

Reference
+++++++++

.. autofunction:: salt_nornir.pillar.salt_nornir_netbox.ext_pillar
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._process_device
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._resolve_secrets
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._resolve_secret
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._fetch_device_secrets
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._host_add_interfaces
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._host_add_connections
.. autofunction:: salt_nornir.pillar.salt_nornir_netbox._netbox_secretstore_get_session_key
"""
import logging
import requests
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from salt_nornir.netbox_utils import nb_graphql, get_interfaces, get_connections

log = logging.getLogger(__name__)

__virtualname__ = "salt_nornir_netbox"

RUNTIME_VARS = {"devices_done": set(), "secrets": {}}


def __virtual__():
    return __virtualname__


def _netbox_secretstore_get_session_key(params):
    """
    Function to retrieve netbox_secretstore session key
    """
    # if salt_jobs_results provided, extract Netbox params from it
    if params.get("ssl_verify") == False:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    if "nb_secretstore_session_key" not in RUNTIME_VARS:
        url_override = params["secrets"]["plugins"]["netbox_secretstore"].get(
            "url_override", "netbox_secretstore"
        )
        url = f"{params['url']}/api/plugins/{url_override}/get-session-key/"
        token = "Token " + params["token"]
        # read private key content from file
        key_file = params["secrets"]["plugins"]["netbox_secretstore"]["private_key"]
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
            RUNTIME_VARS["nb_secretstore_session_key"] = req.json()["session_key"]
        else:
            raise RuntimeError(
                f"salt_nornir_netbox failed to get netbox_secretstore session-key, "
                f"status-code '{req.status_code}', reason '{req.reason}', response "
                f"content '{req.text}'"
            )

    log.debug("salt_nornir_netbox obtained netbox-secretsore session key")

    return RUNTIME_VARS["nb_secretstore_session_key"]


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
    # retrieve device secrets
    for plugin_name in params.get("secrets", {}).get("plugins", {}).keys():
        if RUNTIME_VARS["secrets"].get(device_name, {}).get(plugin_name):
            return RUNTIME_VARS["secrets"][device_name]
        elif plugin_name == "netbox_secretstore":
            url_override = params["secrets"]["plugins"]["netbox_secretstore"].get(
                "url_override", "netbox_secretstore"
            )
            url = f"{params['url']}/api/plugins/{url_override}/secrets/"
            token = "Token " + params["token"]
            session_key = _netbox_secretstore_get_session_key(params)
            # retrieve all device secrets
            req = requests.get(
                url,
                headers={
                    "X-Session-Key": session_key,
                    "authorization": token,
                },
                params={"device": device_name},
                verify=params.get("ssl_verify", True),
            )
            if req.status_code == 200:
                RUNTIME_VARS["secrets"].setdefault(device_name, {})
                RUNTIME_VARS["secrets"][device_name][plugin_name] = [
                    {
                        "role": i["role"]["name"],
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
    Function to retrieve netbox_secretstore secret value at secret_path.

    :param device_name: string, name of device to retrieve secret for
    :param secret_path: string, path to the secret in one of the supported formats
    :param params: dictionary with salt_nornir_netbox parameters
    :param strict: bool, if True raise KeyError if no secret found, return None otherwise
    :return: secret value and secret name or None, None if fail to resolve

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
            if secret_role and secret_role != secret["role"]:
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
                if k in params["secrets"].get("secret_name_map", {}):
                    secret_name_map_key = params["secrets"]["secret_name_map"][k]
                    data[secret_name_map_key] = secret_name
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
        device_name=device["name"],
        params=params,
        add_ip=params.get("host_add_interfaces_ip", False),
        add_inventory_items=params.get("host_add_interfaces_inventory_items", False),
    )

    # save data into Nornir host's inventory
    dk = host_add_interfaces if isinstance(host_add_interfaces, str) else "interfaces"
    host.setdefault("data", {})
    host["data"][dk] = interfaces


def _host_add_connections(device, host, params):
    """
    Function to add interfaces and console ports connections details
    to Nornir host data.

    :param device: device data dictionary
    :param host: Nornir host inventory dictionary
    :param params: dictionary with salt_nornir_netbox parameters
    """
    host_add_connections = params["host_add_connections"]

    cables = get_connections(
        device_name=device["name"],
        params=params,
    )

    # save data into Nornir host's inventory
    dk = (
        host_add_connections if isinstance(host_add_connections, str) else "connections"
    )
    host.setdefault("data", {})
    host["data"][dk] = cables


def _process_device(device, inventory, params):
    """
    Helper function to extract data to form Nornir host entry out
    of Netbox device entry.

    :param device: device dictionary
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
            raise KeyError(f"salt_nornir_netbox no platform found for '{name}' device")
    # add hostname if not provided in config context
    if not host.get("hostname"):
        if device["primary_ip4"]:
            host["hostname"] = device["primary_ip4"]["address"].split("/")[0]
        elif device["primary_ip6"]:
            host["hostname"] = device["primary_ip6"]["address"].split("/")[0]
        else:
            host["hostname"] = name
    # save device data under host data
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
    if fetch_username:
        host["username"], _ = _resolve_secret(
            name, host.get("username", "nb://username"), params, strict=True
        )
    if fetch_password:
        host["password"], _ = _resolve_secret(
            name, host.get("password", "nb://password"), params, strict=True
        )
    if resolve_secrets:
        _resolve_secrets(host, name, params)
    # save host to Nornir inventory
    inventory["hosts"][name] = host
    # add device as processed
    RUNTIME_VARS["devices_done"].add(name)


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
        "site {name}",
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
        _ = nb_graphql("device", {"name": "__dummy__"}, ["id"], params)
    except Exception as e:
        log.exception(
            f"salt_nornir_netbox failed to query GarphQL API, Netbox URL "
            f"'{params['url']}', token ends with '..{params['token'][-6:]}', "
            f"error '{e}'"
        )
        return ret

    # source proxy minion pillar from config context
    if use_minion_id_device is True:
        minion_nb = nb_graphql(
            "device", {"name": minion_id}, ["config_context"], params
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
            # process hosts one by one
            for host_name, host_data in ret.get("hosts", {}).items():
                device = nb_graphql(
                    "device", {"name": host_name}, device_fields, params
                )
                try:
                    if device:
                        _process_device(device[0], ret, params)
                except Exception as e:
                    log.exception(
                        f"salt_nornir_netbox error while processing device '{host_name}' "
                        f"from '{minion_id}' config context data: {e}"
                    )

    # source devices list using tag value equal to minion id
    if use_minion_id_tag is True:
        ret.setdefault("hosts", {})
        filt = {"tag": minion_id}
        devices_by_tag = nb_graphql("device", filt, device_fields, params)
        while devices_by_tag:
            device = devices_by_tag.pop()
            try:
                _process_device(device, ret, params)
            except Exception as e:
                log.exception(
                    f"salt_nornir_netbox error while retrieving devices by "
                    f"tag '{minion_id}': {e}"
                )

    # retrieve devices using hosts filters
    if use_hosts_filters:
        ret.setdefault("hosts", {})
        for filter_item in params.get("hosts_filters") or []:
            devices_by_filter = nb_graphql("device", filter_item, device_fields, params)
            while devices_by_filter:
                device = devices_by_filter.pop()
                try:
                    _process_device(device, ret, params)
                except Exception as e:
                    log.exception(
                        f"salt_nornir_netbox error while retrieving devices "
                        f"by hosts filter '{filter_item}': {e}"
                    )

    return ret
