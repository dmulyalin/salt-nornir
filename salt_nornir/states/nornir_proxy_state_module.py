# -*- coding: utf-8 -*-
"""
Nornir State Module
===================

Nornir State module reference.

Introduction
------------

This state module uses Nornir proxy execution module to apply configuration
to devices.

.. warning:: This module does not implement idempotent behavior, it is up to Nornir task
  plugin to handle idempotency.

Example
-------

Example using ``nr.cfg`` and ``nr.task`` state module functions within SALT state.

File ``salt://states/nr_state_test.sls`` content located on Master::

    apply_logging_commands:
      nr.cfg:
        - commands:
          - logging host 1.1.1.1
          - logging host 2.2.2.2
        - plugin: netmiko

    apply_ntp_cfg_from_file:
      nr.cfg:
        - filename: "salt://templates/nr_state_test_ntp.j2"
        - plugin: netmiko

    use_task_to_save_config:
      nr.task:
        - plugin: "nornir_netmiko.tasks.netmiko_save_config"

    use_task_to_configure_logging:
      nr.task:
        - plugin: "nornir_netmiko.tasks.netmiko_send_config"
        - config_commands: "logging host 3.3.3.3"

File ``salt://templates/nr_state_test_ntp.j2`` content located on Master::

    {%- if host.platform|lower == 'ios' %}
    ntp server 1.1.1.1
    {%- elif host.platform|lower == 'cisco_xr' %}
    ntp peer 1.1.1.1
    {%- endif %}

Apply state running command on master::

    salt nr_minion_id state.apply nr_state_test

Nornir state module functions
-----------------------------

.. autofunction:: salt_nornir.states.nornir_proxy_state_module.cfg
.. autofunction:: salt_nornir.states.nornir_proxy_state_module.task
.. autofunction:: salt_nornir.states.nornir_proxy_state_module.workflow
"""
# Import python libs
import logging
import json
import traceback

log = logging.getLogger(__name__)

# import salt libs, wrapping it in try/except for docs to generate
try:
    from salt.exceptions import CommandExecutionError
except:
    log.error("Nornir Proxy Module - failed importing SALT libraries")

# -----------------------------------------------------------------------------
# globals
# -----------------------------------------------------------------------------

__virtualname__ = "nr"


# ----------------------------------------------------------------------------------------------------------------------
# property functions
# ----------------------------------------------------------------------------------------------------------------------


def __virtual__():
    return __virtualname__


# -----------------------------------------------------------------------------
# callable functions
# -----------------------------------------------------------------------------


def cfg(*args, **kwargs):
    """
    Configure devices using Nornir execution module ``nr.cfg`` function.

    :param commands: list of commands to send to device
    :param filename: path to file with configuration
    :param template_engine: template engine to render configuration, default is jinja
    :param saltenv: name of SALT environment
    :param context: Overrides default context variables passed to the template.
    :param defaults: Default context passed to the template.
    :param plugin: name of configuration task plugin to use - ``napalm`` (default) or ``netmiko`` or ``scrapli``
    :param dry_run: boolean, default False, controls whether to apply changes to device or simulate them
    :param Fx: filters to filter hosts
    :param add_details: boolean, to include details in result or not

    .. warning:: ``dry_run`` not supported by ``netmiko`` plugin

    **Sample Usage**

    File ``salt://states/nr_state_logging_cfg.sls`` content located on Master::

        apply_logging_commands:
          nr.cfg:
            - commands:
              - logging host 1.1.1.1
              - logging host 2.2.2.2
            - plugin: netmiko
            - FB: "*"

    Apply state::

        salt nr_minion_id state.apply nr_state_logging_cfg

    """
    state_name = kwargs.pop("name")
    if __opts__["test"]:
        ret = {
            "name": state_name,
            "changes": "",
            "result": None,
            "comment": "State nr.cfg will execute with param '{}'; '{}'".format(
                args, kwargs
            ),
        }
    else:
        result = __salt__["nr.cfg"](*args, **kwargs)
        ret = {
            "name": state_name,
            "changes": result,
            "result": True,
            "comment": "",
        }
    return ret


def task(*args, **kwargs):
    """
    Interact with devices using ``nr.task`` Execution Module function.

    :param plugin: ``path.to.plugin.task_fun`` to use, should form valid 
      python import statement - ``from path.to.plugin import task_fun``
    :param Fx: filters to filter hosts
    :param add_details: boolean, to include details in result or not
    :param args: arguments to pass on to task plugin
    :param kwargs: keyword arguments to pass on to task plugin

    **Sample Usage**

    File salt://states/nr_state_ntp_cfg.sls content located on Master::

        use_task_to_configure_logging:
          nr.task:
            - plugin: "nornir_netmiko.tasks.netmiko_send_config"
            - config_commands: "ntp server 1.1.1.1"

    Apply state::

        salt nr_minion_id state.apply  nr_state_ntp_cfg
    """
    if __opts__["test"]:
        ret = {
            "name": state_name,
            "changes": "",
            "result": None,
            "comment": "State nr.task will execute with param '{}'; '{}'".format(
                args, kwargs
            ),
        }
    else:
        state_name = kwargs.pop("name")
        result = __salt__["nr.task"](*args, **kwargs)
        ret = {
            "name": state_name,
            "changes": result,
            "result": True,
            "comment": "",
        }
    return ret


def _run_workflow_step(
    step, steps_failed, steps_passed, common_filters, report_all, report, all_hosts
):
    """
    Helper function to run single work flow step.

    :param step: (dict) step parameters
    :param steps_failed: (dict) dictionary keyed by steps names with values set to failed hosts
    :param steps_passed: (dict) dictionary keyed by steps names with values set to passed hosts
    :param common_filters: (dict) Fx filters dictionary to use for all steps
    :param report_all: (bool) if True, add skipped steps in summary report
    :param report: (dict) structure that contains overall workflow execution results
    :param all_hosts: (list) list with host names matched by this workflow options' filters
    """
    try:
        steps_failed[step["name"]] = set()
        steps_passed[step["name"]] = set()

        # form step kwargs
        step.setdefault("kwargs", {})

        # merge step filters with common filters
        for k, v in common_filters.items():
            step["kwargs"].setdefault(k, v)
        step["kwargs"].setdefault("FB", "*")

        # set required attributes
        if step["function"] == "nr.test":
            step["kwargs"]["failed_only"] = False
            step["kwargs"].setdefault("name", step["name"])
        if step["function"] in [
            "nr.cli",
            "nr.task",
            "nr.cfg",
            "nr.cfg_gen",
            "nr.tping",
            "nr.test",
            "nr.nc"
        ]:
            step["kwargs"]["add_details"] = True

        # form FL filter based on run_if criteria
        if step.get("run_if_fail_any") or step.get("run_if_pass_any"):
            FL = set()
            for required_step in step.get("run_if_fail_any", []):
                if not required_step in steps_failed:
                    raise CommandExecutionError(
                        "Step '{a}' run_if_fail_any requires '{b}', but '{b}' not executed".format(
                            a=step["name"], b=required_step
                        )
                    )
                FL.update(steps_failed[required_step])
            for required_step in step.get("run_if_pass_any", []):
                if not required_step in steps_passed:
                    raise CommandExecutionError(
                        "Step '{a}' run_if_pass_any requires '{b}', but '{b}' not executed".format(
                            a=step["name"], b=required_step
                        )
                    )
                FL.update(steps_passed[required_step])
        # run for all hosts otherwise
        else:
            FL = set(all_hosts)

        # form FL filter by intersecting it with FL kwargs argument if any
        if "FL" in step["kwargs"]:
            step["kwargs"]["FL"] = list(set(step["kwargs"]["FL"]).intersection(FL))
        else:
            step["kwargs"]["FL"] = FL

        # get list of hosts matched by this step
        matched_hosts = __salt__["nr.inventory"](**step["kwargs"])
        matched_hosts = list(matched_hosts["hosts"].keys())

        # handle when have no hosts to run step against
        if not matched_hosts and report_all:
            log.info("state:nr.workflow: no hosts matched for step: '{}'".format(step))
            if step.get("report") != False:
                report["details"].append({step["name"]: {}})
            for host_name, host_steps in report["summary"].items():
                host_steps.append({step["name"]: "SKIP"})
            return

        # run step function
        log.debug("state:nr.workflow: executing step: '{}'".format(step))
        result = __salt__[step["function"]](*step.get("args", []), **step["kwargs"])
        log.debug("state:nr.workflow: step '{}'; result:\n {}".format(step, result))

        # record a set of hosts that failed/passed this step
        if step["function"] in [
            "nr.task",
            "nr.cli",
            "nr.cfg_gen",
            "nr.cfg",
            "nr.test",
            "nr.do",
            "nr.nc"
        ]:
            if isinstance(result, dict):
                for host_name, host_results in result.items():
                    for task_result in host_results.values():
                        if task_result["failed"] or task_result.get("success") == False:
                            report["summary"][host_name].append({step["name"]: "FAIL"})
                            steps_failed[step["name"]].add(host_name)
                            break
                    else:
                        report["summary"][host_name].append({step["name"]: "PASS"})
                        steps_passed[step["name"]].add(host_name)
            elif isinstance(result, list):
                for task_result in result:
                    steps_passed.setdefault(task_result["name"], set())
                    steps_failed.setdefault(task_result["name"], set())
                    if task_result["failed"] or task_result.get("success") == False:
                        steps_failed[task_result["name"]].add(task_result["host"])
                        report["summary"][task_result["host"]].append(
                            {task_result["name"]: "FAIL"}
                        )
                    else:
                        steps_passed[task_result["name"]].add(task_result["host"])
                        report["summary"][task_result["host"]].append(
                            {task_result["name"]: "PASS"}
                        )
        else:
            steps_passed[step["name"]] = set(matched_hosts)

        # check if need to add step run results to detailed report
        if step.get("report") != False:
            report["details"].append({step["name"]: result})
        # check if need to add this step info to skipped hosts
        for host_name, host_steps in report["summary"].items():
            if host_name not in matched_hosts and report_all:
                host_steps.append({step["name"]: "SKIP"})
    except:
        tb = traceback.format_exc()
        log.error("state:nr.workflow: step '{}' error: {}".format(step, tb))
        steps_failed[step["name"]] = all_hosts
        report["details"].append({step["name"]: tb})
        # add ERROR for this step to all hosts
        for host_name, host_steps in report["summary"].items():
            host_steps.append({step["name"]: "ERROR"})


def _decide_state_execution_status(options, ret):
    """
    Helper function to decide state execution status based on options
    fail_if... criteria.

    :param options: (dict) state options dictionary
    :param ret: (dict) state execution return structure
    """
    try:
        if options.get("fail_if_any_host_fail_any_step"):
            for step_name in options["fail_if_any_host_fail_any_step"]:
                ret["result"] = False
                ret[
                    "comment"
                ] = "{} condition met - '{}' step has failed hosts:\n{}".format(
                    "fail_if_any_host_fail_any_step", step_name, steps_failed[step_name]
                )
                break
        if options.get("fail_if_any_host_fail_all_step") and ret["result"]:
            failed_hosts = None
            for step_name in options["fail_if_any_host_fail_all_step"]:
                if failed_hosts is None:
                    failed_hosts = steps_failed[step_name]
                else:
                    failed_hosts = steps_failed[step_name].intersection(failed_hosts)
            if failed_hosts:
                ret["result"] = False
                ret[
                    "comment"
                ] = "{} condition met - host(s) failed all steps:\n{}".format(
                    "fail_if_any_host_fail_all_step", failed_hosts
                )
        if options.get("fail_if_all_host_fail_any_step") and ret["result"]:
            # get a set of all hosts that this state touched
            all_hosts_touched = set()
            for hosts in steps_failed.values():
                all_hosts_touched.update(hosts)
            for hosts in steps_passed.values():
                all_hosts_touched.update(hosts)
            # check if any of the steps failed for all hosts
            for step_name in options["fail_if_all_host_fail_any_step"]:
                if steps_failed[step_name] == all_hosts_touched:
                    ret["result"] = False
                    ret[
                        "comment"
                    ] = "{} condition met - '{}' step failed for all hosts:\n{}".format(
                        "fail_if_all_host_fail_any_step", step_name, all_hosts_touched
                    )
                    break
        if options.get("fail_if_all_host_fail_all_step") and ret["result"]:
            # get a set of all hosts that this state touched
            all_hosts_touched = set()
            for hosts in steps_failed.values():
                all_hosts_touched.update(hosts)
            for hosts in steps_passed.values():
                all_hosts_touched.update(hosts)
            # check if all steps failed for all hosts
            failed_all = True
            for step_name in options["fail_if_all_host_fail_all_step"]:
                if steps_failed[step_name] != all_hosts_touched:
                    failed_all = False
            if failed_all:
                ret["result"] = False
                ret[
                    "comment"
                ] = "{} condition met - all hosts {},\nfailed all steps {}".format(
                    "fail_if_all_host_fail_all_step",
                    all_hosts_touched,
                    list(steps_failed.keys()),
                )
    except:
        tb = traceback.format_exc()
        msg = "state:nr.workflow: failed to determine state success, error:\n{}".format(
            tb
        )
        log.error(msg)
        ret["result"] = False
        ret["comment"] = msg

    return ret


def workflow(*args, **kwargs):
    """
    State function to execute work flow steps using SALT Execution modules functions. 
    
    ``run_if_x`` conditions supported only by these SALT Execution Module functions: 
    "nr.task", "nr.cli", "nr.cfg_gen", "nr.cfg", "nr.test", "nr.do" 

    **State Global Options**

    State Global Options defined under ``options`` key. If none of the ``fail_if_x``
    conditions defined, state execution considered successful unconditionally.

    :param report_all: (bool) if True (default) adds skipped steps in summary report
    :param fail_if_any_host_fail_any_step: (list) steps to decide if state execution failed
    :param fail_if_any_host_fail_all_step: (list) steps to decide if state execution failed
    :param fail_if_all_host_fail_any_step: (list) steps to decide if state execution failed
    :param fail_if_all_host_fail_all_step: (list) steps to decide if state execution failed
    :param filters: (dict) set of ``Fx`` filters to apply for all steps, per-step
        filters have higher priority.

    **Individual Step Arguments**

    Each step in a work flow can have a number of mandatory and optional attributes defined.

    :param name: (str) mandatory, name of this step
    :param function: (str) mandatory, name of Nornir Execution Module function to run
        e.g. ``nr.cli``, ``nr.task``, ``nr.cfg``, ``nr.test`` etc.
    :param kwargs: (dict) ``**kwargs`` for Nornir Execution Module function
    :param args: (list) ``*args`` for Nornir Execution Module function
    :param report: (bool) if True (default) adds step execution results in detailed report
    :param run_if_fail_any: (list) this step will run if ``any`` of the previous steps in a list failed
    :param run_if_pass_any: (list) this step will run if ``any`` of the previous steps in a list passed

    If function reference ``nr.test`` with test suite, each test suite test item added to summary
    report, in addition, step's arguments ``run_if_x`` conditions **must** reference test suite
    individual tests' names attribute.

    .. warning:: if you use per host filename feature, e.g. ``filename="salt://path/to/{{ host.name }}.cfg"``
       make sure to either disable state file jinja2 rendering using ``#!yaml`` shebang at the beginning
       of the state file or escape double curly braces in filename argument.

    Execution of steps done on a per host basis, or, say better, each step
    determines a set of hosts it needs to run for using ``Fx`` filters and ``run_if_x`` conditions.

    Sample state ``salt://states/configure_ntp.sls``::

        main_workflow:
          nr.workflow:
            - options:
                fail_if_any_host_fail_any_step: []
                fail_if_any_host_fail_all_step: []
                fail_if_all_host_fail_any_step: []
                fail_if_all_host_fail_all_step: []
                report_all: False
                filters: {"FB": "*"}
            # define pre-check steps
            - pre_check:
                - name: pre_check_if_ntp_ip_is_configured_csr1kv
                  function: nr.test
                  kwargs: {"FB": "CSR*"}
                  args: ["show run | inc ntp", "contains", "8.8.8.8"]
                - name: pre_check_if_ntp_ip_is_configured_xrv
                  function: nr.test
                  kwargs: {"FB": "XR*"}
                  args: ["show run formal ntp", "contains", "8.8.8.8"]
            # here goes definition of change steps
            - change:
                - name: apply_ntp_ip_config
                  function: nr.cfg
                  args: ["ntp server 8.8.8.8"]
                  kwargs: {"plugin": "netmiko"}
                  run_if_fail_any: ["pre_check_if_ntp_ip_is_configured_csr1kv", "pre_check_if_ntp_ip_is_configured_xrv"]
                  report: True
            # run post check steps
            - post_check:
                - name: check_new_config_applied_csr1kv
                  function: nr.test
                  args: ["show run | inc ntp", "contains", "8.8.8.8"]
                  kwargs: {"FB": "CSR*"}
                  run_if_pass_any: ["apply_ntp_ip_config"]
                - name: check_new_config_applied_xrv
                  function: nr.test
                  args: ["show run ntp", "contains", "8.8.8.8"]
                  kwargs: {"FB": "XR*"}
                  run_if_pass_any: ["apply_ntp_ip_config"]
            # execute rollback steps if required
            - rollback:
                - name: run_rollback_commands
                  function: nr.cfg
                  args: ["no ntp server 8.8.8.8"]
                  kwargs: {"plugin": "netmiko"}
                  run_if_fail_any: ["apply_ntp_ip_config", "check_new_config_applied_csr1kv", "check_new_config_applied_xrv"]

    Sample usage::

        salt nrp1 state.sls configure_ntp
    """
    steps_failed, steps_passed = {}, {}
    options = kwargs.pop("options", {})
    report_all = options.get("report_all", True)
    common_filters = options.get("filters", {})

    # get all hosts names
    all_hosts = __salt__["nr.inventory"](**common_filters)
    all_hosts = list(all_hosts["hosts"].keys())

    # form report and ret strutures
    report = {"details": [], "summary": {h: [] for h in all_hosts}}
    ret = {
        "name": kwargs.pop("name"),
        "changes": report,
        "result": True,
        "comment": "",
    }

    # run steps
    for group_name, steps in kwargs.items():
        log.info("state:nr.workflow: running '{}' steps".format(group_name))
        for step in steps:
            log.info("state:nr.workflow: running step: '{}'".format(step))
            _run_workflow_step(
                step,
                steps_failed,
                steps_passed,
                common_filters,
                report_all,
                report,
                all_hosts,
            )

    # decide if this state failed
    ret = _decide_state_execution_status(options, ret)

    return ret
