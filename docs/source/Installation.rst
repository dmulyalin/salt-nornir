Installation
############

From PyPi::

    pip install salt_nornir
    
    or
    
    python3 -m pip install salt_nornir
    
From GitHub master brunch::

    python3 -m pip install git+https://github.com/dmulyalin/salt-nornir
  
Above need to be installed on minion machine. If planning to use runner
module, ``salt_nornir`` should be installed on Salt Master machine as well.

For installation of SaltStack master and minion/proxy-minion modules please
reference `official documentation <https://repo.saltproject.io/>`_.

SaltStack versions tested
=========================

Nornir Proxy minion was tested and confirmed working with these versions of SaltStack:

* salt 3002.6
* salt 3003.1

Other SaltStack versions should work as well, but not yet tested.

Common installation issues
==========================

Issues mainly arise around installing all required dependencies. General rule of thumb - try Googling 
errors you getting or search StackOverflow.

**1** ``PyYAML`` dependency - if getting error while doing ``pip install salt_nornir``::

    ERROR: Cannot uninstall 'PyYAML'. It is a distutils installed project and thus we cannot accurately 
    determine which files belong to it which would lead to only a partial uninstall.

try::

    python3 -m pip install salt-nornir --ignore-installed
    
**2** ``setuptools`` dependency - if getting error while doing ``pip install salt_nornir``::

    ModuleNotFoundError: No module named 'setuptools_rust'

try::

    python3 -m pip install -U pip setuptools
    
Using docker containers
=======================

Refer to `Salt Nornir Docker Repository <https://github.com/dmulyalin/salt-nornir-docker>`_ on how to 
setup SaltStack Master and Nornir Proxy Minion using docker containers.