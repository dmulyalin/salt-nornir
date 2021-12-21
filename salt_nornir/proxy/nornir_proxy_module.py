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
- ``proxy_always_alive`` - boolean, default is True, keep connections with devices alive or tear them down after each job
- ``job_wait_timeout`` - int, default is 600s, seconds to wait for job return until give up
- ``memory_threshold_mbyte`` - int, default is 300, value in MBytes above each to trigger ``memory_threshold_action``
- ``memory_threshold_action`` - str, default is ``log``, action to implement if ``memory_threshold_mbyte`` exceeded,
  possible actions: ``log`` - send syslog message, ``restart`` - shuts down proxy minion process.
- ``files_base_path`` - str, default is ``/var/salt-nornir/{proxy_id}/files/``, OS path to folder where to save files
  on a per-host basis using `ToFileProcessor <https://nornir-salt.readthedocs.io/en/latest/Processors/ToFileProcessor.html>_`,
- ``files_max_count`` - int, default is 5, maximum number of file version for ``tf`` argument used by
  `ToFileProcessor <https://nornir-salt.readthedocs.io/en/latest/Processors/ToFileProcessor.html#tofileprocessor-plugin>`_
- ``nr_cli`` - dictionary of default kwargs to use with ``nr.cli`` execution module function, default is ``{}``
- ``nr_cfg`` - dictionary of default kwargs to use with ``nr.cfg`` execution module function, default is ``{}``
- ``nr_nc`` - dictionary of default kwargs to use with ``nr.nc`` execution module function, default is ``{}``
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

    defaults: {}

In case if want to use other type of inventory or runner plugin can define their settings
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

Runners in Nornir define how to run tasks against hosts. If no ``runner``
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
            "task_timeout": 600
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
   * - `run`_
     - Used to run Nornir Task
   * - `shutdown`_
     - Gracefully shutdown Nornir Instance
   * - `stats`_
     - Produces a dictionary of Nornir Proxy Minion statistics

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

run
+++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.run

shutdown
++++++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.shutdown

stats
+++++

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.stats
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
    "nr": None,
    "initialized": False,
    "stats": stats_dict.copy(),
    "jobs_queue": None,
    "res_queue": None,
    "worker_thread": None,
    "watchdog_thread": None,
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


def init(opts, loader=None):
    """
    Initiate Nornir by calling InitNornir()
    """
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
    nornir_data["nr"] = InitNornir(
        logging={"enabled": False}, runner=runner_config, inventory=inventory_config
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
    nornir_data["stats"]["hosts_count"] = len(nornir_data["nr"].inventory.hosts.keys())
    # Initiate multiprocessing related queus, locks and threads
    nornir_data["connections_lock"] = multiprocessing.Lock()
    nornir_data["jobs_queue"] = multiprocessing.Queue()
    nornir_data["res_queue"] = multiprocessing.Queue()
    # if loader not None, meaning init() called by _refresh_nornir function
    if loader:
        nornir_data["worker_thread"] = threading.Thread(
            target=_worker, name="{}_worker".format(opts["id"]), args=(loader,)
        )
    # salt >3003 requires loader context to call __salt__ within threads
    elif HAS_LOADER_CONTEXT:
        nornir_data["worker_thread"] = threading.Thread(
            target=_worker,
            name="{}_worker".format(opts["id"]),
            args=(__salt__.loader(),),
        )
    # salt <3003 does not use loader context
    else:
        nornir_data["worker_thread"] = threading.Thread(
            target=_worker, name="{}_worker".format(opts["id"]), args=(None,)
        )
    nornir_data["worker_thread"].start()
    nornir_data["watchdog_thread"] = threading.Thread(
        target=_watchdog, name="{}_watchdog".format(opts["id"])
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
        # close connections to devices
        nornir_data["nr"].close_connections(on_good=True, on_failed=True)
        # close queues
        nornir_data["jobs_queue"].close()
        nornir_data["jobs_queue"].join_thread()
        nornir_data["res_queue"].close()
        nornir_data["res_queue"].join_thread()
        # kill child processes left
        for p in multiprocessing.active_children():
            os.kill(p.pid, signal.SIGKILL)
        # delete old Nornir Object
        nornir_data["nr"] = None
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
    elif plugin.startswith("salt://"):
        function_text = None
        function_text = __salt__["cp.get_file_str"](plugin, saltenv="base")
        if not function_text:
            raise CommandExecutionError(
                "Nornir-proxy PID {}, failed download task function file: {}".format(
                    os.getpid(), plugin
                )
            )
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


def _watchdog():
    """
    Thread worker to maintain nornir proxy process and it's children liveability.
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
                        "Nornir-proxy {} MAIN PID {} watchdog, memory_threshold_mbyte exceeded, memory usage {}MByte".format(
                            nornir_data["stats"]["proxy_minion_id"],
                            os.getpid(),
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
            if not nornir_data["worker_thread"].is_alive():
                nornir_data["worker_thread"] = threading.Thread(
                    target=_worker, name="{}_worker".format(opts["id"])
                ).start()
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
        # keepalive connections and clean up dead connections if any
        try:
            if nornir_data["proxy_always_alive"] and nornir_data[
                "connections_lock"
            ].acquire(block=False):
                try:
                    stats = HostsKeepalive(nornir_data["nr"])
                    nornir_data["stats"]["watchdog_dead_connections_cleaned"] += stats[
                        "dead_connections_cleaned"
                    ]
                except Exception as e:
                    raise e
                finally:
                    nornir_data["connections_lock"].release()
        except:
            log.error(
                "Nornir-proxy MAIN PID {} watchdog, HostsKeepalive check error: {}".format(
                    os.getpid(), traceback.format_exc()
                )
            )

        time.sleep(nornir_data["watchdog_interval"])


def _worker(loader=None):
    """
    Target function for worker thread to run jobs from
    jobs_queue submitted by execution module processes
    """
    ppid = os.getpid()
    while nornir_data["initialized"]:
        time.sleep(0.01)
        job, output = None, None
        try:
            # get job from queue
            job = nornir_data["jobs_queue"].get(block=True, timeout=0.1)
            # run job
            nornir_data["stats"]["jobs_started"] += 1
            # check if its a call for a special task
            if job["task_fun"] == "test":
                nornir_data["stats"]["jobs_completed"] += 1
                nornir_data["res_queue"].put(
                    {"output": True, "identity": job["identity"]}
                )
                continue
            if job["task_fun"] == "clear_dcache":
                output = _clear_dcache(**job["kwargs"])
                nornir_data["stats"]["jobs_completed"] += 1
                nornir_data["res_queue"].put(
                    {"output": output, "identity": job["identity"]}
                )
                continue
            if job["task_fun"] == "refresh":
                nornir_data["stats"]["jobs_completed"] += 1
                nornir_data["res_queue"].put(
                    {"output": True, "identity": job["identity"]}
                )
                # loader used by decorator, loader_ used by _refresh_nornir itself
                _refresh_nornir(loader=loader, loader_=loader)
                # stop this worker thread as another one will be started
                break
            if job["task_fun"] == "shutdown":
                nornir_data["stats"]["jobs_completed"] += 1
                nornir_data["res_queue"].put(
                    {"output": True, "identity": job["identity"]}
                )
                # stop this worker thread as another one will be started
                shutdown()
                break
            if job["task_fun"] == "inventory":
                output = InventoryFun(nornir_data["nr"], **job["kwargs"])
                nornir_data["stats"]["jobs_completed"] += 1
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
            with nornir_data["connections_lock"]:
                output = run(
                    task=task_fun,
                    loader=loader,
                    identity=job["identity"],
                    name=job["name"],
                    **job["kwargs"],
                )
            nornir_data["stats"]["hosts_tasks_failed"] += len(
                nornir_data["nr"].data.failed_hosts
            )
            nornir_data["stats"]["jobs_completed"] += 1
        except queue.Empty:
            continue
        except:
            tb = traceback.format_exc()
            output = "Nornir-proxy MAIN PID {} job failed: {}, error:\n'{}'".format(
                ppid, job, tb
            )
            log.error(output)
            nornir_data["stats"]["jobs_failed"] += 1
        # submit job results in results queue
        nornir_data["res_queue"].put({"output": output, "identity": job["identity"]})
        del job, output
        # close connections to devices if proxy_always_alive is False
        if nornir_data["proxy_always_alive"] is False:
            try:
                nornir_data["nr"].close_connections(on_good=True, on_failed=True)
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
    """
    context = kwargs.pop("context", {})
    saltenv = kwargs.pop("saltenv", "base")
    defaults = kwargs.pop("defaults", {})
    template_engine = kwargs.pop("template_engine", "jinja")
    render = render.split(",") if isinstance(render, str) else render
    ignore_keys = (
        ignore_keys.split(",") if isinstance(ignore_keys, str) else ignore_keys
    )

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
        if ret.startswith("salt://"):
            content = __salt__["cp.get_file_str"](ret, saltenv=saltenv)
            if not content:
                raise CommandExecutionError(
                    "Failed to get '{}' file content".format(ret)
                )
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
            if key in ignore_keys:
                continue
            if isinstance(kwargs.get(key), str):
                rendered = __render(kwargs[key])
            elif isinstance(kwargs.get(key), (list, tuple)):
                rendered = [__render(item) for item in kwargs[key]]
            else:
                continue
            log.debug(
                "Nornir-proxy MAIN PID {} worker thread, rendered '{}' '{}' data for '{}' host".format(
                    os.getpid(), key, type(kwargs[key]), host_name
                )
            )
            host_object.data["__task__"][key] = rendered

    # clean up kwargs from render keys to force tasks to use hosts's __task__ attribute
    for key in render:
        _ = kwargs.pop(key) if key in kwargs else None


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
        if key not in kwargs:
            continue
        if not kwargs[key].startswith("salt://"):
            continue

        # download data
        content = __salt__["cp.get_file_str"](kwargs[key], saltenv=saltenv)
        if not content:
            raise CommandExecutionError("Failed to get '{}' file content".format(key))
        kwargs[key] = content

        log.debug(
            "Nornir-proxy MAIN PID {} worker thread, donwloaded '{}' data from Master".format(
                os.getpid(), key
            )
        )


def _add_processors(kwargs, loader, identity):
    """
    Helper function to exctrat processors arguments and add processors
    to Nornir.

    :param kwargs: (dict) dictionary with kwargs
    :param loader: (obj) SaltStack loader context
    :param identity: (dict) task identity dictionary for SaltEventProcessor
    :return: (obj) Nornir object
    """
    processors = []

    # get parameters
    tf = kwargs.pop("tf", None)  # to file
    tests = kwargs.pop("tests", None)  # tests
    remove_tasks = kwargs.pop("remove_tasks", True)  # testsand/or run_ttp
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
            )
        )

    return nornir_data["nr"].with_processors(processors)


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

    # iterate over hosts and save results to data cache
    for host_name, host_object in hosts.inventory.hosts.items():
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
                "salt-nornir:hcache unsupported results type '{}'".format(type(results))
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
    nornir_data["nr"].inventory.defaults.data.setdefault("_dcache_keys_", [])
    if cache_key not in nornir_data["nr"].inventory.defaults.data["_dcache_keys_"]:
        nornir_data["nr"].inventory.defaults.data["_dcache_keys_"].append(cache_key)

    # cache results
    nornir_data["nr"].inventory.defaults.data[cache_key] = results
    log.debug(
        "salt-nornir:dcache saved results in defaults data under '{}' key".format(
            cache_key
        )
    )


def _clear_dcache(**kwargs):
    """
    Function to clear task results cache from defaults data.

    :param cache_keys: (str) list of key names to remove
    """
    result = {}

    # get keys to clear
    cache_keys = kwargs.get("cache_keys", None)
    if cache_keys is None:
        # need to itearete over a copy of the keys - list() makes a copy
        cache_keys = list(
            nornir_data["nr"].inventory.defaults.data.get("_dcache_keys_", [])
        )

    # iterate over given cache keys and clean them up from data
    for key in cache_keys:
        if key in nornir_data["nr"].inventory.defaults.data and key in nornir_data[
            "nr"
        ].inventory.defaults.data.get("_dcache_keys_", []):
            nornir_data["nr"].inventory.defaults.data.pop(key)
            nornir_data["nr"].inventory.defaults.data["_dcache_keys_"].remove(key)
            result[key] = True
        else:
            result[key] = False

    return result


@_use_loader_context
def _refresh_nornir(loader_):
    """
    Function to re-initialise Nornir proxy with latest pillar data.

    This function calls ``shutdown`` function, gets latest modules and pillar
    from master and calls ``init`` function to reinstantiate Nornir object,
    worker&watchod threads and queus.

    It takes about a minute to finish refresh process.

    :param loader_: (obj) ``__salt__.loader`` object instance for ``init``
    """
    log.info("Nornir-proxy refreshing!")
    if shutdown():
        # refresh all modules
        __salt__["saltutil.sync_all"]()
        # refresh im memory pillar
        __salt__["saltutil.refresh_pillar"]()
        # get latest pillar data
        __opts__["pillar"] = __salt__["pillar.items"]()
        # re-init proxy module
        init(__opts__, loader_)
        log.info("Nornir-proxy MAIN PID {}, process refreshed!".format(os.getpid()))
        return True
    return False


def _rm_tasks_data_from_hosts(hosts):
    """
    Helper function to remove __task__ data from hosts inventory produced by rendering.

    :param hosts: (obj) Nornir object
    """
    for host_name, host_object in hosts.inventory.hosts.items():
        _ = host_object.data.pop("__task__", None)


# -----------------------------------------------------------------------------
# callable functions
# -----------------------------------------------------------------------------


def list_hosts(**kwargs):
    """
    Return a list of hosts managed by this Nornir instance

    :param Fx: filters to filter hosts
    """
    return InventoryFun(nornir_data["nr"], call="list_hosts", **kwargs)


def run(task, loader, identity, name, **kwargs):
    """
    Function for worker Thread to run Nornir tasks.

    :param task: (obj) callable task function
    :param loader: (obj) ``__salt__.loader`` object instance
    :param identity: (dict) Task results queue identity for SaltEventProcessor
    :param kwargs: (dict) passed to ``task.run`` after extracting CLI arguments
    :param name: (str) Nornir task name to run
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

    # set dry_run argument
    nornir_data["nr"].data.dry_run = kwargs.get("dry_run", False)

    # reset failed hosts if any
    nornir_data["nr"].data.reset_failed_hosts()

    # download files
    if download:
        _download_files(download, kwargs, loader=loader)

    # add processors
    nr_with_processors = _add_processors(kwargs, loader=loader, identity=identity)

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
        _download_and_render_files(
            hosts, render, kwargs, ignore_keys=download, loader=loader
        )

    # run tasks
    result = hosts.run(
        task, name=name, **{k: v for k, v in kwargs.items() if not k.startswith("_")}
    )

    # post clean-up - remove tasks rendered data from hosts inventory
    if render:
        _rm_tasks_data_from_hosts(hosts)

    # fire events for failed tasks if requested to do so
    if event_failed:
        _fire_events(result, loader=loader)

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
    :param identity: (dict) dictionary of uuid4, jid, funtion_name keys

    ``identity`` parameter used to identify job results in results queue and
    must be unique for each submitted job.
    """
    # add new job in jobs queue
    nornir_data["jobs_queue"].put(
        {"task_fun": task_fun, "kwargs": kwargs, "identity": identity, "name": task_fun}
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
    * ``hosts_count`` - int, number of hosts/devices managed by this proxy minion
    * ``hosts_connections_active`` - int, overall number of connection active to devices
    * ``hosts_tasks_failed`` - int, overall number of tasks failed for hosts
    * ``timestamp`` - ``time.ctime()`` timestamp of ``stats`` function run
    * ``watchdog_runs`` - int, overall number of watchdog thread runs
    * ``watchdog_child_processes_killed`` - int, number of stale child processes killed by watchdog
    * ``watchdog_dead_connections_cleaned`` - int, number of stale hosts' connections cleaned by watchdog
    * ``child_processes_count`` - int, number of child processes currently running
    * ``main_process_fd_count`` - int, number of file descriptors in use by main proxy minion process
    * ``main_process_fd_limit`` - int, fd count limit imposed by Operating System for minion process
    """
    stat = args[0] if args else kwargs.get("stat", None)
    # get approximate queue sizes
    try:
        jobs_job_queue_size = nornir_data["jobs_queue"].qsize()
        jobs_res_queue_size = nornir_data["res_queue"].qsize()
    except:
        jobs_job_queue_size = -1
        jobs_res_queue_size = -1
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
            "jobs_job_queue_size": jobs_job_queue_size,
            "jobs_res_queue_size": jobs_res_queue_size,
            "child_processes_count": len(multiprocessing.active_children()),
            "hosts_connections_active": sum(
                [
                    len(host.connections)
                    for host in nornir_data["nr"].inventory.hosts.values()
                ]
            ),
            "main_process_uptime_seconds": round(
                time.time() - nornir_data["stats"]["main_process_start_time"], 3
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
    used by ``nr.cli``, ``nr.cfg`` anf ``nr.nc`` execution module functions to
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
