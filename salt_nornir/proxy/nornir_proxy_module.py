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
that significantly reduces amount of memory required to run the system.

Proxy-module required way of operating is ``multiprocessing`` set to ``True`` - 
default value, that way each task executed in dedicated process.

Nornir proxy pillar parameters
------------------------------

- ``proxytype`` nornir
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
- ``runner`` - dict, Nornir runner parameters dictionary to use for this proxy module
- ``child_process_max_age`` - int, seconds to wait before forcefully kill child process,
  default 660s
- ``watchdog_interval`` - int, interval in seconds between watchdog runs, default 30s
- ``proxy_always_alive`` - bool, default True, keep connections with devices alive on True
  and tears them down after each job on False
- ``job_wait_timeout`` - int, seconds to wait for job return until give up, default 600s
- ``memory_threshold_mbyte`` - int, value in MBytes above each to trigger ``memory_threshold_action``
- ``memory_threshold_action`` - str, action to implement if ``memory_threshold_mbyte`` exceeded, 
  possible actions: ``log``- send syslog message, ``restart`` - restart proxy minion process.

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
* ``nr_test`` - this task run dummy task against hosts without initiating any connections to them
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

log = logging.getLogger(__name__)

# import salt libs, wrapping it in try/except for docs to generate
try:
    from salt.exceptions import CommandExecutionError, TimeoutError
except:
    log.error("Nornir Proxy Module - failed importing SALT libraries")

minion_process = psutil.Process(os.getpid())

# Import third party libs
try:
    from nornir import InitNornir
    from nornir.core.task import Result, Task
    from nornir_salt.plugins.functions import FFun
    from nornir_salt.plugins.functions import ResultSerializer
    from nornir_salt.plugins.functions import HostsKeepalive
    from nornir_salt.plugins.functions import ToFile
    
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
    "nornir_filter_required": False,
    "jobs_queue": None,
    "res_queue": None,
    "worker_thread": None,
    "watchdog_thread": None,
    "proxy_always_alive": True,
    "watchdog_interval": 30,
    "child_process_max_age": 660,
    "job_wait_timeout": 600,
    "memory_threshold_mbyte": 300,
    "memory_threshold_action": "log",
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
    runner_config = (
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
                "task_timeout": 600
            },
        }
        if not opts["proxy"].get("runner")
        else opts["proxy"]["runner"]
    )
    nornir_data["nr"] = InitNornir(
        logging={"enabled": False},
        runner=runner_config,
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
    nornir_data["initialized"] = True
    # add some stats
    nornir_data["stats"]["proxy_minion_id"] = opts["id"]
    nornir_data["stats"]["main_process_is_running"] = 1
    nornir_data["stats"]["hosts_count"] = len(nornir_data["nr"].inventory.hosts.keys())
    # Initiate multiprocessing related queus, locks and threads
    nornir_data["jobs_queue"] = multiprocessing.Queue()
    nornir_data["res_queue"] = multiprocessing.Queue()
    nornir_data["worker_thread"] = threading.Thread(
        target=_worker, name="{}_worker".format(opts["id"])
    ).start()
    nornir_data["watchdog_thread"] = threading.Thread(
        target=_watchdog, name="{}_watchdog".format(opts["id"])
    ).start()
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
# Nornir task functions
# -----------------------------------------------------------------------------


def _netmiko_send_commands(task, commands, **kwargs):
    """
    Nornir Task function to send show commands to devices using
    ``nornir_netmiko.tasks.netmiko_send_command`` plugin

    :param kwargs: might contain ``netmiko_kwargs`` argument dictionary
         for ``nornir_netmiko.tasks.netmiko_send_command`` method
    :param config: (list) commands list to send to device(s)
    :return result: Nornir result object with task execution results
    """
    task_fun = _get_or_import_task_fun("nornir_netmiko.tasks.netmiko_send_command")
    for command in commands:
        task.run(
            task=task_fun,
            command_string=command,
            name=command,
            **kwargs.get("netmiko_kwargs", {})
        )
    return Result(host=task.host)


def _scrapli_send_commands(task, commands, **kwargs):
    """
    Nornir Task function to send show commands to devices using
    ``nornir_scrapli.tasks.send_command`` plugin

    :param kwargs: might contain ``scrapli_kwargs`` argument dictionary
        for ``nornir_scrapli.tasks.send_command`` method
    :param config: (list) commands list to send to device(s)
    :return result: Nornir result object with task execution results
    """
    task_fun = _get_or_import_task_fun("nornir_scrapli.tasks.send_command")
    for command in commands:
        task.run(
            task=task_fun,
            command=command,
            name=command,
            **kwargs.get("scrapli_kwargs", {})
        )
    return Result(host=task.host)


def _napalm_configure(task, config, **kwargs):
    """
    Nornir Task function to send confgiuration to devices using
    ``nornir_napalm.plugins.tasks.napalm_configure`` plugin

    :param kwargs: arguments for ``file.apply_template_on_contents`` salt function
        for configuration rendering as well as for ``task.run`` method
    :param config: (str) configuration string to render and send to device(s)
    :return result: Nornir result object with task execution results
    """
    # render configuration
    rendered_config = _render_config_template(task, config, kwargs)
    # push config to devices
    task_fun = _get_or_import_task_fun("nornir_napalm.plugins.tasks.napalm_configure")
    task.run(task=task_fun, configuration=rendered_config.result, **kwargs)
    return Result(host=task.host)


def _netmiko_send_config(task, config, **kwargs):
    """
    Nornir Task function to send confgiuration to devices using
    ``nornir_netmiko.tasks.netmiko_send_config`` plugin

    :param kwargs: arguments for ``file.apply_template_on_contents`` salt function
        for configuration rendering as well as for ``task.run`` method
    :param config: (str) configuration string to render and send to device(s)
    :return result: Nornir result object with task execution results
    """
    # render configuration
    rendered_config = _render_config_template(task, config, kwargs)
    # push config to devices
    task_fun = _get_or_import_task_fun("nornir_netmiko.tasks.netmiko_send_config")
    task.run(
        task=task_fun, config_commands=rendered_config.result.splitlines(), **kwargs
    )
    return Result(host=task.host)


def _scrapli_send_config(task, config, **kwargs):
    """
    Nornir Task function to send confgiuration to devices using
    ``nornir_scrapli.tasks.send_config`` plugin

    :param kwargs: arguments for ``file.apply_template_on_contents`` salt function
        for configuration rendering as well as for ``task.run`` method
    :param config: (str) configuration string to render and send to device(s)
    :return result: Nornir result object with task execution results
    """
    # render configuration
    rendered_config = _render_config_template(task, config, kwargs)
    # push config to devices
    task_fun = _get_or_import_task_fun("nornir_scrapli.tasks.send_config")
    task.run(task=task_fun, config=rendered_config.result, **kwargs)
    return Result(host=task.host)


def _cfg_gen(task, config, **kwargs):
    """
    Task function for ``nr.cfg_gen`` function to render template with pillar
    and Nornir host Inventory data.

    :param kwargs: arguments for ``file.apply_template_on_contents`` salt function
    :param config: (str) configuration string to render
    :return result: Nornir result object with task execution results
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

    :param kwargs: arguments for ``file.apply_template_on_contents`` salt function
    :param config: (str) configuration string to render
    :return result: Nornir result object with configuration rendering results
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


def nr_test(task, **kwargs):
    """
    Dummy task that echoes data passed to it. Useful to debug and
    verify Nornir object.

    :param kwargs: Any <key,value> pair you want
    :return result: (``dict``) ``**kwargs`` passed to the task
    """
    return Result(host=task.host, result=kwargs)


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
    if shutdown():
        # kill itself and hope that parent process will revive me
        os.kill(os.getpid(), signal.SIGKILL)


def _get_or_import_task_fun(plugin):
    """
    Tries to get task function from globals() dictionary,
    if its not there tries to import task and inject it
    in globals() dictionary for future reference.
    """
    task_fun = plugin.split(".")[-1]
    if task_fun in globals():
        task_function = globals()[task_fun]
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
        # check if can create test pipe to confirm that have not run out of file descriptors
        try:
            r, w = multiprocessing.Pipe(duplex=False)
            r.close()
            w.close()
            del r, w
        except:
            tb = traceback.format_exc()
            if "Too many open files" in tb:
                log.warning(
                    "Nornir-proxy MAIN PID {} watchdog, detected 'Too many open files' problem, restarting".format(
                        os.getpid()
                    )
                )
                _restart()
            else:
                log.error(
                    "Nornir-proxy MAIN PID {} watchdog, create test pipe error: {}".format(
                        os.getpid(), tb
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
            if nornir_data["proxy_always_alive"]:
                stats = HostsKeepalive(nornir_data["nr"])
                nornir_data["stats"]["watchdog_dead_connections_cleaned"] += stats[
                    "dead_connections_cleaned"
                ]
        except:
            log.error(
                "Nornir-proxy MAIN PID {} watchdog, HostsKeepalive check error: {}".format(
                    os.getpid(), traceback.format_exc()
                )
            )
        time.sleep(nornir_data["watchdog_interval"])


def _worker():
    """
    Target function for worker thread to run jobs from
    jobs_queue submitted by execution module processes
    """
    ppid = os.getpid()
    while nornir_data["initialized"]:
        job, ret, output = None, None, None
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
                continue
            elif job["task_fun"] == "nr_restart":
                nornir_data["res_queue"].put({"output": True, "pid": job["pid"]})
                _restart()
                continue
            # execute nornir task
            task_fun = _get_or_import_task_fun(job["task_fun"])
            log.info(
                "Nornir-proxy MAIN PID {} starting task '{}'".format(ppid, job["name"])
            )
            ret = run(task_fun, *job["args"], **job["kwargs"], name=job["name"])
            output = ResultSerializer(ret, job.get("add_details", False))
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
        del job, ret, output
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
            "Nornir-proxy 'nornir_filter_required' setting is True but no filter provided"
        )
    # run tasks
    return hosts.run(
        task,
        *[i for i in args if not i.startswith("_")],
        **{k: v for k, v in kwargs.items() if not k.startswith("_")}
    )


def execute_job(task_fun, args, kwargs, cpid):
    """
    Function to submit job request in Nornir Proxy minion jobs queue,
    wait for job to be completed and return results.

    :param task_fun: str, name of nornir task function/plugin to run
    :param args: list, any arguments to submit to Nornir task ``*args``
    :param kwargs: dict, any arguments to submit to Nornir task ``**kwargs``
    :param cpid: int, Process ID (PID) of child process submitting job request
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
            "add_details": kwargs.pop("add_details", False),
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
    # save results to file if requested to do so
    if "tf" in kwargs:
        ToFile(res["output"], **kwargs)
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
    """
    stat = args[0] if args else kwargs.get("stat", None)
    # get approximate queue sizes
    try:
        jobs_job_queue_size = nornir_data["jobs_queue"].qsize()
        jobs_res_queue_size = nornir_data["res_queue"].qsize()
    except:
        jobs_job_queue_size = -1
        jobs_res_queue_size = -1
    # update stats
    nornir_data["stats"].update(
        {
            "main_process_ram_usage_mbyte": minion_process.memory_info().rss / 1024000,
            "main_process_uptime_seconds": time.time()
            - nornir_data["stats"]["main_process_start_time"],
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
