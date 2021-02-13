# -*- coding: utf-8 -*-
"""
Nornir State Module
===================

Nornir State module reference.

Introduction
------------

This state module uses Nornir proxy execution module to apply configuration
to devices.

This module does not implement idempotent behaviour, it is up to Nornir task
plugin to handle idempotancy.

Sample usage
------------

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

"""
# Import python libs
import logging


# -----------------------------------------------------------------------------
# globals
# -----------------------------------------------------------------------------


log = logging.getLogger(__name__)
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
    Enforce configuration state on device using Nornir
    execution module ``nr.cfg`` function.

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

    File salt://states/nr_state_logging_cfg.sls content located on Master::

        apply_logging_commands:
          nr.cfg:
            - commands:
              - logging host 1.1.1.1
              - logging host 2.2.2.2
            - plugin: netmiko
            - FB: "*"

    Apply state::

        salt nr_minion_id state.apply  nr_state_logging_cfg

    """
    state_name = kwargs.pop("name")
    if __opts__["test"]:
        ret = {
            "name": state_name,
            "changes": "",
            "result": None,
            "comment": "State nr.cfg will execute with param '{}'; '{}'".format(args, kwargs)
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
    Enforce configuration state on device using Nornir
    execution module ``nr.task`` function.

    :param plugin: ``path.to.plugin.task_fun`` to run ``from path.to.plugin import task_fun``
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
            "comment": "State nr.task will execute with param '{}'; '{}'".format(args, kwargs)
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