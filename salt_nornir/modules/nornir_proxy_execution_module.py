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
   * - `match`_
     - Filters text output using Nornir-Salt DataProcessor match function
   * - `ntfsm`_
     - Parse nr.cli output using TextFSM ntc-templates
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

SaltStack has `cp module <https://docs.saltproject.io/en/latest/ref/renderers/index.html#renderers>`_,
allowing to download files from Salt Master, ``donwload`` keyword can be used to indicate
arguments that should download content for.

Keys listed in ``download`` argument ignored by `render`_ argument even if same key contained
with ``render`` argument. Arguemnts names listed in ``donwload`` are not rendered, only loaded
from Salt Master.

Supported functions: ``nr.task, nr.cli, nr.cfg, nr.cfg_gen, nr.nc, nr.do, nr.http``

CLI Arguments:

* ``download`` - list of arguments to download content for, default is ``["run_ttp", "iplkp"]``

For example, to render content for filename argument::

    salt nrp1 nr.cfg filename="salt://templates/logging_config.txt" download='["filename"]'

Primary use cases for this keyword is revolving around enabling or disabling dowloading
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

Nornir Proxy Minion pillar parameter ``event_progress_all`` can be used to control default bhaviour,
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

render
++++++

SaltStack has `renderers system <https://docs.saltproject.io/en/latest/ref/renderers/index.html#renderers>`_,
that system allows to render text files content while having access to all Salt Execution Module
Functions and inventory data.

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

    <group name="interf" input="interfaces">
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

* ``table`` - boolean or table type indicator, supported values: True, ``brief``, ``extend``
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

Sample usage::

    salt nrp1 nr.cfg "logging host 1.1.1.1" tf="logging_config"

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

    salt nrp1 nr.cli "show clock" add_detals=True
    salt nrp1 nr.cli "show clock" add_detals=True to_dict=False

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
function on proxy minion, this could be processing intensive especially for big confiurations
combined with significant number of devices simelteniously returning results.

Execution Module Functions
--------------------------

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
| `nr.nornir`_    | Function to call Nornir Utility Functions         |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.task`_      | Function to run any Nornir task plugin            |                    |
+-----------------+---------------------------------------------------+--------------------+
| `nr.test`_      | Function to test show commands output             | netmiko (default), |
|                 | produced by nr.cli function                       | scrapli            |
+-----------------+---------------------------------------------------+--------------------+
| `nr.tping`_     | Function to run TCP ping to devices's hostnames   |                    |
+-----------------+---------------------------------------------------+--------------------+

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

nr.nornir
+++++++++

.. autofunction:: salt_nornir.modules.nornir_proxy_execution_module.nornir_fun

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
import os
import traceback
import fnmatch
import uuid
import time

log = logging.getLogger(__name__)


# import salt libs, wrapping it in try/except for docs to generate
try:
    from salt.exceptions import CommandExecutionError
except:
    log.error("Nornir Execution Module - failed importing SALT libraries")

# import nornir libs
try:
    from nornir_salt.plugins.functions import TabulateFormatter, DumpResults

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
    Helper function to form task identity argument, identoty used by nornir
    proxy minion to identify results for tasks submitter to jobs queue.

    :param kwargs: (dict) arguemnts received by Execution Module Function
    :param function_name: (str) Execution Module Function name
    :return: difctionary with uuid4, jid, function_name keys

    If identity already present in kwargs, use it as is.
    """
    return kwargs.pop(
        "identity",
        {
            "uuid4": str(uuid.uuid4()),
            "jid": kwargs.get("__pub_jid"),
            "function_name": "exec.nr.{}".format(function_name),
        },
    )


# -----------------------------------------------------------------------------
# callable module function
# -----------------------------------------------------------------------------


def task(plugin, *args, **kwargs):
    """
    Function to invoke any of supported Nornir task plugins. This function
    performs dynamic import of requested plugin function and executes
    ``nr.run`` using supplied args and kwargs

    :param plugin: (str) ``path.to.plugin.task_fun`` to run ``from path.to.plugin import task_fun``
    :param args: (list) ignored, not used
    :param kwargs: (dict) any additional argument to use with specified task plugin

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

        salt nrp1 nr.task "nornir_napalm.plugins.tasks.napalm_cli" commands='["show ip arp"]' FB="IOL1"
        salt nrp1 nr.task "nornir_netmiko.tasks.netmiko_save_config" add_details=False
        salt nrp1 nr.task "nornir_netmiko.tasks.netmiko_send_command" command_string="show clock"
        salt nrp1 nr.task nr_test a=b c=d add_details=False
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


def cli(*commands, **kwargs):
    """
    Method to retrieve commands output from devices using ``send_command``
    task plugin from either Netmiko or Scrapli library.

    :param commands: (list or str) list of commands or single command
    :param filename: (str) path to file with multiline commands string
    :param kwargs: (dict) any additional arguments to use with specified ``plugin`` send command method
    :param plugin: (str) name of send command task plugin to use - ``netmiko`` (default) or ``scrapli``
      or ``napalm`` or ``pyats``

    Sample Usage::

         salt nrp1 nr.cli "show clock" "show run" FB="IOL[12]" use_timing=True delay_factor=4
         salt nrp1 nr.cli commands='["show clock", "show run"]' FB="IOL[12]"
         salt nrp1 nr.cli "show clock" FO='{"platform__any": ["ios", "nxos_ssh", "cisco_xr"]}'
         salt nrp1 nr.cli commands='["show clock", "show run"]' FB="IOL[12]" plugin=napalm

    Commands can be templates and rendered using Jinja2 Templating Engine::

         salt nrp1 nr.cli "ping 1.1.1.1 source {{ host.lo0 }}"

    Commands to run on devices can be sourced from text file on Salt Master, that text file can also be a
    template and rendered using SaltStack rendering system::

         salt nrp1 nr.cli filename="salt://device_show_commands.txt"

    Combining above two features we can supply per-host commands like this::

         salt nrp1 nr.cli filename="salt://{{ host.name }}_show_commands.txt"

    Where ``{{ host.name }}_show_commands.txt`` faile can be a template as well.

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
    commands = kwargs.pop("commands", commands)
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
    else:
        return "Unsupported plugin name: {}".format(plugin)
    # run commands task
    result = __proxy__["nornir.execute_job"](
        task_fun=task_fun, kwargs=kwargs, identity=_form_identity(kwargs, "cli")
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
    :param plugin: (str) name of configuration task plugin to use - ``napalm`` (default) or ``netmiko``
        or ``scrapli`` or ``pyats``
    :param dry_run: (bool) default False, controls whether to apply changes to device or simulate them
    :param commit: (bool or dict) by default commit is ``True``. With ``netmiko`` plugin
        dictionary ``commit`` argument supplied to commit call using ``**commit``

    .. warning:: ``dry_run`` not supported by ``netmiko`` and ``pyats`` plugins

    .. warning:: ``commit`` not supported by ``scrapli`` and ``pyats`` plugins. To commit need to send commit
        command as part of configuration, moreover, scrapli will not exit configuration mode,
        need to send exit command as part of configuration commands as well.

    For configuration rendering purposes, in addition to normal `context variables
    <https://docs.saltstack.com/en/latest/ref/states/vars.html>`_
    template engine loaded with additional context variable `host`, to access Nornir host
    inventory data.

    Sample usage::

        salt nrp1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" FB="R[12]" dry_run=True
        salt nrp1 nr.cfg commands='["logging host 1.1.1.1", "ntp server 1.1.1.2"]' FB="R[12]"
        salt nrp1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" plugin="netmiko"
        salt nrp1 nr.cfg filename=salt://template/template_cfg.j2 FB="R[12]"
        salt nrp1 nr.cfg filename=salt://template/cfg.j2 FB="XR-1" commit='{"confirm": True}'

    Filename argument can be a template string, for instance::

        salt nrp1 nr.cfg filename=salt://templates/{{ host.name }}_cfg.txt

    In that case filename rendered to form path string, after that, path string used to download file
    from master, downloaded file further rendered using specified template engine (Jinja2 by default).
    That behavior supported only for filenames that start with ``salt://``. This feature allows to
    specify per-host configuration files for applying to devices.

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
    kwargs.setdefault("render", ["commands", "filename"])
    # get configuration commands
    commands = [commands] if isinstance(commands, str) else commands
    if any(commands):
        kwargs.setdefault("commands", commands)
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
    else:
        return "Unsupported plugin name: {}".format(plugin)
    # work and return results
    return __proxy__["nornir.execute_job"](
        task_fun=task_fun, kwargs=kwargs, identity=_form_identity(kwargs, "cfg")
    )


def cfg_gen(*commands, **kwargs):
    """
    Function to render configuration from template file. No configuration pushed
    to devices.

    This function can be useful to stage/test templates or to generate configuration
    without pushing it to devices.

    :param filename: (str) path to template
    :param template_engine: (str) template engine to render configuration, default is jinja
    :param saltenv: (str) name of SALT environment
    :param context: Overrides default context variables passed to the template.
    :param defaults: Default context passed to the template.

    For configuration rendering purposes, in addition to normal `context variables
    <https://docs.saltstack.com/en/latest/ref/states/vars.html>`_
    template engine loaded with additional context variable `host`, to access Nornir host
    inventory data.

    Sample usage::

        salt nrp1 nr.cfg_gen filename=salt://templates/template.j2 FB="R[12]"

    Sample template.j2 content::

        proxy data: {{ pillar.proxy }}
        jumphost_data: {{ host["jumphost"] }}
        hostname: {{ host.name }}
        platform: {{ host.platform }}

    Filename argument can be a template string, for instance::

        salt nrp1 nr.cfg_gen filename="salt://template/{{ host.name }}_cfg.txt"

    In that case filename rendered to form path string, after that, path string used to download file
    from master, downloaded file further rendered using specified template engine (Jinja2 by default).
    That behaviour supported only for filenames that start with ``salt://``. This feature allows to
    specify per-host configuration files for applying to devices.

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
    kwargs.setdefault("render", ["commands", "filename"])
    # get configuration commands
    commands = [commands] if isinstance(commands, str) else commands
    if any(commands):
        kwargs.setdefault("commands", commands)
    # work and return results
    return __proxy__["nornir.execute_job"](
        task_fun="nornir_salt.plugins.tasks.salt_cfg_gen",
        kwargs=kwargs,
        identity=_form_identity(kwargs, "cfg_gen"),
    )


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


def test(*args, **kwargs):
    """
    Function to perform tests for certain criteria against show commands output
    from devices obtained using ``nr.cli`` function.

    ``nr.test`` function related arguments

    :param name: (str) descriptive name of the test, will be added to results
    :param test: (str) type of test to do e.g.: contains, !contains, equal, custom etc.
    :param pattern: (str) pattern to use for testing, usually string, text or
        reference a text file on salt master. For instance if ``test`` is ``contains``,
        ``pattern`` value used as a pattern for containment check.
    :param function_file: (str) path to text file on salt master with function content
        to use for ``custom`` function test
    :param saltenv: (str) name of salt environment to downoad function_file from
    :param suite: (list or str) list of dictionaries with test items or path to file on
        salt-master with a list of test item dictionaries
    :param subset: (list or str) list or string with comma separated glob patterns to
        match tests' names to execute. Patterns are not case-sensitive. Uses
        ``fnmatch.fnmatch`` Python built-in function to do matching.
    :param dump: (str) filegroup name to dump results using Nornir-salt ``DumpResults``
    :param kwargs: (dict) any additional arguments to use with test function

    ``nr.cli`` function related arguments

    :param commands: (str or list) single command or list of commands to get from device
    :param plugin: (str) plugin name to use with ``nr.cli`` function to gather output
        from devices - ``netmiko`` (default) or ``scrapli``
    :param use_ps: (bool) default is False, if True use netmiko plugin experimental
        ``PromptlesS`` method to collect output from devices
    :param cli: (dict) any additional arguments to pass on to ``nr.cli`` function

    Nornir-Salt ``TestsProcessor`` plugin related arguments

    :param failed_only: (bool) default is False, if True ``nr.test`` returns result for
        failed tests only
    :param remove_tasks: (bool) default is True, if False results will include other
        tasks output as well e.g. show commands output. By default results only contain
        tests results.

    Nornir-Salt ``TabulateFormatter`` function related arguments

    :param table: (bool, str or dict) dictionary of arguments or table type indicator e.g. "brief" or True
    :param headers: (list) list of headers to output table for
    :param sortby: (str) Name of comlun name to sort table by
    :param reverse: (bool) reverse table on True, default is False

    Sample usage with inline arguments::

        salt np1 nr.test "show run | inc ntp" contains "1.1.1.1" FB="*host-1"
        salt np1 nr.test "show run | inc ntp" contains "1.1.1.1" --output=table
        salt np1 nr.test "show run | inc ntp" contains "1.1.1.1" table=brief
        salt np1 nr.test commands='["show run | inc ntp"]' test=contains pattern="1.1.1.1"

    Sample usage with a suite of test cases::

        salt np1 nr.test suite=salt://tests/suite_1.txt
        salt np1 nr.test suite=salt://tests/suite_1.txt table=brief
        salt np1 nr.test suite=salt://tests/suite_1.txt table=brief subset="config_test*,rib_check*"

    Where ``salt://tests/suite_1.txt`` content is::

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

    Each item in a test suite executed individually one after another.

    In test suite, ``task`` argument can reference a list of tasks/commands.

    Commands output for each item in a suite collected using ``nr.cli`` function, arguments under
    ``cli`` keyword passed on to ``nr.cli`` function.

    List of arguments in a test suite that can reference text file on salt master using
    ``salt://path/to/file.txt``:

    * ``pattern`` - content of the file rendered and used to run the tests together with
      ``ContainsTest``, ``ContainsLinesTest`` or ``EqualTest`` test functions
    * ``schema`` - used with ``CerberusTest`` test function
    * ``function_file`` - content of the file used with ``CustomFunctionTest`` as ``function_text`` argument

    Starting with Salt-Nornir 0.7.0 support added for ``wait_timeout`` and ``wait_interval`` test item arguments to
    control the behaviour of waiting for test's ``success`` to eveluate to True following these rules:

    1. If ``wait_timeout`` given, keep executing test until result's ``success`` evaluates to True or ``wait_timeout`` expires
    2. Between test item execution attempts sleep for ``wait_interval``, default is 10 seconds
    3. If ``wait_timeout`` expires, return results for last test execution attempt, after updating ``exception``, ``failed``
       and ``success`` fields accordingly

    For example, test below will keep executing for 60 seconds with 20 seconds interval until "show ip route"
    output contains "1.1.1.1/32" pattern for hosts R1 and R2::

        - task: "show ip route"
          test: contains
          pattern: "1.1.1.1/32"
          name: "Check if has 1.1.1.1/32 route"
          wait_timeout: 60
          wait_interval: 20
          cli:
            FL: ["R1", "R2"]

    .. warning:: for ``wait_timeout`` feature to work, test result must contain ``success`` field,
       otherwise test outcome evaluates to False.
    """
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
    sortby = kwargs.pop("sortby", None)  # table
    reverse = kwargs.pop("reverse", False)  # table
    dump = kwargs.pop("dump", False)  # dump final test results
    test_results = []
    filtered_suite = []
    cli_not_command_tasks = ["run_ttp"]

    # check if need to download pattern file from salt master
    if pattern.startswith("salt://"):
        pattern = __salt__["cp.get_file_str"](pattern, saltenv=saltenv)

    # if test suite provided, download it from master and render it
    if isinstance(suite, str) and suite.startswith("salt://"):
        suite_name = suite
        suite = __salt__["slsutil.renderer"](suite)
        if not suite:
            raise CommandExecutionError(
                "Suite file '{}' not on master; path correct?".format(suite_name)
            )
    # if test suite is a list use it as is
    elif isinstance(suite, list) and suite != []:
        pass
    # use inline test and commands
    elif test and commands:
        suite.append(
            {
                "test": test,
                "task": commands[0] if len(commands) == 1 else commands,
                "name": name,
                **{k: v for k, v in kwargs.items() if not str(k).startswith("__")},
            }
        )
    else:
        raise CommandExecutionError("No test suite or inline test&commands provided.")

    # filter suite items and check if need to dowload any files from master
    for item in suite:
        # check if need to filter test case
        if subset and not any(map(lambda m: fnmatch.fnmatch(item["name"], m), subset)):
            continue

        # check if item contains task to do
        if "task" not in item:
            log.warning(
                "nr.test skipping test item as it has no 'task' defined: {}".format(
                    item
                )
            )
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
        wait_timeout = int(test_item.get("wait_timeout", 0))
        wait_interval = int(test_item.get("wait_interval", 10))
        # form arguments for nr.cli call
        cli_keys = [
            "failed_only",
            "remove_tasks",
            "plugin",
            "event_failed",
            "event_progress",
            "use_ps",
        ]
        cli_kwargs = {
            "add_details": kwargs.get("add_details", True),
            **{k: v for k, v in kwargs.items() if k.startswith("F") or k in cli_keys},
            **test_item.pop("cli", {}),
            "to_dict": False,
            "tests": [test_item],
            "identity": _form_identity(kwargs, "test"),
        }
        # check if task is not command e.g. "task: run_ttp"
        if test_item["task"] not in cli_not_command_tasks:
            cli_kwargs["commands"] = test_item["task"]
        # implement wait protocol
        if wait_timeout > 0:
            log.debug(
                "nr.test running nr.cli -'{}', with wait_timeout '{}s'".format(
                    cli_kwargs, wait_timeout
                )
            )
            stime = time.time()
            test_run_attempts = 0
            while (time.time() - stime) < wait_timeout:
                res = cli(**cli_kwargs)
                test_run_attempts += 1
                if all([i.get("success", False) for i in res]):
                    test_results.extend(res)
                    break
                time.sleep(wait_interval)
            else:
                for i in res:
                    i[
                        "exception"
                    ] = "{}s wait timeout expired; test run attempts {}\n{}".format(
                        wait_timeout, test_run_attempts, str(i.get("exception", ""))
                    )
                    i["failed"] = True
                    i["success"] = False
                test_results.extend(res)
        else:
            log.debug("nr.test running nr.cli -'{}'".format(cli_kwargs))
            test_results.extend(cli(**cli_kwargs))

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


def nc(*args, **kwargs):
    """
    Function to interact with devices using NETCONF protocol utilising
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

    Special ``call`` arguments/methods:

    * ``dir`` - returns methods supported by Ncclient connection manager object::

        salt nrp1 nr.nc dir

    * ``help`` - returns ``method_name`` docstring::

        salt nrp1 nr.nc help method_name=edit_config

    * ``transaction`` - same as ``edit_config``, but runs this (presumably more reliable) work flow:

        1. Lock target configuration datastore
        2. If client and server supports it - Discard previous changes if any
        3. Edit configuration
        4. If client and server supports it - validate configuration if ``validate`` argument is True
        5. If client and server supports it - do commit confirmed if ``confirmed`` argument is True
        6. If client and server supports it - do commit operation
        7. Unlock target configuration datastore
        8. If client and server supports it - discard all changes if any of steps 3, 4, 5 or 6 fail
        9. Return results list of dictionaries keyed by step name

        If any of steps 3, 4, 5, 6 fail, all changes discarded.

        Sample usage::

            salt nrp1 nr.nc transaction target="candidate" config="salt://path/to/config_file.xml" FB="*core-1"

    .. warning:: beware of difference in keywords required by different plugins, e.g. ``filter`` for ``ncclient``
      vs ``filter_``/``filters`` for ``scrapli_netconf``, consrefer to  modules' api documentation for required
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
    kwargs = {**default_kwargs, **kwargs}
    plugin = kwargs.pop("plugin", "ncclient")
    # decide on plugin to use
    if plugin.lower() == "ncclient":
        task_fun = "nornir_salt.plugins.tasks.ncclient_call"
        kwargs["connection_name"] = "ncclient"
    elif plugin.lower() == "scrapli":
        task_fun = "nornir_salt.plugins.tasks.scrapli_netconf_call"
        kwargs["connection_name"] = "scrapli_netconf"
    else:
        return "Unsupported plugin name: {}".format(plugin)
    # run task
    return __proxy__["nornir.execute_job"](
        task_fun=task_fun, kwargs=kwargs, identity=_form_identity(kwargs, "nc")
    )


def do(*args, **kwargs):
    """
    Function to perform steps defined under ``nornir:actions`` configuration
    section at:

    * Minion's configuration
    * Minion's grains
    * Minion's pillar data
    * Master configuration (requires ``pillar_opts`` to be set to True in Minion
      config file in order to work)
    * File on master file system

    To retrieve actions content Salt ``nr.do`` uses ``config.get`` execution module
    function with ``merge`` key set to ``True``.

    Each step definition requires these keywords to be defined:

    * ``function`` - mandatory, name of any execution module function to run
    * ``args`` - optional, any arguments to use with function
    * ``kwargs`` - optional, any keyword arguments to use with function
    * ``description`` - optional, used by ``dir`` to list action description

    Any other keywords defined inside the step are ignored.

    :param stop_on_error: (bool) if True (default) stops execution on error in step,
        continue execution in error if False
    :param filepath: (str) path to file with actions steps
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
        loaded using Saltstack ``slsutil.renderer`` execution module function, as a result
        file can contain any of Saltstack supported renderers content and can be located
        at any url supported by ``cp.get_url`` execution module function. File content must
        render to a dictionary keyed by actions names.

    Sample actions steps definition using proxy minion pillar::

        nornir:
          actions:
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

    Sample actions steps definition using text file under ``filepath``::

        awr:
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
            description: "3. Cllect ntp configuration"

    Action name ``awr`` has single step defined, while ``configure_ntp`` action has multiple
    steps defined, each executed in order.

    Multiple actions names can be supplied to ``nr.do`` call.

    .. warning:: having column ``:`` as part of action name not premitted, as ``:`` used by
        Salt ``config.get`` execution module function to split arguments on path items.

    Sample usage::

        salt nrp1 nr.do dir
        salt nrp1 nr.do dir_list
        salt nrp1 nr.do awr
        salt nrp1 nr.do configure_ntp awr stop_on_error=False
        salt nrp1 nr.do configure_ntp FB="*core*" add_details=True
        salt nrp1 nr.do awr filepath="salt://actions/actions_file.txt"

    Sample Python API usage from Salt-Master::

        import salt.client
        client = salt.client.LocalClient()

        task_result = client.cmd(
            tgt="nrp1",
            fun="nr.do",
            arg=["configure_ntp", "awr"],
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
            __salt__["config.get"](key="nornir:actions", merge="recurse")
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
                    key="nornir:actions:{}".format(action_name), merge="recurse"
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


def http(*args, **kwargs):
    """
    HTTP requests related functions

    :param method: (str) HTTP method to use
    :param url: (str) full or partial URL to send request to
    :param kwargs: (dict) any other kwargs to use with requests.<method> call

    This function uses nornir_salt http_call task plugin, reference that task
    plugin diocumentation for additional details.

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


def file(*args, **kwargs):
    """
    Function to manage Nornir-salt files.

    :param call: (str) files task to call - ls, rm, read, diff
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
    kwargs["call"] = kwargs.pop("call", args[0])
    kwargs["identity"] = _form_identity(kwargs, "file")
    kwargs["filegroup"] = kwargs.pop(
        "filegroup", list(args[1:]) if len(args) >= 2 else None
    )
    if kwargs["call"] in ["ls", "rm"]:
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

    return task(
        plugin="nornir_salt.plugins.tasks.files",
        base_url=__proxy__["nornir.nr_data"]("files_base_path"),
        index=__proxy__["nornir.nr_data"]("stats")["proxy_minion_id"],
        render=[],
        **kwargs,
    )


def learn(*args, **kwargs):
    """
    Store task execution results to local filesystem on the minion using
    ``tf`` (to filename) attribute to form filenames.

    :param fun: (str) name of execution module function to call
    :param tf: (str) ``ToFileProcessor`` filegroup name
    :param args: (list) execution module function arguments
    :param kwargs: (dict) execution module function key-word arguments

    This task uses ``ToFileProcessor`` to store results and is a shortcut
    to calling individual exection module functions with ``tf`` argument.

    Supported exection module functions are ``cli, nc, do, http``. By default
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
    supported_functions = ["cli", "do", "http", "nc"]
    fun = kwargs.pop("fun", "do")
    kwargs["tf"] = True if fun == "do" else kwargs.get("tf")
    kwargs["identity"] = _form_identity(
        kwargs, "learn.{}".format(".".join(args) if fun == "do" else fun)
    )

    # run sanity checks
    if fun not in supported_functions:
        raise RuntimeError(
            "salt-nornir:learn unsupported function '{}', supported '{}'".format(
                fun, supported_functions
            )
        )
    if not kwargs.get("tf"):
        raise RuntimeError("salt-nornir:learn no tf attribute provided")

    # run command with added ToFileProcessor argument
    return globals()[fun](*args, **kwargs)


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
        are criterie to check
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
    # do sanity check
    if not args:
        raise CommandExecutionError(
            "No filegroup  to search in provided - args: '{}', kwargs: '{}'".format(
                args, kwargs
            )
        )

    # form kwargs content
    identity = _form_identity(kwargs, "find")
    kwargs = {k: v for k, v in kwargs.items() if not k.startswith("__")}
    Fx = {
        k: kwargs.pop(k)
        for k in list(kwargs.keys())
        if k.startswith("F") and len(k) == 2
    }

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


def diff(*args, **kwargs):
    """
    Provide difference between current and previously learned information or
    between versions of files stored by ``ToFileProcessor``.

    :param diff: (str) ``ToFileProcessor`` filegroup name
    :param last: (int or list or str) filegroup file indexes to diff, default is 1
    :param kwargs: (dict) any additional kwargs to use with ``nr.file diff``
        call or ``DiffProcessor``

    ``diff`` attribute mandatory.

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


def nornir_fun(fun, *args, **kwargs):
    """
    Function to call various Nornir utility functions.

    :param fun: (str) utility function name to call
    :param kwargs: (dict) function arguments

    Available utility functions:

    * ``test`` - this method tests proxy minion module worker thread without invoking any Nornir code
    * ``refresh`` - re-instantiates Nornir object after retrieving latest pillar data from Salt Master
    * ``kill`` - executes immediate shutdown of Nornir Proxy Minion process and child processes
    * ``shutdown`` - gracefully shutdowns Nornir Proxy Minion process and child processes
    * ``inventory`` - interract with Nornir Process inventory data, using ``InventoryFun`` function
    * ``stats`` - returns statistics about Nornir proxy process, accepts ``stat`` argument of stat
      name to return
    * ``version`` - returns a report of Nornir related packages installed versions
    * ``initialized`` - returns Nornir Proxy Minion initialized status - True or False
    * ``hosts`` - returns a list of hosts managed by this Nornir Proxy Minion, accepts ``Fx``
      arguments to return only hosts matched by filter
    * ``connections`` - list hosts' active connections, accepts ``Fx`` arguments to filter hosts to list
    * ``disconnect`` - close host connections, accepts ``Fx`` arguments to filter hosts and ``conn_name``
      of connection to close, by default closes all connections
    * ``clear_hcache`` - clear task results cache from hosts' data, accepts ``cache_keys`` list argument
      of key names to remove, if no ``cache_keys`` argument provided removes all cached data
    * ``clear_dcache`` - clear task results cache from defaults data, accepts ``cache_keys`` list argument
      of key names to remove, if no ``cache_keys`` argument provided removes all cached data

    Sample Usage::

        salt nrp1 nr.nornir inventory FB="R[12]"
        salt nrp1 nr.nornir inventory create_host name="R1" hostname="1.2.3.4" platform="ios" groups='["lab"]'
        salt nrp1 nr.nornir inventory update_host name="R1" data='{"foo": bar}'
        salt nrp1 nr.nornir inventory read_host FB="R1"
        salt nrp1 nr.nornir inventory call=delete_host name="R1"
        salt nrp1 nr.nornir stats stat="proxy_minion_id"
        salt nrp1 nr.nornir version
        salt nrp1 nr.nornir shutdown
        salt nrp1 nr.nornir clear_hcache cache_keys='["key1", "key2]'
        salt nrp1 nr.nornir clear_dcache cache_keys='["key1", "key2]'

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
        return task(plugin="refresh", identity=_form_identity(kwargs, "nornir.refresh"))
    elif fun == "test":
        return task(plugin="test", identity=_form_identity(kwargs, "nornir.test"))
    elif fun == "hosts":
        return __proxy__["nornir.list_hosts"](**kwargs)
    elif fun == "connections":
        return task(
            plugin="nornir_salt.plugins.tasks.connections",
            call="ls",
            identity=_form_identity(kwargs, "nornir.connections"),
            **kwargs,
        )
    elif fun == "disconnect":
        return task(
            plugin="nornir_salt.plugins.tasks.connections",
            call="close",
            identity=_form_identity(kwargs, "nornir.disconnect"),
            **kwargs,
        )
    elif fun == "clear_hcache":
        return task(
            plugin="nornir_salt.plugins.tasks.salt_clear_hcache",
            identity=_form_identity(kwargs, "nornir.clear_hcache"),
            **kwargs,
        )
    elif fun == "clear_dcache":
        return task(
            plugin="clear_dcache",
            identity=_form_identity(kwargs, "nornir.clear_dcache"),
            **kwargs,
        )
    else:
        return "Uncknown function '{}'.format(fun)"


def gnmi(call, *args, **kwargs):
    """
    Function to interact with devices using gNMI protocol utilising one of supported plugins.

    :param call: (str) (str) connection object method to call or name of one of extra methods
    :param plugin: (str) Name of gNMI plugin to use - pygnmi (default)
    :param method_name: (str) name of method to provide docstring for, used only by ``help`` call
    :param path: (list or str) gNMI path string for ``update``, ``delete``, ``replace`` extra methods calls
    :param filename: (str) path to file with call method arguments content
    :param kwargs: (dict) any additional keyword arguments to use with call method
    :return: method call results

    Available gNMI plugin names:

    * ``pygnmi`` - ``nornir-salt`` built-in plugin that uses `PyGNMI library <https://pypi.org/project/pygnmi/>`_
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

    ``salt://path/to/set_args.txt`` content will render to a dictionary supplied to
    ``set`` call as a ``**kwargs``.

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
    else:
        return "Unsupported plugin name: {}".format(plugin)

    # run task
    return __proxy__["nornir.execute_job"](
        task_fun=task_fun, kwargs=kwargs, identity=_form_identity(kwargs, "gnmi")
    )
