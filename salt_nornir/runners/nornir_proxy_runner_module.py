"""
Nornir Runner Module
====================

.. versionadded:: v3001

:maturity:   new
:depends:    Nornir
:platform:   unix

Dependencies
------------

- `Tabulate <https://pypi.org/project/tabulate/>`_ required by ``nr.inventory`` to return table results

Introduction
------------

Nornir-runner module runs on SALT Master to interact with devices behind Nornir proxies.
"""
# Import python libs
import logging
import traceback
import fnmatch
import time

log = logging.getLogger(__name__)

# Import salt modules
try:
    import salt
    from salt.exceptions import CommandExecutionError
    HAS_SALT = True
except:
    log.error("Nornir Runner Module - failed importing SALT libraries")
    HAS_SALT = False

# import salt libs, wrapping it in try/except for docs to generate
try:
    from tabulate import tabulate

    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False
    

if HAS_SALT:
    # initiate execution modules client to run 'salt "*" command' commands
    client = salt.client.LocalClient()
    
    # initiate runner modules client to run 'salt "*" command' commands
    opts = salt.config.master_config("/etc/salt/master")
    opts["quiet"] = True
    runner = salt.runner.RunnerClient(opts)



__virtualname__ = "nr"


def __virtual__():
    """
    Load this Runner module.
    """
    return __virtualname__


# -----------------------------------------------------------------------------
# Private functions
# -----------------------------------------------------------------------------


def _run_job(tgt, fun, arg, kwarg, tgt_type, timeout, retry):
    """
    Helper function to send execution module command using ``client.run_job``
    method and collect results using ``client.get_event_iter_returns``. Implements
    basic retry mechanism.
    
    If ``client.get_event_iter_returns`` return no results, ``_run_job`` will retry 
    the command until minions return results or ``retry`` threshold reached, in
    latter case ``CommandExecutionError`` raised with job details
    """
    ret = {}
    attempt = 1
    while attempt <= retry:
        # publish job command
        pub_data = client.run_job(
            tgt=tgt, fun=fun, arg=arg, kwarg=kwarg, tgt_type=tgt_type, timeout=timeout
        )
        # collect job results
        job_results = client.get_event_iter_returns(timeout=timeout, **pub_data)
        for item in job_results:
            ret.update(item)
        if not set(pub_data["minions"]) == set(ret.keys()):
            minions_no_return = set(pub_data["minions"]) - set(ret.keys())
            log.warning(
                "Nornir-runner:_run_job - {}s timeout; no results from {}; returned {}; jid {}; attempt: {}".format(
                    timeout,
                    list(minions_no_return),
                    list(ret.keys()),
                    pub_data["jid"],
                    attempt,
                )
            )
        if ret:
            break
        attempt += 1
    else:
        raise CommandExecutionError(
            "Nornir-runner:_run_job - no results from minions; tgt: {}; fun: {}; tgt_type: {}; timeout: {}; retry: {}; kwarg: {}".format(
                tgt, fun, tgt_type, timeout, retry, kwarg
            )
        )
    return ret


# -----------------------------------------------------------------------------
# callable module function
# -----------------------------------------------------------------------------


def inventory(*args, **kwargs):
    """
    Function to return inventory data for certain hosts summirised in a
    table format.

    :param FB: glob pattern matching hostnames of devices behind Nornir
    :param Fx: additional filters to filter hosts, e.g. FG, FP, FL etc.
    :param tgt: nornir proxy minion target, by default targets all - "proxy:proxytype:nornir"
    :param tgt_type: SALT targeting type to use, by default "pillar"
    :param verbose: boolean, returns ``nr.cli`` output as is if True, flattens to dictinary
        keyed by devices hostnames if False, default False
    :param retry: how many times to retry command if no return from minions, default 3
    :param job_timeout: seconds to wait for return from minions, overrides
        ``--timeout`` option, default 30s

    Sample Usage::

        salt-run nr.inventory host_name_id
        salt-run nr.inventory FB="host_name_id" FP="10.1.2.0/24"
        salt-run nr.inventory FB="host_name_id" FP="10.1.2.0/24" tk='{"tablefmt": "jira"}'

    If it takes too long to get output because of non-responding/unreachable minions,
    specify ``--timeout`` or ``job_timeout`` option to shorten waiting time, ``job_timeout`` 
    overrides ``--timeout``. Alternatively, instead of targeting all nornir based proxy 
    minions, ``tgt`` and ``tgt_type`` can be used to target a subset of them::

        salt-run nr.inventory host_name_id --timeout=10
        salt-run nr.inventory host_name_id job_timeout=10 tgt="nornir-proxy-id" tgt_type="glob"
    """
    ret = []

    # get hostname target
    if len(args) > 0:
        kwargs["FB"] = args[0]
    elif not any(F in kwargs for F in ["FB", "FP", "FO", "FG", "FP", "FL"]):
        raise CommandExecutionError(
            "Nornir-runner:inventory - hosts filter not provided, args: '{}', kwargs: '{}'".format(
                args, kwargs
            )
        )
    # get other arguments
    tgt = kwargs.pop("tgt", "proxy:proxytype:nornir")
    tgt_type = kwargs.pop("tgt_type", "pillar")
    verbose = kwargs.pop("verbose", False)
    use_tabulate = kwargs.pop("use_tabulate", True)
    tk = kwargs.pop("tk", {"tablefmt": "pretty", "showindex": True})
    timeout = kwargs.pop("job_timeout") if kwargs.get("job_timeout") else __opts__["timeout"]
    retry = kwargs.pop("retry", 3)

    # send nr.inventory command
    query_results = _run_job(
        tgt=tgt,
        fun="nr.inventory",
        arg=[],
        kwarg={k: v for k, v in kwargs.items() if not k.startswith("_")},
        tgt_type=tgt_type,
        timeout=timeout,
        retry=retry,
    )

    # work with command results
    if verbose:
        ret = query_results
    else:
        for minion_id, result in query_results.items():
            if result.get("ret", {}).get("hosts", None):
                for host_name, host_data in result["ret"]["hosts"].items():
                    ret.append(
                        {
                            "minion": minion_id,
                            "hostname": host_data["name"],
                            "ip": host_data["hostname"],
                            "platform": host_data["platform"],
                            "groups": ",".join(host_data.get("groups", [])),
                        }
                    )
    # check if need to pass ret via tabulate
    if HAS_TABULATE and use_tabulate and not verbose:
        ret = tabulate(
            ret,
            headers={
                "minion": "minion",
                "hostname": "hostname",
                "ip": "ip",
                "platform": "platform",
                "groups": "groups",
            },
            **tk
        )
    return ret


def cli(*args, **kwargs):
    """
    Method to retrieve commands output from devices behind Nornir Proxies using
    ``nr.cli`` execution module function.

    :param FB: glob pattern matching hostnames of devices behind Nornir
    :param Fx: additional filters to filter hosts, e.g. FG, FP, FL etc.
    :param tgt: nornir proxy minion target, by default targets all - "proxy:proxytype:nornir"
    :param tgt_type: SALT targeting type to use, by default "pillar"
    :param verbose: boolean, returns ``nr.cli`` output as is if True, flattens to dictinary
        keyed by devices hostnames if False, default False
    :param retry: how many times to retry command if no return from minions, default 3
    :param job_timeout: seconds to wait for return from minions, overrides
        ``--timeout`` option, default 30s

    All the parameters supported by ``nr.cli`` execution module function
    supported by this function as well.

    :param commands: list of commands
    :param netmiko_kwargs: kwargs to pass on to netmiko send_command methods
    :param add_details: boolean, to include details in result or not
    :param add_cpid_to_task_name: boolean, include Child Process ID (cpid) for debugging
    :param plugin: name of send command task plugin to use - ``netmiko`` (default) or ``scrapli``
    :param match: regular expression pattern to search for in results,
        similar to Cisco ``inlclude`` or Juniper ``match`` pipe commands
    :param before: used with match, number of lines before match to include in results, default is 0

    Sample Usage::

         salt-run nr.cli hostname-id "show clock" "show run" FB="IOL[12]" netmiko_kwargs='{"use_timing": True, "delay_factor": 4}'
         salt-run nr.cli hostname-id commands='["show clock", "show run"]' FB="IOL[12]" netmiko_kwargs='{"strip_prompt": False}'
         
    If it takes too long to get output because of non-responding/unreachable minions,
    specify ``--timeout`` or ``job_timeout`` option to shorten waiting time, ``job_timeout`` 
    overrides ``--timeout``. Alternatively, instead of targeting all nornir based proxy 
    minions, ``tgt`` and ``tgt_type`` can be used to target a subset of them::

        salt-run nr.inventory host_name_id --timeout=10
        salt-run nr.inventory host_name_id job_timeout=10 tgt="nornir-proxy-id" tgt_type="glob"
    """
    ret = {}

    # get hostname target
    if len(args) > 0:
        kwargs["FB"] = args[0]
        if len(args) > 1:
            kwargs["commands"] = args[1:]
    elif not any(F in kwargs for F in ["FB", "FP", "FO", "FG", "FP", "FL"]):
        raise CommandExecutionError(
            "Nornir-runner:cli - hosts filter not provided, args: '{}', kwargs: '{}'".format(
                args, kwargs
            )
        )
    if not kwargs.get("commands"):
        raise CommandExecutionError(
            "Nornir-runner:cli - no commands provided, args: '{}', kwargs: '{}'".format(
                args, kwargs
            )
        )
    # get other arguments
    tgt = kwargs.pop("tgt", "proxy:proxytype:nornir")
    tgt_type = kwargs.pop("tgt_type", "pillar")
    verbose = kwargs.pop("verbose", False)
    timeout = kwargs.pop("job_timeout") if kwargs.get("job_timeout") else __opts__["timeout"]
    retry = kwargs.pop("retry", 3)

    # send nr.cli command
    command_results = _run_job(
        tgt=tgt,
        fun="nr.cli",
        arg=[],
        kwarg={k: v for k, v in kwargs.items() if not k.startswith("_")},
        tgt_type=tgt_type,
        timeout=timeout,
        retry=retry,
    )

    # work with command results
    if verbose:
        ret = command_results
    else:
        for minion_id, result in command_results.items():
            if result["ret"]:
                ret.update(result["ret"])
    return ret

def call(*arg, **kwargs):
    """
    Method to call arbitrary command against all Nornir-proxy minions,
    including Nornir-proxy minion excution module functions
    
    Sample Usage::
    
        salt-run nr.call test.ping  
        salt-run nr.call nr.cli "show clock" FB="*" tgt="nr-minion-id*" tgt_type="glob"
        
    
    """
    pass