"""
Nornir Execution Module
=======================

SaltStack Nornir Execution Module exposes functionally of Nornir Proxy Minion to
work with devices and systems. Users can invoke Execution Modules functionality
using SALT CLI or one of SALT API - Python, REST. Usually, execution modules are
the modules that users work with a lot because they directly mapped to managed system
functionality such as CLI or NETCONF server.

Introduction
------------

Nornir Execution Module complements Nornir Proxy Minion Module to interact
with devices over SSH, Telnet, NETCONF or any other methods supported by
Nornir connection plugins.

Things to keep in mind:

* execution module functions executed on same machine where proxy-minion process runs
* ``multiprocessing`` set to ``True`` is recommended way of running Nornir proxy-minion
* with multiprocessing on, dedicated process starts for each job
* tasks executed one after another, but task execution against hosts happening in order
  controlled by logic of Nornir Runner in use, usually in parallel using threading.

Commands timeout
++++++++++++++++

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
++++++++++++++++++

Quiet often AAA servers (Radius, Tacacs) might get overloaded with authentication
and authorization requests coming from devices due to Nornir establishing
connections with them, that effectively results in jobs failures.

To overcome that problem Nornir Proxy Module uses
`Nornir Salt RetryRunner plugin <https://nornir-salt.readthedocs.io/en/latest/Runners/RetryRunner.html#retryrunner-plugin>`_
by default. ``RetryRunner`` developed to address aforementioned issue in addition to implementing
retry logic.

Targeting Nornir Hosts
++++++++++++++++++++++

Nornir can manage many devices and uses it's own inventory,
additional filtering ``Fx`` functions introduced in
`Nornir Salt library <https://github.com/dmulyalin/nornir-salt>`_
to narrow down tasks execution to certain hosts/devices.

Sample command to demonstrate targeting capabilities::

    salt nrp1 nr.cli "show clock" FB="R*" FG="lab" FP="192.168.1.0/24" FO='{"role": "core"}'

Jumphosts or Bastions
+++++++++++++++++++++

``RetryRunner`` included in Nornir Salt library supports ``nr.cli`` and ``nr.cfg``
with ``plugin="netmiko"`` and ``nr.nc`` with ``plugin="ncclient"`` functions to
interact with devices behind SSH Jumphosts.

Sample Jumphost definition in host's inventory data of proxy-minion pillar::

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

``RetryRunner`` on first task execution will initiate single connection to Jumphost,
and will use it to proxy connections to actual devices.

Execution Module Functions Summary
----------------------------------

Table to summarize functions available in Nornir Proxy Execution Module and their purpose.

+-----------------+---------------------------------------------------+--------------------+
| nr.function     | description                                       | supported plugins  |
+=================+===================================================+====================+
| `nr.cfg`_       | Function to modify devices configuration over     | napalm (default),  |
|                 | ssh or telnet connections                         | netmiko, scrapli   |
+-----------------+---------------------------------------------------+--------------------+
| `nr.cfg_gen`_   | Function to generate devices configuration using  |                    |
|                 | SALT templating system with Nornir inventory,     |                    |
|                 | mainly for testing purposes                       |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.cli`_       | Function for show commands output collection over | netmiko (default), |
|                 | ssh or telnet                                     | scrapli            |
+-----------------+---------------------------------------------------+--------------------+
| `nr.diff`_      | To diff content of files or network with files    |                    |
|                 | saved by ``ToFileProcessor``                      |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.do`_        | Function to execute actions with a set of steps   |                    |
|                 | calling other execution functions. Allows to      |                    |
|                 | construct simple work flows.                      |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.file`_      | Function to work with files saved by              |                    |
|                 | ``ToFileProcessor`` - read, delete, list etc.     |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.find`_      | To search for various information in files saved  |                    |
|                 | by ``ToFileProcessor``                            |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.gnmi`_      | Interact with devices using gNMI protocol         | pygnmi             |
+-----------------+---------------------------------------------------+--------------------+
| `nr.http`_      | To run HTTP requests against API endpoints        | requests           |
|                 |                                                   |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.learn`_     | This function is to save task results in files    |                    |
|                 | using ``ToFileProcessor`` and ``nr.do`` actions   |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.nc`_        | Function to work with devices using NETCONF       | ncclient (default),|
|                 |                                                   | scrapli_netconf    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.netbox`_    | Integration with Netbox DCIM                      |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.network`_   | Network related utilities                         |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.nornir`_    | Function to call Nornir Utility Functions         |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.snmp`_      | Function to manage davices over SNMP protocol     |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.task`_      | Function to run any Nornir task plugin            |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.test`_      | Function to test show commands output             | netmiko (default), |
|                 | produced by nr.cli function                       | scrapli            |
+-----------------+---------------------------------------------------+--------------------+
| `nr.tping`_     | Function to run TCP ping to devices' hostnames    |                    |
+-----------------+---------------------------------------------------+--------------------+

Common CLI Arguments
--------------------

A number of Command Line Interface arguments can be supplied to Nornir Proxy
Module Execution Module functions to influence various aspects of task execution
process.

Some of the command line options use Nornir Processor plugins. This plugins tap into
task execution flow to perform additional actions or process task results.

To invoke processor plugin need to supply execution module functions with processors
arguments providing required parameters to control processor plugin behavior.

All supported processors executed in this order::

    event_progress ->
    -> DataProcessor ->
    -> iplkp ->
    -> xml_flake ->
    -> xpath ->
    -> jmespath ->
    -> match ->
    -> run_ttp ->
    -> ntfsm ->
    -> TestsProcessor ->
    -> DiffProcessor ->
    -> ToFileProcessor

.. list-table:: Common CLI Arguments Summary
   :widths: 15 85
   :header-rows: 1

   * - Name
     - Description
   * - `add_details`_
     - Add task execution details to results
   * - `Fx`_
     - Filters to target subset of devices using FFun Nornir-Salt function
   * - `context`
     - Overrides context variables passed by `render`_ to ``file.apply_template_on_contents`` exec mod function
   * - `dcache`_
     - Saves full task execution results to Nornir in-memory (RAM) Inventory ``defaults`` data
   * - `defaults`
     - Default template context passed by `render`_ to ``file.apply_template_on_contents`` exec mod function
   * - `diff`_
     - Calls Nornir-Salt DiffProcessor to produce results difference
   * - `dp`_
     - Allows to call any function supported by Nornir-Salt DataProcessor
   * - `download`_
     - Renders arguments content using Salt cp module
   * - `dump`_
     - Saves complete task results to local file system using Nornir-Salt DumpResults function
   * - `event_failed`_
     - If True, emit events on Salt Events Bus for failed tasks
   * - `event_progress`_
     - If True, emit events on Salt Events Bus for tasks execution progress
   * - `hcache`_
     - Saves host's task execution results to host's in-memory (RAM) Inventory data
   * - `iplkp`_
     - Performs in CSV file or DNS lookup of IPv4 and IPv6 addresses to replace them in output
   * - `jmespath`_
     - uses JMESPath library to run query against structured results data
   * - `job_data`_
     - Job data, string, list or dictionary to load using `slsutil.rendered` function
   * - `match`_
     - Filters text output using Nornir-Salt DataProcessor match function
   * - `ntfsm`_
     - Parse nr.cli output using TextFSM ntc-templates
   * - `RetryRunner parameters`_
     - Task parameters to influence RetryRunner execution logic
   * - `render`_
     - Renders arguments content using Salt renderer system
   * - `run_ttp`_
     - Calls Nornir-Salt DataProcessor run_ttp function to parse results using TTP
   * - `saltenv`
     - `Salt Environment <https://docs.saltproject.io/en/latest/ref/states/top.html#environments>`_ name to use with `render`_ and `download`_ to source files, default is ``base``
   * - `table`_
     - Formats results to text table using Nornir-Salt TabulateFormatter
   * - `template_engine`
     - Template Engine name to use with `render`_ to render files, default is ``jinja``
   * - `tests`_
     - Run tests for task results using Nornir-Salt TestsProcessor
   * - `tf`_
     - Saves results to local file system using Nornir-Salt ToFileProcessor
   * - `to_dict`_
     - Transforms results to structured data using Nornir-Salt ResultSerializer
   * - `xml_flake`_
     - Uses Nornir-Salt DataProcessor ``xml_flake`` function to filter XML output
   * - `xpath`_
     - Uses Nornir-Salt DataProcessor ``xpath`` function to filter XML output
   * - `worker`_
     - Worker to use for task, supported values ``all`` or number from ``1`` to ``nornir_workers`` Proxy Minion parameter of default value 3

add_details
+++++++++++

Controls Nornir-Salt
`ResultSerializer function <https://nornir-salt.readthedocs.io/en/latest/Functions/ResultSerializer.html#resultserializer>`_
to form task results with or without task execution details.

`add_details` by default is False for most of the functions, but can be adjusted
accordingly to produce desired results structure.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http, nr.gnmi``

CLI Arguments:

* ``add_details`` - boolean, if True will add task execution details to the results

Sample usage::

    salt nrp1 nr.cli "show clock" add_details=True
    salt nrp1 nr.cli "show clock" add_details=True to_dict=False
    salt nrp1 nr.cli "show clock" add_details=True to_dict=True

Fx
++

Uses Nornir-Salt ``FFun`` function to form a subset of hosts to run this task for.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.test, nr.nc, nr.do, nr.http, nr.tping, nr.inventory``

CLI Arguments:

* ``Fx`` - any of Nornir Salt `FFun function <https://nornir-salt.readthedocs.io/en/latest/Functions/FFun.html#ffun>`_ filters

Sample usage::

    salt nrp1 nr.cli "show clock" FB="R*" FG="lab" FP="192.168.1.0/24" FO='{"role": "core"}'

dcache
+++++++

Saves full task execution results to Nornir ``defaults`` in-memory (RAM) inventory data. Saved
information non-persistent across Proxy Minion reboots.

Primary usecase is to share task results between tasks for rendering, targeting or processing.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http, nr.tping, nr.gnmi``

CLI Arguments:

* ``dcache`` - nornir inventory ``defaults`` data dictionary key name to save results under
  or if set to boolean True, uses ``dcache`` as a key name

Sample usage::

    salt nrp1 nr.cli "show clock" dcache="show_clock_output"
    salt nrp1 nr.cli "show clock" dcache=True

To view in-memory ``defaults`` inventory can use utility function::

    salt npr1 nr.nornir inventory

To clean up cached data can either restart Proxy Minion or use utility function::

    salt npr1 nr.nornir clear_dcache cache_keys='["key1", "key2"]'

diff
++++

Uses Nornir Salt `DiffProcessor <https://nornir-salt.readthedocs.io/en/latest/Processors/DiffProcessor.html#diffprocessor-plugin>`_
to produce difference between current task results and previous results saved by ``ToFileProcessor``.

Supported functions: ``nr.task, nr.cli, nr.nc, nr.do, nr.http, nr.gnmi``

CLI Arguments:

* ``diff`` - ``ToFileProcessor`` file group name to run difference with
* ``last`` - ``ToFileProcessor`` file version number, default is 1

Sample usage::

    salt nrp1 nr.cli "show ip route" diff="show_route" last=1

dp
++

Uses Nornir-Salt `DataProcessor plugin <https://nornir-salt.readthedocs.io/en/latest/Processors/DataProcessor.html#dataprocessor-plugin>`_
designed to help with processing Nornir task results.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http, nr.gnmi``

CLI Arguments:

* ``dp`` - data processor functions list to process task results

CLI argument ``dp`` can be comma-separated string or list of ``DataProcessor`` function names
or dictionary keyed by ``DataProcessor`` function name with values set to dictionary which
contains arguments for ``DataProcessor`` function.

Sample usage::

    salt nrp1 nr.nc get_config dp="xml_to_json"
    salt nrp1 nr.nc get_config dp="load_xml, flatten"
    salt nrp1 nr.nc get_config dp='["load_xml", "flatten"]'
    salt nrp1 nr.cli "show version" dp='[{"fun": "match", "pattern": "Version"}]'
    salt nrp1 nr.nc get_config source=running dp='[{"fun": "xml_flatten"}, {"fun": "key_filter", "pattern": "*bgp*, *BGP*"}]'

Last example will call ``xml_flatten`` function first following with ``key_filter`` with
``{"pattern": "*bgp*, *BGP*"}`` dictionary arguments.

download
++++++++

SaltStack has `cp module <https://docs.saltproject.io/en/latest/ref/modules/all/salt.modules.cp.html>`_,
allowing to download files from Salt Master, ``donwload`` keyword can be used to indicate
arguments that should download content for.

Supported URL schemes are: salt://, http://, https://, ftp://, s3://, swift:// and file:// (local
filesystem).

Keys listed in ``download`` argument ignored by `render`_ argument even if same key contained
with ``render`` argument. Arguments names listed in ``donwload`` are not rendered, only loaded
from Salt Master.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http``

CLI Arguments:

* ``download`` - list of arguments to download content for, default is ``["run_ttp", "iplkp"]``

For example, to render content for filename argument::

    salt nrp1 nr.cfg filename="salt://templates/logging_config.txt" download='["filename"]'

Primary use cases for this keyword is revolving around enabling or disabling downloading
and rendering for certain arguments. Execution Module Functions adjust ``download`` keyword
list content by themselves and usually do not require manual modifications.

dump
++++

Salt Event bus has limit on the amount of data it can transfer from Proxy Minion to Master,
because of that, results produced by Proxy minion might get trimmed beyond certain threshold.

This can be addressed in several ways:

* increase event bus data transmission threshold
* use returner to return results to external database or other system

In addition to above option, Nornir Proxy Minion can make use of Nornir Salt
`DumpResults <https://nornir-salt.readthedocs.io/en/latest/Functions/DumpResults.html#dumpresults>`_
function to save complete results of task execution to local file system. That data
can be later retrieved from proxy Minion machine.

Another usecase that ``DumpResults`` function can help to solve is results logging for audit,
review or historical data purposes.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.test, nr.nc, nr.do, nr.http``

CLI Arguments:

* ``dump`` - ``ToFileProcessor`` file group name where to save results

Sample usage::

    salt nrp1 nr.cli "show run" dump="show_run_output"

Results saved to proxy minion local file system under ``files_base_path``, default is::

    /var/salt-nornir/{proxy_id}/files/{filegroup}__{timestamp}__{rand}__{proxy_id}.txt

Where:

* ``proxy_id`` - Nornir Proxy Minion ID
* ``filegroup`` - ``ToFileProcessor`` file group name where to save results
* ``timestamp`` - date timestamp
* ``rand`` - random integer between 1 and 1000

event_failed
++++++++++++

Salt Event bus allows Proxy Minion processes to emit events, so that salt-master reactor
system can act upon them and trigger execution of various actions.

``event_failed`` CLI argument instructs Nornir Proxy minion to emit events for failed tasks.

Event's tag formed using this formatter::

    nornir-proxy/{proxy_id}/{host}/task/failed/{name}

Where:

* ``proxy_id`` - Nornir Proxy Minion ID
* ``host`` - hostname of device that failed this task
* ``name`` - name of the failed task

Event body contains task execution results dictionary.

Failed tasks determined using results ``failed`` or ``success`` attributes, if ``failed``
is True or ``success`` is False task considered as failed.

Combining ``event_failed`` with ``nr.test`` function allows to implement event driven
automation in response to certain tests failure. Each test translated to a separate
task result and ``event_failed`` emit events on a per-test basis enabling to construct
very granular react actions on Salt Master.

Sample event content::

    nornir-proxy/nrp1/ceos1/task/failed/nornir_salt.plugins.tasks.nr_test   {
        "_stamp": "2022-02-11T11:14:16.081755",
        "cmd": "_minion_event",
        "data": {
            "changed": false,
            "connection_retry": 3,
            "diff": "",
            "exception": "",
            "failed": true,
            "host": "ceos1",
            "name": "nornir_salt.plugins.tasks.nr_test",
            "result": "Traceback (most recent call last):\\n  File \"/usr/local/lib/python3.6/site-packages/nornir/core/task.py\", line 99, in start\\n    r = self.task(self, **self.params)\\n  File \"/usr/local/lib/python3.6/site-packages/nornir_salt/plugins/tasks/nr_test.py\", line 65, in nr_test\\n    raise RuntimeError(excpt_msg)\\nRuntimeError\\n",
            "task_retry": 3
        },
        "id": "nrp1",
        "pretag": null,
        "tag": "nornir-proxy/nrp1/ceos1/task/failed/nornir_salt.plugins.tasks.nr_test"
    }

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.test, nr.nc, nr.do, nr.http, nr.gnmi, nr.file, nr.diff, nr.find, nr.learn``

CLI Arguments:

* ``event_failed`` - boolean, default is False, if True will emit events for failed tasks.

Sample usage::

    salt nrp1 nr.test suite="salt://tests/suite.txt" event_failed=True

event_progress
++++++++++++++

Argument to use Nornir-Salt ``SaltEventProcessor`` plugin to emit task execution progress events to
SaltStack Events Bus. This is mainly useful for tracking tasks' flow, debugging and general assurance.

For example, ``event_progress`` used by ``nr.call`` Runner Module function to capture and print
messages to terminal informing user about task execution progress.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.test, nr.nc, nr.do, nr.http, nr.gnmi, nr.file, nr.diff, nr.find, nr.learn``

CLI Arguments:

* ``event_progress`` - boolean, default is False, if True will emit events for tasks progress.

Sample usage::

    salt nrp1 nr.cli "show clock" event_progress=True

To listen to events generated by Proxy Minion when ``event_progress=True`` can open additional session
to master server and run ``salt-run nr.event`` runner function.

Nornir Proxy Minion pillar parameter ``event_progress_all`` can be used to control default behavior,
``event_progress`` overrides ``event_progress_all`` parameter.

hcache
++++++

Saves individual host's task execution results in host's in-memory (RAM) inventory data. Saved
information non-persistent across Proxy Minion reboots.

Primary usecase is to share task results data between tasks for rendering, targeting or processing.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http, nr.tping, nr.gnmi``

CLI Arguments:

* ``hcache`` - host's data dictionary key name to save results under or if set to boolean True, uses
  ``hcache`` as a key name

Sample usage::

    salt nrp1 nr.cli "show clock" hcache="show_clock_output"
    salt nrp1 nr.cli "show clock" hcache=True

To view in-memory inventory can use utility function::

    salt npr1 nr.nornir inventory FB="hosname-1"

To clean up cached data can either restart Proxy Minion or use utility function::

    salt npr1 nr.nornir clear_hcache FB="hosname-1"
    salt npr1 nr.nornir clear_hcache cache_keys='["key1", "key2"]'

iplkp
+++++

Uses Nornir-Salt ``DataProcessor``
`iplkp function <https://nornir-salt.readthedocs.io/en/latest/Processors/DataProcessor.html#iplkp>`_
function to lookup IPv4 and IPv6 addresses using DNS or CSV file and replace
them in device output with lookup results.

Supported functions: ``nr.cli``

CLI Arguments:

* ``iplkp`` - value can be ``dns`` to indicate that need to use DNS or reference to
  a CSV file on Salt Master in a format ``salt://path/to/file.txt``

First column in CSV file must be IPv4 or IPv6 address, second column should
contain replacement value.

``iplkp`` uses this formatter to replace IP addresses in results: ``{ip}({lookup})`` -
where ``ip`` is the original IP address string and ``lookup`` is the lookup
result value.

Sample usage::

    salt nrp1 nr.cli "show ip int brief" iplkp="salt://lookup/ip.txt"
    salt nrp1 nr.cli "show ip int brief" iplkp="dns"

Where ``salt://lookup/ip.txt`` content is::

    ip,hostname
    10.0.1.4,ceos1:Eth1
    10.0.1.5,ceos2:Eth1

And this would be the results produced::

    nrp1:
        ----------
        ceos1:
            ----------
            show ip int brief:
                                                                                          Address
                Interface       IP Address        Status       Protocol            MTU    Owner
                --------------- ----------------- ------------ -------------- ----------- -------
                Ethernet1       10.0.1.4(ceos1:Eth1)/24       up           up                 1500
                Loopback1       1.1.1.1/24        up           up                65535

``iplkp`` replaced ``10.0.1.4`` with lookup results ``10.0.1.4(ceos1:Eth1)`` in device output.

jmespath
++++++++

Uses Nornir-Salt ``DataProcessor``
`jmespath function <https://nornir-salt.readthedocs.io/en/latest/Processors/DataProcessor.html#jmespath>`_
to run JMESPath query against structured data results or JSON string.

Supported functions: ``nr.task, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http, nr.cli, nr.gnmi``

CLI Arguments:

* ``jmespath`` - `JMESPath <https://jmespath.org/>`_ query expression string

Sample usage::

    salt nrp1 nr.task nornir_napalm.plugins.tasks.napalm_get getters='["get_interfaces"]' jmespath='interfaces'

job_data
++++++++

Any arbitrary data to load and make available within template under ``job_data`` key. Uses
`slsutil.renderer <https://docs.saltproject.io/en/latest/ref/modules/all/salt.modules.slsutil.html#salt.modules.slsutil.renderer>`_
execution module function. In addition, ``job_data`` key added to Nornir host' ``data["__task__"]``
dictionary to make loaded data available to task plugins.

Supported functions: ``nr.task, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http, nr.cli, nr.gnmi, nr.snmp``

Main purpose of ``job_data`` is to load any arbitrary data from any of supported URLs -
salt://, http://, https://, ftp://, s3://, swift:// and file:// (proxy minion
local filesystem) - rendering and serializing the content using ``slsutil.renderer`` function.
That way proxy minion pillar can contain only information required to connect
to devices and information for hosts targeting, any other parameters can be
loaded from YAML or JSON files on demand.

Job Data is analogous to SaltStack map files, but made to be more flexible.

``job_data`` argument accepts string, list or dictionary, proxy minion
downloads data from provided URLs.

Sample usage::

    salt nrp1 nr.cfg_gen "router bgp {{ job_data.bgp.asn }}" job_data="salt://data/params.yaml"
    salt nrp1 nr.cfg_gen "router bgp {{ job_data[0].bgp.asn }}" job_data='["salt://data/params.yaml", "salt://data/syslog.json"]'
    salt nrp1 nr.cfg_gen "router bgp {{ job_data['bgp'].bgp.asn }}" job_data='{"bgp": "salt://data/params.yaml", "syslog": "salt://data/syslog.json"}'
    salt nrp1 nr.cfg_gen "logging {{ job_data['syslog'].servers[0] }}" job_data='{"bgp": "salt://data/params.yaml", "syslog": "salt://data/syslog.json"}'

Where ``/etc/salt/data/params.yaml`` file content is::

    bgp:
      asn: 65555
      rid: 1.1.1.1
      peers:
        - ip: 1.2.3.4
          asn: 65000
        - ip: 4.3.2.1
          asn: 65123

And ``/etc/salt/data/syslog.json`` file content is::

    #!json
    {
        "servers": ["1.2.3.4", "4.3.2.1"],
        "facility": "local",
        "bufered_size": "64242"
    }

``job_data`` content temporarily saved into host's inventory data
for task execution and removed afterwards. Example of how to access
``job_data`` within Nornir task function::

    from nornir.core.task import Result, Task

    def task(task):
        "This task echoes back job_data content"
        task.name = "job_data_echo"

        job_data = task.host["job_data"]

        return Result(host=task.host, result=job_data)

Assuming above task saved at ``/etc/salt/tasks/job_data_echo.py``,
running this command::

    salt nrp1 nr.task plugin="salt://tasks/job_data_echo.py" job_data='{"foo": 123}' FB=ceos1

Returns this result::

    nrp1:
        ----------
        ceos1:
            ----------
            job_data_echo:
                ----------
                foo:
                    123

match
+++++

Uses Nornir-Salt ``DataProcessor``
`match function <https://nornir-salt.readthedocs.io/en/latest/Processors/DataProcessor.html#match>`_
to filter text results using regular expression pattern.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http``

CLI Arguments:

* ``match`` - regex pattern to search for
* ``before`` - integer indicating how many lines before match to include in results

Sample usage::

    salt nrp1 nr.cli "show version" match="Version.*"
    salt nrp1 nr.cli "show version" match="Version.*" before=1

ntfsm
+++++

Uses Nornir-Salt ``DataProcessor``
`ntfsm function <https://nornir-salt.readthedocs.io/en/latest/Processors/DataProcessor.html#ntfsm>`_
to parse show commands output using TextFSM ntc-templates.

Supported functions: ``nr.cli``

CLI Arguments:

* ``ntfsm`` - bool, if True uses TextFSM ntc-templates to parse output

Sample usage::

    salt nrp1 nr.cli "show version" ntfsm=True
    salt nrp1 nr.cli "show version" dp=ntfsm

RetryRunner parameters
++++++++++++++++++++++

A number of Nornir-Salt Proxy Minion execution module functions support RetryRunner
`parameters <https://nornir-salt.readthedocs.io/en/latest/Runners/RetryRunner.html#retryrunner-task-parameters>`_
to influence task execution logic.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http, nr.gnmi, nr.test``

CLI Arguments:

* ``run_connect_retry`` - number of connection attempts
* ``run_task_retry`` - number of attempts to run task
* ``run_creds_retry`` - list of connection credentials and parameters to retry while connecting to device
* ``run_num_workers`` - number of threads for tasks execution
* ``run_num_connectors`` - number of threads for device connections
* ``run_reconnect_on_fail`` - if True, re-establish connection on task failure

Sample usage - retry various connection parameters::

    salt nrp1 nr.cfg filename="salt://templates/logging_config.txt" run_creds_retry='["local_creds", "dev_creds"]'

Sample usage - disable task and connection retries::

    salt nrp1 nr.cfg filename="salt://templates/logging_config.txt" run_connect_retry=0 run_task_retry=0

Sample usage - run tasks sequentially on hosts one by one::

    salt nrp1 nr.cfg filename="salt://templates/logging_config.txt" run_num_workers=1

Sample usage - set rate of device's connections to 5 per-second::

    salt nrp1 nr.cfg filename="salt://templates/logging_config.txt" run_num_connectors=5

render
++++++

SaltStack has `renderers system <https://docs.saltproject.io/en/latest/ref/renderers/index.html#renderers>`_,
that system allows to render text files content while having access to all Salt Execution Module
Functions and inventory data.

If render argument value points to one of supported URL schemes are: salt://, http://, https://, ftp://,
s3://, swift:// and file:// (local filesystem). File content downloaded from specified URL prior to
rendering.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http, nr.gnmi``

CLI Arguments:

* ``render`` - list of argument to render content for, default is ``["config", "data", "filter", "filter_", "filters", "filename"]``

For example, to render content for filename argument::

    salt nrp1 nr.cfg filename="salt://templates/logging_config.txt" render='["filename"]'

Primary use cases for this keyword is revolving around enabling or disabling rendering for
certain arguments. Execution Module Functions adjust ``render`` keyword list content by
themselves and usually do not require any modifications.

run_ttp
+++++++

Uses Nornir-Salt ``DataProcessor``
`run_ttp function <https://nornir-salt.readthedocs.io/en/latest/Processors/DataProcessor.html#run-ttp>`_
to parse text results using TTP library and produce structured data.

Supported functions: ``nr.task, nr.cli, nr.do``

CLI Arguments:

* ``run_ttp`` - TTP template reference
* ``ttp_structure`` - TTP results structure, supported values: ``flat_list`` (default), ``list`` or ``dictionary``

Sample usage::

    salt nrp1 nr.cli "show version" run_ttp="Version: {{ version }}"
    salt nrp1 nr.cli "show version" run_ttp="salt://ttp/parse_version.txt"
    salt nrp1 nr.cli "show ip arp" run_ttp="ttp://platform/cisco_ios_show_ip_arp.txt"
    salt nrp1 nr.cli run_ttp="salt://ttp/parse_commands.txt" ttp_structure=list

TTP templates can be specified inline, sourced from salt-master using ``salt://path`` or from
TTP Templates collection repository using ``ttp://path`` providing that it is installed on
proxy minion machine.

``run_ttp`` with ``nr.cli`` function also supports sourcing commands to collect from devices
from within TTP template input tags using ``commands`` argument. For example::

    <input name="version">
    commands = ["show version"]
    </input>

    <input name="interfaces">
    commands = ["show run"]
    </input>

    <group name="facts" input="version">
    cEOS tools version: {{ tools_version }}
    Kernel version: {{ kernel_version }}
    Total memory: {{ total_memory}} kB
    Free memory: {{ total_memory}} kB
    </group>

    <group name="interfaces" input="interfaces">
    interface {{ interface }}
       description {{ description | re(".*") }}
       ip address {{ ip }}/{{ mask }}
    </group>

Supplying above template to ``nr.cli`` function with ``run_ttp`` argument will result
in running ``show version`` and ``show run`` commands, placing output in appropriate
inputs and parsing it with dedicated groups, returning parsing results.

table
+++++

Uses Nornir Salt
`TabulateFormatter function <https://nornir-salt.readthedocs.io/en/latest/Functions/TabulateFormatter.html#tabulateformatter>`_
to transform task results in a text table representation.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.test, nr.nc, nr.do``

CLI Arguments:

* ``table`` - boolean or table type indicator, supported values: True, ``brief``, ``extend``, ``terse``
* ``headers`` - list of table headers to form table for
* ``headers_exclude`` - list of table headers to exclude from final table results
* ``sortby`` - name of the header to sort table by, default is ``host``
* ``reverse`` - if True, sorts table in reverse order, False by default

Sample usage::

    salt nrp1 nr.cli "show clock" table=brief
    salt nrp1 nr.cli "show clock" table=True
    salt nrp1 nr.cli "show clock" table=True headers="host, results"
    salt nrp1 nr.cli "show clock" table=True headers="host, results" sortby="host" reverse=True

tests
+++++

Uses Nornir Salt
`TestsProcessor plugin <https://nornir-salt.readthedocs.io/en/latest/Processors/TestsProcessor.html#testsprocessor-plugin>`_
to test task results.

Tests can be specified inline as a list of lists or can reference tests suite
file on salt-master using ``salt://path`` format.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http``

CLI Arguments:

* ``tests`` - reference to a list of tests to run
* ``failed_only`` - boolean, default is False, to indicate if to return results for failed tests only
* ``remove_tasks`` - boolean, default is True, to indicate if need to remove tested task results

Sample usage::

    salt nrp1 nr.cli "show version" "show clock" tests='[["show version", "contains", "5.2.9b"], ["show clock", "contains", "Source: NTP"]]'
    salt nrp1 nr.cli "show version" "show clock" tests="salt://tests/suite.txt"

tf
++

Uses Nornir Salt
`ToFileProcessor plugin <https://nornir-salt.readthedocs.io/en/latest/Processors/ToFileProcessor.html#tofileprocessor-plugin>`_
to save task execution results to proxy minion local file system under ``files_base_path``, default is
``/var/salt-nornir/{proxy_id}/files/``

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http, nr.gnmi``

CLI Arguments:

* ``tf`` - ``ToFileProcessor`` file group name where to save results
* ``tf_skip_failed`` - boolean, default is False, if True, will not save results for failed tasks

Sample usage::

    salt nrp1 nr.cfg "logging host 1.1.1.1" tf="logging_config"
    salt nrp1 nr.cfg "logging host 1.1.1.1" tf="logging_config" tf_skip_failed=True

``tf_skip_failed`` can be useful when only want to save results to file for non failed tasks.
For example, if ``RetryRunner`` runs task and it fails on first attempt but succeed on second,
it might not make sense to store failed task results, which is the case by default, ``tf_skip_failed``
help to alter that behavior.

to_dict
+++++++

Uses Nornir Salt
`ResultSerializer function <https://nornir-salt.readthedocs.io/en/latest/Functions/ResultSerializer.html#resultserializer>`_
to transform task results in a structured data - dictionary or list.

This function used by default for all task results unless ``TabulateFormatter`` ``table``
argument provided.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http, nr.gnmi``

CLI Arguments:

* ``add_details`` - boolean, default is False, if True will add task execution details to the results
* ``to_dict`` - boolean, default is True, if False will produce results list structure

Sample usage::

    salt nrp1 nr.cli "show clock" add_details=True
    salt nrp1 nr.cli "show clock" add_details=True to_dict=False

xml_flake
+++++++++

Uses Nornir-Salt ``DataProcessor``
`xml_flake function <https://nornir-salt.readthedocs.io/en/latest/Processors/DataProcessor.html#xml-flake>`_
to flatten XML results structure to dictionary and filter dictionary keys using glob pattern.

Supported functions: ``nr.task, nr.nc, nr.do, nr.http``

CLI Arguments:

* ``xml_flake`` - glob pattern to filter keys

Sample usage::

    salt nrp1 nr.nc get_config xml_flake="*bgp:config*"

xpath
+++++

Uses Nornir-Salt ``DataProcessor``
`xpath function <https://nornir-salt.readthedocs.io/en/latest/Processors/DataProcessor.html#xpath>`_
to run xpath query against XML results.

Supported functions: ``nr.task, nr.nc, nr.do, nr.http``

CLI Arguments:

* ``xpath`` - `LXML library <https://lxml.de/xpathxslt.html#xpath>`_ supported xpath expression

Sample usage::

    salt nrp1 nr.nc get_config xpath='//config/address[text()="1.1.1.11"]'

Beware that XML namespaces removed from XML results before running xpath
on them. If this behavior is not desirable, need to use ``dp`` keyword instead
with required arguments for ``xpath`` function including namespaces map dictionary.

``xpath`` function processes results received from device and executed locally on the minion
machine, if you need to filter results returned from device, for ``nr.nc`` function consider
using filter arguments. The complication is that if, for example, you running
``get_config`` NETCONF operation, full device config retrieved from device and passed via ``xpath``
function on proxy minion, this could be processing intensive especially for big configurations
combined with significant number of devices simultaneously returning results.

worker
++++++

Starting with Nornir 0.9.0 support added for several Nornir Instances with dedicated worker threads,
allowing to greatly increase Proxy Minion task execution throughput. If no ``worker`` argument provided
task can be executed by any of the workers.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.test, nr.nc, nr.do, nr.http, nr.gnmi, nr.file, nr.diff, nr.find, nr.learn, nr.nornir``

CLI Arguments:

* ``worker`` - Worker to use for task, supported values ``all`` or number from ``1`` to ``nornir_workers`` Proxy Minion parameter of default value 3

Sample usage::

    salt nrp1 nr.cli "show clock" worker=3
    salt nrp1 nr.nornir connections worker=2
    salt nrp1 nr.nornir disconnect worker=all

Execution Module Functions
--------------------------

nr.cfg
++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.cfg

nr.cfg_gen
++++++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.cfg_gen

nr.cli
++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.cli

nr.diff
+++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.diff

nr.do
++++++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.do

nr.file
+++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.file

nr.find
+++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.find

nr.gnmi
+++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.gnmi

nr.http
+++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.http

nr.learn
++++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.learn

nr.nc
+++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.nc

nr.netbox
+++++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.netbox

nr.network
++++++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.network

nr.nornir
+++++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.nornir_fun

nr.service
++++++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.service

nr.snmp
+++++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.snmp

nr.task
+++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.task

nr.test
+++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.test

nr.tping
++++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.tping
"""

# Import python libs
import logging
import traceback
import fnmatch
import uuid
import time
import json
import hashlib

from salt_nornir.utils import _is_url
from salt_nornir.pydantic_models import (
    model_exec_nr_cli,
    model_exec_nr_task,
    model_exec_nr_cfg,
    model_exec_nr_tping,
    model_exec_nr_test,
    model_exec_nr_nc,
    model_exec_nr_http,
    model_exec_nr_do,
    model_exec_nr_file,
    model_exec_nr_learn,
    model_exec_nr_find,
    model_exec_nr_diff,
    model_exec_nr_nornir_fun,
    model_exec_nr_gnmi,
    model_exec_nr_do_action,
    model_exec_nr_snmp,
    model_exec_nr_netbox,
    model_exec_nr_network,
)
from salt_nornir.netbox_utils import netbox_tasks

log = logging.getLogger(__name__)


# import salt libs, wrapping it in try/except for docs to generate
try:
    from salt.exceptions import CommandExecutionError, SaltRenderError
    from salt.utils.yamldumper import safe_dump as yaml_safe_dump
except:
    log.error("Nornir Execution Module - failed importing SALT libraries")

# import nornir libs
try:
    from nornir_salt.plugins.functions import (
        TabulateFormatter,
        DumpResults,
        FFun_functions,
    )
    from nornir_salt.utils.yangdantic import ValidateFuncArgs
    from nornir_salt.utils.pydantic_models import modelTestsProcessorSuite

    HAS_NORNIR = True
except ImportError:
    log.error("Nornir Execution Module - failed importing libraries")
    HAS_NORNIR = False

__virtualname__ = "nr"
__proxyenabled__ = ["nornir"]
__func_alias__ = {"nornir_fun": "nornir"}


def __virtual__():
    if HAS_NORNIR:
        return __virtualname__
    return False


# -----------------------------------------------------------------------------
# private module function
# -----------------------------------------------------------------------------


def _form_identity(kwargs, function_name):
    """
    Helper function to form task identity argument, identity used by Nornir
    proxy minion to identify results for tasks submitter to jobs queue.

    :param kwargs: (dict) arguments received by Execution Module Function
    :param function_name: (str) Execution Module Function name
    :return: dictionary with uuid4, jid, function_name keys

    If identity already present in kwargs, use it as is.
    """
    identity = kwargs.pop("identity", {})

    # make sure we always have mandatory attributes
    identity.setdefault("jid", kwargs.get("__pub_jid"))
    identity.setdefault("uuid4", str(uuid.uuid4()))
    identity.setdefault("user", kwargs.get("__pub_user"))
    identity.setdefault("function", "exec.nr.{}".format(function_name))

    return identity


# -----------------------------------------------------------------------------
# callable module function
# -----------------------------------------------------------------------------


@ValidateFuncArgs(model_exec_nr_task)
def task(plugin, **kwargs):
    """
    Function to invoke any of supported Nornir task plugins. This function
    performs dynamic import of requested plugin function and executes
    ``nr.run`` using supplied args and kwargs

    :param plugin: (str) ``path.to.plugin.task_fun`` to run ``from path.to.plugin import task_fun``
    :param kwargs: (dict) arguments to use with specified task plugin or common arguments

    ``plugin`` attribute can refer to a file on one of remote locations, supported URL schemes
    are: salt://, http://, https://, ftp://, s3://, swift:// and file:// (local filesystem).
    File downloaded, compiled and executed.

    File must contain function named ``task`` accepting Nornir task object as a first positional
    argument, for example::

        # define connection name for RetryRunner to properly detect it
        CONNECTION_NAME = "netmiko"

        # create task function
        def task(nornir_task_object, *args, **kwargs):
            pass

    .. note:: ``CONNECTION_NAME`` must be defined within custom task function file if
        RetryRunner in use, otherwise connection retry logic skipped and connections
        to all hosts initiated simultaneously up to the number of num_workers.

    Sample usage::

        salt nrp1 nr.task "nornir_napalm.plugins.tasks.napalm_cli" commands='["show ip arp"]' FB="IOL1"
        salt nrp1 nr.task "nornir_netmiko.tasks.netmiko_save_config" add_details=False
        salt nrp1 nr.task "nornir_netmiko.tasks.netmiko_send_command" command_string="show clock"
        salt nrp1 nr.task "salt://path/to/task.txt"
        salt nrp1 nr.task plugin="salt://path/to/task.py"

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.task",
            arg=["nornir_napalm.plugins.tasks.napalm_cli"],
            kwarg={"commands": ["show ip arp"]},
        )
    """
    return __proxy__["nornir.execute_job"](
        task_fun=plugin, kwargs=kwargs, identity=_form_identity(kwargs, "task")
    )


@ValidateFuncArgs(model_exec_nr_cli)
def cli(*args, **kwargs):
    """
    Method to retrieve commands output from devices using ``send_command``
    task plugin from either Netmiko or Scrapli library.

    :param args: (list or str) list of cli commands as arguments
    :param commands: (list or str) list of cli commands or single command as key-word argument
    :param filename: (str) path to file with multiline commands string
    :param plugin: (str) name of send command task plugin to use - ``netmiko`` (default), ``scrapli``,
        ``napalm`` or ``pyats``
    :param render: (list) list of arguments to pass through SaltStack rendering system, by default
        renders content of ``["filename", "commands"]`` arguments.
    :param use_ps: (bool) if True, uses Netmiko with promptless mode to send commands
    :param kwargs: (dict) any additional arguments to use with specified ``plugin`` send command method

    Sample Usage::

         salt nrp1 nr.cli "show clock" "show run" FB="IOL[12]" use_timing=True delay_factor=4
         salt nrp1 nr.cli commands='["show clock", "show run"]' FB="IOL[12]"
         salt nrp1 nr.cli "show clock" FO='{"platform__any": ["ios", "nxos_ssh", "cisco_xr"]}'
         salt nrp1 nr.cli commands='["show clock", "show run"]' FB="IOL[12]" plugin=napalm
         salt nrp1 nr.cli "show clock" use_ps=True cutoff=60 initial_sleep=10

    Plugins details:

    * ``netmiko`` - uses `netmiko_send_commands <https://nornir-salt.readthedocs.io/en/latest/Tasks/netmiko_send_commands.html>`_
      Nornir-Salt Task plugin, ``nr.cli`` uses this plugin by default
    * ``scrapli`` - uses `scrapli_send_commands <https://nornir-salt.readthedocs.io/en/latest/Tasks/scrapli_send_commands.html>`_
      Nornir-Salt Task plugin
    * ``napalm`` - uses `napalm_send_commands <https://nornir-salt.readthedocs.io/en/latest/Tasks/napalm_send_commands.html>`_
      Nornir-Salt Task plugin
    * ``pyats`` - uses `pyats_send_commands <https://nornir-salt.readthedocs.io/en/latest/Tasks/pyats_send_commands.html>`_
      Nornir-Salt Task plugin
    * ``use_ps`` - enables promptless mode of interaction with device's CLI, uses
      `netmiko_send_commands_ps <https://nornir-salt.readthedocs.io/en/latest/Tasks/netmiko_send_command_ps.html>`_
      Nornir-Salt task plugin

    Commands can be templates and rendered using Jinja2 Templating Engine::

         salt nrp1 nr.cli "ping 1.1.1.1 source {{ host.lo0 }}"

    Commands to run on devices can be sourced from text file on a Salt Master or any other location
    with supported URL schemes: salt://, http://, https://, ftp://, s3://, swift:// and file:// (local
    filesystem), that text file can also be a template, it is rendered using SaltStack rendering system::

         salt nrp1 nr.cli filename="salt://device_show_commands.txt"

    Combining above two features we can supply per-host commands like this::

         salt nrp1 nr.cli filename="salt://{{ host.name }}_show_commands.txt"

    Where ``{{ host.name }}_show_commands.txt`` file can be a template as well.

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.cli",
            arg=["show clock"],
            kwarg={"plugin": "netmiko"},
        )
    """
    # get arguments
    default_kwargs = __proxy__["nornir.nr_data"]("nr_cli")
    kwargs = {**default_kwargs, **kwargs}
    plugin = kwargs.pop("plugin", "netmiko")
    kwargs.setdefault("render", ["filename", "commands"])
    # decide on commands to send
    commands = kwargs.pop("commands", args)
    commands = [commands] if isinstance(commands, str) else commands
    if any(commands):
        kwargs["commands"] = commands
    # decide on plugin to use
    if plugin.lower() == "netmiko":
        task_fun = "nornir_salt.plugins.tasks.netmiko_send_commands"
        kwargs["connection_name"] = "netmiko"
    elif plugin.lower() == "scrapli":
        task_fun = "nornir_salt.plugins.tasks.scrapli_send_commands"
        kwargs["connection_name"] = "scrapli"
    elif plugin.lower() == "napalm":
        task_fun = "nornir_salt.plugins.tasks.napalm_send_commands"
        kwargs["connection_name"] = "napalm"
    elif plugin.lower() == "pyats":
        task_fun = "nornir_salt.plugins.tasks.pyats_send_commands"
        kwargs["connection_name"] = "pyats"
    # run commands task
    result = __proxy__["nornir.execute_job"](
        task_fun=task_fun, kwargs=kwargs, identity=_form_identity(kwargs, "cli")
    )
    return result


@ValidateFuncArgs(model_exec_nr_cfg)
def cfg(*args, **kwargs):
    """
    Function to push configuration to devices using NAPALM, Netmiko, Scrapli or
    or PyATS task plugin.

    :param commands: (str, list) list of commands or multiline string to send to device
    :param filename: (str) path to file with configuration or template
    :param config: (str, dict) configuration string or reference to configuration template or
        dictionary keyed by host name with value set to configuration string or template
    :param template_engine: (str) template engine to render configuration, default is jinja2
    :param saltenv: (str) name of SALT environment
    :param context: Overrides default context variables passed to the template.
    :param defaults: Default context passed to the template.
    :param plugin: (str) name of configuration task plugin to use - ``napalm`` (default) or ``netmiko``
        or ``scrapli`` or ``pyats``
    :param dry_run: (bool) default False, controls whether to apply changes to device or simulate them
    :param commit: (bool or dict) by default commit is ``True``. With ``netmiko`` plugin
        if ``commit`` argument is a dictionary it is supplied to commit call as arguments

    .. warning:: ``dry_run`` not supported by ``netmiko`` and ``pyats`` plugins

    .. warning:: ``commit`` not supported by ``scrapli`` and ``pyats`` plugins. To commit need to send commit
        command as part of configuration, moreover, scrapli will not exit configuration mode,
        need to send exit command as part of configuration commands as well.

    Plugins details:

    * ``napalm`` - uses `napalm_configure <https://nornir-salt.readthedocs.io/en/latest/Tasks/napalm_configure.html>`_
      Nornir-Salt Task plugin, ``nr.cfg`` uses this plugin by default
    * ``netmiko`` - uses `netmiko_send_config <https://nornir-salt.readthedocs.io/en/latest/Tasks/netmiko_send_config.html>`_
      Nornir-Salt Task plugin
    * ``scrapli`` - uses `scrapli_send_config <https://nornir-salt.readthedocs.io/en/latest/Tasks/scrapli_send_config.html>`_
      Nornir-Salt Task plugin
    * ``pyats`` - uses `pyats_send_config <https://nornir-salt.readthedocs.io/en/latest/Tasks/pyats_send_config.html>`_
      Nornir-Salt Task plugin

    For configuration rendering purposes, in addition to normal `context variables
    <https://docs.saltstack.com/en/latest/ref/states/vars.html>`_
    template engine loaded with additional context variable `host`, to access Nornir host
    inventory data.

    Sample usage::

        salt nrp1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" FB="R[12]" dry_run=True
        salt nrp1 nr.cfg commands='["logging host 1.1.1.1", "ntp server 1.1.1.2"]' FB="R[12]"
        salt nrp1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" plugin="netmiko"
        salt nrp1 nr.cfg filename=salt://template/template_cfg.j2 FB="R[12]"
        salt nrp1 nr.cfg filename=salt://template/cfg.j2 FB="XR-1" commit='{"confirm": True, "confirm_delay": 60}'
        salt nrp1 nr.cfg config="snmp-server location {{ host.location }}"
        salt nrp1 nr.cfg config='{"ceos1": "snmp-server location {{ host.location }}", "ceos2": "ntp server 1.2.3.4"}'
        salt nrp1 nr.cfg "snmp-server location {{ host.location }}"

    Filename argument can be a template string, for instance::

        salt nrp1 nr.cfg filename=salt://templates/{{ host.name }}_cfg.txt

    In that case filename rendered to form path string, after that, path string used to download file
    from master, downloaded file further rendered using specified template engine (Jinja2 by default).
    That behavior supported for URL schemes: salt://, http://, https://, ftp://, s3://, swift:// and
    file:// (local filesystem). This feature allows to specify per-host configuration files for applying
    to devices.

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.cfg",
            arg=["logging host 1.1.1.1", "ntp server 1.1.1.2"],
            kwarg={"plugin": "netmiko"},
        )
    """
    # get arguments
    default_kwargs = __proxy__["nornir.nr_data"]("nr_cfg")
    kwargs = {**default_kwargs, **kwargs}
    plugin = kwargs.pop("plugin", "napalm")
    kwargs.setdefault("add_details", True)
    kwargs.setdefault("render", ["commands", "filename", "config"])
    # get configuration commands
    commands = kwargs.pop("commands", args)
    commands = [commands] if isinstance(commands, str) else commands
    if any(commands):
        kwargs["commands"] = commands
    # decide on task plugin to run
    if plugin.lower() == "napalm":
        task_fun = "nornir_salt.plugins.tasks.napalm_configure"
        kwargs["connection_name"] = "napalm"
    elif plugin.lower() == "netmiko":
        task_fun = "nornir_salt.plugins.tasks.netmiko_send_config"
        kwargs["connection_name"] = "netmiko"
    elif plugin.lower() == "scrapli":
        task_fun = "nornir_salt.plugins.tasks.scrapli_send_config"
        kwargs["connection_name"] = "scrapli"
    elif plugin.lower() == "pyats":
        task_fun = "nornir_salt.plugins.tasks.pyats_send_config"
        kwargs["connection_name"] = "pyats"
    # work and return results
    return __proxy__["nornir.execute_job"](
        task_fun=task_fun, kwargs=kwargs, identity=_form_identity(kwargs, "cfg")
    )


@ValidateFuncArgs(model_exec_nr_cfg)
def cfg_gen(*args, **kwargs):
    """
    Function to render configuration from template file. No configuration pushed
    to devices.

    This function can be useful to stage/test templates or to generate configuration
    without pushing it to devices.

    :param commands: (str, list) list of commands or multiline string to send to device
    :param filename: (str) path to template
    :param config: (str, dict) configuration string or reference to configuration template or
        dictionary keyed by host name with value set to configuration string or template
    :param template_engine: (str) template engine to render configuration, default is jinja2
    :param saltenv: (str) name of SALT environment
    :param context: Overrides default context variables passed to the template.
    :param defaults: Default context passed to the template.

    For configuration rendering purposes, in addition to normal `context variables
    <https://docs.saltstack.com/en/latest/ref/states/vars.html>`_
    template engine loaded with additional context variable `host`, to access Nornir host
    inventory data.

    Sample usage::

        salt nrp1 nr.cfg_gen filename=salt://templates/template.j2 FB="R[12]"
        salt nrp1 nr.cfg_gen config="snmp-server location {{ host.location }}"
        salt nrp1 nr.cfg_gen "snmp-server location {{ host.location }}"
        salt nrp1 nr.cfg_gen config='{"ceos1": "snmp-server location {{ host.location }}", "ceos2": "ntp server 1.2.3.4"}'

    Sample template.j2 content::

        proxy data: {{ pillar.proxy }}
        jumphost_data: {{ host["jumphost"] }}
        hostname: {{ host.name }}
        platform: {{ host.platform }}

    Filename argument can be a template string, for instance::

        salt nrp1 nr.cfg_gen filename="salt://template/{{ host.name }}_cfg.txt"

    In that case filename rendered to form path string, after that, path string used to download file
    from master, downloaded file further rendered using specified template engine (Jinja2 by default).
    That behavior supported for URL schemes: salt://, http://, https://, ftp://, s3://, swift:// and
    file:// (local filesystem). This feature allows to specify per-host configuration files for applying
    to devices.

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.cfg_gen",
            kwarg={"filename": "salt://template/{{ host.name }}_cfg.txt"},
        )
    """
    # get arguments
    default_kwargs = __proxy__["nornir.nr_data"]("nr_cfg")
    kwargs = {**default_kwargs, **kwargs}
    kwargs.setdefault("render", ["commands", "filename", "config"])
    # get configuration commands
    commands = kwargs.pop("commands", args)
    commands = [commands] if isinstance(commands, str) else commands
    if any(commands):
        kwargs["commands"] = commands
    # work and return results
    return __proxy__["nornir.execute_job"](
        task_fun="nornir_salt.plugins.tasks.salt_cfg_gen",
        kwargs=kwargs,
        identity=_form_identity(kwargs, "cfg_gen"),
    )


@ValidateFuncArgs(model_exec_nr_tping)
def tping(ports=None, timeout=1, host=None, **kwargs):
    """
    Tests connection to TCP port(s) by trying to establish a three way
    handshake. Useful for network discovery or testing.

    :param ports (list of int): tcp ports to ping, defaults to host's port or 22
    :param timeout (int): defaults to 1
    :param host (str): defaults to ``hostname``

    Sample usage::

        salt nrp1 nr.tping
        salt nrp1 nr.tping FB="LAB-RT[123]"

    Returns result object with the following attributes set:

    * result (``dict``): Contains port numbers as keys with True/False as values

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.tping",
            kwarg={"FB": "LAB-RT[123]"},
        )
    """
    kwargs["ports"] = ports or []
    kwargs["timeout"] = timeout
    kwargs["host"] = host
    # work and return results
    return __proxy__["nornir.execute_job"](
        task_fun="nornir_salt.plugins.tasks.tcp_ping",
        kwargs=kwargs,
        identity=_form_identity(kwargs, "tping"),
    )


@ValidateFuncArgs(model_exec_nr_test)
def test(*args, **kwargs):
    """
    Function to perform tests for certain criteria against show commands output
    from devices obtained using ``nr.cli`` function by default.

    ``nr.test`` function related arguments

    :param name: (str) descriptive name of the test, will be added to results
    :param test: (str) type of test to do e.g.: contains, !contains, equal, custom etc.
    :param pattern: (str) pattern to use for testing, usually string, text or
        reference a text file on salt master. For instance if ``test`` is ``contains``,
        ``pattern`` value used as a pattern for containment check
    :param function_file: (str) path to text file on salt master with function content
        to use for ``custom`` function test
    :param dry_run: (bool) if True, returns produced per-host tests suites content only,
        no tests performed, ``subset`` not supported with dry run
    :param saltenv: (str) name of salt environment to download function_file from
    :param suite: (list or str) list of dictionaries with test items or path to file on
        salt-master with a list of test item dictionaries
    :param subset: (list or str) list or string with comma separated glob patterns to
        match tests' names to execute. Patterns are not case-sensitive. Uses
        ``fnmatch.fnmatch`` Python built-in function to do matching
    :param dump: (str) filegroup name to dump results using Nornir-salt ``DumpResults``
    :param tests: string or list of strings with key path referring to host's tests list
    :param strict: boolean used with ``tests`` argument, if ``strict`` is True raises
        error when ``tests`` path item not found in any of the hosts' invenotry data,
        default is False
    :param worker: (int) Nornir worker ID to render and execute tests, ``all`` not
        supported, only interger to indicate particular worker, default is None - can
        run on any worker
    :param job_data: (dict, list) job_data argument used for tests rendering

    ``nr.cli`` function related arguments

    ``nr.test`` calls ``nr.cli`` function with ``tests`` argument containing provided
    tests suite content, it is possible to pass any ``nr.cli`` arguments while calling
    ``nr.test`` execution module function. Notable arguments are:

    :param commands: (str or list) single command or list of commands to get from device
    :param plugin: (str) plugin name to use with ``nr.cli`` function to gather output
        from devices - ``netmiko`` (default) or ``scrapli``
    :param use_ps: (bool) default is False, if True uses netmiko plugin experimental
        ``PromptlesS`` method to collect output from devices
    :param kwargs: (dict) any additional arguments to use with ``nr.cli`` function
        to run tests

    Nornir-Salt ``TestsProcessor`` plugin related arguments

    :param failed_only: (bool) default is False, if True ``nr.test`` returns result for
        failed tests only
    :param remove_tasks: (bool) default is True, if False results will include other
        tasks output as well e.g. show commands output. By default results only contain
        tests results.

    Nornir-Salt ``TabulateFormatter`` function related arguments

    :param table: (bool, str or dict) dictionary of arguments or table type indicator e.g. "brief" or True
    :param headers: (list) list of headers to output table for
    :param sortby: (str) Name of column name to sort table by
    :param reverse: (bool) reverse table on True, default is False

    Sample usage with inline arguments::

        salt nrp1 nr.test "show run | inc ntp" contains "1.1.1.1" FB="*host-1"
        salt nrp1 nr.test "show run | inc ntp" contains "1.1.1.1" --output=table
        salt nrp1 nr.test "show run | inc ntp" contains "1.1.1.1" table=brief
        salt nrp1 nr.test commands='["show run | inc ntp"]' test=contains pattern="1.1.1.1" enable=True

    Sample usage with a test cases suite::

        salt np1 nr.test suite=salt://tests/suite_1.txt
        salt np1 nr.test suite=salt://tests/suite_1.txt table=brief
        salt np1 nr.test suite=salt://tests/suite_1.txt table=brief subset="config_test*,rib_check*"
        salt np1 nr.test suite="{{ host.tests.interfaces }}"
        salt np1 nr.test suite='[{"task": "show clock", "test": "contains", "pattern": "NTP", "name": "Test NTP"}]'

    Where ``salt://tests/suite_1.txt`` content is::

        - task: "show run | inc ntp"
          test: contains
          pattern: 1.1.1.1
          name: check NTP cfg
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

    Sample usage with tests argument::

        salt np1 nr.test tests="tests.interfaces"
        salt np1 nr.test tests=["tests.interfaces", "tests.bgp_peers"]

    Where host's inventory data is::

        hosts:
          nrp1:
            data:
              tests:
                interfaces:
                  - name: Test Uplink
                    task: "show interface Ethernet1"
                    test: contains
                    pattern: "line protocol up"
                    err_msg: "Primary uplink is down"
                bgp:
                  - name: Test BGP peers state
                    task: "show bgp ipv4 un sum"
                    test: ncontains
                    pattern: Idle
                    err_msg: Some BGP peers are not UP

    .. warning:: ``tests`` paths should always refer to a list of tests dictionaries

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.test",
            kwarg={"suite": "salt://tests/suite_1.txt"},
        )

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

    Reference `Nornir Salt TestsProcessor <https://nornir-salt.readthedocs.io/en/latest/Processors/TestsProcessor.html#testsprocessor-plugin>`_
    documentation for more details on using tests suite.

    Commands in a test suite colected only once even if multiple tests
    refer to same command.

    In test suite, ``task`` argument can reference a list of tasks/commands.

    Below is a list of arguments in a test suite that can refer to a text file to source
    from one of supported URL schemes: ``salt://``, ``http://``, ``https://``, ``ftp://``,
    ``s3://``, ``swift://`` and ``file://`` (local filesystem), for example ``salt://path/to/file.txt``
    
    * ``pattern`` - content of the file rendered and used to run the tests together with 
      ``ContainsTest``, ``ContainsLinesTest`` or ``EqualTest`` test functions
    * ``schema`` - used with ``CerberusTest`` test function
    * ``function_file`` - content of the file used with ``CustomFunctionTest`` as ``function_text`` argument

    **Rendering Tests Suite using Jinja2 Templates**

    Starting with Salt-Nornir version 0.16.0 support added to dynamically
    render hosts' tests suites from hosts' data using Jinja2 templates of
    YAML formatted strings.

    .. note:: tests rendering done by Nornir-Salt using Jinja2 directly
        and loaded using PyYAML module, SaltStack rendering and templating
        system not used.

    Sample test suite Jinja2 template::

        - task: "show version"
          test: contains
          pattern: "{{ host.software_version }}"
          name: check ceos version

        {% for interface in host.interfaces_test %}
        - task: "show interface {{ interface.name }}"
          test: contains_lines
          pattern:
            - {{ interface.admin_status }}
            - {{ interface.line_status }}
            - {{ interface.mtu }}
            - {{ interface.description }}
          name: check interface {{ interface.name }} status
        {% endfor %}

    Given hosts' Nornir inventory data content::

        hosts:
          ceos1:
            data:
              interfaces_test:
              - admin_status: is up
                description: Description
                line_status: line protocol is up
                mtu: IP MTU 9200
                name: Ethernet1
              - admin_status: is up
                description: Description
                line_status: line protocol is up
                mtu: IP MTU 65535
                name: Loopback1
              software_version: cEOS
          ceos2:
            data:
              software_version: cEOS

    Test suite template rendered using individual host's data
    forming per-host test suite. CLI show commands to collect
    from host device automatically extracted from per-host
    test suite. For example, for above data these are commands
    collected from devices:

    - **ceos1** - "show version", "show interface Ethernet1", "show interface Ethernet2"
    - **ceos2** - "show version"

    Collected show commands output tested using rendered test
    suite on a per-host basis, producing these sample results::

        [root@salt-master /]# salt nrp1 nr.test suite="salt://tests/test_suite_template.j2" table=brief
        nrp1:
            +----+--------+----------------------------------+----------+-------------+
            |    | host   | name                             | result   | exception   |
            +====+========+==================================+==========+=============+
            |  0 | ceos2  | check ceos version               | PASS     |             |
            +----+--------+----------------------------------+----------+-------------+
            |  1 | ceos1  | check ceos version               | PASS     |             |
            +----+--------+----------------------------------+----------+-------------+
            |  2 | ceos1  | check interface Ethernet1 status | PASS     |             |
            +----+--------+----------------------------------+----------+-------------+
            |  3 | ceos1  | check interface Loopback1 status | PASS     |             |
            +----+--------+----------------------------------+----------+-------------+

    Starting with Salt-Nornir 0.20.0 support added to run test suites not only using
    ``nr.cli`` function but also with these Salt-Nornir execution module functions:
    ``nr.tping``, ``nr.task``, ``nr.http``, ``nr.nc``, ``nr.gnmi``, ``nr.network``,
    ``nr.file``, ``nr.snmp``. Other functions are prohibited and suite execution will
    fail with validation error.

    Sample suite that uses ``salt`` argument to customize execution module function
    to collect output from devices::

        - name: Check version using NAPALM get_facts
          test: custom
          function: salt://test/test_software_version.py
          salt:
            function: nr.task
            plugin: nornir_napalm.plugins.tasks.napalm_get
            getters: ["get_facts"]
        - name: Check NTP configuration
          test: contains_lines
          pattern: ["1.1.1.1", "2.2.2.2"]
          task: "show run | inc ntp"
          salt:
            function: nr.cli
            plugin: scrapli
            use_timing: True
            read_timeout: 300
         - name: Check ceos tping
           test: eval
           task: nornir_salt.plugins.tasks.tcp_ping
           expr: assert result[22] is True
           err_msg: SSH Port 22 not reachable
           salt:
             function: nr.tping

    As an optimisation technique, all tests that use ``nr.cli`` with same set of arguments
    are grouped together and commands retrieved from devices in a single ``nr.cli`` call.
    """
    # extract attributes
    test_results = []
    job_identity = _form_identity(
        kwargs, "test"
    )  # form identity before cleaning kwargs
    kwargs = {k: v for k, v in kwargs.items() if not str(k).startswith("__")}
    commands = args[0] if args else kwargs.pop("commands", [])
    test = args[1] if len(args) > 1 else kwargs.pop("test", None)
    pattern = args[2] if len(args) > 2 else kwargs.pop("pattern", "")
    name = args[3] if len(args) > 3 else kwargs.pop("name", "")
    commands = [commands] if isinstance(commands, str) else commands
    saltenv = kwargs.pop("saltenv", "base")
    suite = kwargs.pop("suite", [])
    subset = kwargs.pop("subset", [])
    dry_run = kwargs.pop("dry_run", False)
    table = kwargs.pop("table", {})  # table
    headers = kwargs.pop("headers", "keys")  # table
    sortby = kwargs.pop("sortby", None)  # table
    reverse = kwargs.pop("reverse", False)  # table
    dump = kwargs.pop("dump", False)  # dump final test results
    test_results = []
    tests = kwargs.pop("tests", None)
    strict = kwargs.pop("strict", False)
    worker = kwargs.pop("worker", None)
    job_data = kwargs.pop("job_data", {})
    suites = {}  # dictionary to hold combined test suites

    # if tests given extract them from hosts' inventory data
    if tests:
        # transform tests to a list if required
        tests = tests if isinstance(tests, list) else [tests]
        # retrieve dictionary keyed by tests path
        inventory_data = nornir_fun(
            fun="inventory",
            call="read_host_data",
            keys=tests,
            worker=worker,
            **{k: v for k, v in kwargs.items() if k in FFun_functions},
        )
        # extract tests
        loaded_suite = {}
        for host_name, tests_data in inventory_data.items():
            loaded_suite[host_name] = []
            for test_path in tests:
                reference = tests_data[test_path]
                if isinstance(reference, list):
                    loaded_suite[host_name].extend(reference)
                elif strict:
                    raise CommandExecutionError(
                        f"'{host_name}' no tests found for '{test_path}'"
                    )
                else:
                    log.warning(f"'{host_name}' no tests found for '{test_path}'")
        suite = loaded_suite
    # if test suite provided, download it from master and render it
    elif isinstance(suite, str):
        suite_content = suite
        # try downloading suite content
        if _is_url(suite):
            suite_content = __salt__["cp.get_url"](suite, dest=None, saltenv=saltenv)
            if not suite_content:
                raise CommandExecutionError(
                    f"Tests suite '{suite}' file download failed"
                )
        # render tests suite on a per-host basis
        per_host_suite = cfg_gen(
            config=suite_content,
            saltenv=saltenv,
            worker=worker,
            job_data=job_data,
            **{k: v for k, v in kwargs.items() if k in FFun_functions},
        )
        # process cfg_gen results
        loaded_suite = {}
        for host_name, v in per_host_suite.items():
            v = v["salt_cfg_gen"]
            if "Traceback" in v:
                raise CommandExecutionError(
                    f"Tests suite '{suite}' rendering failed for '{host_name}':\n{v}"
                )
            elif v.strip():
                loaded_host_tests = __salt__["slsutil.renderer"](
                    string=v, default_renderer="yaml"
                )
                if loaded_host_tests:
                    loaded_suite[host_name] = loaded_host_tests
        suite = loaded_suite
    # if test suite is a list or dict - use it as is
    elif isinstance(suite, (list, dict)) and suite:
        pass
    # use inline test and commands
    elif test and commands:
        # form test dictionary
        test_dict = {
            "test": test,
            "task": commands[0] if len(commands) == 1 else commands,
            "name": name,
            **kwargs,
        }

        # clean up kwargs from test related items
        for k in ["schema", "function_file", "use_all_tasks", "add_host"]:
            _ = kwargs.pop(k, None)

        # check if need to download pattern file from salt master
        if _is_url(pattern):
            pattern = __salt__["cp.get_url"](pattern, dest=None, saltenv=saltenv)
        # add pattern content
        if test == "cerberus":
            test_dict.setdefault("schema", pattern)
        elif test == "custom":
            test_dict.setdefault("function_text", pattern)
        else:
            test_dict.setdefault("pattern", pattern)

        # render test dictionary on a per-host basis
        per_host_suite = cfg_gen(
            config=yaml_safe_dump([test_dict]),
            saltenv=saltenv,
            worker=worker,
            job_data=job_data,
            **{k: v for k, v in kwargs.items() if k in FFun_functions},
        )
        # process cfg_gen results
        loaded_suite = {}
        for host_name, v in per_host_suite.items():
            v = v["salt_cfg_gen"]
            if "Traceback" in v:
                raise CommandExecutionError(
                    f"Tests suite '{suite}' rendering failed for '{host_name}', error:\n{v}"
                )
            elif v.strip():
                loaded_suite[host_name] = __salt__["slsutil.renderer"](
                    string=v, default_renderer="yaml"
                )
        suite = loaded_suite
    else:
        raise CommandExecutionError("No test suite or inline test&commands provided.")

    # validate tests suite
    _ = modelTestsProcessorSuite(tests=suite)

    # do dry run - return produced tests suite only
    if dry_run:
        return suite

    # check if tests suite is empty
    if not suite:
        raise CommandExecutionError(
            "No tests to run, either no hosts matched or tests suite is empty"
        )

    # load files contents for suite that is a list of test items
    if isinstance(suite, list):
        for index, item in enumerate(suite):
            for k in ["pattern", "schema", "function_file"]:
                if _is_url(item.get(k)):
                    item[k] = __salt__["cp.get_url"](
                        item[k], dest=None, saltenv=saltenv
                    )
                    if k == "function_file":
                        item["function_text"] = item.pop(k)
            suite[index] = item
    # load files contents for suite that is a per-host dict of test items
    elif isinstance(suite, dict):
        for host_name in suite.keys():
            for index, item in enumerate(suite[host_name]):
                for k in ["pattern", "schema", "function_file"]:
                    if _is_url(item.get(k)):
                        item[k] = __salt__["cp.get_url"](
                            item[k], dest=None, saltenv=saltenv
                        )
                        if k == "function_file":
                            item["function_text"] = item.pop(k)
                suite[host_name][index] = item

    # combine and sort per-host tests in suites based on exec function and its arguments
    if isinstance(suite, dict):
        for host_name, tests in suite.items():
            for test in tests:
                dhash = hashlib.md5()
                # combine nr.cli tests with same kwargs into the same suites
                if test.get("salt", {}).get("function", "nr.cli") == "nr.cli":
                    salt_args = test.pop("salt", {})
                    salt_args_json = json.dumps(salt_args, sort_keys=True).encode()
                    dhash.update(salt_args_json)
                    salt_args_hash = dhash.hexdigest()
                    suites.setdefault(
                        salt_args_hash, {"params": salt_args, "tests": {}}
                    )
                    suites[salt_args_hash]["tests"].setdefault(host_name, [])
                    suites[salt_args_hash]["tests"][host_name].append(test)
                # other exec function tests run individually as is
                else:
                    test_json = json.dumps(test, sort_keys=True).encode()
                    salt_args = test.pop("salt", {})
                    dhash.update(test_json)
                    test_hash = dhash.hexdigest()
                    suites.setdefault(test_hash, {"params": salt_args, "tests": {}})
                    suites[test_hash]["tests"].setdefault(host_name, [])
                    suites[test_hash]["tests"][host_name].append(test)
    else:
        suites = {"all": {"params": {}, "tests": suite}}

    log.debug(f"nr.test per-exec function combined test suites to run {suites}")

    # run test suites collecting output from devices
    for tests_suite_item in suites.values():
        fun = tests_suite_item["params"].pop("function", "nr.cli").split(".")[-1]
        fun_kwargs = {
            **tests_suite_item["params"],
            "add_details": kwargs.get("add_details", True),
            **kwargs,
            "to_dict": False,
            "tests": tests_suite_item["tests"],
            "identity": job_identity,
            "render": [],
            "subset": subset,
            "worker": worker,
        }
        test_results.extend(globals()[fun](**fun_kwargs))

    # format results to table if requested to do so
    if table:
        test_results = TabulateFormatter(
            test_results,
            tabulate=table,
            headers=headers,
            sortby=sortby,
            reverse=reverse,
        )

    if dump and isinstance(dump, str):
        try:
            nr_data = __proxy__["nornir.nr_data"](
                ["files_base_path", "files_max_count"]
            )
            DumpResults(
                results=test_results,
                filegroup=dump,
                base_url=nr_data["files_base_path"],
                index=__opts__["id"],
                max_files=nr_data["files_max_count"],
                proxy_id=__opts__["id"],
            )
        except:
            tb = traceback.format_exc()
            log.error("nr.test failed to dump results at '{}':\n{}".format(dump, tb))

    return test_results


@ValidateFuncArgs(model_exec_nr_nc)
def nc(*args, **kwargs):
    """
    Function to interact with devices using NETCONF protocol utilizing
    one of supported plugins.

    Available NETCONF plugin names:

    * ``ncclient`` - ``nornir-salt`` built-in plugin that uses ``ncclinet`` library to interact with devices
    * ``scrapli`` - uses ``scrapli_netconf`` connection plugin that is part of
      ``nornir_scrapli`` library, it does not use ``scrapli_netconf`` task plugins,
      but rather implements a wrapper around ``scrapli_netconf`` connection plugin
      connection object.

    :param call: (str) ncclient manager or scrapli netconf object method to call
    :param plugin: (str) Name of netconf plugin to use - ncclient (default) or scrapli
    :param data: (str) path to file for ``rpc`` method call or rpc content
    :param method_name: (str) name of method to provide docstring for, used only by ``help`` call

    Plugins details:

    * ``ncclient`` - uses `ncclient_call <https://nornir-salt.readthedocs.io/en/latest/Tasks/ncclient_call.html>`_
      Nornir-Salt Task plugin, ``nr.nc`` uses this plugin by default
    * ``scrapli`` - uses `scrapli_netconf_call <https://nornir-salt.readthedocs.io/en/latest/Tasks/scrapli_netconf_call.html>`_
      Nornir-Salt Task plugin

    Special ``call`` arguments/methods:

    * ``dir`` - returns methods supported by Ncclient connection manager object::

        salt nrp1 nr.nc dir

    * ``help`` - returns ``method_name`` docstring::

        salt nrp1 nr.nc help method_name=edit_config

    * ``transaction`` - same as ``edit_config``, but runs this (presumably more reliable) work flow:

        1. Lock target configuration datastore
        2. If server supports it - Discard previous changes if any
        3. Perform configuration edit using RPC specified in ``edit_rpc`` argument
        4. If server supports it - validate configuration if ``validate`` argument is True
        5. If server supports it - do commit confirmed if ``confirmed`` argument is True
           using ``confirm_delay`` timer with ``commit_arg`` argument
        6. If confirmed commit requested, wait for ``commit_final_delay`` timer before
           sending final commit, final commit does not use ``commit_arg`` arguments
        7. If server supports it - do commit operation
        8. Unlock target configuration datastore
        9. If server supports it - discard all changes if any of steps 3, 4, 5 or 7 fail
        10. Return results list of dictionaries keyed by step name

        Sample usage::

            salt nrp1 nr.nc transaction target="candidate" config="salt://path/to/config_file.xml" FB="*core-1"

    .. warning:: beware of difference in keywords required by different plugins, e.g. ``filter`` for ``ncclient``
      vs ``filter_``/``filters`` for ``scrapli_netconf``, refer to  modules' api documentation for required
      arguments, using, for instance ``help`` call: ``salt nrp1 nr.nc help method_name=get_config``

    Examples of sample usage for ``ncclient`` plugin::

        salt nrp1 nr.nc server_capabilities FB="*"
        salt nrp1 nr.nc get_config filter='["subtree", "salt://rpc/get_config_data.xml"]' source="running"
        salt nrp1 nr.nc edit_config target="running" config="salt://rpc/edit_config_data.xml" FB="ceos1"
        salt nrp1 nr.nc transaction target="candidate" config="salt://rpc/edit_config_data.xml"
        salt nrp1 nr.nc commit
        salt nrp1 nr.nc rpc data="salt://rpc/iosxe_rpc_edit_interface.xml"
        salt nrp1 nr.nc get_schema identifier="ietf-interfaces"
        salt nrp1 nr.nc get filter='<system-time xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-shellutil-oper"/>'

    Examples of sample usage for ``scrapli_netconf`` plugin::

        salt nrp1 nr.nc get filter_=salt://rpc/get_config_filter_ietf_interfaces.xml plugin=scrapli
        salt nrp1 nr.nc get_config source=running plugin=scrapli
        salt nrp1 nr.nc server_capabilities FB="*" plugin=scrapli
        salt nrp1 nr.nc rpc filter_=salt://rpc/get_config_rpc_ietf_interfaces.xml plugin=scrapli
        salt nrp1 nr.nc transaction target="candidate" config="salt://rpc/edit_config_ietf_interfaces.xml" plugin=scrapli

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.nc",
            arg=["get_config"],
            kwarg={"source": "running", "plugin": "ncclient"},
        )
    """
    # get arguments
    default_kwargs = __proxy__["nornir.nr_data"]("nr_nc")
    args = list(args)
    kwargs["call"] = args.pop(0) if args else kwargs.pop("call")
    kwargs.setdefault(
        "render", ["rpc", "config", "data", "filter", "filter_", "filters"]
    )
    kwargs = {**default_kwargs, **kwargs}
    plugin = kwargs.pop("plugin", "ncclient")
    # decide on plugin to use
    if plugin.lower() == "ncclient":
        task_fun = "nornir_salt.plugins.tasks.ncclient_call"
        kwargs["connection_name"] = "ncclient"
    elif plugin.lower() == "scrapli":
        task_fun = "nornir_salt.plugins.tasks.scrapli_netconf_call"
        kwargs["connection_name"] = "scrapli_netconf"
    # run task
    return __proxy__["nornir.execute_job"](
        task_fun=task_fun, kwargs=kwargs, identity=_form_identity(kwargs, "nc")
    )


@ValidateFuncArgs(model_exec_nr_do)
def do(*args, **kwargs):
    """
    Function to perform steps defined under ``nornir:actions`` configuration
    section at either minion's pillar data or file on master file system.

    To retrieve actions content Salt ``nr.do`` uses ``config.get`` execution module
    function with ``merge`` key set to ``recurse``.

    Each step definition requires these keywords to be defined:

    * ``function`` - mandatory, name of any Salt-Nornir execution module function to run
    * ``args`` - optional, any arguments to use with function
    * ``kwargs`` - optional, any keyword arguments to use with function
    * ``description`` - optional, used by ``dir`` to list action description

    Any other keywords defined inside the step are ignored.

    :param stop_on_error: (bool) if True (default) stops execution on error in step,
        continue execution on error if False
    :param filepath: (str) URL to file with actions steps supporting any of ``cp.get_url``
        URIs: salt://, http://, https://, ftp://, s3://, swift:// and file:// (local filesystem)
    :param default_renderer: (str) shebang string to render file using ``slsutil.renderer`,
        default ``jinja|yaml``
    :param describe: (bool) if True, returns action content without executing it, default is False
    :param kwargs: (any) additional ``kwargs`` to use with actions steps, ``kwargs`` override
        ``kwargs`` dictionary defined within each step, for example, in command
        ``salt nrp1 nr.do configure_ntp FB="*core*"``, ``FB`` argument will override ``FB`` arguments
        defined within steps.
    :param tf: (bool) if True, ``ToFileProcessor`` saves each step results in file
        named after step name if no ``tf`` argument provided within step, default is False
    :param diff: (bool) if True, ``DiffProcessor`` runs diff for each step result using files
        named after step name if no ``diff`` argument provided within step, default is False
    :returns: dictionary with keys: ``failed`` bool, ``result`` list; ``result`` key contains
        a list of results for steps; If ``stop_on_error`` set to ``True`` and error happens, ``failed``
        key set to ``True``

    Special action names ``dir`` and ``dir_list`` used to list all actions available for
    proxy minion where ``dir`` returns table and ``dir_list`` produces a list of actions.

    .. note:: if ``filepath`` argument provided, actions defined in other places are ignored; file
        loaded using SaltStack ``slsutil.renderer`` execution module function, as a result
        file can contain any of supported SaltStack renderer content and can be located
        at any URL supported by ``cp.get_url`` execution module function - supported URL schemes
        are: salt://, http://, https://, ftp://, s3://, swift:// and file:// (local filesystem).
        File content must render to a dictionary keyed by actions' names.

    Sample actions steps definition using proxy minion pillar::

        nornir:
          actions:
            arista_wr:
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

    Sample actions steps definition using text file under ``filepath``::

        arista_wr:
          function: nr.cli
          args: ["wr"]
          kwargs: {"FO": {"platform": "arista_eos"}}
          description: "Save Arista devices configuration"
        configure_ntp:
          - function: nr.cfg
            args: ["ntp server 1.1.1.1"]
            kwargs: {"FB": "*"}
            description: "1. Configure NTP server 1.1.1.1"
          - function: nr.cfg
            args: ["ntp server 1.1.1.2"]
            kwargs: {"FB": "*"}
            description: "2. Configure NTP server 1.1.1.2"
          - function: nr.cli
            args: ["show run | inc ntp"]
            kwargs: {"FB": "*"}
            description: "3. Collect NTP configuration"

    Action name ``arista_wr`` has single step defined, while ``configure_ntp`` action has multiple
    steps defined, each executed in order.

    Multiple actions names can be supplied to ``nr.do`` call.

    .. warning:: having column ``:`` as part of action name not permitted, as ``:`` used by
        Salt ``config.get`` execution module function to split arguments on path items.

    Sample usage::

        salt nrp1 nr.do dir
        salt nrp1 nr.do dir_list
        salt nrp1 nr.do arista_wr
        salt nrp1 nr.do configure_ntp arista_wr stop_on_error=False
        salt nrp1 nr.do configure_ntp FB="*core*" add_details=True
        salt nrp1 nr.do arista_wr filepath="salt://actions/actions_file.txt"

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.do",
            arg=["configure_ntp", "arista_wr"],
            kwarg={"FB": "R[12]"},
        )
    """
    ret = {"failed": False, "result": []}
    stop_on_error = kwargs.pop("stop_on_error", True)
    filepath = kwargs.pop("filepath", None)
    default_renderer = kwargs.pop("default_renderer", "jinja|yaml")
    describe = kwargs.pop("describe", False)
    tf = kwargs.pop("tf", False)
    diff = kwargs.pop("diff", False)

    # load file if filepath provided
    if filepath:
        file_content_dict = __salt__["slsutil.renderer"](
            path=filepath, default_renderer=default_renderer
        )
        if not file_content_dict:
            ret["failed"] = True
            ret["result"].append({filepath: "Failed loading filepath content."})
            return ret

    # check if need to list all actions
    if "dir" in args or "dir_list" in args:
        pattern = args[1] if len(args) == 2 else None
        actions_config = (
            __salt__["config.get"](
                key="nornir:actions",
                merge="recurse",
                omit_opts=True,
                omit_master=True,
                omit_grains=True,
            )
            if not filepath
            else file_content_dict
        )
        # iterate over actions and form brief list of them
        for action_name, data in actions_config.items():
            # check if action name mathes the pattern
            if pattern and not fnmatch.fnmatch(action_name, pattern):
                continue
            ret["result"].append(
                {
                    "action name": action_name,
                    "description": data.get("description", "")
                    if isinstance(data, dict)
                    else "\n".join([i.get("description", "") for i in data]).strip(),
                }
            )
        if "dir" in args:
            ret["result"] = TabulateFormatter(
                ret["result"],
                tabulate={"tablefmt": "grid"},
                headers=["action name", "description"],
            )
        return ret

    # run actions
    for action_name in args:
        try:
            if filepath:
                action_config = file_content_dict.get(action_name)
            else:
                action_config = __salt__["config.get"](
                    key="nornir:actions:{}".format(action_name),
                    merge="recurse",
                    omit_opts=True,
                    omit_master=True,
                    omit_grains=True,
                )
            if not action_config:
                raise CommandExecutionError(
                    "'{}' action not loaded, content: '{}'".format(
                        action_name, action_config
                    )
                )
            elif describe:
                ret["result"].append({action_name: action_config})
                continue
            elif isinstance(action_config, dict):
                action_config = [action_config]

            # validate steps content
            _ = model_exec_nr_do_action(action=action_config)

            # run steps
            for step in action_config:
                # form step kwargs
                merged_kwargs = step.get("kwargs", {})
                merged_kwargs.update(kwargs)
                merged_kwargs["identity"] = _form_identity(
                    kwargs, "do.{}".format(action_name)
                )
                # add tf ToFileProcessor name if tf_each is True
                if tf is True:
                    merged_kwargs.setdefault("tf", action_name)
                # add diff for DiffProcessor
                if diff:
                    merged_kwargs.setdefault("diff", action_name)
                # get fun name
                fun_name = step["function"].split(".")[1].strip()
                # run step
                log.debug(
                    "salt_nornir:nr.do running step {}, args {}, kwargs {}".format(
                        fun_name, step.get("args", []), merged_kwargs
                    )
                )
                result = globals()[fun_name](*step.get("args", []), **merged_kwargs)
                ret["result"].append({action_name: result})
        except:
            tb = traceback.format_exc()
            log.error(
                "nr.do error while running '{}' action:\n{}".format(action_name, tb)
            )
            ret["result"].append({action_name: tb})
            if stop_on_error:
                ret["failed"] = True
                break

    return ret


@ValidateFuncArgs(model_exec_nr_http)
def http(*args, **kwargs):
    """
    HTTP requests related functions

    :param method: (str) HTTP method to use
    :param url: (str) full or partial URL to send request to
    :param kwargs: (dict) any other kwargs to use with requests.<method> call

    This function uses Nornir-Salt
    `http_call <https://nornir-salt.readthedocs.io/en/latest/Tasks/http_call.html>`_
    task plugin, refer its documentation for additional details.

    Sample usage::

        salt nrp1 nr.http get "http://1.2.3.4/api/data/"
        salt nrp1 nr.http get "https://sandbox-iosxe-latest-1.cisco.com/restconf/data/" verify=False auth='["developer", "C1sco12345"]'

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.http",
            arg=["get", "http://1.2.3.4/api/data/"],
        )
    """
    if len(args) == 1:
        kwargs["method"] = args[0]
    elif len(args) == 2:
        kwargs["method"] = args[0]
        kwargs["url"] = args[1]
    task_fun = "nornir_salt.plugins.tasks.http_call"
    kwargs["connection_name"] = "http"
    # run task
    return __proxy__["nornir.execute_job"](
        task_fun=task_fun, kwargs=kwargs, identity=_form_identity(kwargs, "http")
    )


@ValidateFuncArgs(model_exec_nr_file)
def file(*args, **kwargs):
    """
    Function to manage Nornir-salt files.

    :param call: (str) files task to call - ls, rm, read, diff
    :param base_url: (str) base path to files, default is ``/var/salt-nornir/{proxy_id}/files/``
    :param index: (str) index filename within ``base_url`` folder to read
        files info from, default value is equal to proxy id
    :param kwargs: (dict) any additional kwargs such ``Fx`` filters or call
        function arguments

    File tasks description:

    * ``ls`` - list files of this Proxy Minions, returns list of dictionaries
    * ``rm`` - removes file with given name and index number
    * ``read`` - displays content of file with given name and index number
    * ``diff`` - reads two files and returns diff

    ``ls`` arguments

    :param filegroup: (str or list) ``tf`` or list of ``tf`` filegroup names of
        the files to list, lists all files by default
    :return: files list

    ``rm`` arguments

    :param filegroup: (str or list) ``tf`` or list of ``tf`` filegroup names of
        the files to remove, if set to True will remove all files for all filegroups
    :return: list of files removed

    ``read`` arguments

    :param filegroup: (str or list) ``tf`` or list of ``tf`` filegroup names of
        the files to read
    :param last: (int) version of content to read
    :return: results reconstructed out of files content

    ``diff`` arguments

    :param filegroup: (str or list) ``tf`` filegroup name to diff
    :param last: (int or list or str) files to diff, default is ``[1, 2]`` -
        last 1 and last 2 files
    :return: files unified difference

    Sample usage::

        salt nrp1 nr.file read ip
        salt nrp1 nr.file rm ip interface
        salt nrp1 nr.file diff routes last='[1,2]'

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.file",
            arg=["ls"],
            kwarg={"filegroup": "interfaces"},
        )
    """
    # form kwargs content
    kwargs["call"] = args[0] if len(args) >= 1 else kwargs["call"]
    kwargs["identity"] = _form_identity(kwargs, "file")
    kwargs["filegroup"] = kwargs.pop(
        "filegroup", list(args[1:]) if len(args) >= 2 else None
    )
    kwargs["base_url"] = kwargs.get(
        "base_url", __proxy__["nornir.nr_data"]("files_base_path")
    )
    kwargs["index"] = kwargs.get(
        "index", __proxy__["nornir.nr_data"]("stats")["proxy_minion_id"]
    )
    if kwargs["call"] in ["ls", "rm", "list"]:
        kwargs.setdefault("table", "extend")
        kwargs.setdefault(
            "headers",
            [
                "host",
                "filegroup",
                "last",
                "timestamp",
                "tasks",
                "filename",
                "exception",
            ],
        )
    if kwargs["call"] in ["remove", "rm", "delete"]:
        # add tf_index_lock in arguments, proxy module will replace it
        # with actual multiprocessing Lock object, this is to control
        # simeltenious access to filegroups index
        kwargs["tf_index_lock"] = None

    return task(
        plugin="nornir_salt.plugins.tasks.files",
        render=[],
        **kwargs,
    )


@ValidateFuncArgs(model_exec_nr_learn)
def learn(*args, **kwargs):
    """
    Store task execution results to local filesystem on the minion using
    ``tf`` (to filename) attribute to form filenames.

    :param fun: (str) name of execution module function to call
    :param tf: (str) ``ToFileProcessor`` filegroup name
    :param tf_skip_failed: (bool) default is True, do not save failed tasks
    :param args: (list) execution module function arguments
    :param kwargs: (dict) execution module function key-word arguments

    This task uses ``ToFileProcessor`` to store results and is a shortcut
    to calling individual execution module functions with ``tf`` argument.

    Supported execution module functions are ``cli, nc, do, http``. By default
    calls ``nr.do`` function.

    ``tf`` attribute mandatory except for cases when using ``nr.do``function
    e.g. ``salt nrp1 nr.learn mac interface``, in that case ``tf`` set equal
    to file group name - ``mac`` and ``interface`` for each action call using
    ``nr.do`` function ``tf=True`` attribute.

    Sample usage::

        salt nrp1 nr.learn mac
        salt nrp1 nr.learn mac ip interface FB="CORE-*"
        salt nrp1 nr.learn "show version" "show int brief" tf="cli_facts" fun="cli"

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.learn",
            arg=["mac", "ip"],
            kwarg={"FB": "CORE-*"},
        )
    """
    fun = kwargs.pop("fun", "do")
    kwargs["tf"] = True if fun == "do" else kwargs.get("tf")
    kwargs.setdefault("tf_skip_failed", True)  # do not learn failed tasks
    kwargs["identity"] = _form_identity(
        kwargs, "learn.{}".format(".".join(args) if fun == "do" else fun)
    )
    # run command with added ToFileProcessor argument
    return globals()[fun](*args, **kwargs)


@ValidateFuncArgs(model_exec_nr_find)
def find(*args, **kwargs):
    """
    Search for information stored in Proxy Minion files.

    This function does not query devices but only uses information
    stored locally by ``ToFileProcessor``.

    :param headers: (str or list) table headers, default is ``keys``
    :param table: (str) TabulateFormatter table directive, default is ``extend``
    :param headers_exclude: (str or list) table headers to exclude, default is
        ``["changed", "diff", "failed", "name", "connection_retry", "task_retry"]``
    :param reverse: (bool) default is False, reverses table order if True
    :param sortby: (str) column header name to sort table by
    :param last: (int) file group version of files to search in
    :param Fx: (str) Nornir host filters
    :param args: (list) list of ``ToFileProcessor`` filegroup names to search in
    :param kwargs: (dict) key-value pairs where keys are keys to search for, values
        are criteria to check
    :returns: list of dictionaries with matched results

    Find uses ``DataProcessor`` ``find`` function to do search and supports
    searching in a list of dictionaries, dictionary and text.

    If no ``args`` provided ``nr.find`` fails.

    Sample usage::

        salt nrp1 nr.find ip ip="1.1.*"
        salt nrp1 nr.find mac arp mac="1b:cd:34:5f:6c"
        salt nrp1 nr.find ip ip="1.1.*" last=5 FB="*CORE*"
        salt nrp1 nr.find ip mask__ge=23 mask__lt=30 FC="CORE"
        salt nrp1 nr.find interfaces description__contains="ID #123321"

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.find",
            arg=["ip"],
            kwarg={"ip": "1.1.*"},
        )
    """
    # form kwargs content
    identity = _form_identity(kwargs, "find")
    kwargs = {k: v for k, v in kwargs.items() if not k.startswith("__")}
    Fx = {k: kwargs.pop(k) for k in list(kwargs.keys()) if k in FFun_functions}

    # read files content running file_read task and filter it using find function
    return task(
        plugin="nornir_salt.plugins.tasks.files",
        call="read",
        filegroup=list(set(args)),
        base_url=__proxy__["nornir.nr_data"]("files_base_path"),
        index=__proxy__["nornir.nr_data"]("stats")["proxy_minion_id"],
        render=[],  # do not render anything
        last=kwargs.pop("last", 1),
        table=kwargs.pop("table", "extend"),
        headers=kwargs.pop("headers", "keys"),
        reverse=kwargs.pop("reverse", False),
        sortby=kwargs.pop("sortby", "host"),
        identity=identity,
        headers_exclude=kwargs.pop(
            "headers_exclude",
            [
                "changed",
                "diff",
                "failed",
                "name",
                "connection_retry",
                "task_retry",
                "exception",
            ],
        ),
        dp=[{"fun": "find", "checks_required": False, **kwargs}],
        **Fx,
    )


@ValidateFuncArgs(model_exec_nr_diff)
def diff(*args, **kwargs):
    """
    Provide difference between current and previously learned information or
    between versions of files stored by ``ToFileProcessor``.

    :param diff: (str) ``ToFileProcessor`` filegroup name
    :param last: (int or list or str) filegroup file indexes to diff, default is 1
    :param kwargs: (dict) any additional kwargs to use with ``nr.file diff``
        call or with ``DiffProcessor``

    ``diff`` or ``args`` attributes are mandatory.

    If last is a single digit e.g. 1, diff uses ``nr.do`` function to execute
    action named same as ``filegroup`` attribute and uses results to produce diff
    with previously saved ``filegroup`` files using ``DiffProcessor``.

    If ``last`` is a list e.g. ``[2, 5]`` or string ``1, 2``- will use ``nr.file diff``
    call to produce diff for previously saved results without retrieving data from devices.

    Sample usage::

        salt nrp1 nr.diff interface
        salt nrp1 nr.diff interface last=1
        salt nrp1 nr.diff interface last='[1, 5]'
        salt nrp1 nr.diff interface last="1,5"

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.diff",
            arg=["interface"],
            kwarg={"last": 1},
        )
    """
    # form kwargs content
    last = kwargs.pop("last", 1)
    kwargs["identity"] = _form_identity(kwargs, "diff")

    # use nr.file diff function to diff files
    if isinstance(last, (list, str)):
        kwargs["filegroup"] = kwargs.pop("diff", list(args))
        return file("diff", last=last, **kwargs)
    # use nr.do with DiffProcessor to diff device state
    elif isinstance(last, int):
        kwargs["diff"] = True
        return do(last=last, *args, **kwargs)


@ValidateFuncArgs(model_exec_nr_nornir_fun)
def nornir_fun(fun, *args, **kwargs):
    """
    Function to call various Nornir utility functions.

    :param fun: (str) utility function name to call
    :param kwargs: (dict) function arguments

    Available utility functions:

    * ``dir`` - return a list of supported functions
    * ``test`` - this method tests proxy minion module worker thread without invoking any Nornir code
    * ``refresh`` - re-instantiates Nornir workers after retrieving latest pillar data from Salt Master,
      if ``workers_only=True`` only refreshes Nornir workers using latest pillar data, without closing
      queues and killing child processes, resulting in inventory refresh but with no interruption to jobs
      execution process.
    * ``kill`` - executes immediate shutdown of Nornir Proxy Minion process and child processes
    * ``shutdown`` - gracefully shutdowns Nornir Proxy Minion process and child processes
    * ``inventory`` - interact with Nornir Process inventory data, using ``InventoryFun`` function,
      by default, for ``read_host, read, read_inventory, list_hosts, list_hosts_platforms`` operations any
      Nornir worker can respond, for other, non-read operations targets all Nornir workers
    * ``stats`` - returns statistics about Nornir proxy process, accepts ``stat`` argument of stat
      name to return
    * ``version`` - returns a report of Nornir related packages installed versions
    * ``initialized`` - returns Nornir Proxy Minion initialized status - True or False
    * ``hosts`` - returns a list of hosts managed by this Nornir Proxy Minion, accepts ``Fx``
      arguments to return only hosts matched by filter
    * ``connections`` - list hosts' active connections for all workers, accepts ``Fx`` arguments to
      filter hosts to list, by default returns connections data for all Nornir workers, uses
      ``nornir_salt.plugins.tasks.connections`` ``ls`` call, accept ``conn_name`` parameter
    * ``disconnect`` - close host connections, accepts ``Fx`` arguments to filter hosts and ``conn_name``
      of connection to close, by default closes all connections from all Nornir workers, uses
      ``nornir_salt.plugins.tasks.connections`` ``close`` call
    * ``connect`` - initiate connection to devices, arguments: ``conn_name, hostname, username, password, port,``
      ``platoform, extras, default_to_host_attributes, close_open``, uses ``nornir_salt.plugins.tasks.connections``
      ``open`` call
    * ``clear_hcache`` - clear task results cache from hosts' data, accepts ``cache_keys`` list argument
      of key names to remove, if no ``cache_keys`` argument provided removes all cached data, by default targets all Nornir workers
    * ``clear_dcache`` - clear task results cache from defaults data, accepts ``cache_keys`` list argument
      of key names to remove, if no ``cache_keys`` argument provided removes all cached data, by default targets all Nornir workers
    * ``workers/worker`` - call nornir worker utilities e.g. ``stats``
    * ``results_queue_dump`` - return content of results queue

    Sample Usage::

        salt nrp1 nr.nornir inventory FB="R[12]"
        salt nrp1 nr.nornir inventory FB="R[12]" worker="all"
        salt nrp1 nr.nornir inventory create_host name="R1" hostname="1.2.3.4" platform="ios" groups='["lab"]'
        salt nrp1 nr.nornir inventory update_host name="R1" data='{"foo": bar}'
        salt nrp1 nr.nornir inventory read_host FB="R1"
        salt nrp1 nr.nornir inventory call=delete_host name="R1"
        salt nrp1 nr.nornir inventory update_defaults username=foo password=bar data='{"f": "b"}'
        salt nrp1 nr.nornir inventory read_host_data keys="['hostname', 'platform', 'circuits']"
        salt nrp1 nr.nornir stats stat="proxy_minion_id"
        salt nrp1 nr.nornir version
        salt nrp1 nr.nornir shutdown
        salt nrp1 nr.nornir clear_hcache cache_keys='["key1", "key2]'
        salt nrp1 nr.nornir clear_dcache cache_keys='["key1", "key2]'
        salt nrp1 nr.nornir workers stats
        salt nrp1 nr.nornir connect conn_name=netmiko username=cisco password=cisco platform=cisco_ios
        salt nrp1 nr.nornir connect scrapli port=2022 close_open=True
        salt nrp1 nr.nornir connect netmiko via=console
        salt nrp1 nr.nornir connections conn_name=netmiko
        salt nrp1 nr.nornir disconnect conn_name=ncclient
        salt nrp1 nr.nornir refresh workers_only=True

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.nornir",
            arg=["stats"],
        )
    """
    kwargs = {k: v for k, v in kwargs.items() if not k.startswith("__")}
    if fun == "inventory":
        kwargs.setdefault("call", args[0] if args else "read_inventory")
        # make sure by default targets all workers for non read operations
        if kwargs["call"] not in [
            "read_host",
            "read",
            "read_inventory",
            "read_host_data",
            "list_hosts",
            "list_hosts_platforms",
        ]:
            kwargs.setdefault("worker", "all")
        return task(plugin="inventory", **kwargs)
    elif fun == "stats":
        return __proxy__["nornir.stats"](*args, **kwargs)
    elif fun == "version":
        return __proxy__["nornir.nr_version"]()
    elif fun == "shutdown":
        return task(plugin="shutdown")
    elif fun == "initialized":
        return __proxy__["nornir.initialized"]()
    elif fun == "kill":
        return __proxy__["nornir.kill_nornir"]()
    elif fun == "refresh":
        return task(
            plugin="refresh",
            identity=_form_identity(kwargs, "nornir.refresh"),
            **kwargs,
        )
    elif fun == "test":
        return task(plugin="test", identity=_form_identity(kwargs, "nornir.test"))
    elif fun == "hosts":
        return __proxy__["nornir.list_hosts"](**kwargs)
    elif fun == "connections":
        kwargs.setdefault("worker", "all")
        return task(
            plugin="nornir_salt.plugins.tasks.connections",
            call="ls",
            identity=_form_identity(kwargs, "nornir.connections"),
            **kwargs,
        )
    elif fun == "disconnect":
        kwargs.setdefault("worker", "all")
        return task(
            plugin="nornir_salt.plugins.tasks.connections",
            call="close",
            identity=_form_identity(kwargs, "nornir.disconnect"),
            **kwargs,
        )
    elif fun == "connect":
        kwargs["conn_name"] = args[0] if args else kwargs["conn_name"]
        return task(
            plugin="nornir_salt.plugins.tasks.connections",
            call="open",
            identity=_form_identity(kwargs, "nornir.connect"),
            **kwargs,
        )
    elif fun == "clear_hcache":
        # make sure to cleare hcache for all workers by default
        kwargs.setdefault("worker", "all")
        return task(
            plugin="nornir_salt.plugins.tasks.salt_clear_hcache",
            identity=_form_identity(kwargs, "nornir.clear_hcache"),
            **kwargs,
        )
    elif fun == "clear_dcache":
        # make sure to always cleare dcache for all workers
        kwargs["worker"] = "all"
        return task(
            plugin="clear_dcache",
            identity=_form_identity(kwargs, "nornir.clear_dcache"),
            **kwargs,
        )
    elif fun in ["workers", "worker"]:
        kwargs["call"] = args[0] if len(args) == 1 else kwargs["call"]
        return __proxy__["nornir.workers_utils"](**kwargs)
    elif fun == "dir":
        return {
            "Supported functions": sorted(
                model_exec_nr_nornir_fun.schema()["definitions"]["EnumNrFun"]["enum"]
            )
        }
    elif fun == "results_queue_dump":
        return __proxy__["nornir.queues_utils"](call="results_queue_dump")


@ValidateFuncArgs(model_exec_nr_gnmi)
def gnmi(call, *args, **kwargs):
    """
    Function to interact with devices using gNMI protocol utilizing one of supported plugins.

    :param call: (str) (str) connection object method to call or name of one of extra methods
    :param plugin: (str) Name of gNMI plugin to use - pygnmi (default)
    :param method_name: (str) name of method to provide docstring for, used only by ``help`` call
    :param path: (list or str) gNMI path string for ``update``, ``delete``, ``replace`` extra methods calls
    :param filename: (str) path to file with call method arguments content
    :param kwargs: (dict) any additional keyword arguments to use with call method
    :return: method call results

    Available gNMI plugin names:

    * ``pygnmi`` - uses `pygnmi_call <https://nornir-salt.readthedocs.io/en/latest/Tasks/pygnmi_call.html>`_
      Nornir-Salt Task plugin that relies on `PyGNMI library <https://pypi.org/project/pygnmi/>`_
      to interact with devices.

    gNMI specification defines several methods to work with devices - ``subscribe``, ``get`` and ``set``.
    ``set`` further supports ``delete``, ``update`` and ``replace`` operations.

    .. warning:: ``subscribe`` is not supported by ``nr.gnmi`` function.

    Sample usage of ``pygnmi`` plugin::

        salt nrp1 nr.gnmi capabilities FB="*"
        salt nrp1 nr.gnmi get "openconfig-interfaces:interfaces/interface[name=Loopback100]"
        salt nrp1 nr.gnmi get path='["openconfig-interfaces:interfaces/interface[name=Loopback100]"]'
        salt nrp1 nr.gnmi get path="openconfig-interfaces:interfaces, openconfig-network-instance:network-instances"
        salt nrp1 nr.gnmi set update='[["openconfig-interfaces:interfaces/interface[name=Loopback100]/config", {"description": "Done by gNMI"}]]'
        salt nrp1 nr.gnmi set replace='[["openconfig-interfaces:interfaces/interface[name=Loopback1234]/config", {"name": "Loopback1234", "description": "New"}]]'
        salt nrp1 nr.gnmi set delete="openconfig-interfaces:interfaces/interface[name=Loopback1234]"

    **Extra Call Methods**

    * ``dir`` - returns methods supported by ``gNMIclient`` connection object, including
      extra methods defined by nornir-salt ``pygnmi_call`` task plugin::

        salt nrp1 nr.gnmi dir

    * ``help`` - returns ``method_name`` docstring::

        salt nrp1 nr.gnmi help method_name=set

    * ``replace`` - shortcut method to ``set`` call with ``replace`` argument,
      first argument must be path string, other keyword arguments are configuration items::

        salt nrp1 nr.gnmi replace "openconfig-interfaces:interfaces/interface[name=Loopback100]/config" name=Loopback100 description=New

    * ``update`` - shortcut method to ``set`` call with ``update`` argument,
      first argument must be path string, other keyword arguments are configuration items::

        salt nrp1 nr.gnmi update "openconfig-interfaces:interfaces/interface[name=Loopback100]/config" description="RID Loop"

    * ``delete`` - shortcut method to ``set`` call with ``delete`` argument,
      accepts a list of path items or ``path`` argument referring to list::

        salt nrp1 nr.gnmi delete "openconfig-interfaces:interfaces/interface[name=Loopback100]" "openconfig-interfaces:interfaces/interface[name=Loopback123]"
        salt nrp1 nr.gnmi delete path='["openconfig-interfaces:interfaces/interface[name=Loopback100]", "openconfig-interfaces:interfaces/interface[name=Loopback123]"]'

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.gnmi",
            arg=["get"],
            kwarg={"path": ["openconfig-interfaces:interfaces"]},
        )

    If ``filename`` argument provided it is rendered using ``slsutil.renderer`` function and
    must produce a dictionary with keys being valid arguments supported by call method.
    For example, ``pygnmi`` plugin ``set`` call can look like this::

        salt nrp1 nr.gnmi set filename="salt://path/to/set_args.txt"

    Where ``salt://path/to/set_args.txt`` content is::

        replace:
          - - "openconfig-interfaces:interfaces/interface[name=Loopback35]/config"
            - {"name": "Loopback35", "description": "RID Loopback"}
          - - "openconfig-interfaces:interfaces/interface[name=Loopback36]/config"
            - {"name": "Loopback36", "description": "MGMT Loopback"}
        update:
          - - "openconfig-interfaces:interfaces/interface[name=Loopback35]/config"
            - {"name": "Loopback35", "description": "RID Loopback"}
          - - "openconfig-interfaces:interfaces/interface[name=Loopback36]/config"
            - {"name": "Loopback36", "description": "MGMT Loopback"}
        delete:
          - "openconfig-interfaces:interfaces/interface[name=Loopback35]"
          - "openconfig-interfaces:interfaces/interface[name=Loopback36]"

    ``salt://path/to/set_args.txt`` content will be rendered to a dictionary and
    supplied to ``set`` call as ``**kwargs``.

    ``pygnmi`` plugin order of operation for above case is ``delete -> replace -> update``
    """
    plugin = kwargs.pop("plugin", "pygnmi")
    kwargs["call"] = call
    kwargs["render"] = []

    # special case, check if "name" argument provided, need to rename it
    # to not collide with nr.run method "name" agrument
    if "name" in kwargs:
        kwargs["name_arg"] = kwargs.pop("name")

    # extract args
    if call in ["update", "replace", "delete"] and not args and "path" not in kwargs:
        return "No path argument provided"
    elif call in ["update", "replace", "delete", "get"] and args:
        kwargs["path"] = list(args) if call in ["delete", "get"] else args[0]
    elif call == "subscribe":
        return "Unsupported method 'subscribe'"

    # render filename argument
    if "filename" in kwargs:
        filename = kwargs.pop("filename")
        content = __salt__["slsutil.renderer"](filename)
        if not content:
            raise CommandExecutionError(
                "Filename '{}' not on master; path correct?".format(filename)
            )
        if not isinstance(content, dict):
            raise CommandExecutionError(
                "Filename '{}' must render to dictionary".format(filename)
            )
        kwargs.update(content)

    # decide on task plugin to use
    if plugin.lower() == "pygnmi":
        task_fun = "nornir_salt.plugins.tasks.pygnmi_call"
        kwargs["connection_name"] = "pygnmi"

    # run task
    return __proxy__["nornir.execute_job"](
        task_fun=task_fun, kwargs=kwargs, identity=_form_identity(kwargs, "gnmi")
    )


@ValidateFuncArgs(model_exec_nr_snmp)
def snmp(call, *args, **kwargs):
    """
    Function to interact with devices using SNMP protocol utilizing one of supported plugins.

    :param call: (str) connection object method to call or name of one of extra methods
    :param plugin: (str) Name of SNMP plugin to use - puresnmp (default)
    :param method_name: (str) name of method to provide docstring for, used only by ``help`` call
    :param kwargs: (dict) any additional keyword arguments to use with call method
    :return: method call results

    Available SNMP plugin names:

    * ``puresnmp`` - uses `puresnmp_call <https://nornir-salt.readthedocs.io/en/latest/Tasks/puresnmp_call.html>`_
        Nornir-Salt Task plugin that relies on `puresnmp library <https://github.com/exhuma/puresnmp>`_
        to interact with devices.

    Sample usage of ``puresnmp`` plugin, ``plugin="puresnmp"``::

        salt nrp1 nr.snmp bulkget scalar_oids='["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.2.0"]' repeating_oids='["1.3.6.1.2.1.3.1"]'
        salt nrp1 nr.snmp bulktable oid="1.3.6.1.2.1.2.2.1"
        salt nrp1 nr.snmp bulkwalk oids='["1.3.6.1.2.1.1.1", "1.3.6.1.2.1.1.5"]'
        salt nrp1 nr.snmp get oid="1.3.6.1.2.1.1.1.0" FB="*"
        salt nrp1 nr.snmp getnext oid="1.3.6.1.2.1.1.1.0"
        salt nrp1 nr.snmp multiget oids='["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.2.0"]'
        salt nrp1 nr.snmp multiset mappings='{"1.3.6.1.2.1.1.4.0": "new contact value", "1.3.6.1.2.1.1.6.0": "new location"}'
        salt nrp1 nr.snmp multiwalk oids='["1.3.6.1.2.1.1.1", "1.3.6.1.2.1.1.5"]'
        salt nrp1 nr.snmp set oid="1.3.6.1.2.1.1.4.0" value="new contact value"
        salt nrp1 nr.snmp table oid="1.3.6.1.2.1.2.2.1"
        salt nrp1 nr.snmp walk oid="1.3.6.1.2.1.1"

    By default ``oid`` and ``oids`` arguments rendered and can be sourced from
    host inventory::

        salt nrp1 nr.snmp get oid="{{ host.oid.get_os }}"
        salt nrp1 nr.snmp multiget oids='["{{ host.oid.get_os }}", "{{ host.oid.get_hostname }}"]'

    Where ``host.oid.get_os`` sourced from Nornir inventory::

        hosts:
          ceos1:
            groups: [lab]
        groups:
          lab:
            data:
              oid:
                get_os: "1.3.6.1.2.1.1.1.0"
                get_hostname: "1.3.6.1.2.1.1.5.0"

    **Extra Call Methods**

    * ``dir`` - returns call methods supported by plugin::

        salt nrp1 nr.snmp dir plugin=puresnmp

    * ``help`` - returns ``method_name`` docstring::

        salt nrp1 nr.snmp help method_name=set

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.snmp",
            arg=["get"],
            kwarg={"oid": "1.3.6.1.2.1.1.1.0"},
        )
    """
    plugin = kwargs.pop("plugin", "puresnmp")
    kwargs["call"] = call
    kwargs["render"] = ["oid", "oids"]

    # decide on task plugin to use
    if plugin.lower() == "puresnmp":
        task_fun = "nornir_salt.plugins.tasks.puresnmp_call"
        kwargs["connection_name"] = "puresnmp"

    # run task
    return __proxy__["nornir.execute_job"](
        task_fun=task_fun, kwargs=kwargs, identity=_form_identity(kwargs, "snmp")
    )


@ValidateFuncArgs(model_exec_nr_netbox)
def netbox(*args, **kwargs):
    """
    Function to interact with `Netbox DCIM <https://github.com/netbox-community/netbox>`_.

    Why? Because data is the key.

    :param task: (str) name of Netbox task function to run
    :param kwargs: (dict) any additional keyword arguments to use with task function
    :return: task results

    For nr.netbox functions to work, Netbox token and url parameters should be defined in
    master's configuration ``ext_pillar`` section and Master's configuration file need
    to have ``pillar_opts`` set to ``True`` for minion to be able to source parameters from
    Salt-Master configuration::

        pillar_opts: True
        ext_pillar:
          - salt_nornir_netbox:
              url: 'http://192.168.115.129:8000'
              token: '837494d786ff420c97af9cd76d3e7f1115a913b4'

    Alternatively, Netbox parameters can be defined in proxy minion pillar settings::

        salt_nornir_netbox_pillar:
          url: 'http://192.168.115.129:8000'
          token: '837494d786ff420c97af9cd76d3e7f1115a913b4'

    Pillar defined parameters take precendence over master's configuration.

    Starting with version ``0.20.0`` support added to cache data retrieved from
    Netbox on a per-device basis. For this functionality to work need to have
    `diskcache <https://github.com/grantjenks/python-diskcache>`_ library installed
    on salt-nornir proxy minion. Cache is persistant and stored on the minion's
    local filesystem.

    Available ``task`` functions are listed below.

    **dir task**

    Returns a list of supported tasks functions. Sample usage::

        salt nrp1 nr.netbox dir

    **query task**

    Helps to retrieve data from Netbox over GraphQL API.

    Supported arguments:

    :param query_string: GraphQL query string to send to Netbox GraphQL API
    :param field: name of the the fields to retirieve e.g. device_list, interface_list
    :param filters: dictionary of filters to use
    :param fields: dictionary of fields to retrieve
    :param queries: dictionary keyed by GraphQL aliases with values being a dictionary of
      `field``, ``filters`` and ``fields`` parameters.

    To use ``query`` task need to provide one of

    - ``query_string`` or
    - ``field``, ``filters`` and ``fields`` parameters to form query string or
    - ``queries`` dictionary to form query strings with aliases

    Sample usage::

        salt nrp1 nr.netbox query field="device_list" filters='{"name": "ceos1"}' fields='["name", "platform {name}", "status"]'
        salt nrp1 nr.netbox query queries='{"devices": {"field": "device_list", "filters": {"platform": "eos"}, "fields": ["name"]}}'
        salt nrp1 nr.netbox query query_string='query{device_list(platform: "eos") {name}}'

    **rest task**

    Qquery Netbox REST API using requests. This task supports any requests module
    arguments in additiona to these arguments:

    :param method: get, ports, put, patch, delete action to query
    :param api: Netbox API endpoint to query e.g. ``dcim/interfaces``

    Sample usage::

        salt nrp1 nr.netbox rest get "dcim/interfaces" params='{"name__ic": "eth1", "device": "fceos4"}'
        salt nrp1 nr.netbox rest method=get api="dcim/interfaces" params='{"device": "fceos4"}'

    **get_interfaces task**

    Retrieves devices' interfaces details from Netbox, supported arguments:

    :param add_ip: boolean, if True adds IP addresses information to interfaces
    :param add_inventory_items: boolean, if True adds inventory items information to interfaces
    :param cache: True (default) - use cache for Netbox data, ``refresh`` - delete cached data,
        False - ignore cache
    :param cache_ttl: integer indicating cache time to live

    Sample usage::

        salt nrp1 nr.netbox get_interfaces FB="ceos1" add_ip=True add_inventory_items=True

    **get_connections task**

    Retrieves devices' interfaces connections from Netbox. Supported arguments:

    :param trace: if True traces full connection path between device interfaces
    :param cache: True (default) - use cache for Netbox data, ``refresh`` - delete cached data,
        False - ignore cache
    :param cache_ttl: integer indicating cache time to live

    Sample usage::

        salt nrp1 nr.netbox get_connections FB="ceos1"
        salt nrp1 nr.netbox get_connections FB="ceos1" trace=True

    **update_config_context task**

    Task to parse device configuration and save results into Netbox device's
    configuration context.

    Dependency: TTP, ``pip install ttp``

    Sample usage::

        salt nrp1 nr.netbox update_config_context FB=ceos1

    **parse_config task**

    Task to parse device configuratoion using TTP templates and return results.
    This task used by ``update_config_context`` to retrieve configuration
    parsing results.

    Dependency: TTP, ``pip install ttp``

    Sample usage::

        salt nrp1 nr.netbox parse_config

    **update_vrf task**

    This task helps to create or update VRFs and Route-Targets in Netbox from
    device configuration.

    Sample usage::

        salt nrp1 nr.netbox update_vrf
    """
    task_name = args[0] if args else kwargs.pop("task")

    # run Netbox task using Salt Jobs results
    return netbox_tasks[task_name](
        *args[1:],
        **{k: v for k, v in kwargs.items() if not k.startswith("_")},
        __salt__=__salt__,
        proxy_id=__opts__["id"],
    )


@ValidateFuncArgs(model_exec_nr_network)
def network(fun, *args, **kwargs):
    """
    Function to call various network related utility functions.

    :param fun: (str) utility function name to call
    :param kwargs: (dict) function arguments

    Available utility functions.

    **resolve_dns function**

    resolves hosts' hostname DNS returning IP addresses using
    ``nornir_salt.plugins.tasks.network.resolve_dns`` Nornir-Salt
    function.

    **ping function**

    Function to execute ICMP ping to host using
    ``nornir_salt.plugins.tasks.network.ping`` Nornir-Salt
    function.

    Sample Usage::

        salt nrp1 nr.network resolve_dns ipv4=True ipv6=False servers='["8.8.8.8", "1.1.1.1"]'
        salt nrp1 nr.network ping count=10 df=true size=1000 timeout=1 interval=0.1

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.network",
            arg=["resolve_dns"],
        )
    """
    kwargs = {k: v for k, v in kwargs.items() if not k.startswith("__")}
    kwargs["call"] = fun
    return __proxy__["nornir.execute_job"](
        task_fun="nornir_salt.plugins.tasks.network",
        kwargs=kwargs,
        identity=_form_identity(kwargs, "network"),
    )


def service(name, *args, **kwargs):
    """
    Function to interact with services definitions.

    :param name: service name
    :param action: what action to do with service - activate, list, deactivate, verify

    **Service Actions Description**

    ``activate`` - implements service into the network

    Sample usage:

        salt nrp1 nr.service ntp apply
    """
    return "nr.service not implemented"
