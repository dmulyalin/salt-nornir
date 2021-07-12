"""
Nornir Proxy module
===================

Nornir Proxy Module reference.

Dependencies
------------

Nornir 3.x uses modular approach for plugins. As a result  required
plugins need to be installed separately from Nornir Core library. Main
collection of plugins to install is:

- `nornir-salt <https://github.com/dmulyalin/nornir-salt>`_ - ``pip install nornir_salt``

``nornir_salt`` will install these additional dependencies automatically::

    netmiko>=3.3.2
    nornir>=3.0.0
    nornir_netmiko>=0.1.1
    nornir_napalm>=0.1.1
    nornir_salt>=0.3.1
    napalm>=3.0.0
    psutil

Introduction
------------

Single Nornir proxy-minion can work with hundreds of devices as opposed to
conventional proxy-minion that normally dedicated to managing one device/system
only.

As a result, Nornir proxy-minion requires less resources to run tasks against same
number of devices. During idle state only one proxy minion process is active,
that significantly reduces amount of memory required to manage devices.

Proxy-module required way of operating is ``multiprocessing`` set to ``True`` -
default value, that way each task executed in dedicated process.

Nornir proxy pillar parameters
------------------------------

- ``proxytype`` nornir
- ``multiprocessing`` set to ``True`` is a recommended way to run this proxy
- ``process_count_max`` maximum number of processes to use to limit
  a number of tasks waiting to execute
- ``nornir_filter_required`` boolean, to indicate if Nornir filter is mandatory
  for tasks executed by this proxy-minion. Nornir has access to
  multiple devices, by default, if no filter provided, task will run for all
  devices, ``nornir_filter_required`` allows to change behaviour to opposite,
  if no filter provided, task will not run at all. It is a safety measure against
  running task for all devices accidentally, instead, filter ``FB="*"`` can be
  used to run task for all devices.
- ``runner`` - dict, Nornir Runner plugin parameters, default is ``RetryRunner``
- ``inventory`` - dict, Nornir Inventory plugin parameters, default is ``DictInventory``
  populated with data from proxy-minion pillar, otherwise pillar data ignored.
- ``child_process_max_age`` - int, seconds to wait before forcefully kill child process,
  default 660s
- ``watchdog_interval`` - int, interval in seconds between watchdog runs, default 30s
- ``proxy_always_alive`` - bool, default True, keep connections with devices alive on True
  and tears them down after each job on False
- ``job_wait_timeout`` - int, seconds to wait for job return until give up, default 600s
- ``memory_threshold_mbyte`` - int, value in MBytes above each to trigger ``memory_threshold_action``
- ``memory_threshold_action`` - str, action to implement if ``memory_threshold_mbyte`` exceeded,
  possible actions: ``log``- send syslog message, ``restart`` - restart proxy minion process.
- ``files_base_path`` - str, OS path to folder where to save ToFile processor files on a 
  per-host basis, default is ``/var/salt-nornir/{proxy_id}/files/``
- ``nr_cli`` - dictionary of default kwargs to use with ``nr.cli`` execution module function
- ``nr_cfg`` - dictionary of default kwargs to use with ``nr.cfg`` execution module function
- ``nr_nc`` - dictionary of default kwargs to use with ``nr.nc`` execution module function

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
      nr_cli: {}
      nr_cfg: {}
      nr_nc: {}
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

Nornir runners
--------------

Runners in Nornir define how to run tasks against hosts. If no ``runner``
dictionary provided in proxy-minion pillar, Nornir initialized using
`RetryRunner <https://nornir-salt.readthedocs.io/en/latest/Runner%20Plugins.html#retryrunner-plugin>`_
plugin with these default settings::

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

``RetryRunner`` runner included in `nornir_salt <https://github.com/dmulyalin/nornir-salt>`_
library.

Nornir proxy module special tasks
---------------------------------

These tasks have special handling by Nornir proxy minion process:

* ``test`` - this task test proxy minion module without invoking any Nornir code
* ``nr_test`` - this task runs dummy task against hosts without initiating any connections to them
* ``nr_refresh`` - task to run ``_refresh`` function
* ``nr_restart`` - task to run ``_restart`` function

Sample invocation::

    salt nrp1 nr.task test
    salt nrp1 nr.task nr_test
    salt nrp1 nr.task nr_refresh
    salt nrp1 nr.task nr_restart

Nornir Proxy Module functions
-----------------------------

.. autofunction:: salt_nornir.proxy.nornir_proxy_module.inventory_data
.. autofunction:: salt_nornir.proxy.nornir_proxy_module.run
.. autofunction:: salt_nornir.proxy.nornir_proxy_module.execute_job
.. autofunction:: salt_nornir.proxy.nornir_proxy_module.stats
.. autofunction:: salt_nornir.proxy.nornir_proxy_module._refresh
.. autofunction:: salt_nornir.proxy.nornir_proxy_module._restart
.. autofunction:: salt_nornir.proxy.nornir_proxy_module.shutdown
.. autofunction:: salt_nornir.proxy.nornir_proxy_module.nr_version
.. autofunction:: salt_nornir.proxy.nornir_proxy_module.nr_data
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
    # starting from SALT 3003 need to use loader_context to reconstruct
    # __salt__ dunder within treads:
    # details: https://github.com/saltstack/salt/issues/59962
    from salt.loader_context import loader_context

    HAS_LOADER_CONTEXT = True
except ImportError:
    HAS_LOADER_CONTEXT = False

minion_process = psutil.Process(os.getpid())

# Import third party libs
try:
    from nornir import InitNornir
    from nornir.core.task import Result, Task
    from nornir_salt.plugins.functions import (
        FFun,
        ResultSerializer,
        HostsKeepalive,
        TabulateFormatter,
    )
    from nornir_salt.plugins.tasks import nr_test
    from nornir_salt.plugins.processors import (
        TestsProcessor,
        ToFileProcessor,
        DiffProcessor,
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
# proxy functions
# -----------------------------------------------------------------------------


def init(opts):
    """
    Initiate nornir by calling InitNornir()
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
    nornir_data["memory_threshold_mbyte"] = int(
        opts["proxy"].get("memory_threshold_mbyte", 300)
    )
    nornir_data["memory_threshold_action"] = opts["proxy"].get(
        "memory_threshold_action", "log"
    )
    nornir_data["files_base_path"] = opts["proxy"].get(
        "files_base_path", "/var/salt-nornir/{}/files/".format(opts["id"])
    )
    nornir_data["nr_cli"] = opts["proxy"].get("nr_cli", {})
    nornir_data["nr_cfg"] = opts["proxy"].get("nr_cfg", {})
    nornir_data["nr_nc"] = opts["proxy"].get("nr_nc", {})
    nornir_data["initialized"] = True
    # add some stats
    nornir_data["stats"]["proxy_minion_id"] = opts["id"]
    nornir_data["stats"]["main_process_is_running"] = 1
    nornir_data["stats"]["hosts_count"] = len(nornir_data["nr"].inventory.hosts.keys())
    # Initiate multiprocessing related queus, locks and threads
    nornir_data["jobs_queue"] = multiprocessing.Queue()
    nornir_data["res_queue"] = multiprocessing.Queue()
    nornir_data["worker_thread"] = threading.Thread(
        target=_worker,
        name="{}_worker".format(opts["id"]),
        args=(__salt__.loader() if HAS_LOADER_CONTEXT else None,),
    )
    nornir_data["worker_thread"].start()
    nornir_data["watchdog_thread"] = threading.Thread(
        target=_watchdog, name="{}_watchdog".format(opts["id"])
    )
    nornir_data["watchdog_thread"].start()
    nornir_data["connections_lock"] = multiprocessing.Lock()
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
    This function implements this shutdown protocol:

    1. Signal worker and watchdog threads to stop
    2. Close all connections to devices
    3. Close jobs and results queues
    4. Kill all child processes
    5. Delete Nornir object
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
    Does nothing, returns empty dictionary
    """
    return {}


def grains_refresh():
    """
    Does nothing, returns empty dictionary
    """
    return grains()


# -----------------------------------------------------------------------------
# proxy module private functions
# -----------------------------------------------------------------------------


def _refresh(*args, **kwargs):
    """
    Function to re-initialise Nornir proxy with latest pillar data.

    This function calls ``shutdown`` function, gets latest pillar
    from master and re-instantiates Nornir object.
    """
    log.info("Nornir-proxy MAIN PID {}, refreshing!".format(os.getpid()))
    time.sleep(10)
    if shutdown():
        # get latest pillar data
        __opts__["pillar"] = __salt__["pillar.items"]()
        # re-init proxy module
        init(__opts__)
        log.info("Nornir-proxy MAIN PID {}, process refreshed!".format(os.getpid()))
        return True
    return False


def _restart(*args, **kwargs):
    """
    This suicidal function serves as a lastage effort to recover Nornir proxy.
    It effectively kills main Nornir proxy process by calling ``os.kill``
    on itself.

    However, SALT starts parent process for each proxy-minion,
    that parent process will restart nornir-proxy minion once
    it detects that minion is shutted down. Overall restart and
    detection time combined might be of **several minutes**.

    Prior to restart, ``shutdown`` function called. Nornir execution
    module calls will be unresponsive. Use ``_restart`` with caution,
    ideally, when no other jobs running.
    """
    log.warning(
        "Nornir-proxy MAIN PID {}, restarting in 10 seconds!".format(os.getpid())
    )
    time.sleep(10)
    # Shutdown Nornir object and close connections
    shutdown()
    # kill itself and hope that parent process will revive me
    os.kill(os.getpid(), signal.SIGKILL)


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


def _get_or_import_task_fun(plugin, loader=None):
    """
    Tries to get task function from globals() dictionary,
    if its not there tries to import task and inject it
    in globals() dictionary for future reference.
    """
    task_fun = plugin.split(".")[-1]
    if task_fun in globals():
        task_function = globals()[task_fun]
    # check if plugin referring to file on master, load and compile it if so
    elif plugin.startswith("salt://"):
        function_text = None
        if HAS_LOADER_CONTEXT and loader != None:
            with loader_context(loader):
                function_text = __salt__["cp.get_file_str"](plugin, saltenv="base")
        else:
            function_text = __salt__["cp.get_file_str"](plugin, saltenv="base")
        if not function_text:
            raise CommandExecutionError(
                "Nornir-proxy PID {}, failed download task function file: {}".format(
                    os.getpid(), plugin
                )
            )
        task_function = _load_custom_task_fun_from_text(function_text, "task")
    else:
        # import task function, below two lines are the same as
        # from nornir.plugins.tasks import task_fun as task_function
        module = __import__(plugin, fromlist=[""])
        task_function = getattr(module, task_fun)
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
                        "Nornir-proxy MAIN PID {} watchdog, file descriptors in use: {}, limit: {}, reached 95% threshold, restarting".format(
                            os.getpid(), fd_in_use, fd_limit
                        )
                    )
                    _restart()
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
                    _restart()
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
                "Nornir-proxy MAIN PID {} watchdog, worker thread is alive check error: {}".format(
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
            # check if its a call for special task
            if job["task_fun"] == "test":
                nornir_data["stats"]["jobs_completed"] += 1
                nornir_data["res_queue"].put({"output": True, "pid": job["pid"]})
                continue
            elif job["task_fun"] == "nr_refresh":
                nornir_data["stats"]["jobs_completed"] += 1
                nornir_data["res_queue"].put({"output": True, "pid": job["pid"]})
                _refresh()
                break
            elif job["task_fun"] == "nr_restart":
                nornir_data["res_queue"].put({"output": True, "pid": job["pid"]})
                _restart()
            # execute nornir task
            task_fun = _get_or_import_task_fun(job["task_fun"], loader)
            log.info(
                "Nornir-proxy MAIN PID {} starting task '{}'".format(ppid, job["name"])
            )
            # lock connections and run the task
            with nornir_data["connections_lock"]:
                output = run(
                    task_fun, loader, *job["args"], **job["kwargs"], name=job["name"]
                )
            nornir_data["stats"]["hosts_tasks_failed"] += len(
                nornir_data["nr"].data.failed_hosts
            )
            nornir_data["stats"]["jobs_completed"] += 1
        except queue.Empty:
            continue
        except:
            tb = traceback.format_exc()
            output = "Nornir-proxy MAIN PID {} job failed: {}, child PID {}, error:\n'{}'".format(
                ppid, job, job["pid"], tb
            )
            log.error(output)
            nornir_data["stats"]["jobs_failed"] += 1
        # submit job results in results queue
        nornir_data["res_queue"].put({"output": output, "pid": job["pid"]})
        del job, output
        # close connections to devices if proxy_always_alive is False
        if nornir_data["proxy_always_alive"] == False:
            try:
                nornir_data["nr"].close_connections(on_good=True, on_failed=True)
            except:
                log.error(
                    "Nornir-proxy MAIN PID {} worker thread, Nornir close_connections error: {}".format(
                        os.getpid(), traceback.format_exc()
                    )
                )


def _fire_events(result):
    """
    Helper function to iterate over results and fire event for
    tasks that either has failed=True or success=False.

    :param result: (obj) Nornir AggregatedResult object
    """
    results_list = ResultSerializer(result, to_dict=False, add_details=True)
    for res in results_list:
        if res.get("failed") == True or res.get("success") == False:
            __salt__["event.send"](
                tag="nornir-proxy/{proxy_id}/{host}/task/failed/{name}".format(
                    proxy_id=nornir_data["stats"]["proxy_minion_id"],
                    host=res["host"],
                    name=res["name"],
                ),
                data=res,
            )


def _load_and_render_files(hosts, render, kwargs):
    """
    Helper function to iterate over hosts and render content for each of them.

    Rendering results saved in host's ``__task__`` attribute as a dictionary
    keyed by the items from ``render`` list.

    :param hosts: (obj) Nornir object with hosts inventory
    :param render: (list or str) list of keys or comma separated string
        of key names from kwargs to run rendering for
    :param kwargs: (dict) dictionary with data to render
    """
    context = kwargs.pop("context", {})
    saltenv = kwargs.pop("saltenv", "base")
    defaults = kwargs.pop("defaults", {})
    template_engine = kwargs.pop("template_engine", "jinja")
    render = render.split(",") if isinstance(render, str) else render

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
            if isinstance(kwargs.get(key), str):
                rendered = __render(kwargs[key])
            elif isinstance(
                kwargs.get(key),
                (
                    list,
                    tuple,
                ),
            ):
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
    return hosts.dict()["inventory"]


def run(task, loader, *args, **kwargs):
    """
    Function for worker Thread to run Nornir tasks.

    :param task: callable task function
    :param Fx: filters to filter hosts
    :param kwargs: arguments to pass to ``nornir_object.run`` method
    """
    # extract attributes
    processors = []
    add_details = kwargs.pop("add_details", False)  # ResultSerializer
    to_dict = kwargs.pop("to_dict", True)  # ResultSerializer
    table = kwargs.pop("table", {})  # tabulate
    headers = kwargs.pop("headers", "keys")  # tabulate
    tf = kwargs.pop("tf", None)  # to file
    tf_format = kwargs.pop("tf_format", "raw")  # to file
    tests = kwargs.pop("tests", None)  # tests
    remove_tasks = kwargs.pop("remove_tasks", True)  # tests
    failed_only = kwargs.pop("failed_only", False)  # tests
    event_failed = kwargs.pop("event_failed", False)  # events
    diff = kwargs.pop("diff", "")  # diff processor
    last = kwargs.pop("last", 1)  # diff processor
    render = kwargs.pop(
        "render", ["config", "data", "filter", "filter_", "filters", "filename"]
    )  # render data

    # set dry_run argument
    nornir_data["nr"].data.dry_run = kwargs.get("dry_run", False)

    # reset failed hosts if any
    nornir_data["nr"].data.reset_failed_hosts()

    # add processors if any
    if tests:
        processors.append(
            TestsProcessor(tests, remove_tasks=remove_tasks, failed_only=failed_only)
        )
    if diff:
        processors.append(
            DiffProcessor(
                diff=diff,
                diff_per_task=True if add_details else False,
                last=int(last),
                base_url=nornir_data["files_base_path"],
            )
        )
    # append ToFileProcessor as the last one in the sequence
    if tf and isinstance(tf, str):
        processors.append(
            ToFileProcessor(
                tf=tf, tf_format=tf_format, base_url=nornir_data["files_base_path"]
            )
        )
    nr_with_processors = nornir_data["nr"].with_processors(processors)

    # Filter hosts to run tasks for
    hosts, has_filter = FFun(
        nr_with_processors, kwargs=kwargs, check_if_has_filter=True
    )

    # check if nornir_filter_required is True but no filter
    if nornir_data["nornir_filter_required"] == True and has_filter == False:
        raise CommandExecutionError(
            "Nornir-proxy 'nornir_filter_required' setting is True but no filter provided"
        )

    # load and render files
    if render and HAS_LOADER_CONTEXT:
        with loader_context(loader):
            _load_and_render_files(hosts, render, kwargs)
    elif render:
        _load_and_render_files(hosts, render, kwargs)

    # run tasks
    result = hosts.run(
        task,
        *[i for i in args if not i.startswith("_")],
        **{k: v for k, v in kwargs.items() if not k.startswith("_")}
    )

    # post clean-up rendered data from hosts inventory
    if render:
        for host_name, host_object in hosts.inventory.hosts.items():
            _ = host_object.data.pop("__task__", None)

    # fire events for failed tasks if requested to do so
    if event_failed and HAS_LOADER_CONTEXT:
        with loader_context(loader):
            _fire_events(result)
    elif event_failed:
        _fire_events(result)

    # run post processing
    if table:
        ret = TabulateFormatter(result, tabulate=table, headers=headers)
    else:
        ret = ResultSerializer(result, to_dict=to_dict, add_details=add_details)

    return ret


def execute_job(task_fun, args, kwargs, cpid):
    """
    Function to submit job request to Nornir Proxy minion jobs queue,
    wait for job to be completed and return results.

    :param task_fun: str, name of nornir task function/plugin to run
    :param args: list, any arguments to submit to Nornir task ``*args``
    :param kwargs: dict, any arguments to submit to Nornir task ``**kwargs``
    :param cpid: int, Process ID (PID) of child process submitting job request

    Additional ``execute_job`` arguments read from ``kwargs``:

    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``
    """
    # add new job in jobs queue
    nornir_data["jobs_queue"].put(
        {
            "task_fun": task_fun,
            "args": args,
            "kwargs": kwargs,
            "pid": cpid,
            "name": "{} CPID {}".format(task_fun, cpid)
            if kwargs.pop("add_cpid_to_task_name", False)
            else task_fun,
        }
    )
    # wait for job to complete and return results
    start_time = time.time()
    while (time.time() - start_time) < nornir_data["job_wait_timeout"]:
        time.sleep(0.1)
        try:
            res = nornir_data["res_queue"].get(block=True, timeout=0.1)
            if res["pid"] == cpid:
                break
            else:
                nornir_data["res_queue"].put(res)
        except queue.Empty:
            continue
    else:
        raise TimeoutError(
            "Nornir-proxy MAIN PID {}, CPID '{}', {}s job_wait_timeout expired.".format(
                os.getpid(), cpid, nornir_data["job_wait_timeout"]
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
    * ``jobs_res_queue_size`` - int, size of results queue, indicating number of
        results waiting to be collected by child process
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
        "jinja2": "",
        "ttp": "",
        "salt-nornir": "",
        "nornir-salt": "",
        "lxml": "",
        "psutil": "",
        "salt": "",
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
    """
    return nornir_data.get(key, None)
