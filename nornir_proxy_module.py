"""
Nornir Proxy module
===================

.. versionadded:: v3001

:codeauthor: Denis Mulyalin <d.mulyalin@gmail.com>
:maturity:   new
:depends:    Nornir
:platform:   unix

Dependencies
------------

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

Single Nornir proxy-minion can work with hundreds of devices as opposed to
conventional proxy-minion that normally dedicated to managing one device/system
only.

As a result, Nornir proxy-minion requires less resources to run tasks, during
idle state only one process is active, that significantly reduces the amount
of memory required on the system.

Proxy-module recommended way of operating is :conf_minion:`multiprocessing <multiprocessing>`
set to ``True``, so that each task executed in dedicated process. That would
imply these consequences:

- multiple tasks can run in parallel handled by different processes
- each process initiates dedicated connections to devices, increasing overall execution time
- multiprocessing mode allows to eliminate problems with memory leaks

.. seealso::

    - :mod:`Nornir execution module <salt.modules.nornir_mod>`

Pillar
------

Proxy parameters:

- ``proxytype`` nornir
- ``proxy_always_alive`` is ignored
- ``multiprocessing`` set to ``True`` is a recommended way to run this proxy
- ``process_count_max`` maximum number of processes to use to limit
  a number of simultaneous tasks and maximum number of active connections
  to devices
- ``nornir_filter_required`` boolean, to indicate if Nornir filter is mandatory 
  for tasks executed by this proxy-minion. Nornir has access to
  multiple devices, by default, if no filter provided, task will run for all
  devices, ``nornir_filter_required`` allows to change behaviour to opposite,
  if no filter provided, task will not run at all. It is a safety measure against
  running task for all devices accidentally, instead, filter ``FB="*"`` can be 
  used to run task for all devices.
- ``runner`` - Nornir runner parameters to use for this proxy module

Nornir uses `inventory <https://nornir.readthedocs.io/en/latest/tutorials/intro/inventory.html>`_
to store information about devices to interact with. Inventory can contain
information about ``hosts``, ``groups`` and ``defaults``. Nornir inventory is
a nested, Python dictionary and it is easy to define it in proxy-minion pillar.

Nornir proxy-minion pillar example:

.. code-block:: yaml

    proxy:
      proxytype: nornir
      process_count_max: 3
      multiprocessing: True
      nornir_filter_required: True
      runner:
         plugin: threaded
         options:
             num_workers: 100
             
    hosts:
      IOL1:
        hostname: 192.168.217.10
        platform: ios
        location: B1
        groups: [lab]
      IOL2:
        hostname: 192.168.217.7
        platform: ios
        location: B2
        groups: [lab]
      IOL3:
        hostname: 192.168.217.11
        platform: ios
        location: B3
        groups: [lab]
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

    groups:
      lab:
        username: nornir
        password: nornir
        connection_options:
          napalm:
            optional_args: {dest_file_system: "system:"}

    defaults: {}

Nornir runners
--------------

Runners in nornir defines how to run tasks for hosts. If no ``runner``
parameters provided in proxy-minion pillar, ``RetryRunner`` will be used.
``RetryRunner`` runner included in 
`nornir-salt <https://github.com/dmulyalin/nornir-salt>`_ library.
"""

# Import python std lib
import logging
import threading
import multiprocessing
import queue

log = logging.getLogger(__name__)

# import SALT libs
from salt.exceptions import CommandExecutionError

# Import third party libs
try:
    from nornir import InitNornir
    from nornir.core.task import Result, Task
    from nornir_salt.plugins.functions import FFun
    from nornir_salt.plugins.functions import ResultSerializer
    from nornir_salt import tcp_ping
    from nornir_netmiko import netmiko_send_command
    from nornir_netmiko import netmiko_send_config
    from nornir_napalm.plugins.tasks import napalm_configure

    HAS_NORNIR = True
except ImportError:
    log.debug("Nornir-proxy - failed importing Nornir modules")
    HAS_NORNIR = False
# -----------------------------------------------------------------------------
# proxy properties
# -----------------------------------------------------------------------------

__proxyenabled__ = ["nornir"]

# -----------------------------------------------------------------------------
# globals
# -----------------------------------------------------------------------------

__virtualname__ = "nornir"
nornir_data = {"initialized": False}

# -----------------------------------------------------------------------------
# propery functions
# -----------------------------------------------------------------------------


def __virtual__():
    """
    Proxy module available only if Nornir is installed.
    """
    if not HAS_NORNIR:
        return (
            False,
            "Nornir proxy module requires https://pypi.org/project/nornir/ library",
        )
    return __virtualname__


# -----------------------------------------------------------------------------
# proxy functions
# -----------------------------------------------------------------------------


def init(opts):
    """
    Initiate nornir by calling InitNornir()
    """
    default_runner = {
        "plugin": "RetryRunner",
        "options": {
            "num_workers": 100,
            "num_connectors": 10,
            "connect_retry": 3,
            "connect_backoff": 1000,
            "connect_splay": 100,
            "task_retry": 3,
            "task_backoff": 1000,
            "task_splay": 100,
        },
    }
    opts["multiprocessing"] = opts["proxy"].get("multiprocessing", True)
    nornir_data["nr"] = InitNornir(
        logging={"enabled": False},
        runner=opts["proxy"].get("runner", default_runner),
        inventory={
            "plugin": "DictInventory",
            "options": {
                "hosts": opts["pillar"]["hosts"],
                "groups": opts["pillar"].get("groups", {}),
                "defaults": opts["pillar"].get("defaults", {}),
            },
        },
    )
    nornir_data["nornir_filter_required"] = opts["proxy"].get(
        "nornir_filter_required", False
    )
    nornir_data["initialized"] = True
    nornir_data["jobs_queue"] = multiprocessing.Queue()
    nornir_data["res_queue"] = multiprocessing.Queue()
    nornir_data["worker_thread"] = threading.Thread(target=_worker).start()
    return True


def ping():
    """
    Return Nornir proxy status
    """
    return nornir_data["initialized"]


def initialized():
    """
    Nornir module finished initializing?
    """
    return nornir_data["initialized"]


def shutdown():
    """
    Closes connections to devices and deletes Nornir object.
    """
    nornir_data["nr"].close_connections(on_good=True, on_failed=True)
    nornir_data["jobs_queue"].put(None)
    del nornir_data["nr"], nornir_data["worker_thread"]
    nornir_data["initialized"] = False
    return True


def grains():
    """
    Does nothing, returns empty dictionary
    """
    return {}


def grains_refresh():
    """
    Does nothing, returns empty dictionary
    """
    return grains()


# -----------------------------------------------------------------------------
# Nornir task functions
# -----------------------------------------------------------------------------


def _netmiko_send_commands(task, commands, **kwargs):
    for command in commands:
        task.run(
            task=netmiko_send_command,
            command_string=command,
            name=command,
            **kwargs.get("netmiko_kwargs", {})
        )
    return Result(host=task.host)


def _napalm_configure(task, config, **kwargs):
    # render configuration
    rendered_config = _render_config_template(task, config, kwargs)
    # push config to devices
    task.run(task=napalm_configure, configuration=rendered_config.result, **kwargs)
    return Result(host=task.host)


def _netmiko_send_config(task, config, **kwargs):
    # render configuration
    rendered_config = _render_config_template(task, config, kwargs)
    # push config to devices
    task.run(
        task=netmiko_send_config,
        config_commands=rendered_config.result.splitlines(),
        **kwargs
    )
    return Result(host=task.host)


def _cfg_gen(task, config, **kwargs):
    """
    Task function for cfg_gen method to render template with pillar
    and Nornir host Inventory data
    """
    task.run(
        task=_render_config_template,
        name="Rendered {} config".format(kwargs.get("filename", task.host.hostname)),
        config=config,
        kwargs=kwargs,
    )
    return Result(host=task.host)


def _render_config_template(task, config, kwargs):
    """
    Helper function to render config template with adding task.host
    to context.

    This function also cleans template engine related arguments
    from kwargs.
    """
    context = kwargs.pop("context", {})
    context.update({"host": task.host})
    rendered_config = __salt__["file.apply_template_on_contents"](
        contents=config,
        template=kwargs.pop("template_engine", "jinja"),
        context=context,
        defaults=kwargs.pop("defaults", {}),
        saltenv=kwargs.pop("saltenv", "base"),
    )
    return Result(host=task.host, result=rendered_config)


# -----------------------------------------------------------------------------
# proxy module private functions
# -----------------------------------------------------------------------------


def _import_task(plugin):
    # import task function, below two lines are the same as
    # from nornir.plugins.tasks import task_name as task_function
    try:
        module = __import__(plugin, fromlist=[""])
        task_function = getattr(module, plugin.split(".")[-1])
        return task_function
    except ImportError:
        return None


def _worker():
    """
    Target function for worker thread to run jobs from
    jobs_queue submitted by execution module processes
    """
    while True:
        try:
            job = nornir_data["jobs_queue"].get(block=True, timeout=0.1)
            if job is None:
                break
        except queue.Empty:
            continue
        try:
            task_name = job["task_name"]
            task_fun = globals().get(task_name, _import_task(task_name))
            # run task function if its found
            if task_fun:
                ret = run(task_fun, *job["args"], **job["kwargs"])
                output = ResultSerializer(ret, job.get("add_details", False))
            else:
                ret = None
                output = "Error - failed to import task function '{}'".format(task_name)
            # submit results in results queue
            nornir_data["res_queue"].put({"output": output, "pid": job["pid"]})
            del ret, output, job  
        except Exception as e:
            output = "Nornir-proxy job failed: {}, error: '{}'".format(job, e)
            nornir_data["res_queue"].put({"output": output, "pid": job["pid"]})
            continue


# -----------------------------------------------------------------------------
# callable functions
# -----------------------------------------------------------------------------


def inventory_data(**kwargs):
    """
    Return Nornir inventory as a dictionary

    :param Fx: filters to filter hosts
    """
    # filter hosts to return inventory for
    hosts = FFun(nornir_data["nr"], kwargs=kwargs)
    return hosts.dict()


def run(task, *args, **kwargs):
    """
    Function to run Nornir tasks

    :param task: callable task function
    :param Fx: filters to filter hosts
    :param kwargs: arguments to pass to ``nornir_object.run`` method
    """
    # set dry_run argument
    nornir_data["nr"].data.dry_run = kwargs.get("dry_run", False)
    # reset failed hosts if any
    nornir_data["nr"].data.reset_failed_hosts()
    # Filter hosts to run tasks for
    hosts = FFun(nornir_data["nr"], kwargs=kwargs)
    # check if nornir_filter_required is True but no filter
    if (
        nornir_data["nornir_filter_required"] == True
        and hosts.state.has_filter == False
    ):
        raise CommandExecutionError(
            "Proxy 'nornir_filter_required' is True but no filter provided"
        )
    # run tasks
    return hosts.run(
        task,
        *[i for i in args if not i.startswith("_")],
        **{k: v for k, v in kwargs.items() if not k.startswith("_")}
    )


def get_jobs_queue():
    """
    Function to return jobs queue to submit jobs into
    """
    return nornir_data["jobs_queue"]


def get_results_queue():
    """
    Function to return results queue to get results from
    """
    return nornir_data["res_queue"]
