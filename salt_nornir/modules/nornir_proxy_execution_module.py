"""
Nornir Execution module
=======================

.. versionadded:: v3001

:codeauthor: Denis Mulyalin <d.mulyalin@gmail.com>
:maturity:   new
:depends:    Nornir
:platform:   unix

Dependencies
------------

- :mod:`Nornir proxy minion <salt.proxy.nornir>`

Nornir 3.x uses modular approach for plugins. As a result  required
plugins need to be installed separately from Nornir Core library. Main
plugin to install is:

- `nornir-salt <https://github.com/dmulyalin/nornir-salt>`_ ``pip install nornir-salt``

``nornir-salt`` will install these additional dependencies automatically:

- `Nornir <https://github.com/nornir-automation/nornir>`_ ``pip install nornir``
- `nornir_netmiko <https://github.com/ktbyers/nornir_netmiko/>`_ ``pip install nornir_netmiko``
- `nornir_napalm <https://github.com/nornir-automation/nornir_napalm/>`_ ``pip install nornir_napalm``

Introduction
------------

This execution module complements `Nornir <https://nornir.readthedocs.io/en/latest/index.html>`_
based :mod:`proxy minion <salt.proxy.nornir>` to interact with devices over SSH, Telnet, NETCONF or
any other supported connection methods.

Things to keep in mind:

- on each call, Nornir object instance re-initiated with latest pillar data
- ``multiprocessing`` set to ``True`` is recommended way of running Nornir proxy-module
- with multiprocessing on, dedicated process starts for each task
- each process initiates new connections to devices, increasing task execution time

Commands timeout
----------------

It is recommended to increase
`salt command timeout <https://docs.saltstack.com/en/latest/ref/configuration/master.html#timeout>`_
or use ``--timeout=60`` option to wait for minion return, as on each call Nornir
has to initiate connections to devices and all together it might take more than
5 seconds for task to complete.

AAA considerations
------------------

Quiet often, AAA servers (Radius, Tacacs) might get overloaded with authentication
and authorization requests coming from devices due to Nornir establishing
connections with them, that effectively results in jobs failures. This problem
equally true for jobs executed from CLI as well as for scheduled jobs.

To overcome above problems Nornir proxy-module uses ``RetryRunner`` by default.
``RetryRunner`` runner included in
`nornir-salt <https://github.com/dmulyalin/nornir-salt>`_ library and was
developed to address aforemention issues.

Devices connections limits
--------------------------

Beacause Nornir proxy has to initiate new connection to devices for each task, running
too many tasks might hit certain devices' limits, such as:

- maximum allowed number of simultaneous VTY connections
- maximum allowed number of simultaneous connections per user

As a result, it make sense to increase above numbers and engineer tasks execution
to work within these limits.

Targeting Nornir Hosts
----------------------

Nornir interacts with many devices and has it's own inventory,
additional filtering capabilities introduced in
`nornir-salt <https://github.com/dmulyalin/nornir-salt>`_ library
to narrow down tasks execution to certain hosts/devices.

Sample command to demonstrate targeting capabilites::

 salt nornir-proxy-1 nr.cli "show clock" FB="R*" FG="lab" FP="192.168.1.0/24" FO='{"role": "core"}'

Jumphosts or Bastions
---------------------

``RetryRunner`` included in
`nornir-salt <https://github.com/dmulyalin/nornir-salt>`_ library has
support for ``nr.cli`` function and ``nr.cfg`` with ``plugin="netmiko"``
to interact with devices behind jumposts, other tasks and runners plugins
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
"""

# Import python libs
import logging
import os
import time
import queue
import traceback

# import salt libs
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

# import nornir libs
try:
    from nornir import InitNornir
    from nornir_salt import tcp_ping

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


def _get_results(task_name, args, kwargs, add_details):
    """
    Function to subm,it work request in parent nornir-proxy
    process and retrieve results from results queue.
    """
    jobs_queue = __proxy__["nornir.get_jobs_queue"]()
    results_queue = __proxy__["nornir.get_results_queue"]()
    start_time = time.time()
    # submit work request to main proxy-minion process
    jobs_queue.put(
        {
            "task_name": task_name,
            "args": args,
            "kwargs": kwargs,
            "pid": os.getpid(),
            "add_details": add_details
        }
    )
    # wait 10 minites for job results return to avoid deadlocks
    while (time.time() - start_time) < 600:
        time.sleep(0.1)
        try:
            res = results_queue.get(block=True, timeout=0.1)
            if res["pid"] == os.getpid():
                return res["output"]
            else:
                results_queue.put(res)
        except queue.Empty:
            continue
        except:
            tb = traceback.format_exc()
            log.error("Nornir-proxy child PID {}, failed get job '{}' results, error: '{}'".format(os.getpid(), task_name, tb))
    log.error("Nornir-proxy child PID {}, job '{}' got no results after 10min waiting.".format(os.getpid(), task_name))


# -----------------------------------------------------------------------------
# callable module function
# -----------------------------------------------------------------------------


def inventory(**kwargs):
    """
    Return inventory dictionary for Nornir hosts

    :param Fx: filters to filter hosts

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

    :param plugin: ``path.to.plugin.task_name`` to run ``from path.to.plugin import task_name``
    :param Fx: filters to filter hosts
    :param add_details: boolean, to include details in result or not

    Sample usage::

        salt nornir-proxy-1 nr.task "nornir_napalm.plugins.tasks.napalm_cli" commands='["show ip arp"]' FB="IOL1"
        salt nornir-proxy-1 nr.task "nornir_netmiko.tasks.netmiko_save_config" add_details=False
    """
    return _get_results(
        task_name=plugin,
        args=args,
        kwargs=kwargs,
        add_details=kwargs.pop("add_details", True)
    )


def cli(*commands, **kwargs):
    """
    Method to retrieve commands output from devices using ``send_command``
    task plugin from either Netmiko or Scrapli library.

    :param commands: list of commands
    :param Fx: filters to filter hosts
    :param netmiko_kwargs: kwargs to pass on to netmiko send_command methods
    :param add_details: boolean, to include details in result or not
    :param plugin: name of send command task plugin to use - ``netmiko`` (default) or ``scrapli``

    Sample Usage::

         salt nornir-proxy-1 nr.cli "show clock" "show run" FB="IOL[12]" netmiko_kwargs='{"use_timing": True, "delay_factor": 4}'
         salt nornir-proxy-1 nr.cli commands='["show clock", "show run"]' FB="IOL[12]" netmiko_kwargs='{"strip_prompt": False}'
    """
    # log.error("Proxy minion nr.cli got kwargs: {}".format(kwargs))
    __pub_jid = kwargs.get("__pub_jid")
    commands = kwargs.pop("commands", commands)
    kwargs["commands"] = [commands] if isinstance(commands, str) else commands
    plugin = kwargs.get("plugin", "netmiko").lower()
    if plugin.lower() == "netmiko":
        task_name="_netmiko_send_commands"
        kwargs["connection_name"] = "netmiko"
    elif plugin.lower() == "scrapli":
        task_name="_scrapli_send_commands"
        kwargs["connection_name"] = "scrapli"
    return _get_results(
        task_name=task_name,
        args=[],
        kwargs=kwargs,
        add_details=kwargs.pop("add_details", False)
    )


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
    # get configuration
    config = commands if commands else kwargs.pop("commands", None)
    config = "\n".join(config) if isinstance(config, (list, tuple)) else config
    if not config:
        config = __salt__["cp.get_file_str"](
            filename, saltenv=kwargs.get("saltenv", "base")
        )
    if not config:
        raise CommandExecutionError("Configuration not found")
    kwargs["config"] = config
    # decide on task name to run
    if plugin.lower() == "napalm":
        task_name = "_napalm_configure"
        kwargs["connection_name"] = "napalm"
    elif plugin.lower() == "netmiko":
        task_name = "_netmiko_send_config"
        kwargs["connection_name"] = "netmiko"
    elif plugin.lower() == "scrapli":
        task_name = "_scrapli_send_config"
        kwargs["connection_name"] = "scrapli"
    # work and return results
    return _get_results(
        task_name=task_name,
        args=[],
        kwargs=kwargs,
        add_details=kwargs.pop("add_details", True)
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
    return _get_results(
        task_name="_cfg_gen",
        args=[],
        kwargs=kwargs,
        add_details=kwargs.pop("add_details", False)
    )


def tping(ports=[], timeout=1, host=None, **kwargs):
    """
    Tests connection to TCP port(s) by trying to establish a three way
    handshake. Useful for network discovery or testing.

    :param ports (list of int, optional): tcp ports to ping, defaults to host's port or 22
    :param timeout (int, optional): defaults to 1
    :param host (string, optional): defaults to ``hostname``

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
    return _get_results(
        task_name="tcp_ping",
        args=[],
        kwargs=kwargs,
        add_details=kwargs.pop("add_details", False)
    )


def stats(*args, **kwargs):
    """
    Function to return useful stats for main nornir proxy process
    """
    return __proxy__["nornir.stats"]()