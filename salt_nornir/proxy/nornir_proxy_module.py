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
- ``child_process_timeout`` - int, how much seconds wait before kill child process,
  default 660 seconds

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
import os
import psutil
import time
import traceback
import signal

log = logging.getLogger(__name__)
minion_process = psutil.Process(os.getpid())

# import SALT libs
from salt.exceptions import CommandExecutionError

# Import third party libs
try:
    from nornir import InitNornir
    from nornir.core.task import Result, Task
    from nornir_salt.plugins.functions import FFun
    from nornir_salt.plugins.functions import ResultSerializer

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
stats_dict = {
    "proxy_minion_id": None,
    "main_process_is_running": 0,
    "main_process_start_time": time.time(),
    "main_process_start_date": time.ctime(),
    "main_process_uptime_seconds": 0,
    "main_process_ram_usage_mbyte": minion_process.memory_info().rss / 1000000,
    "main_process_pid": os.getpid(),
    "main_process_proxy_id": None,
    "jobs_started": 0,
    "jobs_completed": 0,
    "jobs_failed": 0,
    "jobs_job_queue_size": 0,
    "jobs_res_queue_size": 0,
    "hosts_count": 0,
    # "hosts_connections": 0,
    "hosts_tasks_failed": 0,
    "timestamp": time.ctime(),
    "child_processes_killed": 0,
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
    nornir_data["child_process_timeout"] = opts["proxy"].get(
        "child_process_timeout", 660
    )
    nornir_data["initialized"] = True
    # add some stats
    nornir_data["stats"]["proxy_minion_id"] = opts["id"]
    nornir_data["stats"]["main_process_is_running"] = 1
    nornir_data["stats"]["hosts_count"] = len(nornir_data["nr"].inventory.hosts.keys())
    # Initiate multiprocessing related queus, locks and threads
    nornir_data["jobs_queue"] = multiprocessing.Queue()
    nornir_data["res_queue"] = multiprocessing.Queue()
    nornir_data["worker_thread"] = threading.Thread(target=_worker).start()
    nornir_data["watchdog_thread"] = threading.Thread(target=_watchdog).start()
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
    nornir_data["initialized"] = False  # trigger worker and watchdogs threads to stop
    nornir_data["stats"] = stats_dict.copy()
    del nornir_data["nr"], nornir_data["worker_thread"], nornir_data["watchdog_thread"]
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
    task_fun = _get_or_import_task_fun("nornir_scrapli.tasks.send_command")
    for command in commands:
        task.run(
            task=task_fun,
            command=command,
            name=command,
            **kwargs.get("netmiko_kwargs", {})
        )
    return Result(host=task.host)


def _napalm_configure(task, config, **kwargs):
    # render configuration
    rendered_config = _render_config_template(task, config, kwargs)
    # push config to devices
    task_fun = _get_or_import_task_fun("nornir_napalm.plugins.tasks.napalm_configure")
    task.run(task=task_fun, configuration=rendered_config.result, **kwargs)
    return Result(host=task.host)


def _netmiko_send_config(task, config, **kwargs):
    # render configuration
    rendered_config = _render_config_template(task, config, kwargs)
    # push config to devices
    task_fun = _get_or_import_task_fun("nornir_netmiko.tasks.netmiko_send_config")
    task.run(
        task=task_fun,
        config_commands=rendered_config.result.splitlines(),
        **kwargs
    )
    return Result(host=task.host)


def _scrapli_send_config(task, config, **kwargs):
    # render configuration
    rendered_config = _render_config_template(task, config, kwargs)
    # push config to devices
    task_fun = _get_or_import_task_fun("nornir_scrapli.tasks.send_config")
    task.run(
        task=task_fun,
        config=rendered_config.result,
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


def _get_or_import_task_fun(plugin):
    """
    Tries to get task function from globals() dictionary,
    if its not there tries to import task and inject it
    in globals() dictionary for future reference.
    """
    task_name = plugin.split(".")[-1]
    if task_name in globals():
        task_function = globals()[task_name]
    else:
        # import task function, below two lines are the same as
        # from nornir.plugins.tasks import task_name as task_function
        module = __import__(plugin, fromlist=[""])
        task_function = getattr(module, task_name)
        globals()[task_name] = task_function
    return task_function


def _watchdog():
    """
    Thread worker to maintain nornir proxy process and it's children
    liveability.
    """
    child_processes = {}
    while nornir_data["initialized"]:
        mem_usage = minion_process.memory_info().rss / 1000000
        log.error(
            "Nornir-proxy MAIN PID {} watchdog, memory usage {}MByte".format(
                os.getpid(), mem_usage
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
                    child_processes[cpid]["age"] > nornir_data["child_process_timeout"]
                ):
                    os.kill(cpid, signal.SIGKILL)
                    nornir_data["stats"]["child_processes_killed"] += 1
                    log.error(
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
            tb = traceback.format_exc()
            log.error(
                "Nornir-proxy MAIN PID {} watchdog, child processes error: {}".format(
                    os.getpid(), tb
                )
            )
        time.sleep(30)


def _worker():
    """
    Target function for worker thread to run jobs from
    jobs_queue submitted by execution module processes
    """
    while nornir_data["initialized"]:
        job, ret, output = None, None, None
        try:
            # get job from queue
            job = nornir_data["jobs_queue"].get(block=True, timeout=0.1)
            if job is None:
                break
            # run job
            nornir_data["stats"]["jobs_started"] += 1
            task_fun = _get_or_import_task_fun(job["task_name"])
            ret = run(task_fun, *job["args"], **job["kwargs"])
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
                os.getpid(), job, job["pid"], tb
            )
            log.error(output)
            nornir_data["stats"]["jobs_failed"] += 1
        # submit job results in results queue
        nornir_data["res_queue"].put({"output": output, "pid": job["pid"]})
        del job, ret, output


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


def stats():
    """
    Function to gather and return stats about Nornir proxy process
    """
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
            "main_process_ram_usage_mbyte": minion_process.memory_info().rss / 1000000,
            "main_process_uptime_seconds": time.time() - nornir_data["stats"]["main_process_start_time"],
            "timestamp": time.ctime(),
            "jobs_job_queue_size": jobs_job_queue_size,
            "jobs_res_queue_size": jobs_res_queue_size,
            "child_processes_count": len(multiprocessing.active_children()),
        }
    )
    return nornir_data["stats"]
