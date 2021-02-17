Installation
############

From PyPi::

    pip install salt_nornir
    
    or
    
    python3 -m pip install salt_nornir
    
From GitHub master brunch::

    python3 -m pip install git+https://github.com/dmulyalin/salt-nornir
  
Above need to be installed on minion machine. If planning to use runner
module, ``salt_nornir`` should be installed on SALT Master machine as well.

For installation of SALTSTACK master and minion/proxy-minion modules please
reference `official documentation <https://repo.saltproject.io/>`_.


Common installation issues
==========================

Issues mainly arise around installing all required dependencies. General rule of thumb - try Googling errors you getting or search stackoverflow.

(1) ``PyYAML`` dependency - if getting error while doing ``pip install salt_nornir``::

      Attempting uninstall: pyYAML
        Found existing installation: PyYAML 3.11
    ERROR: Cannot uninstall 'PyYAML'. It is a distutils installed project and thus we cannot accurately determine which files belong to it which would lead to only a partial uninstall.
    
try::

    python3 -m pip install salt-nornir --ignore-installed
    
(2) ``setuptools`` dependency - if getting error while doing ``pip install salt_nornir``::

    Traceback (most recent call last):
      File "<string>", line 1, in <module>
      File "/tmp/pip-build-o239gdvn/cryptography/setup.py", line 14, in <module>
        from setuptools_rust import RustExtension
    ModuleNotFoundError: No module named 'setuptools_rust'
    
try::

    python3 -m pip install -U pip setuptools