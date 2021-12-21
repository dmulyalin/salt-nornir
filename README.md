[![Downloads](https://pepy.tech/badge/salt-nornir)](https://pepy.tech/project/salt-nornir)
[![PyPI versions](https://img.shields.io/pypi/pyversions/salt-nornir.svg)](https://pypi.python.org/pypi/salt-nornir/)
[![Documentation status](https://readthedocs.org/projects/salt-nornir/badge/?version=latest)](http://salt-nornir.readthedocs.io/?badge=latest)

![logo][logo]

# Salt Nornir

Repository to store Nornir based SaltStack modules:

- salt-nornir proxy minion module
- salt-nornir execution module
- salt-nornir state module
- salt-nornir runner module

Nornir Proxy Minion helps to manage network devices at scale, reference
[documentation](https://salt-nornir.readthedocs.io/en/latest/index.html)
for details.

# Architecture

Python and Plugins.

![architecture][architecture]

Nornir Proxy acts as a bridge between SaltStack and a wide set of network automation libraries.

# Advantages

Some notable benefits:

- Well tested - overall 382 tests combined as of release 0.8.0
- Brings together SaltStack and a wealth of open-source libraries - Nornir, Netmiko, NAPALM, Scrapli, Scrapli-Netconf, Ncclient, Genie&PyATS (free, not open-source), PyGNMI, NTC-Templates, TTP, Jmespath, lxml, xmltodict, requests
- Capable of addressing overwhelming set of use cases from simple data retrieval and parsing to infrastructure provisioning, testing, orchestration and self-healing
- Python is a first class citizen, need something special - write your own plugins, modules, scripts, codify your work flows
- Integrate anything with anything, all you can do via CLI you can do via SaltStack and Nornir Python API or SaltStack REST API

# Communication and discussion

Network To Code [salt-nornir Slack Channel](https://app.slack.com/client/T09LQ7E9E/C02MPR34DGF)

Open an [issue](https://github.com/dmulyalin/salt-nornir/issues)

Start a [discussion](https://github.com/dmulyalin/salt-nornir/discussions)

# Contributing

Issues, bug reports and feature requests are welcomed.

[logo]: docs/source/_images/SaltNornirLogo.png "salt nornir logo"
[architecture]: docs/source/_images/Nornir_proxy_minion_architecture_v2.png "salt nornir architecture"
