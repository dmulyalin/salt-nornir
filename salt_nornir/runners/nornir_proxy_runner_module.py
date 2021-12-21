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
from threading import Thread, Event

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

    HAS_NORNIR = True
except ImportError:
    log.error("Nornir-proxy - failed importing Nornir modules")
    HAS_NORNIR = False

try:
    from rich.tree import Tree
    from rich.live import Live
    from rich.progress import track
    from rich.progress import (
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

    HAS_RICH = True
except ImportError:
    log.debug("Nornir-proxy - failed importing rich library")
    HAS_RICH = False

if HAS_SALT:
    opts = salt.config.master_config("/etc/salt/master")

__virtualname__ = "nr"


def __virtual__():
    """
    Load this Runner module.
    """
    if HAS_SALT:
        return __virtualname__
    else:
        return False


# -----------------------------------------------------------------------------
# Private functions
# -----------------------------------------------------------------------------


def _run_job(
    tgt,
    fun,
    arg,
    kwarg,
    tgt_type,
    timeout,
    job_retry=0,
    mode="log",
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
    :param mode: (str) progress display style, default is "log"
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
        if show_progress:
            events_thread = Thread(
                target=event,
                kwargs={
                    "jid": pub_data["jid"],
                    "stop_signal": stop_signal,
                    "mode": mode,
                },
            )
            events_thread.start()
        # check for job results until timeout
        while (time.time() - start_time) < timeout:
            job_results = client.get_event_iter_returns(timeout=1, **pub_data)
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
        events_thread.join(timeout=5)

    # kill local client instance
    client.destroy()

    return ret


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
    elif not any(F in kwargs for F in ["FB", "FP", "FO", "FG", "FP", "FL", "FC", "FR"]):
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
    :param tgt: (str) SaltStack Nornir Proxy Minions to target, targets all of them by default - ``roxy:proxytype:nornir``
    :param tgt_type: (str) SaltStack targeting type to use, default is ``pillar``
    :param verbose: (bool) returns job results output as is if True, flattens to dictionary
        keyed by devices hostnames if False (default)
    :param job_retry: (int) how many times to retry if no results returned from all minions, default 0
    :param timeout: (int) seconds to wait for results from minions before retry, default 300s
    :param show_progress: (bool) if True (default), adds ``event_progress`` argument to call function and prints
        execution progress using ``event`` function
    :param mode: (str) progress display style, default is "log"
    :param args: (list) any other arguments to use with call function
    :param kwargs: (dict) any other keyword arguments to use with call function

    Sample Usage::

        salt-run nr.call fun="cfg" "logging host 1.2.3.4" FC="CORE"
        salt-run nr.call cli "show clock" FB="*" tgt="nr-minion-id*" tgt_type="glob"
    """
    ret = {}
    args = list(args)
    fun = args.pop(0) if len(args) >= 1 else kwargs.pop("fun")
    tgt = kwargs.pop("tgt", "proxy:proxytype:nornir")
    tgt_type = kwargs.pop("tgt_type", "pillar")
    verbose = kwargs.pop("verbose", False)
    timeout = kwargs.pop("timeout", 300)
    job_retry = kwargs.pop("job_retry", 0)
    mode = kwargs.pop("mode", "log")
    show_progress = kwargs.pop("show_progress", True)
    kwargs["event_progress"] = True if show_progress else False

    # run job
    job_results = _run_job(
        tgt=tgt,
        fun="nr.{}".format(fun),
        arg=args,
        kwarg={k: v for k, v in kwargs.items() if not k.startswith("_")},
        tgt_type=tgt_type,
        timeout=timeout,
        job_retry=job_retry,
        mode=mode,
        show_progress=show_progress,
    )

    # work with command results
    if verbose:
        ret = job_results
    else:
        for minion_id, result in job_results.items():
            if result["ret"] and isinstance(result["ret"], dict):
                ret.update(result["ret"])
            else:
                ret[minion_id] = result["ret"]

    return ret


def event(jid="all", tag=None, mode="log", stop_signal=None):
    """
    Function to listen to events emited by Nornir Proxy Minions. Matched
    event printed to terminal.

    :param tag: (str) tag regex string, default is ``nornir\-proxy/.*``
    :param jid: (int, str) Job ID to listen events for, default is ``all``
    :param mode: (str) display mode - ``log``, ``raw``
    :param stop_signal: (obj) thread Event object, stops listening to events if ``stop_signal.is_set()``,
        if ``stop_signal is None``, listens and print events until keyboard interrupt hit - ``ctrl+c``
    """
    tag = (
        tag
        if tag
        else (
            r"nornir\-proxy\/.*"
            if jid == "all"
            else r"nornir\-proxy\/{jid}\/.*".format(jid=jid)
        )
    )
    event = salt.utils.event.get_event(
        "master", sock_dir=opts["sock_dir"], transport=opts["transport"], opts=opts
    )
    # display events
    if HAS_RICH and mode == "bars":
        tasks = {}
        progress = Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "{task.completed}/{task.total}",
            TimeElapsedColumn(),
            TextColumn("{task.fields[info]}"),
            refresh_per_second=3,
        )
        # listen to events indefinitely if stop_signal is None
        with progress:
            while (
                True
                if stop_signal is None
                else not (
                    stop_signal.is_set() and all([t.finished for t in progress.tasks])
                )
            ):
                # get event
                e = event.get_event(
                    wait=1,
                    full=False,
                    no_block=False,
                    auto_reconnect=False,
                    match_type="regex",
                    tag=tag,
                )
                if e is None:
                    continue
                edata = e["data"]
                # catch task started events and add new progress bar
                if edata["task_type"] == "task" and edata["task_event"] == "started":
                    tasks[edata["jid"]] = [
                        progress.add_task(
                            "{jid}:{proxy_id}:{function}".format(**edata),
                            total=len(edata["hosts"]),
                            info="{task_type}".format(**edata),
                        ),
                        len(edata["hosts"]),
                    ]
                elif (
                    edata["task_type"] == "task_instance"
                    and edata["task_event"] == "completed"
                ):
                    progress.update(tasks[edata["jid"]][0], advance=1)
                elif (
                    edata["task_type"] == "task" and edata["task_event"] == "completed"
                ):
                    progress.stop_task(tasks.pop(edata["jid"])[0])
                # handle subtask progress
                elif (
                    edata["task_type"] == "subtask"
                    and edata["task_event"] == "started"
                    and "{jid}:{task_name}".format(**edata) not in tasks
                ):
                    tasks["{jid}:{task_name}".format(**edata)] = progress.add_task(
                        "{jid}:{proxy_id}:{function}".format(**edata),
                        total=tasks[edata["jid"]][1],
                        info="{task_type}:{task_name}".format(**edata),
                    )
                elif (
                    edata["task_type"] == "subtask"
                    and edata["task_event"] == "completed"
                ):
                    progress.update(
                        tasks["{jid}:{task_name}".format(**edata)], advance=1
                    )
    elif mode == "raw":
        # listent to events indefinitely if stop_signal is None
        while True if stop_signal is None else not stop_signal.is_set():
            # get event
            e = event.get_event(
                wait=1,
                full=False,
                no_block=False,
                auto_reconnect=False,
                match_type="regex",
                tag=tag,
            )
            if e is None:
                continue
            print(e)
    else:
        # listent to events indefinitely if stop_signal is None
        while True if stop_signal is None else not stop_signal.is_set():
            # get event
            e = event.get_event(
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
            edata = e["data"]
            # form message string and print it
            if edata["task_type"] == "task":
                msg = "{timestamp}: {proxy_id} {function} {hosts} {task_type} {task_event} '{task_name}', status - {status}".format(
                    **edata
                )
            elif edata["task_type"] in ["task_instance", "subtask"]:
                msg = "{timestamp}: {proxy_id} {function} {host} {task_type} {task_event} '{task_name}', status - {status}".format(
                    **edata
                )
            print(msg)


def service(*args, **kwargs):
    """
    Function to deploy service on a set of network devices.

    Sample usage::

        salt-run nr.service activate Loopback1234
        salt-run nr.service deactivate Loopback1234
        salt-run nr.service activate Loopback1234 FB="host-1" pillar="{'host-1': {'ip': '10.0.0.1', 'mask': 32}}"
        salt-run nr.service list Loopback1234
        salt-run nr.service dry-run Loopback1234
    """
    pass
