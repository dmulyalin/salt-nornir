"""
Nornir Execution Module
=======================

Nornir Execution module reference.

.. note:: Keep in mind that execution module functions executed on same machine where proxy-minion process runs.

Introduction
------------

This execution module complements Nornir Proxy module to interact with devices over SSH, Telnet,
NETCONF or any other methods supported by Nornir connection plugins.

Things to keep in mind:

* ``multiprocessing`` set to ``True`` is recommended way of running Nornir proxy-minion
* with multiprocessing on, dedicated process starts for each task consuming resources
* tasks executed one after another, but task execution against hosts happening in order
    controlled by logic of Nornir runner in use, usually in parallel using threading.

Commands timeout
----------------

It is recommended to increase
`salt command timeout <https://docs.saltstack.com/en/latest/ref/configuration/master.html#timeout>`_
or use ``--timeout=60`` option to wait for minion return, as all together it might take more than
5 seconds for task to complete. Alternatively, use ``--async`` option and query results afterwards::

    [root@localhost /]# salt nrp1 nr.cli "show clock" --async

    Executed command with job ID: 20210211120453972915
    [root@localhost /]# salt-run jobs.lookup_jid 20210211120453972915
    nrp1:
        ----------
        IOL1:
            ----------
            show clock:

                *08:17:22.691 EET Sat Feb 13 2021
        IOL2:
            ----------
            show clock:
                *08:17:22.632 EET Sat Feb 13 2021
    [root@localhost /]#

AAA considerations
------------------

Quiet often AAA servers (Radius, Tacacs) might get overloaded with authentication
and authorization requests coming from devices due to Nornir establishing
connections with them, that effectively results in jobs failures.

To overcome above problems Nornir proxy-module uses ``RetryRunner`` by default.
``RetryRunner`` runner included in
`nornir-salt <https://github.com/dmulyalin/nornir-salt>`_ library and was
developed to address aforementioned issue in addition to implementing retry logic.

Targeting Nornir Hosts
----------------------

Nornir interacts with many devices and has it's own inventory,
additional filtering capabilities introduced in
`nornir_salt <https://github.com/dmulyalin/nornir-salt>`_ library
to narrow down tasks execution to certain hosts/devices.

Sample command to demonstrate targeting capabilites::

    salt nornir-proxy-1 nr.cli "show clock" FB="R*" FG="lab" FP="192.168.1.0/24" FO='{"role": "core"}'

Jumphosts or Bastions
---------------------

``RetryRunner`` included in
`nornir_salt <https://github.com/dmulyalin/nornir-salt>`_ library has
support for ``nr.cli`` function and ``nr.cfg`` with ``plugin="netmiko"``
to interact with devices behind jumphosts, other tasks and runners plugins
does not support that.

Sample jumphost definition in host's inventory data in proxy-minion pillar::

    hosts:
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

Nornir Execution module functions summary
-----------------------------------------

Table to summarize functions available in Nornir Proxy Execution Module.

+--------------+---------------------------------------------------+--------------------+
| nr.function  | description                                       | supported plugins  |
+==============+===================================================+====================+
| inventory    | To retrive nornir inventory information           |                    |
+--------------+---------------------------------------------------+--------------------+
| task         | Function to run any nornir task plugin            |                    |
+--------------+---------------------------------------------------+--------------------+
| cli          | Function for show commands output collection over | netmiko (default), |
|              | ssh or telnet                                     | scrapli            |
+--------------+---------------------------------------------------+--------------------+
| cfg          | Function to modify devices configuration over     | napalm (default),  |
|              | ssh or telnet connections                         | netmiko, scrapli   |
+--------------+---------------------------------------------------+--------------------+
| cfg_gen      | Function to generate devices configuration using  |                    |
|              | SALT templating system with Nornir inventory,     |                    |
|              | mainly for testing purposes                       |                    |
+--------------+---------------------------------------------------+--------------------+
| test         | Function to test show commands output             | napalm (default),  |
|              | produced by nr.cli function                       | netmiko, scrapli   |
+--------------+---------------------------------------------------+--------------------+
| tping        | Function to run TCP ping to devices's hostnames   |                    |
+--------------+---------------------------------------------------+--------------------+
| nc           | Function to work with devices using NETCONF       | ncclient (default),|
|              |                                                   | scrapli_netconf    |
+--------------+---------------------------------------------------+--------------------+
| do           | Function to execute alias with a set of steps     |                    |
|              | calling other execution functions, allows to      |                    |
|              | construct simple workflows                        |                    |
+--------------+---------------------------------------------------+--------------------+

Nornir Execution module functions
---------------------------------

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.inventory
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.task
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.cli
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.cfg
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.cfg_gen
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.tping
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.stats
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.test
.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.nc
"""

# Import python libs
import logging
import os
import time
import traceback
import fnmatch

log = logging.getLogger(__name__)


# import salt libs, wrapping it in try/except for docs to generate
try:
    from salt.exceptions import CommandExecutionError
except:
    log.error("Nornir Execution Module - failed importing SALT libraries")

# import nornir libs
try:
    from nornir import InitNornir
    from nornir_salt import tcp_ping
    from nornir_salt.plugins.functions import (
        FindString,
        RunTestSuite,
        TabulateFormatter,
    )

    HAS_NORNIR = True
except ImportError:
    log.error("Nornir Execution Module - failed importing libraries")
    HAS_NORNIR = False

# import salt libs, wrapping it in try/except for docs to generate
try:
    from salt.exceptions import CommandExecutionError
except:
    log.error("Nornir Proxy Module - failed importing SALT libraries")

__virtualname__ = "nr"
__proxyenabled__ = ["nornir"]


def __virtual__():
    if HAS_NORNIR:
        return __virtualname__
    return False


# -----------------------------------------------------------------------------
# callable module function
# -----------------------------------------------------------------------------


def inventory(**kwargs):
    """
    Return inventory dictionary for Nornir hosts

    :param Fx: filters to filter hosts
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``

    Sample Usage::

        salt nornir-proxy-1 nr.inventory
        salt nornir-proxy-1 nr.inventory FB="R[12]"
    """
    return __proxy__["nornir.inventory_data"](**kwargs)


def task(plugin, *args, **kwargs):
    """
    Function to invoke any of supported Nornir task plugins. This function
    performs dynamic import of requested plugin function and executes
    ``nr.run`` using supplied args and kwargs

    :param plugin: ``path.to.plugin.task_fun`` to run ``from path.to.plugin import task_fun``
    :param Fx: filters to filter hosts
    :param add_details: boolean, to include details in result or not
    :param add_cpid_to_task_name: boolean, include Child Process ID (cpid) for debugging
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``

    ``plugin`` attribute can reference file on SALT Master with ``task`` function content,
    that file downloaded from master, compiled and executed. File must contain function
    named ``task`` accepting Nornir task object as a first positional argument, for
    instance::

        # define connection name for RetryRunner to properly detect it
        CONNECTION_NAME = "netmiko"

        # create task function
        def task(nornir_task_object, *args, **kwargs):
            pass

    .. note:: ``CONNECTION_NAME`` must be defined within custom task function file if
        RetryRunner in use, otherwise connection retry logic skipped and connections
        to all hosts initiated simultaneously up to the number of num_workers.

    Sample usage::

        salt nornir-proxy-1 nr.task "nornir_napalm.plugins.tasks.napalm_cli" commands='["show ip arp"]' FB="IOL1"
        salt nornir-proxy-1 nr.task "nornir_netmiko.tasks.netmiko_save_config" add_details=False
        salt nornir-proxy-1 nr.task "nornir_netmiko.tasks.netmiko_send_command" command_string="show clock"
        salt nornir-proxy-1 nr.task nr_test a=b c=d add_details=False
        salt nornir-proxy-1 nr.task salt://path/to/task.txt
        salt nornir-proxy-1 nr.task plugin=salt://path/to/task.py
    """
    return __proxy__["nornir.execute_job"](
        task_fun=plugin, args=args, kwargs=kwargs, cpid=os.getpid()
    )


def cli(*commands, **kwargs):
    """
    Method to retrieve commands output from devices using ``send_command``
    task plugin from either Netmiko or Scrapli library.

    :param commands: list of commands or multiline string
    :param Fx: filters to filter hosts
    :param netmiko_kwargs: kwargs to pass on to netmiko send_command methods
    :param add_details: boolean, to include details in result or not
    :param add_cpid_to_task_name: boolean, include Child Process ID (cpid) for debugging
    :param plugin: name of send command task plugin to use - ``netmiko`` (default) or ``scrapli``
    :param match: regular expression pattern to search for in results,
        similar to Cisco ``inlclude`` or Juniper ``match`` pipe commands
    :param before: used with match, number of lines before match to include in results, default is 0
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``

    Sample Usage::

         salt nornir-proxy-1 nr.cli "show clock" "show run" FB="IOL[12]" netmiko_kwargs='{"use_timing": True, "delay_factor": 4}'
         salt nornir-proxy-1 nr.cli commands='["show clock", "show run"]' FB="IOL[12]" netmiko_kwargs='{"strip_prompt": False}'
         salt nornir-proxy-1 nr.cli "show run" FL="SW1,RTR1,RTR2" match="CPE[123]+" before=1
         salt nornir-proxy-1 nr.cli "show clock" FO='{"platform__any": ["ios", "nxos_ssh", "cisco_xr"]}' for filtering
    """
    commands = kwargs.pop("commands", commands)
    kwargs["commands"] = [commands] if isinstance(commands, str) else commands
    plugin = kwargs.pop("plugin", __proxy__["nornir.nr_data"]("default_nr_cli_plugin"))
    if plugin.lower() == "netmiko":
        task_fun = "netmiko_send_commands"
        kwargs["connection_name"] = "netmiko"
    elif plugin.lower() == "scrapli":
        task_fun = "_scrapli_send_commands"
        kwargs["connection_name"] = "scrapli"
    else:
        return "Unsupported plugin name: {}".format(plugin)
    result = __proxy__["nornir.execute_job"](
        task_fun=task_fun, args=[], kwargs=kwargs, cpid=os.getpid()
    )
    if "match" in kwargs:
        result = FindString(
            result, pattern=kwargs["match"], before=kwargs.get("before", 0)
        )
    return result


def cfg(*commands, **kwargs):
    """
    Function to push configuration to devices using ``napalm_configure`` or
    ``netmiko_send_config`` or Scrapli ``send_config`` task plugin.

    :param commands: (list) list of commands or multiline string to send to device
    :param filename: (str) path to file with configuration
    :param template_engine: (str) template engine to render configuration, default is jinja
    :param saltenv: (str) name of SALT environment
    :param context: Overrides default context variables passed to the template.
    :param defaults: Default context passed to the template.
    :param plugin: (str) name of configuration task plugin to use - ``napalm`` (default) or ``netmiko`` or ``scrapli``
    :param dry_run: (bool) default False, controls whether to apply changes to device or simulate them
    :param Fx: filters to filter hosts
    :param add_details: (bool) to include details in result or not
    :param add_cpid_to_task_name: (bool) include Child Process ID (cpid) for debugging
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``
    :param commit: (bool or dict) by default commit is ``True``. If ``plugin=netmiko``
        connection ``commit`` method called following with ``exit_config_mode`` call. If
        ``commit`` argument is a dictionary, it is supplied to commit call using
        ``**commit``.

    .. warning:: ``dry_run`` not supported by ``netmiko`` plugin

    .. warning:: ``commit`` not supported by ``scrapli`` plugin. To commit need to send commit
        command as part of configuration, moreover, scrapli will not exit configuration mode,
        need to send exit command as part of configuration mode as well.

    In addition to normal `context variables <https://docs.saltstack.com/en/latest/ref/states/vars.html>`_
    template engine loaded with additional context variable `host`, to access Nornir host
    inventory data.

    Sample usage::

        salt nornir-proxy-1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" FB="R[12]" dry_run=True
        salt nornir-proxy-1 nr.cfg commands='["logging host 1.1.1.1", "ntp server 1.1.1.2"]' FB="R[12]"
        salt nornir-proxy-1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" plugin="netmiko"
        salt nornir-proxy-1 nr.cfg filename=salt://template/template_cfg.j2 FB="R[12]"
        salt nornir-proxy-1 nr.cfg filename=salt://template/cfg.j2 FB="XR-1" commit='{"confirm": True"}'

    Filename argument can be a template string, for instance::

        salt nornir-proxy-1 nr.cfg filename=salt://templates/{{ host.name }}_cfg.txt

    In that case filename rendered to form path string, after that, path string used to download file
    from master, downloaded file further rendered using specified template engine (Jinja2 by default).
    That behaviour supported only for filenames that start with ``salt://``. This feature allows to
    specify per-host configuration files for applying to devices.
    """
    # get arguments
    filename = kwargs.pop("filename", None)
    plugin = kwargs.pop("plugin", __proxy__["nornir.nr_data"]("default_nr_cfg_plugin"))
    kwargs.setdefault("add_details", True)
    # get configuration
    config = commands if commands else kwargs.pop("commands", None)
    config = "\n".join(config) if isinstance(config, (list, tuple)) else config
    if not config:
        config = __salt__["cp.get_file_str"](
            filename, saltenv=kwargs.get("saltenv", "base")
        )
    kwargs["config"] = config if config else filename
    # decide on task name to run
    if plugin.lower() == "napalm":
        task_fun = "_napalm_configure"
        kwargs["connection_name"] = "napalm"
    elif plugin.lower() == "netmiko":
        task_fun = "_netmiko_send_config"
        kwargs["connection_name"] = "netmiko"
    elif plugin.lower() == "scrapli":
        task_fun = "_scrapli_send_config"
        kwargs["connection_name"] = "scrapli"
    else:
        return "Unsupported plugin name: {}".format(plugin)
    # work and return results
    return __proxy__["nornir.execute_job"](
        task_fun=task_fun, args=[], kwargs=kwargs, cpid=os.getpid()
    )


def cfg_gen(filename, *args, **kwargs):
    """
    Function to render configuration from template file. No configuration pushed
    to devices.

    This function can be useful to stage/test templates or to generate configuration
    without pushing it to devices.

    :param filename: path to template
    :param template_engine: template engine to render configuration, default is jinja
    :param saltenv: name of SALT environment
    :param context: Overrides default context variables passed to the template.
    :param defaults: Default context passed to the template.
    :param add_details: boolean, to include details in result or not
    :param add_cpid_to_task_name: boolean, include Child Process ID (cpid) for debugging
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``

    In addition to normal `context variables <https://docs.saltstack.com/en/latest/ref/states/vars.html>`_
    template engine loaded with additional context variable `host`, to access Nornir host's
    inventory data.

    Returns rendered configuration.

    Sample usage::

        salt nornir-proxy-1 nr.cfg_gen filename=salt://templates/template.j2 FB="R[12]"

    Sample template.j2 content::

        proxy data: {{ pillar.proxy }}
        jumphost_data: {{ host["jumphost"] }} # "jumphost" defined in host's data
        hostname: {{ host.name }}
        platform: {{ host.platform }}

    Filename argument can be a template string, for instance::

        salt nornir-proxy-1 nr.cfg_gen filename=salt://template/{{ host.name }}_cfg.txt

    In that case filename rendered to form path string, after that, path string used to download file
    from master, downloaded file further rendered using specified template engine (Jinja2 by default).
    That behaviour supported only for filenames that start with ``salt://``. This feature allows to
    specify per-host configuration files for applying to devices.
    """
    # get configuration file content
    kwargs["config"] = __salt__["cp.get_file_str"](
        filename, saltenv=kwargs.get("saltenv", "base")
    )
    kwargs["filename"] = filename
    # work and return results
    return __proxy__["nornir.execute_job"](
        task_fun="_cfg_gen", args=[], kwargs=kwargs, cpid=os.getpid()
    )


def tping(ports=[], timeout=1, host=None, **kwargs):
    """
    Tests connection to TCP port(s) by trying to establish a three way
    handshake. Useful for network discovery or testing.

    :param ports (list of int, optional): tcp ports to ping, defaults to host's port or 22
    :param timeout (int, optional): defaults to 1
    :param host (string, optional): defaults to ``hostname``
    :param add_details: boolean, to include details in result or not
    :param add_cpid_to_task_name: boolean, include Child Process ID (cpid) for debugging
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``

    Sample usage::

        salt nornir-proxy-1 nr.tping
        salt nornir-proxy-1 nr.tping FB="LAB-RT[123]"

    Returns result object with the following attributes set:

    * result (``dict``): Contains port numbers as keys with True/False as values
    """
    kwargs["ports"] = ports
    kwargs["timeout"] = timeout
    kwargs["host"] = host
    # work and return results
    return __proxy__["nornir.execute_job"](
        task_fun="nornir_salt.plugins.tasks.tcp_ping",
        args=[],
        kwargs=kwargs,
        cpid=os.getpid(),
    )


def stats(*args, **kwargs):
    """
    Function to gather and return stats about Nornir proxy process.

    :param stat: name of stat to return, returns all by default
    """
    return __proxy__["nornir.stats"](*args, **kwargs)


def test(*args, **kwargs):
    """
    Function to perform tests for certain criteria against show commands output
    from devices.

    :param commands: (str or list) single command or list of commands to get from
        device, each command retrieved as a separate task named after the command
    :param name: (str) descriptive name of the test, will be added to results
    :param Fx: filters to filter hosts
    :param test: (str) type of test to do e.g.: contains, !contains, equal, custom etc.
    :param pattern: (str) pattern to use for testing, usually string, text or
        reference a text file on salt master. For instance if ``test`` is ``contains``,
        ``pattern`` value used as a pattern for containment check.
    :param name: (str) test name, task name will be set to test name
    :param function_file: (str) path to text file on salt master with function content
        to use for ``custom`` function test
    :param saltenv: (str) name of salt environment to downoad files from
    :param suite: (list) list of dictionaries with test items
    :param plugin: (str) plugin name to use with ``nr.cli`` function to gather output
        from devices, default is ``netmiko``
    :param brief: (bool) default is False, if True nr.test returns nested dictionary,
        top dictionary keyed by ``name``, nested dictionary keyd by hosts' name
    :param failed_only: (bool) default is False, if True ``nr.cli`` returns result for
        failed tests only
    :param subset: (list or str) list or string with comma separated glob patterns to
        match tests' names to execute. Patterns are not case-sensitive. Uses
        ``fnmatch.fnmatch`` Python built-in function to do matching.
    :param **kwargs: any additional arguments to pass on to ``nr.cli`` and test function

    Sample usage::

        salt np1 nr.test "show run | inc ntp" contains "1.1.1.1" FB="*host-1"
        salt np1 nr.test "show run | inc ntp" contains "1.1.1.1" --output=table
        salt np1 nr.test "show run | inc ntp" contains "1.1.1.1" brief=True
        salt np1 nr.test commands='["show run | inc ntp"]' test=contains pattern="1.1.1.1" brief=True

    Function nr.test can run a suite of test cases::

        salt np1 nr.test suite=salt://tests/suite_1.txt

    Where salt://tests/suite_1.txt content is::

        - task: "show run | inc ntp"
          test: contains
          pattern: 1.1.1.1
          name: check NTP cfg
          cli:
            FB: core-*
            plugin: netmiko
        - test: contains_lines
          pattern: ["1.1.1.1", "2.2.2.2"]
          task: "show run | inc ntp"
          name: check NTP cfg lines
        - test: custom
          function_file: salt://tests/ntp_config.py
          task: "show run | inc ntp"
          name: check NTP cfg pattern from file
        - test: custom
          function_file: salt://tests/ntp_config.py
          task:
            - "show ntp status"
            - "show ntp associations"
          name: "Is NTP in sync"

    Returns a list of dictionaries with check results, each dictionary contains::

        {
            "host": name of host,
            "name": descriptive name of the test,
            "task": name of task results of which used for test,
            "result": PASS or FAIL,
            "success": True or False,
            "error": None or Error description,
            "test_type": Type of test performed,
            "criteria": Validation criteria used
        }

    Reference
    `nornir-salt <https://nornir-salt.readthedocs.io/en/latest/Functions.html#run-tests-suite>`_
    documentation for more details on using test suite.

    In test suite, ``task`` argument can reference a list of tasks.

    Commands output for each item in a suite collected using ``nr.cli`` function, arguments under
    ``cli`` keyword pass on to ``nr.cli`` function.

    List of arguments in a test suite that can reference text file on salt master using
    ``salt://path/to/file.txt``:

    * ``pattern`` - content of the file rendered and used to perform the test together with
        ``ContainsTest``, ``ContainsLinesTest`` or ``EqualTest``
        `test functions <https://nornir-salt.readthedocs.io/en/latest/Functions.html#test-functions>`_
    * ``schema`` - used with
        `<CerberusTest https://nornir-salt.readthedocs.io/en/latest/Functions.html#cerberus-validation>`_
        function
    * ``function_file`` - content of the file passed to nornir-salt's
        `<CustomFunctionTest https://nornir-salt.readthedocs.io/en/latest/Functions.html#custom-test-function>`_
        function using function_text argument
    """
    # filter kwargs
    kwargs = {k: v for k, v in kwargs.items() if not str(k).startswith("__")}

    # extract attributes
    commands = args[0] if args else kwargs.pop("commands", [])
    test = args[1] if len(args) > 1 else kwargs.pop("test", None)
    pattern = args[2] if len(args) > 2 else kwargs.pop("pattern", "")
    name = args[3] if len(args) > 3 else kwargs.pop("name", "")
    commands = [commands] if isinstance(commands, str) else commands
    saltenv = kwargs.pop("saltenv", "base")
    suite = kwargs.pop("suite", [])
    subset = kwargs.pop("subset", [])
    subset = (
        [i.strip() for i in subset.split(",")] if isinstance(subset, str) else subset
    )
    table = kwargs.pop("table", {})  # table
    headers = kwargs.pop("headers", "keys")  # table
    test_results = []
    filtered_suite = []

    # make sure return structe is a list of dicts, with details by default
    kwargs["to_dict"] = False
    kwargs.setdefault("add_details", True)

    # check if need to download pattern file from salt master
    if pattern.startswith("salt://"):
        pattern = __salt__["cp.get_file_str"](pattern, saltenv=saltenv)

    # if test suite provided, download it from master and render it
    if suite:
        suite_name = suite
        suite = __salt__["slsutil.renderer"](suite)
        if not suite:
            raise CommandExecutionError(
                "Suite file '{}' not on master; path correct?".format(suite_name)
            )
    else:
        suite.append(
            {
                "test": test,
                "task": commands[0] if len(commands) == 1 else commands,
                "name": name,
                **kwargs,
            }
        )

    # filter suite items and check if need to dowload any files from master
    for item in suite:
        # check if need to filter test case
        if subset and not any(map(lambda m: fnmatch.fnmatch(item["name"], m), subset)):
            continue

        # see if item's pattern referring to file
        if isinstance(item.get("pattern"), str) and item["pattern"].startswith(
            "salt://"
        ):
            item["pattern"] = __salt__["cp.get_file_str"](
                item["pattern"], saltenv=saltenv
            )
        # check if cerberus schema referring to file
        elif item.get("schema", "").startswith("salt://"):
            item["schema"] = __salt__["cp.get_file_str"](
                item["schema"], saltenv=saltenv
            )
            item["schema"] = __salt__["slsutil.renderer"](item["schema"])
        # check if function file given
        elif "function_file" in item:
            item["function_text"] = __salt__["cp.get_file_str"](
                item.pop("function_file"), saltenv=saltenv
            )

        # use pattern content otherwise
        elif item["test"] == "cerberus":
            item.setdefault("schema", pattern)
        elif item["test"] == "custom":
            item.setdefault("function_text", pattern)
        else:
            item.setdefault("pattern", pattern)

        filtered_suite.append(item)

    # run test items in a suite
    for test_item in filtered_suite:
        cli_kwargs = kwargs.copy()
        cli_kwargs.update(test_item.pop("cli", {}))
        cli_kwargs["commands"] = test_item["task"]
        cli_kwargs["tests"] = [test_item]
        log.debug("nr.test running nr.cli -'{}'".format(cli_kwargs))
        test_results += cli(**cli_kwargs)

    # format results to table if requested to do so
    if table:
        return TabulateFormatter(test_results, tabulate=table, headers=headers)

    return test_results


def nc(*args, **kwargs):
    """
    Function to interact with devices using NETCONF protocol utilising
    one of supported plugins.

    Available NETCONF plugin names:

    * ``ncclient`` - ``nornir_salt`` built-in plugin that uses ``ncclinet`` library to
        interact with devices
    * ``scrapli`` - uses ``scrapli_netconf`` connection plugin that is part of
        ``nornir_scrapli`` library, it does not use ``scrapli_netconf`` task plugins,
        but rather implements a wrapper around ``scrapli_netconf`` connection plugin
        connection object.

    :param call: (str) ncclient manager or scrapli netconf object method to call
    :param plugin: (str) Name of netconf plugin to use - ncclient (default) or scrapli
    :param Fx: filters to filter hosts
    :param data: (str) path to file for ``rpc`` method call or rpc content
    :param fmt: (str) result formatter to use - xml (default), raw_xml, json, yaml, pprint, py
    :param add_details: (bool) to include additional details in result or not
    :param tf: `ToFile <https://nornir-salt.readthedocs.io/en/latest/Functions.html#tofile>`_
        function's OS path to file where to save results, if present, ToFile function called
        together with provided ``**kwargs``
    :param method_name: (str) name of method to provide docstring for, used only by ``help`` call

    Special ``call`` arguments/methods:

    * ``dir`` - returns methods supported by Ncclient connection manager object::

        salt nrp1 nr.nc dir

    * ``help`` - returns ``method_name`` docstring::

        salt nrp1 nr.nc help method_name=edit_config

    * ``locked`` - same as ``edit_config``, but runs this (presumably more reliable) work flow:

        1. Lock target configuration/datastore
        2. Discard/clean previous changes if any
        3. Edit configuration
        4. Validate new confiugration if plugin and server supports it
        5. Run commit confirmed if plugin and server supports it
        6. Run final commit
        7. Unlock target configuration/datastore

        If any of steps 3, 4, 5, 6 fails, all changes discarded.

        Sample usage::

            salt nrp1 nr.nc locked target="candidate" config="salt://path/to/config_file.xml" FB="*core-1"

    .. warning:: beware of difference in keywords required by different plugins, e.g. ``filter`` for ``ncclient``
      vs ``filter_``/``filters`` for ``scrapli_netconf``, consult modules' api help for required arguments,
      using, for instance ``help`` call: ``salt nrp1 nr.nc help method_name=get_config``

    Examples of sample usage for ``ncclient`` plugin::

        salt nrp1 nr.nc server_capabilities FB="*"
        salt nrp1 nr.nc get_config filter='["subtree", "salt://rpc/get_config_data.xml"]' source="running"
        salt nrp1 nr.nc edit_config target="running" config="salt://rpc/edit_config_data.xml" FB="ceos1"
        salt nrp1 nr.nc commit

    Examples of sample usage for ``scrapli_netconf`` plugin::

        salt nrp1 nr.nc get filter_=salt://rpc/get_config_filter_ietf_interfaces.xml plugin=scrapli
        salt nrp1 nr.nc get_config source=running plugin=scrapli
        salt nrp1 nr.nc server_capabilities FB="*" plugin=scrapli
        salt nrp1 nr.nc rpc filter_=salt://rpc/get_config_rpc_ietf_interfaces.xml plugin=scrapli
        salt nrp1 nr.nc rpc data=salt://rpc/get_config_rpc_ietf_interfaces.xml plugin=scrapli
        salt nrp1 nr.nc locked target="candidate" config="salt://rpc/edit_config_ietf_interfaces.xml" plugin=scrapli
    """
    args = list(args)
    kwargs["call"] = args.pop(0) if args else kwargs.pop("call")
    plugin = kwargs.pop("plugin", __proxy__["nornir.nr_data"]("default_nr_nc_plugin"))

    if plugin.lower() == "ncclient":
        task_fun = "_ncclient_call"
        kwargs["connection_name"] = "ncclient"
    elif plugin.lower() == "scrapli":
        task_fun = "_scrapli_netconf_call"
        kwargs["connection_name"] = "scrapli_netconf"
    else:
        return "Unsupported plugin name: {}".format(plugin)

    result = __proxy__["nornir.execute_job"](
        task_fun=task_fun, args=args, kwargs=kwargs, cpid=os.getpid()
    )

    return result


def do(*args, **kwargs):
    """
    Function to perform steps defined under ``nornir:aliases`` configuration
    section at:

    * Minion's configuration
    * Minion's grains
    * Minion's pillar data
    * Master configuration (requires ``pillar_opts`` to be set to True in Minion
      config file in order to work)

    To retrieve aliases content Salt ``nr.do`` uses ``config.get`` execution module
    function with ``merge`` key set to ``True``.

    Each step definition requires these keywords to be defined:

    * ``function`` - mandatory, name of any execution module function to run
    * ``args`` - optional, any arguments to use with function
    * ``kwargs`` - optional, any keyword arguments to use with function

    Any other keywords defined inside the step are ignored.

    :param stop_on_error: (bool) if True (default), stop execution on error in the step, continue otherwise
    :param filepath: (str) path to file with aliases steps
    :param default_renderer: (str) shebang string to render file, default is 'jinja|yaml'
    :param describe: (bool) if True, returns alias content without executing it, default is False
    :param **kwargs: (any) additional ``kwargs`` to use with aliases steps, ``kwargs`` override
        ``kwargs`` dictionary defined within each step, for example, in command
        ``salt nrp1 nr.do configure_ntp FB="*core*"``, ``FB`` argument will override ``FB`` arguments
        defined within steps
    :returns: dictionary with keys: ``failed`` bool, ``result`` list; ``result`` key contains
        a list of results for steps; If ``stop_on_error`` set to ``True`` and error happens, ``failed``
        key set to ``True``

    .. note:: if ``filepath`` argument provided, aliases defined in other places are ignored; file
        loaded using Saltstack ``slsutil.renderer`` execution module function, as a result
        file can contain any of Saltstack supported renderers content and can be located
        at any url supported by ``cp.get_url`` execution module function. File content must
        render to a dictionary keyed by aliases names.

    Sample aliases steps definition using proxy minion pillar:

        nornir:
          aliases:
            awr:
              function: nr.cli
              args: ["wr"]
              kwargs: {"FO": {"platform": "arista_eos"}}
              description: "Save Arista devices configuration"
            configure_ntp:
              - function: nr.cfg
                args: ["ntp server 1.1.1.1"]
                kwargs: {"FB": "*"}
              - function: nr.cfg
                args: ["ntp server 1.1.1.2"]
                kwargs: {"FB": "*"}
              - function: nr.cli
                args: ["show run | inc ntp"]
                kwargs: {"FB": "*"}

    Sample aliases steps definition using text file under ``filepath``:

        awr:
          function: nr.cli
          args: ["wr"]
          kwargs: {"FO": {"platform": "arista_eos"}}
          description: "Save Arista devices configuration"
        configure_ntp:
          - function: nr.cfg
            args: ["ntp server 1.1.1.1"]
            kwargs: {"FB": "*"}
          - function: nr.cfg
            args: ["ntp server 1.1.1.2"]
            kwargs: {"FB": "*"}
          - function: nr.cli
            args: ["show run | inc ntp"]
            kwargs: {"FB": "*"}

    Alias ``awr`` has single step defined, while ``configure_ntp`` alias has multiple
    steps defined, each executed in order.

    Multiple aliases can be supplied to ``nr.do`` call.

    .. warning:: having column ``:`` as part of alias name not premitted, as ``:`` used by
        Salt ``config.get`` execution module function to split arguments on path items.

    Sample usage::

        salt nrp1 nr.do awr
        salt nrp1 nr.do configure_ntp awr stop_on_error=False
        salt nrp1 nr.do configure_ntp FB="*core*" add_details=True
        salt nrp1 nr.do awr filepath="salt://aliases/aliases_file.txt"
    """
    ret = {"failed": False, "result": []}
    kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}
    stop_on_error = kwargs.pop("stop_on_error", True)
    filepath = kwargs.pop("filepath", None)
    default_renderer = kwargs.pop("default_renderer", "jinja|yaml")
    describe = kwargs.pop("describe", False)

    # load file if filepath provided
    if filepath:
        file_content_dict = __salt__["slsutil.renderer"](
            path=filepath,
            default_renderer=default_renderer,
        )
        if not file_content_dict:
            ret["failed"] = True
            ret["result"].append({filepath: "Failed loading filepath content."})
            return ret

    # run aliases
    for alias_name in args:
        try:
            if filepath:
                alias_config = file_content_dict.get(alias_name)
            else:
                alias_config = __salt__["config.get"](
                    key="nornir:aliases:{}".format(alias_name), merge="recurse"
                )
            if not alias_config:
                raise CommandExecutionError(
                    "'{}' alias not loaded, content: '{}'".format(
                        alias_name, alias_config
                    )
                )
            elif describe:
                ret["result"].append({alias_name: alias_config})
                continue
            elif isinstance(alias_config, dict):
                alias_config = [alias_config]

            # run steps
            for step in alias_config:
                merged_kwargs = step.get("kwargs", {})
                merged_kwargs.update(kwargs)
                result = __salt__[step["function"]](
                    *step.get("args", []), **merged_kwargs
                )
                ret["result"].append({alias_name: result})
        except:
            tb = traceback.format_exc()
            log.error(
                "nr.do error while running '{}' alias:\n{}".format(alias_name, tb)
            )
            ret["result"].append({alias_name: tb})
            if stop_on_error:
                ret["failed"] = True
                break

    return ret


def gnmi(*arg, **kwarg):
    """ GNMI related function"""
    pass


def file(*arg, **kwarg):
    """ Manage Nornir-salt files """
    pass


def http(*arg, **kwarg):
    """ HTTP requests related functions """
    pass
