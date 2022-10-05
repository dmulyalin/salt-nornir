[![Downloads][pepy-downloads-badge]][pepy-downloads-link]
[![PyPI][pypi-latest-release-badge]][pypi-latest-release-link]
[![PyPI versions][pypi-versions-badge]][pypi-versions-link]
[![GitHub Discussion][github-discussions-badge]][github-discussions-link]
[![Code style: black][black-badge]][black-link]
[![Documentation status][readthedocs-badge]][readthedocs-link]

![logo][logo]

# Salt Nornir

Repository to store Nornir based SaltStack modules:

- salt-nornir proxy minion module
- salt-nornir execution module
- salt-nornir state module
- salt-nornir runner module
- salt-nornir Netbox pillar module

Nornir Proxy Minion helps to manage network devices at scale, refer to
[documentation](https://salt-nornir.readthedocs.io/en/latest/index.html)
for details.

# Architecture

Python and Plugins.

![architecture][architecture]

Nornir Proxy acts as a bridge between SaltStack and a wide set of open
source network automation libraries.

# Key Features

- **CLI** Manage your devices over SSH or Telnet using Netmiko, Scrapli, Cisco Genie/PyATS or NAPALM
- **NETCONF** management of network devices one command away using Ncclient or Scrapli-Netconf
- **HTTP API**/**RESTCONF** Interact with devices using Python requests library, automate your networking fleet using 
- **gNMI** device management supported thanks to integration with PyGNMI library
- **SNMPv1/2/3** Capability to manage device using puresnmp library
- **Data Processing** with the help of NTC-Templates, TTP, Jmespath, lxml, xmltodict
- **Network Testing** to test network state and configuration using SSH, Netconf, gNMI, HTTP or SNMP
- **Python** is a first class citizen, need something special - write your own plugins, modules, scripts, codify your work flows
- **API** Integrate with anythingusing SaltStack and Nornir Python API or SaltStack HTTP API
- **Netbox** Source of Truth inventory integration for infrastructure management

# Communication and discussion

Network To Code [salt-nornir Slack Channel](https://app.slack.com/client/T09LQ7E9E/C02MPR34DGF)

Open an [issue](https://github.com/dmulyalin/salt-nornir/issues)

Start a [discussion](https://github.com/dmulyalin/salt-nornir/discussions)

# Contributing

Issues, bug reports and feature requests are welcomed. Feedback is a gift and we truly value it.

# Authors Guidelines

- if it is not in the docs it does not exist
- if it is not tested it is broken
- done is better than perfect
- keep it stupid simple

[logo]:                        docs/source/_images/SaltNornirLogo.png "salt nornir logo"
[architecture]:                docs/source/_images/Nornir_proxy_minion_architecture_v2.png "salt nornir architecture"
[pepy-downloads-badge]:        https://pepy.tech/badge/salt-nornir
[pepy-downloads-link]:         https://pepy.tech/project/salt-nornir
[pypi-versions-badge]:         https://img.shields.io/pypi/pyversions/salt-nornir.svg
[pypi-versions-link]:          https://pypi.python.org/pypi/salt-nornir/
[readthedocs-badge]:           https://readthedocs.org/projects/salt-nornir/badge/?version=latest
[readthedocs-link]:            http://salt-nornir.readthedocs.io/?badge=latest
[pypi-latest-release-badge]:   https://img.shields.io/pypi/v/salt-nornir.svg
[pypi-latest-release-link]:    https://pypi.python.org/pypi/salt-nornir
[github-discussions-link]:     https://github.com/dmulyalin/salt-nornir/discussions
[github-discussions-badge]:    https://img.shields.io/static/v1?label=Discussions&message=Ask&color=blue&logo=github
[black-badge]:                 https://img.shields.io/badge/code%20style-black-000000.svg
[black-link]:                  https://github.com/psf/black
[github-tests-badge]:          https://github.com/dmulyalin/salt-nornir/actions/workflows/main.yml/badge.svg
[github-tests-link]:           https://github.com/dmulyalin/salt-nornir/actions
