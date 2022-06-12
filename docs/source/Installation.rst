Installation
############

SaltStack Nornir Proxy Minion tested only for Linux, it is never tested with and
unlikely will work on Windows. It is recommended to use Red Hat/CentOS or Ubuntu
Linux distributions.

Python 2 is not supported, recommended version is Python 3.6 and higher.

Install from PyPi::

    pip install salt-nornir[prodmin]

Or explicitly specifying Python version::

    python3 -m pip install salt-nornir[prodmin]

Or install GIT and run installation of latest source code from GitHub master brunch::

    python3 -m pip install git+https://github.com/dmulyalin/salt-nornir

Salt Nornir need to be installed on proxy minion machine. If planning to use runner
module, ``salt-nornir`` should be installed on Salt Master machine as well.

For installation of SaltStack master and minion/proxy-minion modules
refer to `official documentation <https://repo.saltproject.io/>`_.

.. warning:: Python 3.6 support deprecated starting with version 0.12.0.

Installation extras
===================

Salt-Nornir comes with these installation extras.

.. list-table:: Salt-Nornir extras packages
   :widths: 15 85
   :header-rows: 1

   * - Name
     - Description
   * - ``dev``
     - Installs libraries required for development e.g. pytest, black, pre-commit etc.
   * - ``prodmin``
     - Production ready minimum set. Installs Netmiko, Ncclient and requests libraries
       to provide support for managing devices over SSH, NETCONF and RESTCONF. In addition,
       installs libraries to extended Salt-Nornir functionality such as Tabulate, Rich, TTP
       etc. All libraries have versions fixed to produce tested and working environment.
   * - ``prodmax``
     - Production ready maximum set. Installs all ``prodmin`` libraries together with
       additional modules required to support complete Salt-Nornir feature set such as
       PyGNMI, PyATS, Scrapli, NAPALM etc. All libraries have versions fixed to produce
       tested and working environment.
   * - ``netmiko``
     - Installs these libraries: netmiko, nornir-netmiko
   * - ``napalm``
     - Installs these libraries: napalm, nornir-napalm
   * - ``scrapli``
     - Installs these libraries: scrapli, scrapli-community
   * - ``pyats``
     - Installs these libraries: genie, pyats
   * - ``netconf``
     - Installs these libraries: ncclient, scrapli-netconf
   * - ``gnmi``
     - Installs these libraries:  pygnmi
   * - ``restconf``
     - Installs these libraries:  requests
   * - ``dataprocessor``
     - Installs these libraries: cerberus, jmespath, ntc-templates, pyyaml, tabulate, ttp,
       ttp-templates, xmltodict, lxml

To install Salt-Nornir only, without any additional plugins::

    pip install salt-nornir

To install minimum production set::

    pip install salt-nornir[prodmin]

To install maximum production set::

    pip install salt-nornir[prodmax]

SaltStack versions tested
=========================

Nornir Proxy minion was well tested and confirmed working with these versions of SaltStack:

* salt 3002
* salt 3003
* salt 3004

Other SaltStack versions might work too, but not tested.

Nornir Salt Dependency
======================

Salt-Nornir and Nornir-Salt uses SemVer approach for version numbering following
this naming convention ``<major number>.<minor number>.<maintenance number>`` for example
``0.11.1``,  ``1.2.3`` etc.

Main dependency for Salt-Nornir is `nornir-salt package <https://pypi.org/project/nornir-salt/>`_,
it must be of the same major and minor versions as ``salt-nornir`` package itself. For example,
compatible Salt-Nornir and Nornir-Salt versions are ``0.11.*``, on the other hand Salt-Nornir
of version ``0.11.0`` is not compatible with Nornir-Salt ``0.8.0``.

Upgrade Procedure
=================

Uninstall existing packages:

    python3 -m pip uninstall nornir-salt salt-nornir

Install updated packages::

    python3 -m pip install nornir-salt salt-nornir --upgrade

Optionally, upgrade sets of extras libraries:

    python3 -m pip install salt-nornir[extras-name-here] --upgrade

Restart your proxy minions to pick up updated version.

Optionally run to verify software versions after Proxy Minions Started::

    salt nrp1 nr.nornir version

Common installation issues
==========================

Issues mainly arise around installing all required dependencies. General rule of thumb - try Googling
errors you getting or search StackOverflow.

**1** ``PyYAML`` dependency - if getting error while doing ``pip install salt-nornir``::

    ERROR: Cannot uninstall 'PyYAML'. It is a distutils installed project and thus we cannot accurately
    determine which files belong to it which would lead to only a partial uninstall.

try::

    python3 -m pip install salt-nornir --ignore-installed

**2** ``setuptools`` dependency - if getting error while doing ``pip install salt-nornir``::

    ModuleNotFoundError: No module named 'setuptools_rust'

try::

    python3 -m pip install -U pip setuptools

Using docker containers
=======================

Refer to `Salt Nornir Docker Repository <https://github.com/dmulyalin/salt-nornir-docker>`_ on how to
setup SaltStack Master and Nornir Proxy Minion using docker containers.
