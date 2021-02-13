Examples
########

.. contents:: :local:

Doing one-liner configuration changes
=====================================

With NAPALM::

    salt nrp1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2"
    
Make sure that device configured accordingly and NAPALM can interact with it, e.g. SCP server enabled on Cisco IOS.

With Netmiko::

    salt nrp1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" plugin=netmiko
    
With Scrapli::

    salt nrp1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" plugin=scrapli
    
Make sure that host has Scrapli connection options specified in inventory, e.g.::

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

First, let's generate configuration only using ``nr.cfg_gen`` function without applying it to devices::

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

TBD

Sending Nornir stats to Elasticsearch and visualizing in Grafana
================================================================

TBD

Using runner to work with inventory information and search for hosts
====================================================================

TBD

Calling task plugins using nr.task
==================================

TBD

Targeting devices behind Nornir proxy
=====================================

TBD

