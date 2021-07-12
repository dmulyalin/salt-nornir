.. _salt_nornir_examples:

Examples
########

.. contents:: :local:

Doing one-liner configuration changes
=====================================

With NAPALM plugin::

    salt nrp1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2"
    
Make sure that device configured accordingly and NAPALM can interact with it, e.g. SCP server enabled on Cisco IOS.

With Netmiko plugin::

    salt nrp1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" plugin=netmiko
    
With Scrapli plugin::

    salt nrp1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" plugin=scrapli
    
Make sure that Scrapli library installed on minion machine and hosts' connection options specified in 
inventory, e.g.::

    hosts:
      IOL1:
        hostname: 192.168.217.10
        platform: ios
        groups: [lab]
        connection_options:
          scrapli:
            platform: cisco_iosxe
            port: 22
            extras:
              ssh_config_file: True
              auth_strict_key: False

Using JINJA2 templates to generate and apply configuration
==========================================================

Going to take data defined in pillar file ``/etc/salt/pillar/nrp1.sls``::

    hosts:
      IOL1:
        hostname: 192.168.217.10
        platform: ios
        groups: [lab]
        data:
          syslog: ["1.1.1.1", "2.2.2.2"]
      IOL2:
        hostname: 192.168.217.7
        platform: ios
        groups: [lab]
        data:
          syslog: ["1.1.1.2", "2.2.2.1"]

    groups: 
      lab:
        username: nornir
        password: nornir

And combine it with template file ``/etc/salt/template/nr_syslog_cfg.j2``::

    hostname {{ host.name }}
    !
    {%- for server in host.syslog %}
    logging host {{ server }}
    {%- endfor %}
    
.. note:: Hosts' data injected in templates under ``host`` variable.

First, let's only generate configuration using ``nr.cfg_gen`` function without applying it to devices::

    [root@localhost /]# salt nrp1 nr.cfg_gen filename=salt://templates/nr_syslog_cfg.j2
    nrp1:
        ----------
        IOL1:
            ----------
            Rendered salt://templates/nr_syslog_cfg.j2 config:
                hostname IOL1
                !
                logging host 1.1.1.1
                logging host 2.2.2.2
        IOL2:
            ----------
            Rendered salt://templates/nr_syslog_cfg.j2 config:
                hostname IOL2
                !
                logging host 1.1.1.2
                logging host 2.2.2.1
    [root@localhost /]# 
    
Configuration looks ok, should be fine to apply it to devices::

    [root@localhost /]# salt nrp1 nr.cfg filename=salt://templates/nr_syslog_cfg.j2 plugin=netmiko
    nrp1:
        ----------
        IOL1:
            ----------
            netmiko_send_config:
                ----------
                changed:
                    True
                diff:
                exception:
                    None
                failed:
                    False
                result:
                    configure terminal
                    Enter configuration commands, one per line.  End with CNTL/Z.
                    IOL1(config)#hostname IOL1
                    IOL1(config)#!
                    IOL1(config)#logging host 1.1.1.1
                    IOL1(config)#logging host 2.2.2.2
                    IOL1(config)#end
        IOL2:
            ----------
            netmiko_send_config:
                ----------
                changed:
                    True
                diff:
                exception:
                    None
                failed:
                    False
                result:
                    IOL2#configure terminal
                    IOL2(config)#hostname IOL2
                    IOL2(config)#!
                    IOL2(config)#logging host 1.1.1.2
                    IOL2(config)#logging host 2.2.2.1
                    IOL2(config)#end
                    IOL2#
    
Verify configuration applied::

    [root@localhost /]# salt nrp1 nr.cli "show run | inc logging"
    nrp1:
        ----------
        IOL1:
            ----------
            show run | inc logging:
                logging host 1.1.1.1
                logging host 2.2.2.2
        IOL2:
            ----------
            show run | inc logging:
                logging host 1.1.1.2
                logging host 2.2.2.1
             

Using Nornir state module to do configuration changes
=====================================================

Salt master configuration defining base environment pillar and states location,
file ``/etc/salt/master`` snippet::

    ...
    file_roots:
      base:
        - /etc/salt
        - /etc/salt/states
    
    pillar_roots:
      base:
        - /etc/salt/pillar
    ...

Define data in pillar file ``/etc/salt/pillar/nrp1.sls``::

    hosts:
      IOL1:
        hostname: 192.168.217.10
        platform: ios
        groups: [lab]
        data:
          syslog: ["1.1.1.1", "2.2.2.2"]
      IOL2:
        hostname: 192.168.217.7
        platform: ios
        groups: [lab]
        data:
          syslog: ["1.1.1.2", "2.2.2.1"]

    groups: 
      lab:
        username: nornir
        password: nornir

Content of jinja2 template used with state to configure syslog servers,
file ``salt://templates/nr_syslog_cfg.j2`` or same as
absolute path ``/etc/salt/template/nr_syslog_cfg.j2``::

    hostname {{ host.name }}
    !
    {%- for server in host.syslog %}
    logging host {{ server }}
    {%- endfor %}

Content of state file ``/etc/salt/states/nr_cfg_syslog_and_ntp_state.sls``::

    # apply logging configuration using jinja2 template
    configure_logging:
      nr.cfg:
        - filename: salt://templates/nr_syslog_cfg.j2
        - plugin: netmiko
        
    # apply NTP servers configuration using inline commands
    configure_ntp:
      nr.task:
        - plugin: nornir_netmiko.tasks.netmiko_send_config
        - config_commands: ["ntp server 7.7.7.7", "ntp server 7.7.7.8"]
        
    # save configuration using netmiko_save_config task plugin
    save_configuration:
      nr.task:
        - plugin: nornir_netmiko.tasks.netmiko_save_config

Run ``state.apply`` command to apply state to devices::

    [root@localhost /]# salt nrp1 state.apply nr_cfg_syslog_and_ntp_state
    nrp1:
    ----------
              ID: configure_logging
        Function: nr.cfg
          Result: True
         Comment: 
         Started: 12:45:41.339857
        Duration: 2066.863 ms
         Changes:   
                  ----------
                  IOL1:
                      ----------
                      netmiko_send_config:
                          ----------
                          changed:
                              True
                          diff:
                          exception:
                              None
                          failed:
                              False
                          result:
                              configure terminal
                              Enter configuration commands, one per line.  End with CNTL/Z.
                              IOL1(config)#hostname IOL1
                              IOL1(config)#!
                              IOL1(config)#logging host 1.1.1.1
                              IOL1(config)#logging host 2.2.2.2
                              IOL1(config)#end
                  IOL2:
                      ----------
                      netmiko_send_config:
                          ----------
                          changed:
                              True
                          diff:
                          exception:
                              None
                          failed:
                              False
                          result:
                              configure terminal
                              Enter configuration commands, one per line.  End with CNTL/Z.
                              IOL2(config)#hostname IOL2
                              IOL2(config)#!
                              IOL2(config)#logging host 1.1.1.2
                              IOL2(config)#logging host 2.2.2.1
                              IOL2(config)#end
                              IOL2#
    ----------
              ID: configure_ntp
        Function: nr.task
          Result: True
         Comment: 
         Started: 12:45:43.407745
        Duration: 717.144 ms
         Changes:   
                  ----------
                  IOL1:
                      ----------
                      nornir_netmiko.tasks.netmiko_send_config:
                          
                          IOL1#configure terminal
                          IOL1(config)#ntp server 7.7.7.7
                          IOL1(config)#ntp server 7.7.7.8
                          IOL1(config)#end
                  IOL2:
                      ----------
                      nornir_netmiko.tasks.netmiko_send_config:
                          configure terminal
                          Enter configuration commands, one per line.  End with CNTL/Z.
                          IOL2(config)#ntp server 7.7.7.7
                          IOL2(config)#ntp server 7.7.7.8
                          IOL2(config)#end
                          IOL2#
    ----------
              ID: save_configuration
        Function: nr.task
          Result: True
         Comment: 
         Started: 12:45:44.126463
        Duration: 573.964 ms
         Changes:   
                  ----------
                  IOL1:
                      ----------
                      nornir_netmiko.tasks.netmiko_save_config:
                          write mem
                          Building configuration...
                          [OK]
                          IOL1#
                  IOL2:
                      ----------
                      nornir_netmiko.tasks.netmiko_save_config:
                          write mem
                          Building configuration...
                            [OK]
                          IOL2#
    
    Summary for nrp1
    ------------
    Succeeded: 3 (changed=3)
    Failed:    0
    ------------
    Total states run:     3
    Total run time:   3.358 s
    [root@localhost /]#

Sending Nornir stats to Elasticsearch and visualizing in Grafana
================================================================

To send stats about Nornir proxy operation using returners need to define 
scheduler to periodically call ``nr.stats`` function using returner of choice.

Scheduler configuration in proxy minion pillar file ``/etc/salt/pillar/nrp1.sls``::

    schedule:
      stats_to_elasticsearch:
        function: nr.stats
        seconds: 60
        return_job: False
        returner: elasticsearch
        
Sample Elasticsearch cluster configuration defined in Nornir Proxy minion pillar,
file ``/etc/salt/pillar/nrp1.sls``::

    elasticsearch:
      host: '10.10.10.100:9200'
      
Reference 
`documentation <https://docs.saltproject.io/en/latest/ref/modules/all/salt.modules.elasticsearch.html#module-salt.modules.elasticsearch>`_ 
for more details on Elasticsearch returner and module configuration.

If all works well, should see new ``salt-nr_stats-v1`` indice created in Elasticsearch database::

    [root@localhost ~]# curl 'localhost:9200/_cat/indices?v'
    health status index                    uuid                   pri rep docs.count docs.deleted store.size pri.store.size
    green  open   salt-nr_stats-v1         p4w66-12345678912345   1   0      14779            0      6.3mb          6.3mb
    
Sample document entry::

    [root@localhost ~]# curl -XGET 'localhost:9200/salt-nr_stats-v1/_search?pretty' -H 'Content-Type: application/json' -d '
    > {
    > "size" : 1,
    > "query": {
    > "match_all": {}
    > },
    > "sort" : [{"@timestamp":{"order": "desc"}}]
    > }'
    {
      "took" : 774,
      "timed_out" : false,
      "_shards" : {
        "total" : 1,
        "successful" : 1,
        "skipped" : 0,
        "failed" : 0
      },
      "hits" : {
        "total" : {
          "value" : 10000,
          "relation" : "gte"
        },
        "max_score" : null,
        "hits" : [
          {
            "_index" : "salt-nr_stats-v1",
            "_type" : "default",
            "_id" : "12345678",
            "_score" : null,
            "_source" : {
              "@timestamp" : "2021-02-13T22:56:53.294947+00:00",
              "success" : true,
              "retcode" : 0,
              "minion" : "nrp1",
              "fun" : "nr.stats",
              "jid" : "20210213225653251137",
              "counts" : { },
              "data" : {
                "proxy_minion_id" : "nrp1",
                "main_process_is_running" : 1,
                "main_process_start_time" : 1.6131744901391668E9,
                "main_process_start_date" : "Sat Feb 13 11:01:30 2021",
                "main_process_uptime_seconds" : 82523.12118172646,
                "main_process_ram_usage_mbyte" : 151.26,
                "main_process_pid" : 17031,
                "main_process_host" : "vm1.lab.local",
                "jobs_started" : 1499,
                "jobs_completed" : 1499,
                "jobs_failed" : 0,
                "jobs_job_queue_size" : 0,
                "jobs_res_queue_size" : 0,
                "hosts_count" : 12,
                "hosts_connections_active" : 38,
                "hosts_tasks_failed" : 0,
                "timestamp" : "Sun Feb 14 09:56:53 2021",
                "watchdog_runs" : 2748,
                "watchdog_child_processes_killed" : 6,
                "watchdog_dead_connections_cleaned" : 0,
                "child_processes_count" : 0
              }
            },
            "sort" : [
              1613257013294
            ]
          }
        ]
      }
    }

Elasticsearch can be polled with Grafana to visualize stats, reference 
`Grafana documentation <https://grafana.com/docs/grafana/latest/datasources/elasticsearch/>`_ 
for details.

Using runner to work with inventory information and search for hosts
====================================================================

**Problem** - have 100 Nornir Proxy Minions managing 10000 devices, how do I know which
device managed by which proxy.

**Solution** - Nornir runner ``nr.inventory`` function can be used to present brief summary
about hosts::

    # find which Nornir Proxy minion manages IOL1 device
    [root@localhost /]# salt-run nr.inventory IOL1
    +---+--------+----------+----------------+----------+--------+
    |   | minion | hostname |       ip       | platform | groups |
    +---+--------+----------+----------------+----------+--------+
    | 0 |  nrp1  |   IOL1   | 192.168.217.10 |   ios    |  lab   |
    +---+--------+----------+----------------+----------+--------+

    # or produce JIRA style table report about all hosts
    [root@localhost /]# salt-run nr.inventory FB="*" tk='{"tablefmt": "jira"}'
    || minion   || hostname   || ip             || platform   || groups   ||
    | nrp1     | IOL1       | 192.168.217.10 | ios        | lab      |
    | nrp1     | IOL2       | 192.168.217.7  | ios        | lab      |


Calling task plugins using nr.task
==================================

Any task plugin supported by Nornir can be called using ``nr.task`` execution 
module function providing that plugins installed and can be imported. 

For instance calling task::

    salt nrp1 nr.task "nornir_netmiko.tasks.netmiko_save_config"

internally is equivalent to running this code::

    from nornir_netmiko.tasks import netmiko_save_config
    
    result = nr.run(task=netmiko_save_config, *args, **kwargs)

where ``args`` and ``kwargs`` are arguments (if any) supplied on cli.

Targeting devices behind Nornir proxy
=====================================

Nornir uses ``mornir_salt`` package to provide targeting capabilities built on top of
Nornir module itself. Because of that it is good to read 
`this <https://nornir-salt.readthedocs.io/en/latest/Functions.html#ffun>`_
documentation notes first.

Combining SALT and nornir_salt targeting capabilities can help to address various usecase.

Examples::

    # targeting all devices behind Nornir proxies:
    salt -I "proxy:proxytype:nornir" nr.cli "show clock" FB="*"
    
    # target all Cisco IOS devices behind all Nornir proxies
    salt -I "proxy:proxytype:nornir" nr.cli "show clock" FO='{"platform": "ios"}'

    # target all Cisco IOS or NXOS devices behind all Nornir proxies
    salt -I "proxy:proxytype:nornir" nr.cli "show clock" FO='{"platform__any": ["ios", "nxos_ssh"]}'
    
    # targeting All Nornir Proxies with ``LON`` in name and all hosts behind them that has ``core`` in their name
    salt "*LON*" nr.cli "show clock" FB="*core*"
    
    # targeting all hosts that has name ending with ``accsw1``
    salt -I "proxy:proxytype:nornir" nr.cli "show clock" FB="*accsw1"
    
By default Nornir does not use any filtering and simply run task against all devices, 
there is Nornir proxy minion configuration ``nornir_filter_required`` parameter exists 
to alter behavior to opposite resulting in error if no ``Fx`` filter provided.

Saving results to files
=======================

``ToFileProcessor`` distributed with ``nornir_salt`` package can be used to save execution 
module functions results to the file system of machine where proxy-minion process running.

Sample usage::

    [root@localhost /]# salt nrp1 nr.cli "show clock" "show ip int brief" tf="show_commands_output"
    nrp1:
        ----------
        IOL1:
            ----------
            show clock:
                *12:05:06.633 EET Sun Feb 14 2021
            show ip int brief:
                Interface                  IP-Address      OK? Method Status                Protocol
                Ethernet0/0                unassigned      YES NVRAM  up                    up      
                Ethernet0/0.102            10.1.102.10     YES NVRAM  up                    up      
                Ethernet0/0.107            10.1.107.10     YES NVRAM  up                    up      
                Ethernet0/0.2000           192.168.217.10  YES NVRAM  up                    up      
                Ethernet0/1                unassigned      YES NVRAM  up                    up      
                Ethernet0/2                unassigned      YES NVRAM  up                    up      
                Ethernet0/3                unassigned      YES NVRAM  administratively down down    
                Loopback0                  10.0.0.10       YES NVRAM  up                    up      
                Loopback100                1.1.1.100       YES NVRAM  up                    up      
        IOL2:
            ----------
            show clock:
                *12:05:06.605 EET Sun Feb 14 2021
            show ip int brief:
                Interface                  IP-Address      OK? Method Status                Protocol
                Ethernet0/0                unassigned      YES NVRAM  up                    up      
                Ethernet0/0.27             10.1.27.7       YES NVRAM  up                    up      
                Ethernet0/0.37             10.1.37.7       YES NVRAM  up                    up      
                Ethernet0/0.107            10.1.107.7      YES NVRAM  up                    up      
                Ethernet0/0.117            10.1.117.7      YES NVRAM  up                    up      
                Ethernet0/0.2000           192.168.217.7   YES NVRAM  up                    up      
                Ethernet0/1                unassigned      YES NVRAM  administratively down down    
                Ethernet0/2                unassigned      YES NVRAM  administratively down down    
                Ethernet0/3                unassigned      YES NVRAM  administratively down down    
                Loopback0                  10.0.0.7        YES NVRAM  up                    up      

    [root@localhost /]# tree /var/salt-nornir/nrp1/files/
    ├── show_commands_output__11_July_2021_07_11_26__IOL1.txt
    ├── show_commands_output__11_July_2021_07_11_26__IOL2.txt
    ├── tf_aliases.json
    
    [root@localhost /]# cat /var/salt-nornir/nrp1/files/show_commands_output__11_July_2021_07_11_26__IOL1.txt
    *12:05:06.633 EET Sun Feb 14 2021
    Interface                  IP-Address      OK? Method Status                Protocol
    Ethernet0/0                unassigned      YES NVRAM  up                    up      
    Ethernet0/0.102            10.1.102.10     YES NVRAM  up                    up      
    Ethernet0/0.107            10.1.107.10     YES NVRAM  up                    up      
    Ethernet0/0.2000           192.168.217.10  YES NVRAM  up                    up      
    Ethernet0/1                unassigned      YES NVRAM  up                    up      
    Ethernet0/2                unassigned      YES NVRAM  up                    up      
    Ethernet0/3                unassigned      YES NVRAM  administratively down down    
    Loopback0                  10.0.0.10       YES NVRAM  up                    up      
    Loopback100                1.1.1.100       YES NVRAM  up                    up      
