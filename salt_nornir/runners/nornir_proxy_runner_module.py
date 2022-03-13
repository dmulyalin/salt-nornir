"""
Nornir Runner Module
====================

Nornir Runner module reference.

.. note:: Runner module functions executed on same machine where salt-master process runs.

Introduction
------------

Nornir-runner module runs on SALT Master and allows to interact with devices behind Nornir proxy minions.

Nornir Runner module functions
------------------------------

.. autofunction:: salt_nornir.runners.nornir_proxy_runner_module.inventory
.. autofunction:: salt_nornir.runners.nornir_proxy_runner_module.call
.. autofunction:: salt_nornir.runners.nornir_proxy_runner_module.event
"""
# Import python libs
import logging
import traceback
import fnmatch
import time
import os
import pprint
import queue

from threading import Thread, Event
from typing import Union

log = logging.getLogger(__name__)

# Import salt modules
try:
    import salt.client
    import salt.config
    import salt.utils.event
    from salt.exceptions import CommandExecutionError

    HAS_SALT = True
except:
    log.error("Nornir Runner Module - failed importing SALT libraries")
    HAS_SALT = False

# import Nornir libs
try:
    from nornir_salt.plugins.functions import TabulateFormatter
    from nornir_salt.plugins.functions import FFun_functions  # list of Fx names
    from nornir_salt.utils import MakePlugin

    HAS_NORNIR = True
except ImportError:
    log.error("Nornir-proxy - failed importing Nornir modules")
    HAS_NORNIR = False

try:
    from rich.tree import Tree
    from rich.live import Live
    from rich.progress import (
        track,
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TimeRemainingColumn,
        TimeElapsedColumn,
    )
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt
    from rich.console import Console
    from rich.pretty import pprint

    HAS_RICH = True
except ImportError:
    log.debug("Nornir-proxy - failed importing rich library")
    HAS_RICH = False

__virtualname__ = "nr"


def __virtual__():
    """
    Load this Runner module.
    """
    if HAS_SALT:
        # inject salt master file options dictionary in global space
        globals()["opts"] = salt.config.master_config(__opts__["conf_file"])
        opts["quiet"] = True  # make runners calls not emit results to cli
        # initialise runner client
        globals()["runner"] = salt.runner.RunnerClient(opts)
        return __virtualname__
    else:
        return False


# -----------------------------------------------------------------------------
# Private functions
# -----------------------------------------------------------------------------


def _start_rich(func):
    """
    Decorator function to initiate rich

    :param func: (obj) function to wrap
    """
    if HAS_RICH:
        globals()["console"] = Console()

    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def _run_job(
    tgt,
    fun,
    arg,
    kwarg,
    tgt_type,
    timeout,
    job_retry=0,
    progress="log",
    show_progress=False,
):
    """
    Helper function to send execution module command using ``client.run_job``
    method and collect results using ``client.get_event_iter_returns``. Implements
    basic retry mechanism.

    If ``client.get_event_iter_returns`` checks every second for job results, for minions
    that return no results after timeout expires, ``_run_job`` retries the job for such a minions
    until minions return results or ``job_retry`` threshold reached, in latter case ``error``
    message logged with job details.

    :param tgt: (str) target to use with ``client.run_job`` function
    :param tgt_type: (str) target type to use with ``client.run_job`` function
    :param fun: (str) function name to use with ``client.run_job`` function
    :param arg: (list) arguments list to use with ``client.run_job`` function
    :param kwarg: (dict) kwyword arguments dictionary to use with ``client.run_job`` function
    :param timeout: (int) timeout to use with ``client.run_job`` function
    :param job_retry: (int) times to retry the job
    :param progress: (str) progress display style, default is "log"
    :param show_progress: (bool) if True, prints execution progress
    """
    if HAS_SALT:
        # initiate local client to run execution module commands 'salt "*" ...'
        client = salt.client.LocalClient()
    else:
        return {}

    ret = {}
    attempt = 0
    minions_no_return = None
    stop_signal = Event()
    while attempt <= job_retry:
        stop_signal.clear()
        start_time = time.time()
        # publish job command
        pub_data = client.run_job(
            tgt=tgt, fun=fun, arg=arg, kwarg=kwarg, tgt_type=tgt_type, timeout=timeout
        )
        # check if no minions matched by target
        if "jid" not in pub_data:
            # kill local client instance
            if hasattr(client, "destroy"):
                client.destroy()
            raise CommandExecutionError(
                "No minions matched by tgt '{}', tgt_type '{}'".format(tgt, tgt_type)
            )
        if show_progress:
            events_thread = Thread(
                target=event,
                kwargs={
                    "jid": pub_data["jid"],
                    "stop_signal": stop_signal,
                    "progress": progress,
                },
                daemon=True,  # to not block once main process finishes
            )
            events_thread.start()
        # check for job results until timeout
        while (time.time() - start_time) < timeout:
            # print(">>> Waiting job return: {}".format(pub_data))
            job_results = client.get_event_iter_returns(timeout=1, **pub_data)
            # print(">>>> Got job results: {}".format(job_results))
            # form results
            for item in job_results:
                ret.update(item)
            # check if all minions returned results
            if set(pub_data["minions"]) == set(ret.keys()):
                minions_no_return = None
                break
            else:
                minions_no_return = set(pub_data["minions"]) - set(ret.keys())
        else:
            log.warning(
                "Nornir-runner:_run_job - {}s timeout; no results from {}; returned {}; jid {}; attempt: {}".format(
                    timeout,
                    list(minions_no_return),
                    list(ret.keys()),
                    pub_data["jid"],
                    attempt,
                )
            )
            # retry job but only for minions that did not return results
            attempt += 1
            tgt = list(minions_no_return)
            tgt_type = "list"
            # stop progress thread and wait for 5 seconds
            stop_signal.set()
            time.sleep(5)
            # inform user about retry
            log.info(
                "Retrying '{fun}' for '{tgt}', attempt {attempt}\n".format(
                    fun=fun, tgt=tgt, attempt=attempt
                )
            )
            continue
        # if we get to this point - job did not timeout and we received results from all minions
        if minions_no_return is None:
            break
    else:
        log.error(
            "Nornir-runner:_run_job - no results from minions '{}'; tgt: {}; fun: {}; tgt_type: {}; timeout: {}; job_retry: {}; kwarg: {}".format(
                minions_no_return, tgt, fun, tgt_type, timeout, job_retry, kwarg
            )
        )
    # stop eventloop thread
    if show_progress:
        stop_signal.set()
        events_thread.join(timeout=10)

    # kill local client instance
    if hasattr(client, "destroy"):
        client.destroy()

    return ret


def _form_ret_results(ret, job_results, ret_struct):
    """
    Helper function to form return results.

    :param ret: results return data
    :param job_results: job results to merge into ret
    :param ret_struct: results return structure - ``dictionary`` or ``list``
    """
    if ret_struct == "list" and isinstance(ret, list):
        for minion_id, result in job_results.items():
            if isinstance(result["ret"], str):
                ret.append(result["ret"])
            elif isinstance(result["ret"], list):
                for i in result["ret"]:
                    i["minion_id"] = minion_id
                    ret.append(i)
            else:
                raise TypeError(
                    "Unsupported result type '{}', supported str or list".format(
                        type(result["ret"])
                    )
                )
    elif ret_struct == "dictionary" and isinstance(ret, dict):
        for minion_id, result in job_results.items():
            # in case if execution done in batches - e.g. by nr.cfg - need
            # to merge results from multiple runs into a single string
            if isinstance(result["ret"], str):
                if minion_id in ret:
                    ret[minion_id] += "\n\n" + result["ret"]
                else:
                    ret[minion_id] = result["ret"]
            elif isinstance(result["ret"], list):
                for i in result["ret"]:
                    i["minion_id"] = minion_id
                    host = i.pop("host")
                    ret.setdefault(host, [])
                    ret[host].append(i)
            else:
                raise TypeError(
                    "Unsupported result type '{}', supported str or list".format(
                        type(result["ret"])
                    )
                )
    else:
        raise TypeError(
            "Unsupported combination of ret_struct and ret type: {} and {}".format(
                ret_struct, type(ret)
            )
        )


def _check_ret_struct(ret_struct):
    """
    Helper function to check return structure arguemnt correctness
    """
    if ret_struct == "dictionary":
        return {}
    elif ret_struct == "list":
        return []
    else:
        raise ValueError(
            "ret_struct  '{}' unsupported, supported 'dictionary' or 'list'".format(
                ret_struct
            )
        )


def _get_hosts_minions(hosts, tgt, tgt_type):
    """
    This function requests a list of hosts minions manage using Fx filters. This
    data can be used to narrow down minions targeting for the tasks.

    :param hosts: (list or dict) list of Nornir hosts/devices to find minion targets for
        or dictionary with Fx filters.
    :return: dictionary keyed by host name with values being list of minion ids
        that manage that host
    """
    # form Fx filters arguments
    if isinstance(hosts, list):
        Fx_filters = {"FL": hosts}
    elif isinstance(hosts, dict):
        Fx_filters = {k: v for k, v in hosts.items() if k in FFun_functions}
    # get minions hosts
    job_result = _run_job(
        tgt=tgt,
        fun="nr.nornir",
        arg=["hosts"],
        kwarg=Fx_filters,
        tgt_type=tgt_type,
        timeout=15,
        job_retry=1,
    )
    # form host to minions mapping
    ret = {
        host: minion_id
        for minion_id, result in job_result.items()
        for host in result["ret"]
    }
    # check if some hosts have no minions if FL filter was used
    if isinstance(hosts, list):
        requested_hosts = set(hosts)
        managed_hosts = set(ret.keys())
        if requested_hosts != managed_hosts:
            raise CommandExecutionError(
                "No minions found that manage hosts: {}".format(
                    ", ".join(list(requested_hosts.difference(managed_hosts)))
                )
            )
    # check if nothing matched
    if not ret:
        raise CommandExecutionError(
            "Hosts not found for filters '{}', minions tgt '{}', tgt_type '{}'".format(
                Fx_filters, tgt, tgt_type
            )
        )
    return ret


def _get_salt_nornir_event(stop_signal, tag, events_queue):
    """
    Helper function to get event from Event bus based on tag regex. Events enqued back
    into events_queue for consumption.

    Mainly used to capture event generatd by Nornir-Salt EventsProcessor.

    Need to use events_queue to catch and cache all events, initially coded _get_salt_nornir_event
    aa generator, but it was skipping/missing/not catching some events, due to parent
    function was processing previous event results and new events came at that exact time.

    :param stop_signal: (obj) Threading event object to signal if need to stop
    :param tag: (str) tag pattern of events to listen for
    :param events_queue: (obj) queue.Queue object to enqueue catched events
    """
    event_bus = salt.utils.event.get_event(
        "master", sock_dir=opts["sock_dir"], transport=opts["transport"], opts=opts
    )
    while not stop_signal.is_set():
        e = event_bus.get_event(
            wait=1,
            full=False,
            no_block=False,
            auto_reconnect=False,
            match_type="regex",
            tag=tag,
        )
        # event is None if wait timeout reached, need to continue to wait for more
        if e is None:
            continue
        events_queue.put(e)


# -----------------------------------------------------------------------------
# callable module function
# -----------------------------------------------------------------------------


def inventory(*args, **kwargs):
    """
    Function to return brief inventory data for certain hosts in a table format.

    :param FB: glob pattern matching hostnames of devices behind Nornir
    :param Fx: additional filters to filter hosts, e.g. FG, FP, FL etc.
    :param tgt: nornir proxy minion target, by default targets all - "proxy:proxytype:nornir"
    :param tgt_type: SALT targeting type to use, by default "pillar"
    :param verbose: boolean, returns ``nr.cli`` output as is if True, flattens to dictionary
        keyed by devices hostnames if False, default False
    :param job_retry: how many times to retry command if no return from minions, default 0
    :param job_timeout: seconds to wait for return from minions, overrides
        ``--timeout`` option, default 30s
    :param table: (str, dict or bool) supplied to TabulateFormatter under ``table`` keyword
        to control output table formatting
    :param headers: (list) headers list, default ``["minion", "host", "ip", "platform", "groups"]``
    :param reverse: (bool) reverse table order if True, defualt is False
    :param sortby: (str) header to sort table by, default is ``host``


    Sample Usage::

        salt-run nr.inventory host_name_id
        salt-run nr.inventory FB="host_name_id" FP="10.1.2.0/24"

    If it takes too long to get output because of non-responding/unreachable minions,
    specify ``--timeout`` or ``job_timeout`` option to shorten waiting time, ``job_timeout``
    overrides ``--timeout``. Alternatively, instead of targeting all nornir based proxy
    minions, ``tgt`` and ``tgt_type`` can be used to target a subset of them::

        salt-run nr.inventory host_name_id --timeout=10
        salt-run nr.inventory host_name_id job_timeout=10 tgt="nornir-proxy-id" tgt_type="glob"

    Sample output::

        [root@localhost /]# salt-run nr.inventory IOL1
        +---+--------+----------+----------------+----------+--------+
        |   | minion |   host   |       ip       | platform | groups |
        +---+--------+----------+----------------+----------+--------+
        | 0 |  nrp1  |   IOL1   | 192.168.217.10 |   ios    |  lab   |
        +---+--------+----------+----------------+----------+--------+
    """
    ret = []

    # get hostname target
    if len(args) > 0:
        kwargs["FB"] = args[0]
    elif not any(F in kwargs for F in FFun_functions):
        raise CommandExecutionError(
            "Nornir-runner:inventory - hosts filter not provided, args: '{}', kwargs: '{}'".format(
                args, kwargs
            )
        )

    # get other arguments
    tgt = kwargs.pop("tgt", "proxy:proxytype:nornir")
    tgt_type = kwargs.pop("tgt_type", "pillar")
    verbose = kwargs.pop("verbose", False)
    timeout = kwargs.pop("job_timeout", 300)
    job_retry = kwargs.pop("job_retry", 0)

    # get table formatter arguments
    table = kwargs.pop("table", {"tablefmt": "pretty", "showindex": True})
    headers = kwargs.pop("headers", ["minion", "host", "ip", "platform", "groups"])
    sortby = kwargs.pop("sortby", "hostname")
    reverse = kwargs.pop("reverse", False)

    # send nr.nornir inventory command
    query_results = _run_job(
        tgt=tgt,
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={k: v for k, v in kwargs.items() if not k.startswith("_")},
        tgt_type=tgt_type,
        timeout=timeout,
        job_retry=job_retry,
    )

    # work with results
    if verbose:
        ret = query_results
    else:
        for minion_id, result in query_results.items():
            for host_name, host_data in result.get("ret", {}).get("hosts", {}).items():
                ret.append(
                    {
                        "minion": minion_id,
                        "host": host_data["name"],
                        "ip": host_data["hostname"],
                        "platform": host_data["platform"],
                        "groups": ",".join(host_data.get("groups", [])),
                    }
                )
        # check if need to pass ret via tabulate
        if table:
            ret = TabulateFormatter(
                ret, tabulate=table, headers=headers, sortby=sortby, reverse=reverse
            )
    return ret


def call(*args, **kwargs):
    """
    Method to call any Nornir Proxy Minion Exection Module function agains minions. By default this function
    targets all Nornir Proxy Minions, allowing to simplify targeting hosts managed by them.

    :param fun: (str) Nornir Proxy Minion Exection Module function name e.g. ``cli, cfg, nc, gnmi`` etc.
    :param tgt: (str) SaltStack Nornir Proxy Minions to target, targets all of them by default - ``proxy:proxytype:nornir``
    :param tgt_type: (str) SaltStack targeting type to use, default is ``pillar``
    :param job_retry: (int) how many times to retry if no results returned from all minions, default 0
    :param timeout: (int) seconds to wait for results from minions before retry, default 300s
    :param progress: progress display type to use - bars, raw, log, if False, no progress displayed
    :param ret_struct: results return structure, default is ``dictionary``, also can be ``list``
    :param args: (list) any other arguments to use with call function
    :param kwargs: (dict) any other keyword arguments to use with call function

    Sample Usage::

        salt-run nr.call fun="cfg" "logging host 1.2.3.4" FC="CORE"
        salt-run nr.call cli "show clock" FB="*" tgt="nr-minion-id*" tgt_type="glob"
    """
    ret_struct = kwargs.pop("ret_struct", "dictionary")
    ret = _check_ret_struct(ret_struct)
    args = list(args)
    fun = args.pop(0) if len(args) >= 1 else kwargs.pop("fun")
    tgt = kwargs.pop("tgt", "proxy:proxytype:nornir")
    tgt_type = kwargs.pop("tgt_type", "pillar")
    timeout = kwargs.pop("timeout", 300)
    job_retry = kwargs.pop("job_retry", 0)
    progress = kwargs.pop("progress", "log")

    # get hosts to minions mapping to form tgt value
    hosts_minions = _get_hosts_minions(kwargs, tgt, tgt_type)

    # run job
    job_results = _run_job(
        tgt=list(set(hosts_minions.values())),
        fun="nr.{}".format(fun),
        arg=args,
        kwarg={
            **kwargs,
            "to_dict": False,
            "event_progress": True if progress else False,
        },
        tgt_type="list",
        timeout=timeout,
        job_retry=job_retry,
        progress=progress if isinstance(progress, str) else None,
        show_progress=True if progress else False,
    )

    _form_ret_results(ret, job_results, ret_struct)

    return ret


def event(jid="all", tag=None, progress="log", stop_signal=None):
    """
    Function to listen to events emited by Nornir Proxy Minions. Matched
    event printed to terminal.

    :param tag: (str) tag regex string, default is ``nornir\-proxy/.*``
    :param jid: (int, str) Job ID to listen events for, default is ``all``
    :param progress: (str) progress display mode - ``log``, ``raw``, ``bars``, ``tree``
    :param stop_signal: (obj) thread Event object, stops listening to events if ``stop_signal.is_set()``,
        if ``stop_signal is None``, listens and print events until keyboard interrupt hit - ``ctrl+c``

	``bars`` and ``tree`` progress display modes use Rich library, to properly display various
	symbols and characters need to make sure to use utf-8 enocding for your environment,
	to ensure that issue these commands in your terminal::

		[root@salt-master ~]# PYTHONIOENCODING=utf-8
		[root@salt-master ~]# export PYTHONIOENCODING
    """
    stop_signal = stop_signal or Event()
    events_queue = queue.Queue()
    tag = (
        tag
        if tag
        else (
            r"nornir\-proxy\/.*"
            if jid == "all"
            else r"nornir\-proxy\/{jid}\/.*".format(jid=jid)
        )
    )
    # start events thread
    listen_events_thread = Thread(
        target=_get_salt_nornir_event,
        kwargs={"stop_signal": stop_signal, "tag": tag, "events_queue": events_queue},
        daemon=True,  # to not block once main process finishes
    )
    listen_events_thread.start()
    # display events
    if HAS_RICH and progress == "bars":
        tasks = {}
        stop_events_loop = Event()
        rich_progress = Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            TextColumn("{task.percentage:>3.0f}%"),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            TextColumn("{task.fields[info]}"),
            TextColumn("{task.fields[status]}"),
            refresh_per_second=5,
        )
        # listen to events indefinitely if stop_signal is None
        with rich_progress:
            while True:
                try:
                    e = events_queue.get(timeout=1)
                except queue.Empty:
                    continue
                finally:
                    # check if need to finish
                    if stop_signal.is_set() and all(
                        [t.finished for t in rich_progress.tasks]
                    ):
                        stop_events_loop.set()
                        break
                edata = e["data"]
                jid = edata["jid"]
                task_type = edata["task_type"]
                task_event = edata["task_event"]
                status = edata["status"]
                task_name = edata["task_name"]
                status_str = (
                    f"[red]{status}" if status == "FAILED" else f"[green]{status}"
                )
                description_str = (
                    "[blue]{timestamp}[/]:{jid}:[bright_magenta]{function}[/]"
                )
                # catch task started events and add new progress bar
                if task_type == "task" and task_event == "started":
                    # if job runs on multiple proxy minions
                    if jid in tasks:
                        task = rich_progress.tasks[tasks[jid]]
                        task.total += len(edata["hosts"])
                        rich_progress.update(tasks[jid])
                    else:
                        total = len(edata["hosts"])
                        description = description_str.format(**edata)
                        info = "[cyan]{}[/]:{}".format(
                            task_type, task_name.split(".")[-1]
                        )
                        tasks[jid] = rich_progress.add_task(
                            description, total=total, info=info, status=status
                        )
                # catch task instance end events to advance progress bar
                elif task_type == "task_instance" and task_event == "completed":
                    if jid in tasks:
                        task = rich_progress.tasks[tasks[jid]]
                        if status == "PASSED":
                            rich_progress.update(tasks[jid], advance=1)
                        if task.completed >= task.total or status == "FAILED":
                            rich_progress.tasks[tasks[jid]].fields[
                                "status"
                            ] = status_str
                elif task_type == "task" and task_event == "completed":
                    if jid in tasks:
                        task = rich_progress.tasks[tasks[jid]]
                        if task.completed >= task.total or status == "FAILED":
                            rich_progress.tasks[tasks[jid]].fields[
                                "status"
                            ] = status_str
                        rich_progress.stop_task(tasks[jid])
                        # stop all subtasks for this jid and update their status
                        for task in tasks:
                            if task.startswith(jid):
                                rich_progress.tasks[tasks[task]].fields[
                                    "status"
                                ] = status_str
                                rich_progress.stop_task(tasks[task])
                # handle subtask progress
                elif task_type == "subtask" and task_event == "started":
                    tid = "{jid}:{task_name}".format(**edata)
                    if tid not in tasks and jid in tasks:
                        total = rich_progress.tasks[tasks[jid]].total
                        description = description_str.format(**edata)
                        info = "[cyan]{task_type}[/]:{task_name}".format(**edata)
                        tasks[tid] = rich_progress.add_task(
                            description, total=total, info=info, status=status
                        )
                    # update task total if got additional start events
                    elif tid in tasks and jid in tasks:
                        task = rich_progress.tasks[tasks[tid]]
                        task.total = rich_progress.tasks[tasks[jid]].total
                        rich_progress.update(tasks[tid])
                elif task_type == "subtask" and task_event == "completed":
                    tid = "{jid}:{task_name}".format(**edata)
                    if tid in tasks:
                        task = rich_progress.tasks[tasks[tid]]
                        if status == "PASSED":
                            rich_progress.update(tasks[tid], advance=1)
                        if task.completed >= task.total or status == "FAILED":
                            rich_progress.tasks[tasks[tid]].fields[
                                "status"
                            ] = status_str
                # hide tasks beyond vertical overflow point
                hght = console.size.height - 2
                for tindx, _ in enumerate(rich_progress.tasks[:-hght]):
                    rich_progress.update(tindx, visible=False)
    elif progress == "tree":
        pass
    elif progress == "raw":
        while not stop_signal.is_set():
            try:
                e = events_queue.get(timeout=1)
                print(e)
            except queue.Empty:
                continue
    # handle 'log' progress mode
    else:
        while not stop_signal.is_set():
            try:
                e = events_queue.get(timeout=1)
            except queue.Empty:
                continue
            edata = e["data"]
            # form message string and print it
            if edata["task_type"] == "task":
                edata["hs"] = ", ".join(edata["hosts"])
            elif edata["task_type"] in ["task_instance", "subtask"]:
                edata["hs"] = edata["host"]
            msg = "{timestamp}:{jid}:{proxy_id}:w{worker_id} {function} {hs} {task_type} {task_event} {task_name}; {status}"
            print(msg.format(**edata))


@_start_rich
def cfg(
    host_batch=0,
    first_batch=1,
    fromdir=None,
    fromdict=None,
    tgt="proxy:proxytype:nornir",
    tgt_type="pillar",
    job_timeout=300,
    job_retry=0,
    progress="log",
    saltenv="base",
    interactive=True,
    ret_struct="dictionary",
    dry_run=False,
    **kwargs,
):
    """
    Function that uses Salt-Nornir execution module ``nr.cfg`` function to
    configure network devices over CLI sourcing configuration from file system
    directory or dictionary.

    In interactive mode this function requests input from user on the actions to
    perform for each batch of hosts, helping to apply confiugration to devices in a
    manually controlled manner.

    :param host_batch: number of hosts to target at a time, targets all by default
    :param first_batch: number of batch to start with, allows to skip previous batches
    :param fromdir: directory to source per-host configuration files from and
        to form host targets list based on files names. Files names must contain only
        device host name, but can have any extension e.g. ``ceos1.txt``
    :param fromdict: (dict) dictionary keyed by host names with values of configuration to apply
    :param tgt: SaltStack Nornir Proxy Minions to target, targets all of them by default
    :param tgt_type: SaltStack targeting type to use
    :param job_retry: how many times to retry if no results returned from all minions within given timeout
    :param job_timeout: seconds to wait for results from minions before retry, default 300s
    :param progress: progress display type to use - bars, raw, log, if False, no progress displayed
    :param saltenv: SaltStack environment to pull fromdir data from
    :param ret_struct: results return structure, default is ``dictionary``, also can be ``list``
    :param interactive: (bool) if True (Default), asks user for input for each batch of hosts
    :param dry_run: (bool) if True, uses ``nr.cfg_gen`` execution module function to test
        configuration rendering
    :param kwargs: any additional arguments to pass to ``nr.cfg`` execution module function

    Sample usage::

        salt-run nr.cfg fromdict='{"ceos*": ["logging host 1.2.3.4", "logging host 1.2.3.5"]}'
        salt-run nr.cfg fromdir="salt://templates/config_xyz/" host_batch=5
        salt-run nr.cfg fromdir="salt://templates/config_xyz/" host_batch=5 first_batch=10 add_details=False

    """
    ret = _check_ret_struct(ret_struct)
    fromdict = fromdict or {}

    if fromdir:
        # form abs_files_path
        if fromdir.startswith("salt://"):
            abs_files_path = os.path.join(
                os.path.split(__opts__["conf_file"])[0], fromdir.split("//")[1:][0]
            )
        elif os.path.isdir(fromdir):
            abs_files_path = os.path.abspath(fromdir)
        else:
            raise CommandExecutionError(
                "Failed to locate fromdir directory '{}'".format(fromdir)
            )
        # form a list of absolute filepaths to files
        files = [
            os.path.join(abs_files_path, f)
            for f in os.listdir(abs_files_path)
            if os.path.isfile(os.path.join(abs_files_path, f))
        ]
        # extract file names without extension
        hosts = [os.path.split(os.path.splitext(f)[0])[1] for f in files]
        # load files content to a dictionary
        for hostname, filepath in zip(hosts, files):
            with open(filepath, "r", encoding="utf-8") as f:
                fromdict[hostname] = f.read()
    elif fromdict:
        hosts = list(fromdict.keys())
    else:
        raise CommandExecutionError(
            "nr.cfg runner expect 'fromdict' or 'fromdir' argument"
        )

    # sort the hosts to make sure order is always the same
    hosts = sorted(hosts)
    # get a dictionary keyed by hosts with minions lists
    hosts_minions = _get_hosts_minions(hosts, tgt, tgt_type)
    # calculate hosts batch size, number of batches and first batch
    host_batch = len(hosts) if host_batch == 0 else min(host_batch, len(hosts))
    batches_num = round(len(hosts) / host_batch)
    first_batch = min(first_batch, batches_num)

    # send config to devices
    for indx in range(0, len(hosts), host_batch):
        batch_num = round(indx / host_batch) + 1
        # check if need to skip the batch
        if batch_num < first_batch:
            continue
        chunk = hosts[indx : indx + host_batch]
        hconfig = {h: fromdict[h] for h in chunk}
        if interactive:
            console.rule("Batch {} / {}".format(batch_num, batches_num), style="green")
            console.print("Ready to configure: {}".format(", ".join(chunk)))
            reply = Prompt.ask("Display configuration", choices=["y", "n"], default="n")
            if reply == "y":
                for h, hcfg in hconfig.items():
                    console.print(f"[bold green]--- {h} ---[/]\n{hcfg}")
            reply = Prompt.ask(
                "Configure, Exit, Skip", choices=["c", "e", "s"], default="c"
            )
            if reply == "e":
                console.print("Exiting...")
                return ret
            elif reply == "s":
                continue
        # run the job through saltstack
        job_results = _run_job(
            tgt=list(set([hosts_minions[i] for i in chunk])),
            fun="nr.cfg_gen" if dry_run else "nr.cfg",
            arg=[],
            kwarg={
                **kwargs,
                "config": hconfig,
                "FL": chunk,
                "to_dict": False,
                "event_progress": True if progress else False,
            },
            tgt_type="list",
            timeout=job_timeout,
            job_retry=job_retry,
            progress=progress if isinstance(progress, str) else None,
            show_progress=True if progress else False,
        )
        if interactive:
            console.print("Configured: {}".format(", ".join(chunk)))
            reply = Prompt.ask(
                "Display batch {} results yes/no/table".format(batch_num),
                choices=["y", "n", "t"],
                default="n",
            )
            if reply in ["y", "t"]:
                for minion_id, result in job_results.items():
                    if isinstance(result["ret"], list) and reply == "y":
                        for i in result["ret"]:
                            console.print(
                                f"[bold green]--- {minion_id}:{i['host']} ---[/]"
                            )
                            console.print(f"{i['result']}")
                            if i["exception"]:
                                console.print(f"Exception: {i['exception']}")
                    elif isinstance(result["ret"], list) and reply == "t":
                        console.print(f"[bold green]--- {minion_id} ---[/]")
                        console.print(
                            TabulateFormatter(
                                result=result["ret"],
                                tabulate={"tablefmt": "simple"},
                                headers=["host", "result", "exception"],
                                sortby="host",
                            )
                        )
                    else:
                        console.print(f"[bold green]--- {minion_id} ---[/]")
                        console.print(result["ret"])
        _form_ret_results(ret, job_results, ret_struct)
    return ret


def make_plugin(kind, name=None):
    """
    Function to generate boilerplate code for Salt-Nornir plugins
    using Nornir-Salt MakePlugin utility function.

    :param kind: (str) plugin kind to generate code for
    :param name: (str) plugin file name to use

    Supported plugin kinds:

    * ``task`` - creates Nornir task plugin in current directory
    * ``test`` - creates ``TestsProcessor`` custom test function in current directory

    Sample usage:

        salt-run nr.make_plugin dir
        salt-run nr.make_plugin ?
        salt-run nr.make_plugin task name=run_check_commands
    """
    return MakePlugin(kind=kind, name=name)


def service(*args, **kwargs):
    """
    Function to deploy service on a set of network devices.

    Sample usage::

        salt-run nr.service activate Loopback1234
        salt-run nr.service deactivate Loopback1234
        salt-run nr.service activate Loopback1234 FB="host-1" data="{'host-1': {'ip': '10.0.0.1', 'mask': 32}}"
        salt-run nr.service list Loopback1234
        salt-run nr.service dry-run Loopback1234
    """
    pass
