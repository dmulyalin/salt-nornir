"""
Nornir Proxy module
===================

Nornir Proxy Module is a core component of Nornir Proxy Minion. However,
users rarely have to interact with it directly unless they writing their
own Execution or Runner or State or whatever modules for SaltStack.

What is important to understand are configuration parameters you can use with
Nornir Proxy Minion, as they can help to alter default behavior or control
various aspects of Nornir Proxy Minion life cycle.

Introduction
------------

Single Nornir proxy-minion can work with hundreds of devices as opposed to
conventional proxy-minion that normally dedicated to managing one device/system
only.

As a result, Nornir proxy-minion requires less resources to run tasks against same
number of devices. During idle state only one proxy minion process is active,
that significantly reduces amount of memory required to manage device endpoints.

Proxy-module required way of operating is ``multiprocessing`` set to ``True`` -
default value, that way each task executed in dedicated process.

Dependencies
------------

Nornir 3.x uses modular approach for plugins. As a result  required
plugins need to be installed separately from Nornir Core library. Main
collection of plugins to install is `nornir-salt <https://github.com/dmulyalin/nornir-salt>`_.
Nornir Salt repository contains many function used by Salt Nornir Proxy
Minion module and is mandatory to have on the system where proxy minion
process runs.

Nornir Proxy Configuration Parameters
-------------------------------------

Below parameters can be specified in Proxy Minion Pillar.

- ``proxytype`` - string of value ``nornir``
- ``multiprocessing`` - boolean, ``True`` by default, multiprocessing is a recommended way to run this proxy,
  threading mode also works, but might be prone to memory consumption issues
- ``process_count_max`` - int, default is ``-1`` no limit, maximum number of processes to use to limit a number
  of tasks waiting to execute
- ``nornir_filter_required`` - boolean, default is ``False``, to indicate if Nornir filter is mandatory
  for tasks executed by this proxy-minion. Nornir has access to multiple devices, by default, if no filter
  provided, task will run for all devices, ``nornir_filter_required`` allows to change behavior to opposite,
  if no filter provided, task will not run at all. It is a safety measure against running task for all
  devices accidentally, instead, filter ``FB="*"`` can be used to run task for all devices.
- ``runner`` - dictionary, Nornir Runner plugin parameters, default is
  `RetryRunner <https://nornir-salt.readthedocs.io/en/latest/Runners/RetryRunner.html#retryrunner-plugin>`_
- ``inventory`` - dictionary, Nornir Inventory plugin parameters, default is
  `DictInventory  <https://nornir-salt.readthedocs.io/en/latest/Inventory%20Plugins.html#dictinventory-plugin>`_
  populated with data from proxy-minion pillar, pillar data ignored by any other inventory plugins
- ``child_process_max_age`` - int, default is 660s, seconds to wait before forcefully kill child process
- ``watchdog_interval`` - int, default is 30s, interval in seconds between watchdog runs
- ``proxy_always_alive`` - boolean, default is True, keep connections with devices alive or tear them down
  immediately after each job
- ``connections_idle_timeout`` - int, seconds, default is 1 equivalent to ``proxy_always_alive`` set to True, if
  value equals 0 renders same behavior as if ``proxy_always_alive`` is False, if value above 1 - all host's
  device connections torn down after it was not in use for longer then idle timeout value even if
  ``proxy_always_alive`` set to True
- ``job_wait_timeout`` - int, default is 600s, seconds to wait for job return until give up
- ``memory_threshold_mbyte`` - int, default is 300, value in MBytes above each to trigger ``memory_threshold_action``
- ``memory_threshold_action`` - str, default is ``log``, action to implement if ``memory_threshold_mbyte`` exceeded,
  possible actions: ``log`` - send syslog message, ``restart`` - shuts down proxy minion process.
- ``nornir_workers`` - number of Nornir instances to create, each instance has worker thread associated with it
  allowing to run multiple tasks against hosts, as each worker dequeue tasks from jobs queue, default is 3
- ``files_base_path`` - str, default is ``/var/salt-nornir/{proxy_id}/files/``, OS path to folder where to save files
  on a per-host basis using `ToFileProcessor <https://nornir-salt.readthedocs.io/en/latest/Processors/ToFileProcessor.html>_`,
- ``files_max_count`` - int, default is 5, maximum number of file version for ``tf`` argument used by
  `ToFileProcessor <https://nornir-salt.readthedocs.io/en/latest/Processors/ToFileProcessor.html#tofileprocessor-plugin>`_
- ``nr_cli`` - dictionary of default arguments to use with ``nr.cli`` execution module function, default is none
- ``nr_cfg`` - dictionary of default arguments to use with ``nr.cfg`` execution module function, default is none
- ``nr_nc`` - dictionary of default arguments to use with ``nr.nc`` execution module function, default is none
- ``event_progress_all`` - boolean, default is False, if True emits progress events for all tasks using
  `SaltEventProcessor <https://nornir-salt.readthedocs.io/en/latest/Processors/SaltEventProcessor.html>_`,
  per-task ``event_progress`` argument overrides ``event_progress_all`` parameter.

Nornir uses `inventory <https://nornir.readthedocs.io/en/latest/tutorials/intro/inventory.html>`_
to store information about devices to interact with. Inventory can contain
information about ``hosts``, ``groups`` and ``defaults``. Nornir inventory
defined in proxy-minion pillar.

Nornir proxy-minion pillar example:

.. code-block:: yaml

    proxy:
      proxytype: nornir
      process_count_max: 3
      multiprocessing: True
      nornir_filter_required: True
      proxy_always_alive: True
      connections_idle_timeout: 1
      watchdog_interval: 30
      child_process_max_age: 660
      job_wait_timeout: 600
      memory_threshold_mbyte: 300
      memory_threshold_action: log
      files_base_path: "/var/salt-nornir/{proxy_id}/files/"
      files_max_count: 5
      event_progress_all: True
      nr_cli: {}
      nr_cfg: {}
      nr_nc: {}
      runner:
         plugin: RetryRunner
         options:
            num_workers: 100
            num_connectors: 10
            connect_retry: 3
            connect_backoff: 1000
            connect_splay: 100
            task_retry: 3
            task_backoff: 1000
            task_splay: 100
            reconnect_on_fail: True
            task_timeout: 600
            creds_retry: ["local_creds"]
      inventory:
         plugin: DictInventory

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

    groups:
      lab:
        username: nornir
        password: nornir
        connection_options:
          napalm:
            optional_args: {dest_file_system: "system:"}

    defaults:
      data:
        credentials:
          local_creds:
            username: admin
            password: admin

To use other type of inventory or runner plugins define their settings
in pillar configuration:

.. code-block:: yaml

    proxy:
      runner:
         plugin: threaded
         options:
             num_workers: 100
      inventory:
         plugin: SimpleInventory
         options:
           host_file: "/var/salt-nonir/proxy-id-1/hosts.yaml"
           group_file: "/var/salt-nonir/proxy-id-1/groups.yaml"
           defaults_file: "/var/salt-nonir/proxy-id-1/defaults.yaml"

Nornir runners
--------------

Nornir Runner plugins define how to run tasks against hosts. If no ``runner``
dictionary provided in proxy-minion pillar, Nornir initialized using Nornir Salt
`RetryRunner plugin <https://nornir-salt.readthedocs.io/en/latest/Runners/RetryRunner.html#retryrunner-plugin>`_
with these default settings::

    runner = {
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
            "reconnect_on_fail": True,
            "task_timeout": 600,
            "creds_retry": [{"username": "admin", "password": "admin", "port": 2022}]
        },
    }

Nornir Proxy Module Functions
-----------------------------

.. list-table:: Common CLI Arguments Summary
   :widths: 15 85
   :header-rows: 1

   * - Name
     - Description
   * - `refresh_nornir`_
     - Function to re-instantiate Nornir object instance refreshing pillar
   * - `execute_job`_
     - Function to place job in worker thread jobs queue
   * - `grains`_
     - Retrieve Nornir Proxy Minion grains
   * - `grains_refresh`_
     - Refresh Nornir Proxy Minion grains
   * - `init`_
     - Initiate Nornir Proxy-module
   * - `kill_nornir`_
     - Un-gracefully shutdown Nornir Proxy Minion process
   * - `list_hosts`_
     - Produces a list of hosts' names managed by this Proxy
   * - `nr_data`_
     - To retrieve values from ``nornir_data`` Nornir Proxy Minion dictionary
   * - `ping`_
     - To test Nornir Proxy Minion process
   * - `queues_utils`_
     - Utility function to manage Proxy Minion queues
   * - `run`_
     - Used to run Nornir Task
   * - `shutdown`_
     - Gracefully shutdown Nornir Instance
   * - `stats`_
     - Produces a dictionary of Nornir Proxy Minion statistics
   * - `workers_utils`_
     - Utility function to manage Proxy Minion workers

refresh_nornir
++++++++++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module._refresh_nornir

execute_job
+++++++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.execute_job

grains
++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.grains

grains_refresh
++++++++++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.grains_refresh

init
++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.init

kill_nornir
+++++++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.kill_nornir

list_hosts
++++++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.list_hosts

nr_data
+++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.nr_data

nr_version
++++++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.nr_version

ping
++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.ping

queues_utils
++++++++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.queues_utils

run
+++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.run

shutdown
++++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.shutdown

stats
+++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.stats

workers_utils
+++++++++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.workers_utils
"""

# Import python std lib
import logging
import threading
import multiprocessing
import queue
import os
import time
import traceback
import signal
import psutil
import copy
import sys

from salt_nornir.utils import _is_url
from salt_nornir.pydantic_models import model_nornir_config

try:
    import resource

    HAS_RESOURCE_LIB = True
except ImportError:
    HAS_RESOURCE_LIB = False

log = logging.getLogger(__name__)

# import salt libs, wrapping it in try/except for docs to generate
try:
    from salt.exceptions import CommandExecutionError, TimeoutError
except:
    log.error("Nornir Proxy Module - failed importing SALT libraries")

try:
    # starting with salt 3003 need to use loader_context to reconstruct
    # __salt__ dunder within treads:
    # details: https://github.com/saltstack/salt/issues/59962
    try:
        from salt.loader_context import loader_context

    except ImportError:
        # after salt 3004 api was updated - https://github.com/saltstack/salt/pull/60595
        from salt.loader.context import loader_context

    HAS_LOADER_CONTEXT = True
except ImportError:
    HAS_LOADER_CONTEXT = False

minion_process = psutil.Process(os.getpid())

# Import third party libs
try:
    from nornir import InitNornir
    from nornir.core.task import MultiResult, Result
    from nornir_salt.plugins.functions import (
        FFun,
        ResultSerializer,
        HostsKeepalive,
        TabulateFormatter,
        DumpResults,
        InventoryFun,
    )
    from nornir_salt.plugins.processors import (
        TestsProcessor,
        ToFileProcessor,
        DiffProcessor,
        DataProcessor,
        SaltEventProcessor,
    )

    HAS_NORNIR = True
except ImportError:
    log.error("Nornir-proxy - failed importing Nornir modules")
    HAS_NORNIR = False

# -----------------------------------------------------------------------------
# proxy properties
# -----------------------------------------------------------------------------

__proxyenabled__ = ["nornir"]

# -----------------------------------------------------------------------------
# globals
# -----------------------------------------------------------------------------

__virtualname__ = "nornir"
stats_dict = {
    "proxy_minion_id": None,
    "main_process_is_running": 0,
    "main_process_start_time": time.time(),
    "main_process_start_date": time.ctime(),
    "main_process_uptime_seconds": 0,
    "main_process_ram_usage_mbyte": minion_process.memory_info().rss / 1024000,
    "main_process_pid": os.getpid(),
    "main_process_host": os.uname()[1] if hasattr(os, "uname") else "",
    "main_process_fd_count": 0,
    "jobs_started": 0,
    "jobs_completed": 0,
    "jobs_failed": 0,
    "jobs_job_queue_size": 0,
    "jobs_res_queue_size": 0,
    "tasks_completed": 0,
    "tasks_failed": 0,
    "nornir_workers": 0,
    "hosts_count": 0,
    "hosts_connections_active": 0,
    "hosts_tasks_failed": 0,
    "timestamp": time.ctime(),
    "watchdog_runs": 0,
    "watchdog_child_processes_killed": 0,
    "watchdog_dead_connections_cleaned": 0,
    "child_processes_count": 0,
    # "child_processes_ram_usage": 0
}
nornir_data = {
    "initialized": False,
    "stats": copy.deepcopy(stats_dict),
    "jobs_queue": None,
    "res_queue": None,
    "worker_thread": None,
    "watchdog_thread": None,
    "nornir_workers": None,
    "nrs": [],
}

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
# salt proxy functions
# -----------------------------------------------------------------------------


def init(opts, loader=None, init_queues=True):
    """
    Initiate Nornir by calling InitNornir()

    :param opts: (dict) proxy minion options
    :param loader: (obj) SaltStack loader context object
    :param init_queues: (bool) if True, initialises multiprocessing queues,
        set to False if "nr.nornir refresh workers_only=True" called
    """
    # validate Salt-Nornir minion configuration
    _ = model_nornir_config(
        proxy=opts["proxy"],
        hosts=opts["pillar"].get("hosts"),
        groups=opts["pillar"].get("groups"),
        defaults=opts["pillar"].get("defaults"),
    )
    opts["multiprocessing"] = opts["proxy"].get("multiprocessing", True)
    opts["process_count_max"] = opts["proxy"].get("process_count_max", -1)
    runner_config = opts["proxy"].get(
        "runner",
        {
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
                "reconnect_on_fail": True,
                "task_timeout": 600,
            },
        },
    )
    inventory_config = opts["proxy"].get(
        "inventory",
        {
            "plugin": "DictInventory",
            "options": {
                "hosts": opts["pillar"]["hosts"],
                "groups": opts["pillar"].get("groups", {}),
                "defaults": opts["pillar"].get("defaults", {}),
            },
        },
    )
    nornir_data["salt_download_lock"] = multiprocessing.Lock()
    nornir_data["tf_index_lock"] = multiprocessing.Lock()
    nornir_data["nornir_workers"] = opts["proxy"].get("nornir_workers", 3)
    for i in range(nornir_data["nornir_workers"]):
        nornir_data["nrs"].append(
            {
                "nr": InitNornir(
                    logging={"enabled": False},
                    runner=copy.deepcopy(runner_config),
                    inventory=copy.deepcopy(inventory_config),
                ),
                "connections_lock": multiprocessing.Lock(),
                "is_busy": multiprocessing.Event(),
                "worker_jobs_started": 0,
                "worker_jobs_completed": 0,
                "worker_jobs_failed": 0,
                "worker_tasks_completed": 0,
                "worker_tasks_failed": 0,
                "worker_hosts_tasks_failed": 0,
                "worker_connections": {},
                "worker_id": i + 1,
                "worker_jobs_queue": multiprocessing.Queue(),
            }
        )
    # add parameters from proxy configuration
    nornir_data["nornir_filter_required"] = opts["proxy"].get(
        "nornir_filter_required", False
    )
    nornir_data["child_process_max_age"] = opts["proxy"].get(
        "child_process_max_age", 660
    )
    nornir_data["watchdog_interval"] = int(opts["proxy"].get("watchdog_interval", 30))
    nornir_data["job_wait_timeout"] = int(opts["proxy"].get("job_wait_timeout", 600))
    nornir_data["proxy_always_alive"] = opts["proxy"].get("proxy_always_alive", True)
    nornir_data["connections_idle_timeout"] = opts["proxy"].get(
        "connections_idle_timeout",
        1 if nornir_data["proxy_always_alive"] is True else 0,
    )
    nornir_data["event_progress_all"] = opts["proxy"].get("event_progress_all", False)
    nornir_data["memory_threshold_mbyte"] = int(
        opts["proxy"].get("memory_threshold_mbyte", 300)
    )
    nornir_data["memory_threshold_action"] = opts["proxy"].get(
        "memory_threshold_action", "log"
    )
    nornir_data["files_base_path"] = opts["proxy"].get(
        "files_base_path", "/var/salt-nornir/{}/files/".format(opts["id"])
    )
    nornir_data["files_max_count"] = int(opts["proxy"].get("files_max_count", 5))
    nornir_data["nr_cli"] = opts["proxy"].get("nr_cli", {})
    nornir_data["nr_cfg"] = opts["proxy"].get("nr_cfg", {})
    nornir_data["nr_nc"] = opts["proxy"].get("nr_nc", {})
    nornir_data["initialized"] = True
    # add some stats
    nornir_data["stats"]["proxy_minion_id"] = opts["id"]
    nornir_data["stats"]["main_process_is_running"] = 1
    nornir_data["stats"]["hosts_count"] = len(
        nornir_data["nrs"][0]["nr"].inventory.hosts.keys()
    )
    # Initiate multiprocessing related queus if they are not initialised
    # already, which is the case if we doing workers_only refresh
    if not nornir_data.get("jobs_queue") or init_queues:
        nornir_data["jobs_queue"] = multiprocessing.Queue()
        nornir_data["res_queue"] = multiprocessing.Queue()
    # if loader not None, meaning init() called by _refresh_nornir function
    if loader:
        loader = loader
    # salt >3003 requires loader context to call __salt__ within threads
    elif HAS_LOADER_CONTEXT:
        loader = __salt__.loader()
    # salt <3003 does not use loader context
    else:
        loader = None
    # start worker threads
    for i in range(nornir_data["nornir_workers"]):
        nornir_data["nrs"][i]["worker_thread"] = threading.Thread(
            target=_worker, args=(nornir_data["nrs"][i], loader)
        )
    for nr in nornir_data["nrs"]:
        nr["worker_thread"].start()
    # start watchdog thread
    nornir_data["watchdog_thread"] = threading.Thread(
        target=_watchdog, name="{}_watchdog".format(opts["id"]), args=(loader,)
    )
    nornir_data["watchdog_thread"].start()
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
    This function implements this protocol to perform Nornir graceful shutdown:

    1. Signal worker and watchdog threads to stop
    2. Close all connections to devices
    3. Close jobs and results queues
    4. Kill all child processes
    5. Delete Nornir object

    Proxy Minion process keeps running afterwards, but cannot do anything.
    """
    log.info("Nornir-proxy MAIN PID {}, shutting down Nornir".format(os.getpid()))
    try:
        # trigger worker and watchdogs threads to stop
        nornir_data["initialized"] = False
        # close connections to devices and delete old Nornir Objects
        while nornir_data["nrs"]:
            nr = nornir_data["nrs"].pop()
            nr["nr"].close_connections(on_good=True, on_failed=True)
            del nr
        # close queues
        nornir_data["jobs_queue"].close()
        nornir_data["jobs_queue"].join_thread()
        nornir_data["res_queue"].close()
        nornir_data["res_queue"].join_thread()
        # kill child processes left
        for p in multiprocessing.active_children():
            os.kill(p.pid, signal.SIGKILL)
        log.info("Nornir-proxy MAIN PID {}, Nornir shutted down".format(os.getpid()))
        return True
    except:
        tb = traceback.format_exc()
        log.error(
            "Nornir-proxy MAIN PID {}, Nornir shutdown failed, error: {}".format(
                os.getpid(), tb
            )
        )
        return False


def grains():
    """
    Populate grains
    """
    return {"hosts": list_hosts(FB="*")}


def grains_refresh():
    """
    Does nothing, returns empty dictionary
    """
    return grains()


# -----------------------------------------------------------------------------
# proxy module private functions
# -----------------------------------------------------------------------------


def _use_loader_context(func):
    """
    Decorator utility function to check if need to use loader context and wrap
    function into it if so. Need it cause after salt >3003 calling __salt__
    from within the threads requires to use loader context.

    Any function that called by worker thread that uses ``__salt__`` dunder must
    be wrapped by this decorator.

    :param loader: (obj) ``__salt__.loader`` object instance
    """

    def wrapper(*args, **kwargs):
        loader = kwargs.pop("loader", None)

        if HAS_LOADER_CONTEXT and loader is not None:
            with loader_context(loader):
                return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    return wrapper


def _load_custom_task_fun_from_text(function_text, function_name):
    """
    Helper function to load custom function code from text using
    Python ``exec`` built-in function
    """
    log.debug(
        "Nornir-proxy PID {} loading '{}' task function from master {}".format(
            os.getpid(), function_name, function_text
        )
    )
    assert function_name in function_text

    data = {}
    globals_dict = {
        "__builtins__": __builtins__,
        "False": False,
        "True": True,
        "None": None,
    }

    # load function by running exec
    exec(compile(function_text, "<string>", "exec"), globals_dict, data)

    # add extracted functions to globals for recursion to work
    globals_dict.update(data)

    return data[function_name]


def _file_download(url, saltenv="base"):
    """
    Helper function to download files from salt master or other locations.

    :param url: string url to file location
    :param saltenv: saltenv name to download files from
    """
    with nornir_data["salt_download_lock"]:
        file_path = __salt__["cp.get_url"](url, dest="", saltenv=saltenv)
        if file_path is False:
            raise CommandExecutionError(
                "Salt-Nornir proxy pid {}, '{}' file download failed, saltenv '{}'".format(
                    nornir_data["stats"]["main_process_pid"], url, saltenv
                )
            )
    with open(file_path, mode="r", encoding="utf-8") as f:
        return f.read()


@_use_loader_context
def _get_or_import_task_fun(plugin):
    """
    Tries to get task function from globals() dictionary,
    if its not there tries to import task and inject it
    in globals() dictionary for future reference.
    """
    task_fun = plugin.split(".")[-1]
    if task_fun in globals() and plugin == globals()[task_fun].__module__:
        task_function = globals()[task_fun]
    # check if plugin referring to file on master, download and compile it if so
    elif _is_url(plugin):
        function_text = None
        function_text = _file_download(plugin)
        task_function = _load_custom_task_fun_from_text(function_text, "task")
    else:
        log.debug(
            "Nornir-proxy PID {}, _get_or_import_task_fun, importing {} from {}".format(
                os.getpid(), task_fun, plugin
            )
        )
        # import task function, below two lines are the same as
        # from nornir.plugins.tasks import task_fun as task_function
        module = __import__(plugin, fromlist=[""])
        task_function = getattr(module, task_fun)
        # save loaded task function to globals
        globals()[task_fun] = task_function
    return task_function


def _watchdog(loader):
    """
    Thread worker to maintain nornir proxy process and it's children livability.
    """
    child_processes = {}
    while nornir_data["initialized"]:
        nornir_data["stats"]["watchdog_runs"] += 1
        # run FD limit checks
        try:
            if HAS_RESOURCE_LIB:
                fd_in_use = len(os.listdir("/proc/{}/fd/".format(os.getpid())))
                fd_limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
                # restart if reached 95% of available file descriptors limit
                if fd_in_use > fd_limit * 0.95:
                    log.critical(
                        "Nornir-proxy MAIN PID {} watchdog, file descriptors in use: {}, limit: {}, reached 95% threshold, shutting down".format(
                            os.getpid(), fd_in_use, fd_limit
                        )
                    )
                    if shutdown():
                        kill_nornir()
        except:
            log.error(
                "Nornir-proxy MAIN PID {} watchdog, file descritors usage check error: {}".format(
                    os.getpid(), traceback.format_exc()
                )
            )
        # run memory checks
        try:
            mem_usage = minion_process.memory_info().rss / 1024000
            if mem_usage > nornir_data["memory_threshold_mbyte"]:
                if nornir_data["memory_threshold_action"] == "log":
                    log.warning(
                        "Nornir-proxy {} MAIN PID {} watchdog, '{}' memory_threshold_mbyte exceeded, memory usage {}MByte".format(
                            nornir_data["stats"]["proxy_minion_id"],
                            os.getpid(),
                            nornir_data["memory_threshold_mbyte"],
                            mem_usage,
                        )
                    )
                elif nornir_data["memory_threshold_action"] == "restart":
                    if shutdown():
                        kill_nornir()
        except:
            log.error(
                "Nornir-proxy MAIN PID {} watchdog, memory usage check error: {}".format(
                    os.getpid(), traceback.format_exc()
                )
            )
        # check if worker thread is alive and restart it if not
        try:
            for nr in nornir_data["nrs"]:
                if not nr["worker_thread"].is_alive():
                    nr["worker_thread"] = threading.Thread(
                        target=_worker, args=(nr, loader)
                    )
                    nr["worker_thread"].start()
        except:
            log.error(
                "Nornir-proxy MAIN PID {} watchdog, worker thread is_alive check error: {}".format(
                    os.getpid(), traceback.format_exc()
                )
            )
        # Handle child processes lifespan
        try:
            for p in multiprocessing.active_children():
                cpid = p.pid
                if not p.is_alive():
                    _ = child_processes.pop(cpid, None)
                elif cpid not in child_processes:
                    child_processes[cpid] = {
                        "first_seen": time.time(),
                        "process": p,
                        "age": 0,
                    }
                elif (
                    child_processes[cpid]["age"] > nornir_data["child_process_max_age"]
                ):
                    # kill process
                    os.kill(cpid, signal.SIGKILL)
                    nornir_data["stats"]["watchdog_child_processes_killed"] += 1
                    log.info(
                        "Nornir-proxy MAIN PID {} watchdog, terminating child PID {}: {}".format(
                            os.getpid(), cpid, child_processes[cpid]
                        )
                    )
                    _ = child_processes.pop(cpid, None)
                else:
                    child_processes[cpid]["age"] = (
                        time.time() - child_processes[cpid]["first_seen"]
                    )
        except:
            log.error(
                "Nornir-proxy MAIN PID {} watchdog, child processes error: {}".format(
                    os.getpid(), traceback.format_exc()
                )
            )
        # check if need to tear down connections that are idle
        try:
            # iterate over Nornir worker instances
            timeout = nornir_data["connections_idle_timeout"]
            for nr in nornir_data["nrs"]:
                # get a list of hosts that aged beyond idle timeout
                hosts_to_disconnect = []
                if timeout > 1:
                    for host_name in list(nr["worker_connections"].keys()):
                        conn_data = nr["worker_connections"][host_name]
                        age = time.time() - conn_data["last_use_timestamp"]
                        if age > timeout:
                            hosts_to_disconnect.append(host_name)
                # run task to disconnect connections for aged hosts
                if hosts_to_disconnect and nr["connections_lock"].acquire(block=False):
                    try:
                        aged_hosts = FFun(nr["nr"], FL=hosts_to_disconnect)
                        aged_hosts.run(
                            task=_get_or_import_task_fun(
                                "nornir_salt.plugins.tasks.connections"
                            ),
                            call="close",
                        )
                        log.debug(
                            "Nornir-proxy MAIN PID {} watchdog, nornir-worker-{}, disconnected: {}".format(
                                os.getpid(), nr["worker_id"], hosts_to_disconnect
                            )
                        )
                        # remove disconnected hosts from stats
                        for h_name in hosts_to_disconnect:
                            nr["worker_connections"].pop(h_name)
                    except Exception as e:
                        raise e
                    finally:
                        nr["connections_lock"].release()
        except:
            log.error(
                "Nornir-proxy MAIN PID {} watchdog, connections idle check error: {}".format(
                    os.getpid(), traceback.format_exc()
                )
            )
        # keepalive connections and clean up dead connections if any
        try:
            for nr in nornir_data["nrs"]:
                if nornir_data["proxy_always_alive"] and nr["connections_lock"].acquire(
                    block=False
                ):
                    log.debug(
                        "Nornir-proxy {} MAIN PID {} watchdog, nornir-worker-{} connections keepalive".format(
                            nornir_data["stats"]["proxy_minion_id"],
                            nornir_data["stats"]["main_process_pid"],
                            nr["worker_id"],
                        )
                    )
                    try:
                        stats = HostsKeepalive(nr["nr"])
                        nornir_data["stats"][
                            "watchdog_dead_connections_cleaned"
                        ] += stats["dead_connections_cleaned"]
                    except Exception as e:
                        raise e
                    finally:
                        nr["connections_lock"].release()
        except:
            log.error(
                "Nornir-proxy MAIN PID {} watchdog, HostsKeepalive check error: {}".format(
                    os.getpid(), traceback.format_exc()
                )
            )

        time.sleep(nornir_data["watchdog_interval"])


def _worker(wkr_data, loader):
    """
    Target function for worker thread to run jobs from
    jobs_queue submitted by execution module processes

    :param wkr_data: (dict) dictionary that contain nornir instance and other parameters
    :param loader: (obj or None) SaltStack loader context object
    """
    worker_id = wkr_data["worker_id"]  # get worker ID integer
    ppid = nornir_data["stats"]["main_process_pid"]
    while nornir_data["initialized"]:
        wkr_data["is_busy"].clear()  # no longer busy
        time.sleep(0.01)
        job, output = None, None
        try:
            # try to get job from worker specific queue
            try:
                job = wkr_data["worker_jobs_queue"].get(block=True, timeout=0.1)
            except queue.Empty:
                # check if all higher order workers are busy
                if all(
                    [
                        wkr["is_busy"].is_set()
                        for wkr in nornir_data["nrs"][: worker_id - 1]
                    ]
                ):
                    # try to get job from shared queue
                    job = nornir_data["jobs_queue"].get(block=True, timeout=0.1)
                else:
                    continue
            # got the job, I am busy now
            wkr_data["is_busy"].set()
            wkr_data["worker_jobs_started"] += 1
            # check if its a call for a special task
            if job["task_fun"] == "test":
                wkr_data["worker_jobs_completed"] += 1
                nornir_data["res_queue"].put(
                    {"output": True, "identity": job["identity"]}
                )
                continue
            if job["task_fun"] == "clear_dcache":
                output = _clear_dcache(
                    nr=wkr_data["nr"], cache_keys=job["kwargs"].get("cache_keys")
                )
                wkr_data["worker_jobs_completed"] += 1
                nornir_data["res_queue"].put(
                    {"output": output, "identity": job["identity"]}
                )
                continue
            if job["task_fun"] == "refresh":
                wkr_data["worker_jobs_completed"] += 1
                nornir_data["res_queue"].put(
                    {"output": True, "identity": job["identity"]}
                )
                # loader used by decorator, loader_ used by _refresh_nornir itself
                _refresh_nornir(loader=loader, loader_=loader, **job["kwargs"])
                # stop this worker thread as another one will be started
                break
            if job["task_fun"] == "shutdown":
                wkr_data["worker_jobs_completed"] += 1
                nornir_data["res_queue"].put(
                    {"output": True, "identity": job["identity"]}
                )
                # stop this worker thread as another one will be started
                shutdown()
                break
            if job["task_fun"] == "inventory":
                output = InventoryFun(wkr_data["nr"], **job["kwargs"])
                wkr_data["worker_jobs_completed"] += 1
                nornir_data["res_queue"].put(
                    {"output": output, "identity": job["identity"]}
                )
                continue
            # execute nornir task
            task_fun = _get_or_import_task_fun(job["task_fun"], loader=loader)
            log.info(
                "Nornir-proxy MAIN PID {} starting task '{}'".format(ppid, job["name"])
            )
            # lock connections and run the task
            with wkr_data["connections_lock"]:
                output = run(
                    task=task_fun,
                    loader=loader,
                    identity=job["identity"],
                    name=job["name"],
                    nr=wkr_data["nr"],
                    wkr_data=wkr_data,
                    **job["kwargs"],
                )
            wkr_data["worker_jobs_completed"] += 1
        except queue.Empty:
            continue
        except:
            tb = traceback.format_exc()
            output = "Nornir-proxy MAIN PID {} job failed: {}, error:\n'{}'".format(
                ppid, job, tb
            )
            log.error(output)
            wkr_data["worker_jobs_failed"] += 1
        # submit job results in results queue
        nornir_data["res_queue"].put({"output": output, "identity": job["identity"]})
        del job, output
        # close connections to devices if proxy_always_alive is False
        if (
            nornir_data["proxy_always_alive"] is False
            or nornir_data["connections_idle_timeout"] == 0
        ):
            try:
                wkr_data["nr"].close_connections(on_good=True, on_failed=True)
            except:
                log.error(
                    "Nornir-proxy MAIN PID {} worker thread, Nornir close_connections error: {}".format(
                        ppid, traceback.format_exc()
                    )
                )


@_use_loader_context
def _fire_events(result):
    """
    Helper function to iterate over results and fire event for
    tasks that either has failed=True or success=False.

    :param result: (obj) Nornir AggregatedResult object
    """
    results_list = ResultSerializer(result, to_dict=False, add_details=True)
    for res in results_list:
        if res.get("failed") is True or res.get("success") is False:
            __salt__["event.send"](
                tag="nornir-proxy/{proxy_id}/{host}/task/failed/{name}".format(
                    proxy_id=nornir_data["stats"]["proxy_minion_id"],
                    host=res["host"],
                    name=res["name"],
                ),
                data=res,
            )


@_use_loader_context
def _download_and_render_files(hosts, render, kwargs, ignore_keys):
    """
    Helper function to iterate over hosts and render content for each of them.

    Rendering results saved in host's ``__task__`` attribute as a dictionary
    keyed by the items from ``render`` list.

    :param hosts: (obj) Nornir object with hosts inventory
    :param render: (list or str) list of keys or comma separated string
        of key names from kwargs to run rendering for
    :param kwargs: (dict) dictionary with data to render
    :param ignore_keys: (list or str) key names to ignore rendering for
    :return: dictionary of failed hosts
    """
    context = kwargs.pop("context", {})
    saltenv = kwargs.pop("saltenv", "base")
    defaults = kwargs.pop("defaults", {})
    template_engine = kwargs.pop("template_engine", "jinja")
    render = render.split(",") if isinstance(render, str) else render
    ignore_keys = (
        ignore_keys.split(",") if isinstance(ignore_keys, str) else ignore_keys
    )
    hosts_failed_prep = {}  # dictionary keyed by host name and error message

    def __render(data):
        # do initial data rendering
        ret = __salt__["file.apply_template_on_contents"](
            contents=data,
            template=template_engine,
            context=context,
            defaults=defaults,
            saltenv=saltenv,
        )
        # check if per-host data was provided, e.g. filename=salt://path/to/{{ host.name }}_cfg.txt
        if _is_url(ret):
            content = _file_download(ret, saltenv)
            # render final file
            ret = __salt__["file.apply_template_on_contents"](
                contents=content,
                template=template_engine,
                context=context,
                defaults=defaults,
                saltenv=saltenv,
            )
        return ret

    for host_name, host_object in hosts.inventory.hosts.items():
        context.update({"host": host_object})
        host_object.data["__task__"] = {}
        for key in render:
            if not kwargs.get(key) or key in ignore_keys:
                continue
            try:
                value = kwargs[key]
                # if string given use it as is
                if isinstance(value, str):
                    rendered = __render(value)
                # check if list of strings given
                elif isinstance(value, (list, tuple)):
                    rendered = [__render(item) for item in value]
                # check if given dictionary keyed by host names
                elif isinstance(value, dict):
                    rendered = __render(value[host_name])
                else:
                    raise TypeError(
                        "Unsupported type for render key '{}': '{}', supported str, list, tuple, dict".format(
                            key, type(value)
                        )
                    )
            except:
                tb = traceback.format_exc()
                hosts_failed_prep[host_name] = tb
                continue

            log.debug(
                "Nornir-proxy MAIN PID {} worker thread, rendered '{}' '{}' data for '{}' host".format(
                    os.getpid(), key, type(value), host_name
                )
            )
            host_object.data["__task__"][key] = rendered

    # clean up kwargs from render keys to force tasks to use hosts's __task__ attribute
    for key in render:
        _ = kwargs.pop(key) if key in kwargs else None

    return hosts_failed_prep


@_use_loader_context
def _download_files(download, kwargs):
    """
    Helper function to download files content from Salt Master.

    :param download: (list or str) list of keys or comma separated string
        of key names from kwargs to download
    :param kwargs: (dict) dictionary with data to download
    """
    saltenv = kwargs.get("saltenv", "base")
    download = download.split(",") if isinstance(download, str) else download

    # iterate over download keys and download data from master
    for key in download:
        if not _is_url(kwargs.get(key)):
            continue

        # download data
        content = _file_download(kwargs[key], saltenv)
        kwargs[key] = content

        log.debug(
            "Nornir-proxy MAIN PID {} worker thread, donwloaded '{}' data from Master".format(
                os.getpid(), key
            )
        )


def _add_processors(kwargs, loader, identity, nr, worker_id):
    """
    Helper function to extract processors arguments and add processors
    to Nornir.

    :param kwargs: (dict) dictionary with kwargs
    :param loader: (obj) SaltStack loader context
    :param identity: (dict) task identity dictionary for SaltEventProcessor
    :param worker_id: (int) Nornir worker ID
    :param nr: (obj) Nornir object to add processors to
    :return: (obj) Nornir object
    """
    processors = []

    # get parameters
    tf = kwargs.pop("tf", None)  # to file
    tf_skip_failed = kwargs.pop("tf_skip_failed", False)  # to file
    tests = kwargs.pop("tests", None)  # tests
    remove_tasks = kwargs.pop("remove_tasks", True)  # tests and/or run_ttp
    failed_only = kwargs.pop("failed_only", False)  # tests
    diff = kwargs.pop("diff", "")  # diff processor
    last = kwargs.pop("last", 1) if diff else None  # diff processor
    dp = kwargs.pop("dp", [])  # data processor
    xml_flake = kwargs.pop("xml_flake", "")  # data processor xml_flake function
    match = kwargs.pop("match", "")  # data processor match function
    before = kwargs.pop("before", 0)  # data processor match function
    run_ttp = kwargs.pop("run_ttp", None)  # data processor run_ttp function
    ttp_structure = kwargs.pop(
        "ttp_structure", "flat_list"
    )  # data processor run_ttp function
    xpath = kwargs.pop("xpath", "")  # xpath DataProcessor
    jmespath = kwargs.pop("jmespath", "")  # jmespath DataProcessor
    iplkp = kwargs.pop("iplkp", "")  # iplkp - ip lookup - DataProcessor
    ntfsm = kwargs.pop("ntfsm", False)  # ntfsm - ntc-templates TextFSM parsing
    event_progress = kwargs.pop(
        "event_progress", nornir_data["event_progress_all"]
    )  # SaltEventProcessor

    # add processors if any
    if event_progress:
        processors.append(
            SaltEventProcessor(
                __salt__=__salt__,
                loader=loader,
                proxy_id=nornir_data["stats"]["proxy_minion_id"],
                identity=identity,
                worker_id=worker_id,
            )
        )
    if dp:
        processors.append(DataProcessor(dp))
    if iplkp:
        processors.append(
            DataProcessor(
                [
                    {
                        "fun": "iplkp",
                        "use_dns": True if iplkp == "dns" else False,
                        "use_csv": iplkp if iplkp else False,
                    }
                ]
            )
        )
    if xml_flake:
        processors.append(DataProcessor([{"fun": "xml_flake", "pattern": xml_flake}]))
    if xpath:
        processors.append(
            DataProcessor(
                [{"fun": "xpath", "expr": xpath, "recover": True, "rm_ns": True}]
            )
        )
    if jmespath:
        processors.append(DataProcessor([{"fun": "jmespath", "expr": jmespath}]))
    if match:
        processors.append(
            DataProcessor([{"fun": "match", "pattern": match, "before": before}])
        )
    if run_ttp:
        processors.append(
            DataProcessor(
                [
                    {
                        "fun": "run_ttp",
                        "template": run_ttp,
                        "res_kwargs": {"structure": ttp_structure},
                        "remove_tasks": remove_tasks,
                    }
                ]
            )
        )
    if ntfsm:
        processors.append(DataProcessor([{"fun": "ntfsm"}]))
    if tests:
        processors.append(
            TestsProcessor(tests, remove_tasks=remove_tasks, failed_only=failed_only)
        )
    if diff:
        processors.append(
            DiffProcessor(
                diff=diff,
                last=int(last),
                base_url=nornir_data["files_base_path"],
                index=nornir_data["stats"]["proxy_minion_id"],
            )
        )
    # append ToFileProcessor as the last one in the sequence
    if tf and isinstance(tf, str):
        processors.append(
            ToFileProcessor(
                tf=tf,
                base_url=nornir_data["files_base_path"],
                index=nornir_data["stats"]["proxy_minion_id"],
                max_files=nornir_data["files_max_count"],
                skip_failed=tf_skip_failed,
                tf_index_lock=nornir_data["tf_index_lock"],
            )
        )

    return nr.with_processors(processors)


def _cache_task_results_to_host_data(hosts, results, cache_key):
    """
    Function to save task results to host data under cache key.

    :param hosts: (obj) Nornir object
    :param results: (dict, str, list) Results to save
    :param cache_key: (str or bool) key to save results under, if True
        ``cache_key`` set equal to ``hcache``
    """
    cache_key = cache_key if isinstance(cache_key, str) else "hcache"
    log.debug(
        "salt-nornir:hcache saving results in hosts data under '{}' key".format(
            cache_key
        )
    )

    # form a list of hosts to add hcache to
    hosts_to_cache = list(hosts.inventory.hosts.keys())

    # iteare over Nornir instances and cache results to hosts
    for nr in nornir_data["nrs"]:
        # iterate over hosts and save results to data cache
        for host_name, host_object in nr["nr"].inventory.hosts.items():
            if host_name not in hosts_to_cache:
                continue
            # add metadata on cache keys so that can clean them up
            host_object.data.setdefault("_hcache_keys_", [])
            if cache_key not in host_object.data["_hcache_keys_"]:
                host_object.data["_hcache_keys_"].append(cache_key)
            # cache results
            host_object.data.setdefault(cache_key, {})
            # dictionary results should be keyed by host name
            if isinstance(results, dict):
                host_object.data[cache_key].update(results.get(host_name, {}))
            # save string results as is
            elif isinstance(results, str):
                host_object.data[cache_key] = results
            # convert list results back to dictionary keyd by task name
            elif isinstance(results, list):
                host_object.data[cache_key].update(
                    {i["name"]: i["result"] for i in results if i["host"] == host_name}
                )
            else:
                log.error(
                    "salt-nornir:hcache unsupported results type '{}'".format(
                        type(results)
                    )
                )

    log.debug(
        "salt-nornir:hcache saved results in hosts data under '{}' key".format(
            cache_key
        )
    )


def _cache_all_task_results_to_defaults_data(results, cache_key):
    """
    Function to save full task results to default data under cache key.

    :param results: (any) Results to save
    :param cache_key: (str or bool) key to save results under, if True
        ``cache_key`` set equal to ``dcache``
    """
    cache_key = cache_key if isinstance(cache_key, str) else "dcache"
    log.debug(
        "salt-nornir:dcache saving results in defaults data under '{}' key".format(
            cache_key
        )
    )

    # add metadata about cache keys so that can clean them up later on
    for nr in nornir_data["nrs"]:
        nr["nr"].inventory.defaults.data.setdefault("_dcache_keys_", [])
        if cache_key not in nr["nr"].inventory.defaults.data["_dcache_keys_"]:
            nr["nr"].inventory.defaults.data["_dcache_keys_"].append(cache_key)

        # cache results
        nr["nr"].inventory.defaults.data[cache_key] = results
    log.debug(
        "salt-nornir:dcache saved results in defaults data under '{}' key".format(
            cache_key
        )
    )


def _clear_dcache(nr, cache_keys=None):
    """
    Function to clear task results cache from defaults data.

    :param cache_keys: (str) list of key names to remove
    :param nr: (obj) Nornir Instance to clear dcache for
    """
    result = {}

    # get keys to clear
    if cache_keys is None:
        # need to itearete over a copy of the keys - list() makes a copy
        cache_keys = list(nr.inventory.defaults.data.get("_dcache_keys_", []))

    # iterate over given cache keys and clean them up from data
    for key in cache_keys:
        if key in nr.inventory.defaults.data and key in nr.inventory.defaults.data.get(
            "_dcache_keys_", []
        ):
            nr.inventory.defaults.data.pop(key)
            nr.inventory.defaults.data["_dcache_keys_"].remove(key)
            result[key] = True
        else:
            result[key] = False

    return result


@_use_loader_context
def _refresh_nornir(loader_, workers_only=False, **kwargs):
    """
    Function to re-initialize Nornir proxy with latest pillar data.

    If ``workers_only`` is False, this function calls ``shutdown`` function, gets latest
    modules and pillar from master and calls ``init`` function to re-instantiate Nornir
    workers objects, watchdog thread and queues.

    If ``workers_only`` is True, only refreshes Nornir workers without closing queues and
    killing child processes, resulting in inventory refresh without interrupting jobs
    execution process.

    It takes about a minute to finish refresh process.

    :param loader_: (obj) ``__salt__.loader`` object instance for ``init``
    :param workers_only: (bool) if True, only refreshes Nornir workers
    """
    if workers_only:
        log.info(
            "Nornir-proxy MAIN PID {}, doing inventory only refresh".format(os.getpid())
        )
        # trigger worker and watchdogs threads to stop
        nornir_data["initialized"] = False
        # close connections to devices and delete old Nornir Objects
        while nornir_data["nrs"]:
            nr = nornir_data["nrs"].pop()
            nr["nr"].close_connections(on_good=True, on_failed=True)
            del nr
        # signal to init() method that needs to keep queues intact
        init_queues = False
    elif shutdown():
        log.info("Nornir-proxy MAIN PID {}, doing hard refresh".format(os.getpid()))
        init_queues = True
    else:
        return False

    # refresh all modules
    __salt__["saltutil.sync_all"]()
    # refresh in memory pillar
    __salt__["saltutil.refresh_pillar"]()
    # get latest pillar data from master
    __opts__["pillar"] = __salt__["pillar.items"]()
    __opts__["proxy"] = __opts__["pillar"]["proxy"]
    log.debug(
        "Nornir-proxy MAIN PID {}, refreshing, new proxy data: {}".format(
            os.getpid(), __opts__["proxy"]
        )
    )
    log.debug(
        "Nornir-proxy MAIN PID {}, refreshing, new pillar data: {}".format(
            os.getpid(), __opts__["pillar"]
        )
    )
    # re-init proxy module
    init(__opts__, loader_, init_queues)
    # refresh in memory pillar one more time for salt to read updated data
    __salt__["saltutil.refresh_pillar"]()
    log.info("Nornir-proxy MAIN PID {}, process refreshed!".format(os.getpid()))

    return True


def _rm_tasks_data_from_hosts(hosts):
    """
    Helper function to remove __task__ data from hosts inventory produced by rendering.

    :param hosts: (obj) Nornir object
    """
    for host_name, host_object in hosts.inventory.hosts.items():
        _ = host_object.data.pop("__task__", None)


def _update_worker_connections(hosts, wkr_data):
    """
    Helper function to update stats for worker's hosts connections.

    :param hosts: (obj) Nornir Object filtered instance
    :param wkr_data: (dict) worker data dictionary
    """
    for host_name in hosts.inventory.hosts:
        wkr_data["worker_connections"].setdefault(host_name, {})
        wkr_data["worker_connections"][host_name]["last_use_timestamp"] = time.time()


def _add_hosts_failed_prep_to_result(agg_result, hosts_failed_prep):
    """
    Helper function to add hosts that failed prep steps to overall results
    together with error message.

    :param result: (Obj) Nornir AggregatedResult object
    :param hosts_failed_prep: (dict) dictionary keyed by host name and error message
    """
    for host_name, error in hosts_failed_prep.items():
        agg_result[host_name] = MultiResult(name=None)
        agg_result[host_name].append(
            Result(
                host=None,
                result=error,
                exception=error,
                failed=True,
                name=agg_result.name.split(".")[-1],  # yields task function name
            )
        )


def _update_nornir_worker_stats(wkr_data, nr_results):
    """
    Helper function to calculate tasks stats.

    :param wkr_data: (dict) Nornir worker dictionary
    :param nr_results: (obj) Nornir AggregatedResult object
    """
    wkr_data["worker_hosts_tasks_failed"] += len(wkr_data["nr"].data.failed_hosts)
    for hostname, results in nr_results.items():
        for i in results:
            if i.exception or i.failed:
                wkr_data["worker_tasks_failed"] += 1
            elif (
                isinstance(i.result, str)
                and "Traceback (most recent call last)" in i.result
            ):
                wkr_data["worker_tasks_failed"] += 1
            # dont count tasks with skip_results flag
            elif not (hasattr(i, "skip_results") and i.skip_results is True):
                wkr_data["worker_tasks_completed"] += 1


# -----------------------------------------------------------------------------
# callable functions
# -----------------------------------------------------------------------------


def list_hosts(**kwargs):
    """
    Return a list of hosts managed by this Nornir instance

    :param Fx: filters to filter hosts
    """
    # get a list of filtered hosts
    filtered_hosts, has_filter = FFun(
        nornir_data["nrs"][0]["nr"], kwargs=kwargs, check_if_has_filter=True
    )

    # check if nornir_filter_required is True but no filter
    if nornir_data["nornir_filter_required"] is True and has_filter is False:
        raise CommandExecutionError(
            "Nornir-proxy 'nornir_filter_required' setting is True but no filter provided"
        )

    return InventoryFun(filtered_hosts, call="list_hosts", **kwargs)


def run(task, loader, identity, name, nr, wkr_data, **kwargs):
    """
    Function for worker Thread to run Nornir tasks.

    :param task: (obj) callable task function
    :param loader: (obj) ``__salt__.loader`` object instance
    :param identity: (dict) Task results queue identity for SaltEventProcessor
    :param kwargs: (dict) passed to ``task.run`` after extracting CLI arguments
    :param name: (str) Nornir task name to run
    :param nr: (obj) Worker instance Nornir object
    """
    # extract attributes
    add_details = kwargs.pop("add_details", False)  # ResultSerializer
    to_dict = kwargs.pop("to_dict", True)  # ResultSerializer
    table = kwargs.pop("table", {})  # tabulate
    headers = kwargs.pop("headers", "keys")  # tabulate
    headers_exclude = kwargs.pop("headers_exclude", [])  # tabulate
    sortby = kwargs.pop("sortby", "host")  # tabulate
    reverse = kwargs.pop("reverse", False)  # tabulate
    dump = kwargs.pop("dump", None)  # dump results to file
    download = kwargs.pop("download", ["run_ttp", "iplkp"])  # download data
    render = kwargs.pop(
        "render", ["config", "data", "filter", "filter_", "filters", "filename"]
    )  # render data
    event_failed = kwargs.pop("event_failed", False)  # events
    hcache = kwargs.pop("hcache", False)  # cache task results
    dcache = kwargs.pop("dcache", False)  # cache task results
    hosts_failed_prep = {}

    # add tf_index_lock to control tf index access
    if "tf_index_lock" in kwargs:
        kwargs["tf_index_lock"] = nornir_data["tf_index_lock"]

    # only RetryRunner supports connection_name
    if nr.config.runner.plugin != "RetryRunner":
        _ = kwargs.pop("connection_name", None)

    # set dry_run argument
    nr.data.dry_run = kwargs.get("dry_run", False)

    # reset failed hosts if any
    nr.data.reset_failed_hosts()

    # download files
    if download:
        _download_files(download, kwargs, loader=loader)

    # add processors
    nr_with_processors = _add_processors(
        kwargs, loader=loader, identity=identity, nr=nr, worker_id=wkr_data["worker_id"]
    )

    # Filter hosts to run tasks for
    hosts, has_filter = FFun(
        nr_with_processors, kwargs=kwargs, check_if_has_filter=True
    )

    # check if nornir_filter_required is True but no filter
    if nornir_data["nornir_filter_required"] is True and has_filter is False:
        raise CommandExecutionError(
            "Nornir-proxy 'nornir_filter_required' setting is True but no filter provided"
        )

    # download and render files
    if render:
        hosts_failed_prep = _download_and_render_files(
            hosts, render, kwargs, ignore_keys=download, loader=loader
        )

    # update hosts connections ages
    _update_worker_connections(hosts, wkr_data)

    # exclude hosts that failed prep steps
    hosts = FFun(hosts, FL=list(hosts_failed_prep.keys()), FN=True)

    # run tasks
    result = hosts.run(
        task, name=name, **{k: v for k, v in kwargs.items() if not k.startswith("_")}
    )

    # add back hosts that failed prep but with error message
    _add_hosts_failed_prep_to_result(result, hosts_failed_prep)

    # post clean-up - remove tasks rendered data from hosts inventory
    if render:
        _rm_tasks_data_from_hosts(hosts)

    # fire events for failed tasks if requested to do so
    if event_failed:
        _fire_events(result, loader=loader)

    # calculate task stats
    _update_nornir_worker_stats(wkr_data, result)

    # form return results
    if table:
        ret = TabulateFormatter(
            result,
            tabulate=table,
            headers=headers,
            headers_exclude=headers_exclude,
            sortby=sortby,
            reverse=reverse,
        )
    else:
        ret = ResultSerializer(result, to_dict=to_dict, add_details=add_details)

    # check if need to cache task results to inventory data
    if hcache:
        _cache_task_results_to_host_data(hosts, ret, hcache)
    if dcache:
        _cache_all_task_results_to_defaults_data(ret, dcache)

    # save all results to file
    if dump:
        DumpResults(
            results=ret,
            filegroup=dump,
            base_url=nornir_data["files_base_path"],
            index=nornir_data["stats"]["proxy_minion_id"],
            max_files=nornir_data["files_max_count"],
            proxy_id=nornir_data["stats"]["proxy_minion_id"],
        )

    return ret


def execute_job(task_fun, kwargs, identity):
    """
    Function to submit job request to Nornir Proxy minion jobs queue,
    wait for job to be completed and return results.

    :param task_fun: (str) name of nornir task function/plugin to import and run
    :param kwargs: (dict) any arguments to submit to Nornir task ``**kwargs``
    :param identity: (dict) dictionary of uuid4, jid, function_name keys

    ``identity`` parameter used to identify job results in results queue and
    must be unique for each submitted job.
    """
    # broadcast job to all nornir workers
    if kwargs.get("worker") == "all":
        _ = kwargs.pop("worker")
        identities = []
        results = []
        # add jobs to the queue for each worker
        for nr in nornir_data["nrs"]:
            # make sure each worker receives its own copy of identity and kwargs
            job_identity = copy.deepcopy(identity)
            job_kwargs = copy.deepcopy(kwargs)
            job_identity["worker"] = nr["worker_id"]
            identities.append(job_identity)
            nr["worker_jobs_queue"].put(
                {
                    "task_fun": task_fun,
                    "kwargs": job_kwargs,
                    "identity": job_identity,
                    "name": task_fun,
                }
            )
        # wait for jobs to complete and return results
        start_time = time.time()
        while (time.time() - start_time) < nornir_data["job_wait_timeout"]:
            time.sleep(0.1)
            try:
                res = nornir_data["res_queue"].get(block=True, timeout=0.1)
                if res["identity"] in identities:
                    results.append(res)
                else:
                    nornir_data["res_queue"].put(res)
            except queue.Empty:
                continue
            except OSError:
                raise CommandExecutionError(
                    f"Nornir-proxy failed all-workers-job '{identity}', jobs queues closed "
                    f"while main process refreshing, traceback:\n{traceback.format_exc()}"
                )
            # check if collected results from all workers
            if len(results) == nornir_data["nornir_workers"]:
                break
        else:
            raise TimeoutError(
                "Nornir-proxy MAIN PID {}, identities '{}', {}s job_wait_timeout expired.".format(
                    os.getpid(), identities, nornir_data["job_wait_timeout"]
                )
            )
        return {
            "nornir-worker-{}".format(r["identity"]["worker"]): r["output"]
            for r in results
        }
    # submit job to certain worker's queue only
    elif kwargs.get("worker"):
        if kwargs["worker"] not in list(range(1, len(nornir_data["nrs"]) + 1)):
            return "Error: Non existing worker '{}'; worker IDs 1 - {}".format(
                kwargs["worker"], len(nornir_data["nrs"])
            )
        nr = nornir_data["nrs"][kwargs.pop("worker") - 1]
        identity["worker"] = nr["worker_id"]
        # add job to the worker queue
        nr["worker_jobs_queue"].put(
            {
                "task_fun": task_fun,
                "kwargs": kwargs,
                "identity": identity,
                "name": task_fun,
            }
        )
    # submit job to shared queue for one of the workers to execute
    else:
        nornir_data["jobs_queue"].put(
            {
                "task_fun": task_fun,
                "kwargs": kwargs,
                "identity": identity,
                "name": task_fun,
            }
        )

    # wait for job to complete and return results
    start_time = time.time()
    while (time.time() - start_time) < nornir_data["job_wait_timeout"]:
        time.sleep(0.1)
        try:
            res = nornir_data["res_queue"].get(block=True, timeout=0.1)
            if res["identity"] == identity:
                break
            else:
                nornir_data["res_queue"].put(res)
        except queue.Empty:
            continue
        except OSError:
            raise CommandExecutionError(
                f"Nornir-proxy failed job '{identity}', jobs queues closed "
                f"while main process refreshing, traceback:\n{traceback.format_exc()}"
            )
    else:
        raise TimeoutError(
            "Nornir-proxy MAIN PID {}, identity '{}', {}s job_wait_timeout expired.".format(
                os.getpid(), identity, nornir_data["job_wait_timeout"]
            )
        )
    return res["output"]


def stats(*args, **kwargs):
    """
    Function to gather and return stats about Nornir proxy process.

    :param stat: name of stat to return, returns all by default

    Returns dictionary with these parameters:

    * ``proxy_minion_id`` - if of this proxy minion
    * ``main_process_is_running`` - set to 0 if not running and to 1 otherwise
    * ``main_process_start_time`` - ``time.time()`` function to indicate process start time in ``epoch``
    * ``main_process_start_date`` - ``time.ctime()`` function date to indicate process start time
    * ``main_process_uptime_seconds`` - int, main proxy minion process uptime
    * ``main_process_ram_usage_mbyte`` - int, RAM usage
    * ``main_process_pid`` - main process ID i.e. PID
    * ``main_process_host`` - hostname of machine where proxy minion process is running
    * ``jobs_started`` - int, overall number of jobs started
    * ``jobs_completed`` - int, overall number of jobs completed
    * ``jobs_failed``  - int, overall number of jobs failed
    * ``jobs_job_queue_size`` - int, size of jobs queue, indicating number of jobs waiting to start
    * ``jobs_res_queue_size`` - int, size of results queue, indicating number of results waiting to be collected by child process
    * ``tasks_completed`` - overall number of completed Nornir tasks (including subtasks)
    * ``tasks_failed`` - overall number of failed Nornir tasks (including subtasks)
    * ``hosts_count`` - int, number of hosts/devices managed by this proxy minion
    * ``hosts_connections_active`` - int, overall number of connection active to devices
    * ``hosts_tasks_failed`` - overall number of hosts that failed all tasks within single job
    * ``timestamp`` - ``time.ctime()`` timestamp of ``stats`` function run
    * ``watchdog_runs`` - int, overall number of watchdog thread runs
    * ``watchdog_child_processes_killed`` - int, number of stale child processes killed by watchdog
    * ``watchdog_dead_connections_cleaned`` - int, number of stale hosts' connections cleaned by watchdog
    * ``child_processes_count`` - int, number of child processes currently running
    * ``main_process_fd_count`` - int, number of file descriptors in use by main proxy minion process
    * ``main_process_fd_limit`` - int, fd count limit imposed by Operating System for minion process
    """
    stat = args[0] if args else kwargs.get("stat", None)
    # get File Descriptors limit and usage
    try:
        if HAS_RESOURCE_LIB:
            fd_count = len(os.listdir("/proc/{}/fd/".format(os.getpid())))
            fd_limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
    except:
        fd_count = -1
        fd_limit = -1
    # update stats
    nornir_data["stats"].update(
        {
            "main_process_ram_usage_mbyte": minion_process.memory_info().rss / 1024000,
            "main_process_fd_count": fd_count,
            "main_process_fd_limit": fd_limit,
            "timestamp": time.ctime(),
            "jobs_job_queue_size": nornir_data["jobs_queue"].qsize(),
            "jobs_res_queue_size": nornir_data["res_queue"].qsize(),
            "child_processes_count": len(multiprocessing.active_children()),
            "hosts_connections_active": sum(
                [
                    len(host.connections)
                    for nr in nornir_data["nrs"]
                    for host in nr["nr"].inventory.hosts.values()
                ]
            ),
            "hosts_connections_idle_timeout": nornir_data["connections_idle_timeout"],
            "main_process_uptime_seconds": round(
                time.time() - nornir_data["stats"]["main_process_start_time"], 3
            ),
            "nornir_workers": len(nornir_data["nrs"]),
            "jobs_started": sum([w["worker_jobs_started"] for w in nornir_data["nrs"]]),
            "jobs_completed": sum(
                [w["worker_jobs_completed"] for w in nornir_data["nrs"]]
            ),
            "tasks_completed": sum(
                [w["worker_tasks_completed"] for w in nornir_data["nrs"]]
            ),
            "tasks_failed": sum([w["worker_tasks_failed"] for w in nornir_data["nrs"]]),
            "jobs_failed": sum([w["worker_jobs_failed"] for w in nornir_data["nrs"]]),
            "hosts_tasks_failed": sum(
                [w["worker_hosts_tasks_failed"] for w in nornir_data["nrs"]]
            ),
        }
    )
    # check if need to return single stat
    if isinstance(stat, str):
        try:
            return {stat: nornir_data["stats"][stat]}
        except KeyError:
            raise CommandExecutionError(
                "Not valid stat name '{}', valid options - {}".format(
                    stat, list(nornir_data["stats"].keys())
                )
            )
    # return full stats otherwise
    else:
        return nornir_data["stats"]


def nr_version():
    """
    Function to return a report of installed packages
    and their versions, useful for troubleshooting dependencies.
    """
    try:
        from pkg_resources import working_set

    except ImportError:
        return (
            "Failed importing pkg_resources, install: python3 -m pip install setuptools"
        )

    formatter = "{:>20} : {:<20}"
    libs = {
        "scrapli": "",
        "scrapli-netconf": "",
        "scrapli-community": "",
        "paramiko": "",
        "netmiko": "",
        "napalm": "",
        "nornir": "",
        "ncclient": "",
        "nornir-netmiko": "",
        "nornir-napalm": "",
        "nornir-scrapli": "",
        "nornir-utils": "",
        "tabulate": "",
        "xmltodict": "",
        "pyyaml": "",
        "jmespath": "",
        "jinja2": "",
        "ttp": "",
        "salt-nornir": "",
        "nornir-salt": "",
        "lxml": "",
        "psutil": "",
        "salt": "",
        "pygnmi": "",
        "ttp-templates": "",
        "ntc-templates": "",
        "pyats": "",
        "cerberus": "",
        "genie": "",
        "pydantic": "",
        "python": sys.version.split(" ")[0],
    }

    # get version of packages installed
    for pkg in working_set:
        if pkg.project_name.lower() in libs:
            libs[pkg.project_name.lower()] = pkg.version

    # form report and return it
    return ("\n").join([formatter.format(k, libs[k]) for k in sorted(libs)])


def nr_data(key):
    """
    Helper function to return values from nornir_data dictionary,
    used by ``nr.cli``, ``nr.cfg`` and ``nr.nc`` execution module functions to
    retrieve default kwargs values from respective proxy settings' attributes.

    :param key: (str or list) if string return value for single key, if list
        return a dictionary keyed by items in given key list.
    """
    if isinstance(key, str):
        return nornir_data.get(key, None)
    elif isinstance(key, list):
        return {k: nornir_data.get(k, None) for k in key}
    else:
        raise TypeError(
            "salt-nornir:nr_data bad key type '{}', need string or list of strings".format(
                type(key)
            )
        )


def kill_nornir(*args, **kwargs):
    """
    This function kills Nornir process and its child process as fast as possible.

    .. warning:: this function kills main Nornir process and does not recover it
    """
    log.warning(
        "Killing Nornir-proxy MAIN PID {}".format(
            nornir_data["stats"]["main_process_pid"]
        )
    )
    # kill child processes
    for p in multiprocessing.active_children():
        if p.pid == os.getpid():
            continue
        os.kill(p.pid, signal.SIGKILL)
    # kill main process
    os.kill(nornir_data["stats"]["main_process_pid"], signal.SIGKILL)
    # kill itself if still can
    os.kill(os.getpid(), signal.SIGKILL)


def workers_utils(call):
    """
    Function to retrieve operational data for Nornir Worker instances

    :param call: (str) utility to invoke

    Supported calls:

    * ``stats`` - return worker statistics keyed by worker id with these parameters:

       * ``is_busy`` - boolean, indicates if worker doing the work
       * ``worker_jobs_completed`` - counter of completed jobs
       * ``worker_jobs_failed`` - counter of completely failed jobs
       * ``worker_connections`` - hosts' connections info
       * ``worker_jobs_queue`` - size of the worker specific jobs queue
       * ``worker_hosts_tasks_failed`` - counter of overall host failed tasks
       * ``worker_jobs_started`` - counter of started jobs

    """
    supported_calls = ["stats"]
    if call == "stats":
        ret = {}
        for w in nornir_data["nrs"]:
            # calculate connections age
            worker_connections = {
                host_name: {
                    "last_use_timestamp": conn_data["last_use_timestamp"],
                    "age": int(time.time() - conn_data["last_use_timestamp"]),
                }
                for host_name, conn_data in w["worker_connections"].items()
            }
            # form workers stats
            ret["nornir-worker-{}".format(w["worker_id"])] = {
                "is_busy": w["is_busy"].is_set(),
                "worker_jobs_completed": w["worker_jobs_completed"],
                "worker_jobs_failed": w["worker_jobs_failed"],
                "worker_tasks_completed": w["worker_tasks_completed"],
                "worker_tasks_failed": w["worker_tasks_failed"],
                "worker_connections": worker_connections,
                "worker_jobs_queue": w["worker_jobs_queue"].qsize(),
                "worker_hosts_tasks_failed": w["worker_hosts_tasks_failed"],
                "worker_jobs_started": w["worker_jobs_started"],
            }
        return ret
    else:
        raise CommandExecutionError(
            "Nornir-proxy workers_utils unsupported call - '{}', supported - '{}'".format(
                call, ", ".join(supported_calls)
            )
        )


def queues_utils(call):
    """
    Function to retrieve operational data for job queues

    :param call: (str) utility to invoke - ``results_queue_dump``

    Supported calls:

    * ``results_queue_dump`` - drain items from result queue and return their content,
        put items copies back into the queue afterwards
    """
    supported_calls = ["results_queue_dump"]
    if call == "results_queue_dump":
        ret = []
        # drain items from results queue
        while True:
            try:
                ret.append(nornir_data["res_queue"].get(block=True, timeout=0.5))
            except queue.Empty:
                break
        # put drained items copies back into the queue
        for i in ret:
            nornir_data["res_queue"].put(copy.deepcopy(i))
        return ret
    else:
        raise CommandExecutionError(
            "Nornir-proxy queues_utils unsupported call - '{}', supported - '{}'".format(
                call, ", ".join(supported_calls)
            )
        )
