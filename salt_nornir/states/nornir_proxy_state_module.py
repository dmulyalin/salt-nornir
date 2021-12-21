"""
Nornir State Module
===================

Nornir State module reference.

Introduction
------------

This state module uses Nornir proxy execution module to apply configuration
to devices.

.. warning:: This module does not implement idempotent behavior, it is up to Nornir task
  plugin to handle idempotency or up to user to define work flow steps to achieve desired
  level of idempotency.

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

Nornir State Module Functions
-----------------------------

.. list-table:: State Functions Summary
   :widths: 15 85
   :header-rows: 1

   * - Name
     - Description
   * - `cfg`_
     - Configure devices using Nornir execution module ``nr.cfg`` function
   * - `task`_
     - Interact with devices using ``nr.task`` Execution Module function.
   * - `workflow`_
     - Executes work flow steps using any SaltStack Execution modules functions

cfg
+++
.. autofunction:: salt_nornir.states.nornir_proxy_state_module.cfg

task
++++
.. autofunction:: salt_nornir.states.nornir_proxy_state_module.task

workflow
++++++++
.. autofunction:: salt_nornir.states.nornir_proxy_state_module.workflow
"""
# Import python libs
import logging
import traceback
import uuid

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
# private functions
# -----------------------------------------------------------------------------


def _form_identity(function_name):
    """
    Helper function to form execution module function identity argument, identity
    used by nornir proxy minion to identify results for tasks submitter to jobs queue,
    it also used by SaltEventProcessor to add function name details to events.

    :param function_name: (str) Execution Module Function name
    :return: difctionary with uuid4, jid, function_name keys

    If identity already present in kawargs, use it as is.
    """
    return {
        "uuid4": str(uuid.uuid4()),
        "jid": "state.nr.{}".format(function_name),
        "function_name": "state.nr.{}".format(function_name),
    }


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
        ret = {"name": state_name, "changes": result, "result": True, "comment": ""}
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
    state_name = kwargs.pop("name")
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
        result = __salt__["nr.task"](*args, **kwargs)
        ret = {"name": state_name, "changes": result, "result": True, "comment": ""}
    return ret


def _run_workflow_step(
    step,
    steps_failed,
    steps_passed,
    common_filters,
    report_all,
    report,
    all_hosts,
    hcache,
    dcache,
    state_name,
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
    :param hcache: (bool) if True saves step results in host's data
    :param dcache: (bool) if True saves step results in defaults data
    :param state_name: (str) Name of this state
    """
    nr_fun = [
        "nr.cli",
        "nr.task",
        "nr.cfg",
        "nr.cfg_gen",
        "nr.tping",
        "nr.test",
        "nr.nc",
        "nr.http",
        "nr.do",
        "nr.gnmi",
    ]
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
        if step["function"] in nr_fun:
            step["kwargs"]["add_details"] = True

        # form FL filter based on run_if criteria
        FL = set(all_hosts)
        if step.get("run_if_fail_any"):
            hosts_failed_any_required_step = set()
            for required_step in step["run_if_fail_any"]:
                if required_step not in steps_failed:
                    raise CommandExecutionError(
                        "Step '{a}' run_if_fail_any requires '{b}', but '{b}' not executed".format(
                            a=step["name"], b=required_step
                        )
                    )
                # add all hosts that failed this step
                hosts_failed_any_required_step.update(steps_failed[required_step])
            FL = hosts_failed_any_required_step.intersection(FL)
        if step.get("run_if_pass_any"):
            hosts_passed_any_required_step = set()
            for required_step in step["run_if_pass_any"]:
                if required_step not in steps_passed:
                    raise CommandExecutionError(
                        "Step '{a}' run_if_pass_any requires '{b}', but '{b}' not executed".format(
                            a=step["name"], b=required_step
                        )
                    )
                # add all hosts that passed this step
                hosts_passed_any_required_step.update(steps_passed[required_step])
            FL = hosts_passed_any_required_step.intersection(FL)
        if step.get("run_if_fail_all"):
            for required_step in step["run_if_fail_all"]:
                if required_step not in steps_failed:
                    raise CommandExecutionError(
                        "Step '{a}' run_if_fail_all requires '{b}', but '{b}' not executed".format(
                            a=step["name"], b=required_step
                        )
                    )
                # leave only hosts that failed required step
                FL = steps_failed[required_step].intersection(FL)
        if step.get("run_if_pass_all"):
            for required_step in step["run_if_pass_all"]:
                if required_step not in steps_passed:
                    raise CommandExecutionError(
                        "Step '{a}' run_if_pass_all requires '{b}', but '{b}' not executed".format(
                            a=step["name"], b=required_step
                        )
                    )
                # leave only hosts that passed required step
                FL = steps_passed[required_step].intersection(FL)

        # form FL filter by intersecting it with FL kwargs argument if any
        if "FL" in step["kwargs"]:
            step["kwargs"]["FL"] = list(set(step["kwargs"]["FL"]).intersection(FL))
        else:
            step["kwargs"]["FL"] = list(FL)

        # get list of hosts matched by this step
        matched_hosts = __salt__["nr.nornir"]("hosts", **step["kwargs"])

        # handle when have no hosts to run step against
        if not matched_hosts and report_all:
            log.info("state:nr.workflow: no hosts matched for step: '{}'".format(step))
            if step.get("report") is not False:
                report["details"].append({step["name"]: {}})
            for host_name, host_steps in report["summary"].items():
                host_steps.append({step["name"]: "SKIP"})
            return

        # add cache argument
        if step["function"] in nr_fun:
            if hcache:
                step["kwargs"].setdefault("hcache", step["name"])
            if dcache:
                step["kwargs"].setdefault("dcache", step["name"])

        # run step function
        log.debug("state:nr.workflow: executing step: '{}'".format(step))
        result = __salt__[step["function"]](
            identity=_form_identity("workflow.{}.{}".format(state_name, step["name"])),
            *step.get("args", []),
            **step["kwargs"]
        )
        log.debug("state:nr.workflow: step '{}'; result:\n {}".format(step, result))

        # record a set of hosts that failed/passed this step
        if step["function"] == "nr.do":
            # decide on test execution result - fail or pass
            if result["failed"] is True:
                steps_failed[step["name"]] = set(matched_hosts)
            else:
                steps_passed[step["name"]] = set(matched_hosts)
            # form report content
            for host_name in set(matched_hosts):
                report["summary"][host_name].append(
                    {step["name"]: "FAIL" if result["failed"] else "PASS"}
                )
        elif step["function"] in nr_fun:
            # result is a dict if to_dict set to True
            if isinstance(result, dict):
                for host_name, host_results in result.items():
                    for task_result in host_results.values():
                        if task_result["failed"] or task_result.get("success") is False:
                            report["summary"][host_name].append({step["name"]: "FAIL"})
                            steps_failed[step["name"]].add(host_name)
                            break
                    else:
                        report["summary"][host_name].append({step["name"]: "PASS"})
                        steps_passed[step["name"]].add(host_name)
            # result is a list if to_dict set to false
            elif isinstance(result, list):
                for task_result in result:
                    steps_passed.setdefault(task_result["name"], set())
                    steps_failed.setdefault(task_result["name"], set())
                    if task_result["failed"] or task_result.get("success") is False:
                        steps_failed[task_result["name"]].add(task_result["host"])
                        report["summary"][task_result["host"]].append(
                            {task_result["name"]: "FAIL"}
                        )
                    else:
                        steps_passed[task_result["name"]].add(task_result["host"])
                        report["summary"][task_result["host"]].append(
                            {task_result["name"]: "PASS"}
                        )
            # result can be a string if table formatter used or received a traceback
            elif isinstance(result, str):
                if "Traceback (most recent call last)" in result:
                    steps_failed[step["name"]] = set(matched_hosts)
                    for host_name in matched_hosts:
                        report["summary"][host_name].append({step["name"]: "ERROR"})
                else:
                    steps_passed[step["name"]] = set(matched_hosts)
                    for host_name in matched_hosts:
                        report["summary"][host_name].append({step["name"]: "PASS"})
        else:
            steps_passed[step["name"]] = set(matched_hosts)
            for host_name in matched_hosts:
                report["summary"][host_name].append({step["name"]: "PASS"})

        # check if need to add step run results to detailed report
        if step.get("report") is not False:
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


def _decide_state_execution_status(options, ret, steps_failed, steps_passed):
    """
    Helper function to decide state execution status based on options
    fail_if... criteria.

    :param options: (dict) state options dictionary
    :param ret: (dict) state execution return structure
    :param steps_failed: (dict) dictionary of failed steps
    :param steps_passed: (dict) dictionary of passed steps
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

    **State Global Options**

    State Global Options defined under ``options`` key.

    :param report_all: (bool) if True (default) adds skipped steps in summary report
    :param fail_if_any_host_fail_any_step: (list) steps to decide if state execution failed
    :param fail_if_any_host_fail_all_step: (list) steps to decide if state execution failed
    :param fail_if_all_host_fail_any_step: (list) steps to decide if state execution failed
    :param fail_if_all_host_fail_all_step: (list) steps to decide if state execution failed
    :param filters: (dict) set of ``Fx`` filters to apply for all steps, per-step
        filters have higher priority. If no ``Fx`` filters provided, state steps run
        without any filters, depending on proxy ``nornir_filter_required`` setting,
        steps might fail (if ``nornir_filter_required`` is True) or run for all hosts
        (if ``nornir_filter_required`` is False).
    :param hcache: (bool) if True (default) saves step's per-host results in host's data under
        step's name key so that other steps can use it
    :param dcache: (bool) if True (default) saves step's full results in defaults data under
        step's name key so that other steps can use it

    **Individual Step Arguments**

    Each step in a work flow can have a number of mandatory and optional attributes defined.

    :param name: (str) mandatory, name of this step
    :param function: (str) mandatory, name of Nornir Execution Module function to run
    :param kwargs: (dict) ``**kwargs`` for Execution Module function
    :param args: (list) ``*args`` for Execution Module function
    :param report: (bool) if True (default) adds step execution results in detailed report
    :param run_if_fail_any: (list) this step will run if ``any`` of the previous steps in a list failed
    :param run_if_pass_any: (list) this step will run if ``any`` of the previous steps in a list passed
    :param run_if_fail_all: (list) this step will run if ``all`` of the previous steps in a list failed
    :param run_if_pass_all: (list) this step will run if ``all`` of the previous steps in a list passed

    While workflow steps can call any execution module function, ``run_if_x``
    properly supported only for Nornir Execution Module functions: ``nr.task``,
    ``nr.cli``, ``nr.cfg_gen``, ``nr.cfg``, ``nr.test``, ``nr.nc``, ``nr.http``,
    ``nr.do`` - for all other functions step considered as ``PASS`` unconditionally.

    If function reference ``nr.test`` with test suite, each test suite test
    item added to summary report, in addition, step's arguments ``run_if_x``
    conditions **must** reference test suite individual tests' names attribute.

    .. warning:: if you use per host filename feature, e.g. ``filename="salt://path/to/{{ host.name }}.cfg"``
       make sure to either disable state file jinja2 rendering using ``#!yaml``
       shebang at the beginning of the state file or escape double curly braces
       in filename argument.

    Execution of steps done on a per host basis, or, say better, each step
    determines a set of hosts it needs to run for using ``Fx`` filters and
    ``run_if_x`` conditions. If multiple ``run_if_x`` conditions specified,
    host must satisfy all of them - AND logic - for step to be executed
    for that host.

    If no ``run_if_x`` conditions provided, step executed for all hosts matched
    by ``filters`` provided in state global options and/or step ``**kwargs``.

    If ``hcache`` or ``dcache`` set to True in State Global Options in that case for compatible
    Nornir Execution Module function each step results saved in Nornir in-memory Inventory
    host's and ``defaults`` data under step's name key. That way results become part of inventory
    and available for use by Nornir Execution Module function in other steps. Once workflow execution
    completed, cached results cleaned. Individual step's ``hcache`` or ``dcache`` kwargs can be
    specified to save step's results under certain key name, in such a case after workflow completed
    cache not removed for that particular step's results.

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
                hcache: True
                dcache: False
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

    Executing workflow returns detailed and summary reports. Detailed
    report contains run details for each step being executed. Summary
    report contains per-host brief report of all steps statuses, where
    status can be:

    * ``PASS`` - step passed, Nornir Execution Module task result ``failed``
      attribute is False or ``success`` attribute is True
    * ``FAIL`` - step failed, Nornir Execution Module task result ``failed``
      attribute is True or ``success`` attribute is False
    * ``SKIP`` - step skipped and not executed, usually due to ``run_if_x``
      conditions not met for the host
    * ``ERROR`` - State Module encountered exception while running this step

    Sample report::

        nrp1:
        ----------
                  ID: change_step_1
            Function: nr.workflow
              Result: True
             Comment:
             Started: 12:01:58.578925
            Duration: 5457.171 ms
             Changes:
                      ----------
                      details:
                          |_
                            ----------
                            apply_logging_config:
                                ----------
                                ceos1:
                                    ----------
                                    netmiko_send_config:
                                        ----------
                                        changed:
                                            True
                                        connection_retry:
                                            0
                                        diff:
                                        exception:
                                            None
                                        failed:
                                            False
                                        result:
                                            configure terminal
                                            ceos1(config)#logging host 5.5.5.5
                                            ceos1(config)#end
                                            ceos1#
                                        task_retry:
                                            0
                                ceos2:
                                    ----------
                                    netmiko_send_config:
                                        ----------
                                        changed:
                                            True
                                        connection_retry:
                                            0
                                        diff:
                                        exception:
                                            None
                                        failed:
                                            False
                                        result:
                                            configure terminal
                                            ceos2(config)#logging host 5.5.5.5
                                            ceos2(config)#end
                                            ceos2#
                                        task_retry:
                                            0
                      summary:
                          ----------
                          ceos1:
                              |_
                                ----------
                                apply_logging_config:
                                    PASS
                          ceos2:
                              |_
                                ----------
                                apply_logging_config:
                                    PASS
    """
    steps_failed, steps_passed = {}, {}
    options = kwargs.pop("options", {})
    report_all = options.get("report_all", True)
    common_filters = options.get("filters", {})
    hcache = options.get("hcache", True)
    dcache = options.get("dcache", True)
    state_name = kwargs.pop("name")

    # get all hosts names
    all_hosts = __salt__["nr.nornir"]("hosts", **common_filters)

    # form report and ret strutures
    report = {"details": [], "summary": {h: [] for h in all_hosts}}
    ret = {"name": state_name, "changes": report, "result": True, "comment": ""}

    # run steps
    steps_names = []
    for group_name, steps in kwargs.items():
        log.info("state:nr.workflow: running '{}' steps".format(group_name))
        for step in steps:
            log.info("state:nr.workflow: running step: '{}'".format(step))
            steps_names.append(step["name"])
            _run_workflow_step(
                step,
                steps_failed,
                steps_passed,
                common_filters,
                report_all,
                report,
                all_hosts,
                hcache,
                dcache,
                state_name,
            )

    # clean up cached data
    if hcache:
        _ = __salt__["nr.nornir"]("clear_hcache", cache_keys=steps_names)
        log.info("state:nr.workflow: cleaned steps' hcache")
    if dcache:
        _ = __salt__["nr.nornir"]("clear_dcache", cache_keys=steps_names)
        log.info("state:nr.workflow: cleaned steps' dcache")

    # decide if this state failed
    ret = _decide_state_execution_status(options, ret, steps_failed, steps_passed)

    return ret
