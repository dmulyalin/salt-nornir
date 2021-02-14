"""
Nornir Execution Module
=======================

Nornir Execution module reference. 

.. note:: Keep in mind that execution module functions executed on same machine where proxy-minion process runs.

Introduction
------------

This execution module complements Nornir Proxy module to interact with devices over SSH, Telnet, 
NETCONF or any other methods supported by Nornir connection plugins.

Things to keep in mind:

* ``multiprocessing`` set to ``True`` is recommended way of running Nornir proxy-minion
* with multiprocessing on, dedicated process starts for each task consuming resources
* tasks executed one after another, but task execution against hosts happening in order
    controlled by logic of Nornir runner in use, usually in parallel using threading.

Commands timeout
----------------

It is recommended to increase
`salt command timeout <https://docs.saltstack.com/en/latest/ref/configuration/master.html#timeout>`_
or use ``--timeout=60`` option to wait for minion return, as all together it might take more than
5 seconds for task to complete. Alternatively, use ``--async`` option and query results afterwards::

    [root@localhost /]# salt nrp1 nr.cli "show clock" --async
    
    Executed command with job ID: 20210211120453972915
    [root@localhost /]# salt-run jobs.lookup_jid 20210211120453972915
    nrp1:
        ----------
        IOL1:
            ----------
            show clock:
                
                *08:17:22.691 EET Sat Feb 13 2021
        IOL2:
            ----------
            show clock:
                *08:17:22.632 EET Sat Feb 13 2021
    [root@localhost /]# 

AAA considerations
------------------

Quiet often AAA servers (Radius, Tacacs) might get overloaded with authentication
and authorization requests coming from devices due to Nornir establishing
connections with them, that effectively results in jobs failures.

To overcome above problems Nornir proxy-module uses ``RetryRunner`` by default.
``RetryRunner`` runner included in
`nornir-salt <https://github.com/dmulyalin/nornir-salt>`_ library and was
developed to address aforementioned issue in addition to implementing retry logic.

Targeting Nornir Hosts
----------------------

Nornir interacts with many devices and has it's own inventory,
additional filtering capabilities introduced in
`nornir_salt <https://github.com/dmulyalin/nornir-salt>`_ library
to narrow down tasks execution to certain hosts/devices.

Sample command to demonstrate targeting capabilites::

    salt nornir-proxy-1 nr.cli "show clock" FB="R*" FG="lab" FP="192.168.1.0/24" FO='{"role": "core"}'

Jumphosts or Bastions
---------------------

``RetryRunner`` included in
`nornir_salt <https://github.com/dmulyalin/nornir-salt>`_ library has
support for ``nr.cli`` function and ``nr.cfg`` with ``plugin="netmiko"``
to interact with devices behind jumphosts, other tasks and runners plugins
does not support that.

Sample jumphost definition in host's inventory data in proxy-minion pillar::

    hosts:
      LAB-R1:
        hostname: 192.168.1.10
        platform: ios
        password: user
        username: user
        data:
          jumphost:
            hostname: 172.16.0.10
            port: 22
            password: admin
            username: admin

Nornir Execution module functions
---------------------------------

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.inventory
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.task
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.cli
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.cfg
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.cfg_gen
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.tping
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.stats

"""

# Import python libs
import logging
import os
import time
import traceback

log = logging.getLogger(__name__)


# import salt libs, wrapping it in try/except for docs to generate
try:
    from salt.exceptions import CommandExecutionError
except:
    log.error("Nornir Execution Module - failed importing SALT libraries")

# import nornir libs
try:
    from nornir import InitNornir
    from nornir_salt import tcp_ping
    from nornir_salt.plugins.functions import FindString

    HAS_NORNIR = True
except ImportError:
    log.error("Nornir Execution Module - failed importing libraries")
    HAS_NORNIR = False
__virtualname__ = "nr"
__proxyenabled__ = ["nornir"]


def __virtual__():
    if HAS_NORNIR:
        return __virtualname__
    return False


# -----------------------------------------------------------------------------
# execution module private functions
# -----------------------------------------------------------------------------
    
    
# -----------------------------------------------------------------------------
# callable module function
# -----------------------------------------------------------------------------


def inventory(**kwargs):
    """
    Return inventory dictionary for Nornir hosts

    :param Fx: filters to filter hosts
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_ 
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``
        
    Sample Usage::

        salt nornir-proxy-1 nr.inventory
        salt nornir-proxy-1 nr.inventory FB="R[12]"
    """
    return __proxy__["nornir.inventory_data"](**kwargs)


def task(plugin, *args, **kwargs):
    """
    Function to invoke any of supported Nornir task plugins. This function
    performs dynamic import of requested plugin function and executes
    ``nr.run`` using supplied args and kwargs

    :param plugin: ``path.to.plugin.task_fun`` to run ``from path.to.plugin import task_fun``
    :param Fx: filters to filter hosts
    :param add_details: boolean, to include details in result or not
    :param add_cpid_to_task_name: boolean, include Child Process ID (cpid) for debugging
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_ 
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``
        
    Sample usage::

        salt nornir-proxy-1 nr.task "nornir_napalm.plugins.tasks.napalm_cli" commands='["show ip arp"]' FB="IOL1"
        salt nornir-proxy-1 nr.task "nornir_netmiko.tasks.netmiko_save_config" add_details=False
        salt nornir-proxy-1 nr.task "nornir_netmiko.tasks.netmiko.netmiko_send_command" command_string="show clock"
        salt nornir-proxy-1 nr.task nr_test a=b c=d add_details=False
    """
    return __proxy__["nornir.execute_job"](
        task_fun=plugin, args=args, kwargs=kwargs, cpid=os.getpid()
    )


def cli(*commands, **kwargs):
    """
    Method to retrieve commands output from devices using ``send_command``
    task plugin from either Netmiko or Scrapli library.

    :param commands: list of commands
    :param Fx: filters to filter hosts
    :param netmiko_kwargs: kwargs to pass on to netmiko send_command methods
    :param add_details: boolean, to include details in result or not
    :param add_cpid_to_task_name: boolean, include Child Process ID (cpid) for debugging
    :param plugin: name of send command task plugin to use - ``netmiko`` (default) or ``scrapli``
    :param match: regular expression pattern to search for in results,
        similar to Cisco ``inlclude`` or Juniper ``match`` pipe commands
    :param before: used with match, number of lines before match to include in results, default is 0
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_ 
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``
        
    Sample Usage::

         salt nornir-proxy-1 nr.cli "show clock" "show run" FB="IOL[12]" netmiko_kwargs='{"use_timing": True, "delay_factor": 4}'
         salt nornir-proxy-1 nr.cli commands='["show clock", "show run"]' FB="IOL[12]" netmiko_kwargs='{"strip_prompt": False}'
         salt nornir-proxy-1 nr.cli "show run" FL="SW1,RTR1,RTR2" match="CPE[123]+" before=1
         salt nornir-proxy-1 nr.cli "show clock" FO='{"platform__any": ["ios", "nxos_ssh", "cisco_xr"]}' for filtering
    """
    commands = kwargs.pop("commands", commands)
    kwargs["commands"] = [commands] if isinstance(commands, str) else commands
    plugin = kwargs.pop("plugin", "netmiko").lower()
    if plugin.lower() == "netmiko":
        task_fun = "_netmiko_send_commands"
        kwargs["connection_name"] = "netmiko"
    elif plugin.lower() == "scrapli":
        task_fun = "_scrapli_send_commands"
        kwargs["connection_name"] = "scrapli"
    result = __proxy__["nornir.execute_job"](
        task_fun=task_fun, args=[], kwargs=kwargs, cpid=os.getpid()
    )
    if "match" in kwargs:
        result = FindString(
            result, pattern=kwargs["match"], before=kwargs.get("before", 0)
        )
    return result


def cfg(*commands, **kwargs):
    """
    Function to push configuration to devices using ``napalm_configure`` or
    ``netmiko_send_config`` or Scrapli ``send_config`` task plugin.

    :param commands: list of commands to send to device
    :param filename: path to file with configuration
    :param template_engine: template engine to render configuration, default is jinja
    :param saltenv: name of SALT environment
    :param context: Overrides default context variables passed to the template.
    :param defaults: Default context passed to the template.
    :param plugin: name of configuration task plugin to use - ``napalm`` (default) or ``netmiko`` or ``scrapli``
    :param dry_run: boolean, default False, controls whether to apply changes to device or simulate them
    :param Fx: filters to filter hosts
    :param add_details: boolean, to include details in result or not
    :param add_cpid_to_task_name: boolean, include Child Process ID (cpid) for debugging
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_ 
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``
        
    .. warning:: ``dry_run`` not supported by ``netmiko`` plugin

    In addition to normal `context variables <https://docs.saltstack.com/en/latest/ref/states/vars.html>`_
    template engine loaded with additional context variable `host`, to access Nornir host
    inventory data.

    Sample usage::

        salt nornir-proxy-1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" FB="R[12]" dry_run=True
        salt nornir-proxy-1 nr.cfg commands='["logging host 1.1.1.1", "ntp server 1.1.1.2"]' FB="R[12]"
        salt nornir-proxy-1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" plugin="netmiko"
        salt nornir-proxy-1 nr.cfg filename=salt://template/template_cfg.j2 FB="R[12]"
    """
    # get arguments
    filename = kwargs.pop("filename", None)
    plugin = kwargs.pop("plugin", "napalm")
    kwargs.setdefault("add_details", True)
    # get configuration
    config = commands if commands else kwargs.pop("commands", None)
    config = "\n".join(config) if isinstance(config, (list, tuple)) else config
    if not config:
        config = __salt__["cp.get_file_str"](
            filename, saltenv=kwargs.get("saltenv", "base")
        )
    if not config:
        raise CommandExecutionError(
            "Configuration not found. filename: {}; commands: {}".format(
                filename, commands
            )
        )
    kwargs["config"] = config
    # decide on task name to run
    if plugin.lower() == "napalm":
        task_fun = "_napalm_configure"
        kwargs["connection_name"] = "napalm"
    elif plugin.lower() == "netmiko":
        task_fun = "_netmiko_send_config"
        kwargs["connection_name"] = "netmiko"
    elif plugin.lower() == "scrapli":
        task_fun = "_scrapli_send_config"
        kwargs["connection_name"] = "scrapli"
    # work and return results
    return __proxy__["nornir.execute_job"](
        task_fun=task_fun, args=[], kwargs=kwargs, cpid=os.getpid()
    )


def cfg_gen(filename, *args, **kwargs):
    """
    Function to render configuration from template file. No configuration pushed
    to devices.

    This function can be useful to stage/test templates or to generate configuration
    without pushing it to devices.

    :param filename: path to template
    :param template_engine: template engine to render configuration, default is jinja
    :param saltenv: name of SALT environment
    :param context: Overrides default context variables passed to the template.
    :param defaults: Default context passed to the template.
    :param add_details: boolean, to include details in result or not
    :param add_cpid_to_task_name: boolean, include Child Process ID (cpid) for debugging
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_ 
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``
        
    In addition to normal `context variables <https://docs.saltstack.com/en/latest/ref/states/vars.html>`_
    template engine loaded with additional context variable `host`, to access Nornir host's
    inventory data.

    Returns rendered configuration.

    Sample usage::

        salt nornir-proxy-1 nr.cfg_gen filename=salt://templates/template.j2 FB="R[12]"

    Sample template.j2 content::

        proxy data: {{ pillar.proxy }}
        jumphost_data: {{ host["jumphost"] }} # "jumphost" defined in host's data
        hostname: {{ host.name }}
        platform: {{ host.platform }}
    """
    # get configuration file content
    config = __salt__["cp.get_file_str"](
        filename, saltenv=kwargs.get("saltenv", "base")
    )
    if not config:
        raise CommandExecutionError(
            message="Failed to get '{}' content".format(filename)
        )
    kwargs["config"] = config
    kwargs["filename"] = filename
    # work and return results
    return __proxy__["nornir.execute_job"](
        task_fun="_cfg_gen", args=[], kwargs=kwargs, cpid=os.getpid()
    )


def tping(ports=[], timeout=1, host=None, **kwargs):
    """
    Tests connection to TCP port(s) by trying to establish a three way
    handshake. Useful for network discovery or testing.

    :param ports (list of int, optional): tcp ports to ping, defaults to host's port or 22
    :param timeout (int, optional): defaults to 1
    :param host (string, optional): defaults to ``hostname``
    :param add_details: boolean, to include details in result or not
    :param add_cpid_to_task_name: boolean, include Child Process ID (cpid) for debugging
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_ 
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``
        
    Sample usage::

        salt nornir-proxy-1 nr.tping
        salt nornir-proxy-1 nr.tping FB="LAB-RT[123]"

    Returns result object with the following attributes set:

    * result (``dict``): Contains port numbers as keys with True/False as values
    """
    kwargs["ports"] = ports
    kwargs["timeout"] = timeout
    kwargs["host"] = host
    # work and return results
    return __proxy__["nornir.execute_job"](
        task_fun="nornir_salt.plugins.tasks.tcp_ping",
        args=[],
        kwargs=kwargs,
        cpid=os.getpid(),
    )


def stats(*args, **kwargs):
    """
    Function to gather and return stats about Nornir proxy process.

    :param stat: name of stat to return, returns all by default
    """
    return __proxy__["nornir.stats"](*args, **kwargs)

