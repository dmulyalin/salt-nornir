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

.. list-table:: Runner Functions Summary
   :widths: 15 85
   :header-rows: 1

   * - Name
     - Description
   * - `nr.call`_
     - Method to call any Nornir Proxy Minion Execution Module function against minions
   * - `nr.cfg`_
     - Runner that uses Salt-Nornir execution module function ``nr.cfg`` to configure devices over CLI
   * - `nr.event`_
     - Listen to events emitted by Nornir Proxy Minions and log progress to terminal screen
   * - `nr.inventory`_
     - Function to return brief inventory data for certain hosts in a table format
   * - `nr.make_plugin`_
     - Function to generate boilerplate code for Salt-Nornir plugins
   * - `nr.diagram`_
     - Function to retrieve output from devices and produce diagram using N2G library

nr.call
+++++++
.. autofunction:: salt_nornir.runners.nornir_proxy_runner_module.call

nr.cfg
++++++
.. autofunction:: salt_nornir.runners.nornir_proxy_runner_module.cfg

nr.event
++++++++
.. autofunction:: salt_nornir.runners.nornir_proxy_runner_module.event

nr.inventory
++++++++++++
.. autofunction:: salt_nornir.runners.nornir_proxy_runner_module.inventory

nr.make_plugin
++++++++++++++
.. autofunction:: salt_nornir.runners.nornir_proxy_runner_module.make_plugin

nr.diagram
++++++++++++++
.. autofunction:: salt_nornir.runners.nornir_proxy_runner_module.diagram
"""
# Import python libs
import logging
import time
import os
import pprint
import queue
import copy

from threading import Thread, Event
from salt_nornir.pydantic_models import (
    model_runner_nr_inventory,
    model_runner_nr_call,
    model_runner_nr_event,
    model_runner_nr_cfg,
    model_runner_nr_diagram,
    SaltNornirMasterModel,
)

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
    from nornir_salt.utils.yangdantic import ValidateFuncArgs

    HAS_NORNIR = True
except ImportError:
    log.error("Nornir-proxy - failed importing Nornir modules")
    HAS_NORNIR = False

try:
    from rich import print as rich_print
    from rich.tree import Tree
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    from rich.prompt import Prompt
    from rich.console import Console
    from rich.pretty import pprint

    HAS_RICH = True
except ImportError:
    log.warning("Nornir-proxy - failed importing rich library")
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
    raise_no_tgt_match=True,
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
    :param kwarg: (dict) keyword arguments dictionary to use with ``client.run_job`` function
    :param timeout: (int) timeout to use with ``client.run_job`` function
    :param job_retry: (int) times to retry the job
    :param progress: (str) progress display style, default is "log"
    :param show_progress: (bool) if True, prints execution progress
    :param raise_no_tgt_match: (bool) if True (default) raises error if no hosts matched
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
        # print(pub_data)
        if "jid" not in pub_data:
            # kill local client instance
            if hasattr(client, "destroy"):
                client.destroy()
            if raise_no_tgt_match:
                raise CommandExecutionError(
                    "No minions matched by tgt '{}', tgt_type '{}'".format(
                        tgt, tgt_type
                    )
                )
            else:
                return {}
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
        # collect job results until timeout
        while (time.time() - start_time) < timeout:
            job_results = client.get_cli_returns(
                jid=pub_data["jid"],
                minions=pub_data["minions"],
                timeout=1,
                tgt=tgt,
                tgt_type=tgt_type,
            )
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
    Helper function to check return structure argument correctness
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


def _get_hosts_minions(hosts, tgt, tgt_type, raise_no_tgt_match=True):
    """
    This function requests a list of hosts minions manage using Fx filters. This
    data can be used to narrow down minions targeting for the tasks.

    :param hosts: (list or dict) list of Nornir hosts/devices to find minion targets for
        or dictionary with Fx filters.
    :param raise_no_tgt_match: (bool) if True, raise exception of no return from devices
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
    if not ret and raise_no_tgt_match:
        raise CommandExecutionError(
            "Hosts not found for filters '{}', minions tgt '{}', tgt_type '{}'".format(
                Fx_filters, tgt, tgt_type
            )
        )
    return ret


def _get_salt_nornir_event(stop_signal, tag, events_queue):
    """
    Helper function to get event from Event bus based on tag regex. Events placed back
    into events_queue for consumption.

    Mainly used to capture event generated by Nornir-Salt EventsProcessor.

    Need to use events_queue to catch and cache all events, initially coded _get_salt_nornir_event
    as generator, but it was skipping/missing/not catching some events, due to parent
    function was processing previous event results and new events came at that exact time.

    :param stop_signal: (obj) Threading event object to signal if need to stop
    :param tag: (str) tag pattern of events to listen for
    :param events_queue: (obj) queue.Queue object to enqueue captured events
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


def _built_inventory_tree(inventory_data, nodes_data):
    """
    Helper function to form inventory tree representation

    :param inventory_data: 'nr.nornir inventory' call dictionary results
    :param nodes_data: 'grains.item node-name' call dictionary results
    """
    inventory_tree = Tree("[bold cyan]Salt-Master")
    tree_data = {}
    # recursively from tree structure
    for minion_id in sorted(inventory_data.keys()):
        hosts_data = inventory_data[minion_id].get("ret", {}).get("hosts", {})
        # skip if no hosts matched for this minion
        if not hosts_data:
            continue
        # create tree for minion_host if not created already
        minion_host = nodes_data[minion_id]["ret"]["nodename"]
        tree_data.setdefault(
            minion_host, inventory_tree.add("[bold blue]{} node".format(minion_host))
        )
        # form minion tree object
        minion_tree = tree_data[minion_host].add(
            f"[bold green]{minion_id} proxy-minion"
        )
        # add hosts to the tree
        for host_name, host_data in hosts_data.items():
            minion_tree.add(
                "[bold purple]{name}[/] {ip}; platform: {platform}; groups: {groups}".format(
                    name=host_data["name"],
                    ip=host_data["hostname"],
                    platform=host_data["platform"],
                    groups=", ".join(host_data["groups"] or ["None"]),
                )
            )

    rich_print(inventory_tree)
    return ""


# -----------------------------------------------------------------------------
# callable module function
# -----------------------------------------------------------------------------


@ValidateFuncArgs(model_runner_nr_inventory)
def inventory(*args, **kwargs):
    """
    Function to query inventory data for Nornir hosts and present it in various formats.

    :param FB: first argument - glob pattern matching hostnames of devices behind Nornir
    :param Fx: additional filters to filter hosts, e.g. FG, FP, FL etc.
    :param tgt: nornir proxy minion target, by default targets all - "proxy:proxytype:nornir"
    :param tgt_type: SALT targeting type to use, by default "pillar"
    :param verbose: boolean, returns ``nr.nornir inventory`` output as is if True, flattens to dictionary
        keyed by devices hostnames if False, default False
    :param job_retry: how many times to retry command if no return from minions, default 0
    :param job_timeout: seconds to wait for return from minions, overrides
        ``--timeout`` option, default 30s
    :param table: (str, dict or bool) supplied to TabulateFormatter under ``table`` keyword
        to control output table formatting
    :param headers: (list) headers list, default ``["minion", "host", "ip", "platform", "groups"]``
    :param reverse: (bool) reverse table order if True, default is False
    :param sortby: (str) header to sort table by, default is ``host``
    :param tree: (bool) display inventory in tree format instead of table

    Sample Usage::

        salt-run nr.inventory ceos1
        salt-run nr.inventory FB="host_name_id" FP="10.1.2.0/24"
        salt-run nr.inventory "*" tree=True
        salt-run nr.inventory "ceos2" verbose=True

    If it takes too long to get output because of non-responding/unreachable minions,
    specify ``--timeout`` or ``job_timeout`` option to shorten waiting time, ``job_timeout``
    overrides ``--timeout``. Alternatively, instead of targeting all nornir based proxy
    minions, ``tgt`` and ``tgt_type`` can be used to target a subset of them::

        salt-run nr.inventory core-sw-31 --timeout=10
        salt-run nr.inventory edge-router-42 job_timeout=10 tgt="nornir-proxy-id" tgt_type="glob"

    Sample ``table`` formatted output::

        [root@localhost /]# salt-run nr.inventory IOL1
        +---+--------+----------+----------------+----------+--------+
        |   | minion |   host   |       ip       | platform | groups |
        +---+--------+----------+----------------+----------+--------+
        | 0 |  nrp1  |   IOL1   | 192.168.217.10 |   ios    |  lab   |
        +---+--------+----------+----------------+----------+--------+

    Sample ``tree`` formatted output::

        Salt-Master
        ├── salt-minion-nrp1 node
        │   └── nrp1 proxy-minion
        │       ├── ceos1 10.0.1.4; platform: arista_eos; groups: lab, eos_params
        │       └── ceos2 10.0.1.5; platform: arista_eos; groups: lab, eos_params
        └── salt-minion-nrp2 node
            └── nrp2 proxy-minion
                ├── csr1000v-1 sandbox-iosxe-latest-1.cisco.com; platform: cisco_ios; groups: None
                ├── iosxr1 sandbox-iosxr-1.cisco.com; platform: cisco_xr; groups: None
                └── nxos1 sandbox-nxos-1.cisco.com; platform: nxos_ssh; groups: None
    """
    ret = []

    # get hostname target
    if len(args) > 0:
        kwargs["FB"] = args[0]

    # get other arguments
    tgt = kwargs.pop("tgt", "proxy:proxytype:nornir")
    tgt_type = kwargs.pop("tgt_type", "pillar")
    verbose = kwargs.pop("verbose", False)
    timeout = kwargs.pop("job_timeout", 300)
    job_retry = kwargs.pop("job_retry", 0)
    tree = kwargs.pop("tree", False)

    # get table formatter arguments
    table = kwargs.pop("table", {"tablefmt": "pretty", "showindex": True})
    headers = kwargs.pop("headers", ["minion", "host", "ip", "platform", "groups"])
    sortby = kwargs.pop("sortby", "hostname")
    reverse = kwargs.pop("reverse", False)

    # send nr.nornir inventory command
    inventory_data = _run_job(
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
        ret = inventory_data
    # form tree structure using Rich Tree
    elif tree:
        # query hosting nodes information from minions
        nodes_data = _run_job(
            tgt=list(inventory_data),
            fun="grains.item",
            arg=["nodename"],
            kwarg={},
            tgt_type="list",
            timeout=timeout,
            job_retry=job_retry,
        )
        ret = _built_inventory_tree(inventory_data, nodes_data)
    else:
        for minion_id, result in inventory_data.items():
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


@ValidateFuncArgs(model_runner_nr_call)
def call(*args, **kwargs):
    """
    Method to call any Nornir Proxy Minion Execution Module function against minions. By default this function
    targets all Nornir Proxy Minions, allowing to simplify targeting hosts managed by them.

    :param fun: (str) Nornir Proxy Minion Execution Module function name e.g. ``cli, cfg, nc, gnmi`` etc.
    :param tgt: (str) SaltStack Nornir Proxy Minions to target, targets all of them by default - ``proxy:proxytype:nornir``
    :param tgt_type: (str) SaltStack targeting type to use, default is ``pillar``
    :param job_retry: (int) how many times to retry if no results returned from all minions, default 0
    :param job_timeout: (int) seconds to wait for results from minions before retry, default 300s
    :param progress: progress display type to use - bars, raw, log, if False, no progress displayed
    :param ret_struct: results return structure, default is ``dictionary``, also can be ``list``
    :param args: (list) any other arguments to use with call function
    :param raise_no_tgt_match: (bool) if True (default) raises error if no hosts matched to target
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
    job_timeout = kwargs.pop("job_timeout", 300)
    job_retry = kwargs.pop("job_retry", 0)
    progress = kwargs.pop("progress", "log")
    raise_no_tgt_match = kwargs.pop("raise_no_tgt_match", True)

    # get hosts to minions mapping to form tgt value
    hosts_minions = _get_hosts_minions(kwargs, tgt, tgt_type, raise_no_tgt_match)

    if not hosts_minions:
        Fx = {k: v for k, v in kwargs.items() if k in FFun_functions}
        log.debug(
            f"nr.call no hosts matched by target '{tgt}', target type '{tgt_type}', Fx filters: '{Fx}'"
        )
        return {} if ret_struct == "dictionary" else []

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
        timeout=job_timeout,
        job_retry=job_retry,
        progress=progress if isinstance(progress, str) else None,
        show_progress=True if progress else False,
        raise_no_tgt_match=raise_no_tgt_match,
    )

    _form_ret_results(ret, job_results, ret_struct)

    return ret


@ValidateFuncArgs(model_runner_nr_event)
def event(jid="all", tag=None, progress="log", stop_signal=None):
    """
    Function to listen to events emitted by Nornir Proxy Minions. Matched
    event printed to terminal.

    :param tag: (str) tag regex string, default is ``nornir\-proxy/.*``
    :param jid: (int, str) Job ID to listen events for, default is ``all``
    :param progress: (str) progress display mode - ``log``, ``raw``, ``bars``, ``tree``
    :param stop_signal: (obj) thread Event object, stops listening to events if ``stop_signal.is_set()``,
        if ``stop_signal is None``, listens and print events until keyboard interrupt hit - ``ctrl+c``

    ``bars`` and ``tree`` progress display modes use Rich library, to properly display various
    symbols and characters need to make sure to use utf-8 encoding for your environment for example
    by running these commands::

        [root@salt-master ~]# PYTHONIOENCODING=utf-8
        [root@salt-master ~]# export PYTHONIOENCODING
    """
    # start rich console
    globals().setdefault("console", Console())

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
                    "[blue]{timestamp}[/]:{user}:{jid}:[bright_magenta]{function}[/]"
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
            msg = "{timestamp}:{user}:{jid}:{proxy_id}:w{worker_id} {function} {hs} {task_type} {task_event} {task_name}; {status}"
            print(msg.format(**edata))


@ValidateFuncArgs(model_runner_nr_cfg)
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
    perform for each batch of hosts, helping to apply configuration to devices in a
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
    # start rich console
    globals().setdefault("console", Console())

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

    # get a dictionary keyed by filtered hosts with minions lists
    hosts_minions = _get_hosts_minions({**kwargs, "FL": hosts}, tgt, tgt_type)
    # sort filtered hosts to make sure order is always the same
    hosts = sorted(hosts_minions.keys())
    # calculate hosts batch size, number of batches and first batch
    host_batch = len(hosts) if host_batch == 0 else min(host_batch, len(hosts))
    batches_num = len(hosts) / host_batch
    # account for cases like 7 / 3 when one extra batch required
    batches_num = (
        round(batches_num)
        if round(batches_num) == batches_num
        else round(batches_num) + 1
    )
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
    console.rule("Done", style="green")
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


@ValidateFuncArgs(model_runner_nr_diagram)
def diagram(*args, **kwargs):
    """
    Function to retrieve output from devices and produce diagram using N2G library.

    This function depends on N2G, TTP and TTP-Templates libraries to obtain list of
    per-platfrom commands to retrieve from devices, parse output and build diagram.

    Alternativly, instead of getting show commands output from devices, ``nr.diagram``
    can retrieve previously saved show commands output using ``nr.file read`` execution
    module function if ``filegroup`` name provided.

    :param data_plugin: (str) data plugin name to use to process output from devices
    :param diagram_plugin: (str) N2G diagram plugin name - ``yed``, ``drawio``, ``v3d``
    :param outfile: (str) OS path to save diagram file, default is
        ``./Output/{data plugin name}_{curent time}.{diagram plugin extension}``
    :param save_data: (bool, str) if True, saves commands otput results retrieve from devices
        in "Data" folder next to diagram file, if ``save_dat``a is a string, it must be an OS path
        to folder where to save devices output. This is useful during troubleshooting to be able
        to check what output devices return.
    :param cli: (dict) arguments for ``nr.cli`` execution module function to get devices output
    :param filegroup: (str) ``filegroup`` argument value for ``nr.file read`` function to
        retrieve previously saved devices show commands output
    :param last: (int) ``last`` argument value for ``nr.file read`` function, default value is 1
    :param Fx: (str) Nornir filter functions to filter list of devices (hosts) to get output from
    :param tgt: (str) SaltStack Nornir Proxy Minions to target, targets all of them by default - ``proxy:proxytype:nornir``
    :param tgt_type: (str) SaltStack targeting type to use, default is ``pillar``
    :param job_retry: (int) how many times to retry if no results returned from all minions, default 0
    :param job_timeout: (int) seconds to wait for results from minions before retry, default 300s
    :param progress: progress display type to use - bars, raw, log, if False, no progress displayed
    :param **kwargs: any additional arguments to use with
        `N2G data plugins <https://n2g.readthedocs.io/en/latest/data_plugins/index.html>`_

    N2G ``data_plugin`` names and details:

    - ``L2`` - `CLI L2 Data Plugin <https://n2g.readthedocs.io/en/latest/data_plugins/cli_l2_data.html>`_
        uses CDP and LLDP protocols peerings data to produce L2 diagram of the network
    - ``L3` or ``IP`` - `CLI IP Data Plugin <https://n2g.readthedocs.io/en/latest/data_plugins/cli_ip_data.html>`_
        uses IP related data to produce L3 diagram of the network
    - ``ISIS`` - `CLI ISIS LSDB Data Plugin <https://n2g.readthedocs.io/en/latest/data_plugins/cli_isis_data.html>`_
        uses ISIS LSDB data to produce L3 diagram of the network
    - ``OSPF`` - `CLI OSPFv2 LSDB Data Plugin <https://n2g.readthedocs.io/en/latest/data_plugins/cli_ospf_data.html>`_
        uses OSPFv2 LSDB data to produce L3 diagram of the network

    Sample usage::

        salt-run nr.diagram L2 v3d FB="ceos*"
        salt-run nr.diagram L2 v3d FB="ceos*" cli='{"plugin": "scrapli"}' save_data=True
        salt-run nr.diagram data_plugin=L2 diagram_plugin=v3d FB="ceos1" outfile="cdp_lldp_diagram.json"
        salt-run nr.diagram IP drawio FM="cisco_ios" add_arp=True group_links=True label_interface=True label_vrf=True
        salt-run nr.diagram L2 v3d FC="core" group_links=True add_all_connected=True
        salt-run nr.diagram L2 yed filegroup="cdp_and_lldp_output" last=3
    """
    try:
        import N2G
        from ttp import ttp
        from ttp_templates import list_templates
    except ImportError as e:
        log.exception(e)
        return f"nr.diagram failed importing required modules - {e}"

    n2g_data = {}  # to store collected from devices data
    collected_hosts_list = []  # list of devices collected data from
    ctime = time.strftime("%Y-%m-%d_%H-%M-%S")
    data_plugin = args[0] if len(args) >= 1 else kwargs.pop("data_plugin")
    diagram_plugin = args[1] if len(args) == 2 else kwargs.pop("diagram_plugin", "yed")
    Fx = {k: kwargs.pop(k) for k in list(kwargs) if k in FFun_functions}
    cli = {**kwargs.pop("cli", {}), **Fx}
    cli.setdefault("plugin", "netmiko")
    save_data = kwargs.pop("save_data", False)
    filegroup = kwargs.pop("filegroup", None)
    last = kwargs.pop("last", 1)

    # construct argument for call functions
    call_kwargs = {
        "tgt": kwargs.pop("tgt", "proxy:proxytype:nornir"),
        "tgt_type": kwargs.pop("tgt_type", "pillar"),
        "job_timeout": kwargs.pop("job_timeout", 300),
        "job_retry": kwargs.pop("job_retry", 0),
        "progress": kwargs.pop("progress", "log"),
        "raise_no_tgt_match": False,
    }

    # decide on how to retrieve the data - using nr.cli or nr.file read
    if filegroup:
        call_kwargs["fun"] = "file"
        file = {**Fx, "filegroup": filegroup, "last": last, "call": "read"}
        FM = file.pop("FM", [])
    else:
        call_kwargs["fun"] = "cli"
        FM = cli.pop("FM", [])

    drawing_plugin, ext = {
        "yed": (N2G.yed_diagram, "graphml"),
        "drawio": (N2G.drawio_diagram, "drawio"),
        "v3d": (N2G.v3d_diagramm, "json"),
    }[diagram_plugin]

    template_dir, n2g_data_plugin = {
        "L2": ("cli_l2_data", N2G.cli_l2_data),
        "IP": ("cli_ip_data", N2G.cli_ip_data),
        "L3": ("cli_ip_data", N2G.cli_ip_data),
        "ISIS": ("cli_isis_data", N2G.cli_isis_data),
        "OSPF": ("cli_ospf_data", N2G.cli_ospf_data),
    }[data_plugin]

    # get folders info
    outfile = kwargs.pop("outfile", f"./Output/{data_plugin}_{ctime}.{ext}")
    out_filename = outfile.split(os.sep)[-1]
    out_folder = os.sep.join(outfile.split(os.sep)[:-1])
    # check if need to save devices output to local folder
    if isinstance(save_data, str):
        data_out_folder = save_data
    elif save_data is True:
        data_out_folder = os.path.join(out_folder, f"{data_plugin}_Data_{ctime}")

    # form list of platforms to collect output for
    n2g_supported_platorms = [
        ".".join(i.split(".")[:-1])
        for i in list_templates()["misc"]["N2G"][template_dir]
    ]
    # if FM filter provided, leave only supported platforms
    platforms = (
        [p for p in n2g_supported_platorms if p in FM] if FM else n2g_supported_platorms
    )

    print(
        "Retrieving output for devices using '{}'".format(
            f"nr.file read {filegroup}" if filegroup else "nr.cli"
        )
    )

    # retrieve output on a per-platform basis to save it
    # in n2g_data dict keyed by platform name
    for platform in platforms:
        n2g_data.setdefault(platform, [])
        cli_args = copy.deepcopy(cli)
        file_args = copy.deepcopy(file) if filegroup else {}

        # use N2G ttp templates to get list of commands and list of platforms
        # to collect show commands output from devices
        parser = ttp(
            template=f"ttp://misc/N2G/{template_dir}/{platform}.txt",
            log_level="CRITICAL",
        )
        ttp_inputs_load = parser.get_input_load()
        for template_name, inputs in ttp_inputs_load.items():
            for input_name, input_params in inputs.items():
                cli_args["commands"] = input_params["commands"]
                cli_args["FM"] = input_params.get("platform", platform)
                file_args["FM"] = input_params.get("platform", platform)
                if cli_args["plugin"] == "netmiko":
                    cli_args.update(input_params.get("kwargs", {}))

        # get output for previously saved commands using "nr.file read"
        if filegroup:
            devices_output = call(**call_kwargs, **file_args)
        # get show commands output from devices using "nr.cli"
        else:
            devices_output = call(**call_kwargs, **cli_args)

        # populate n2g data dictionary keyed by platform and save results to files
        for host_name, host_results in devices_output.items():
            collected_hosts_list.append(host_name)
            n2g_data[platform].append("\n".join([i["result"] for i in host_results]))
            if save_data:
                data_folder = os.path.join(data_out_folder, platform)
                data_file = os.path.join(data_folder, f"{host_name}.txt")
                os.makedirs(data_folder, exist_ok=True)
                with open(data_file, mode="w", encoding="utf-8") as f:
                    f.write(n2g_data[platform][-1])

    print(
        "Retrieved output for platforms - {} - from devices: {}".format(
            ", ".join([k for k in n2g_data.keys() if n2g_data[k] != []]),
            ", ".join(collected_hosts_list),
        )
    )

    # create, populate and save diagram
    drawing = drawing_plugin()
    drawer = n2g_data_plugin(drawing, **kwargs)
    drawer.work(n2g_data)
    drawing.dump_file(folder=out_folder, filename=out_filename)

    return f"'{data_plugin}' diagram in '{diagram_plugin}' format saved at: '{out_folder}{os.sep}{out_filename}'"


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


def generate_bash_autocomplete(*args, **kwargs):
    """
    Function to generate bash autocompletion for Salt-Nornir functions
    """
    pprint(SaltNornirMasterModel.schema())
