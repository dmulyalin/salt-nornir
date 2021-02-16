Getting started
###############

.. contents:: :local:

Install SALTSTACK
=================

For installation of SALTSTACK master and minion/proxy-minion modules please
reference `official documentation <https://repo.saltproject.io/>`_.

Install Nornir
==============

From PyPi::

    pip install salt_nornir
    
Installing``salt_nornir`` should automatically install these dependencies::

    netmiko>=3.3.2
    nornir>=3.0.0
    nornir_netmiko>=0.1.1
    nornir_napalm>=0.1.1
    nornir_salt>=0.3.0
    napalm>=3.0.0
    psutil

Make sure to update above libraries if required:

* netmiko - ``pip install netmiko --upgrade``
* nornir - ``pip install nornir --upgrade``
* napalm - ``pip install napalm --upgrade``
* nornir_netmiko - ``pip install nornir_netmiko --upgrade``
* nornir_napalm - ``pip install nornir_napalm --upgrade``
* nornir_salt - ``pip install nornir_salt --upgrade``

Configure SALT Master
=====================

Master configuration file located on SALT Master machine - machine where you installed 
``salt-master`` software.

File ``/etc/salt/master``::

    interface: 0.0.0.0 # indicates IP address to listen/use for connections
    master_id: lab_salt_master
    pki_dir: /etc/salt/pki/master
    
    file_roots:
      base:
        - /etc/salt
    
    pillar_roots:
      base:
        - /etc/salt/pillar

Define Proxy Minion pillar configuration
========================================

Pillar files located on SALT Master machine. 

File ``/etc/salt/pillar/nrp1.sls``::

    proxy:
      proxytype: nornir
  
    hosts:
      IOL1:
        hostname: 192.168.217.10
        platform: ios
        groups: [lab]
      IOL2:
        hostname: 192.168.217.7
        platform: ios
        groups: [lab]
        
    groups: 
      lab:
        username: nornir
        password: nornir
              
    defaults: {}
    
File ``/etc/salt/pillar/top.sls``::

    base:
      nrp1: 
        - nrp1

Start SALT Master
=================

Start salt-master process::

    systemctl start salt-master
    systemctl enable salt-master

Verify::

    systemctl status salt-master

Configure Proxy Minion
======================

Proxy minion configuration files located on SALT Minion machine - machine where you installed 
``salt-minion`` software.

File ``/etc/salt/minion``::

    master: 192.168.1.1 # IP address or FQDN of master machine
    multiprocessing: false # default, but overridden in Nornir proxy minion pillar
    mine_enabled: true # not required, but nice to have
    pki_dir: /etc/salt/pki/proxy # not required - this separates the proxy keys into a different directory

Create proxy-minion service.

File ``/etc/systemd/system/salt-proxy@.service``::

    [Unit]
    Description=Salt proxy minion
    After=network.target
    
    [Service]
    Type=simple
    ExecStart=/usr/bin/salt-proxy -l debug --proxyid=%i
    User=root
    Group=root
    Restart=always
    RestartPreventExitStatus=SIGHUP
    RestartSec=5
    
    [Install]
    WantedBy=default.target
    
Start Nornir Proxy Minion process
=================================

Run command to start Nornir Proxy Minion process::

    systemctl start salt-proxy@nrp1.service
    systemctl enable salt-proxy@nrp1.service
    
Verify::

    systemctl status salt-proxy@nrp1.service
    
Or, run in debug mode::

    salt-proxy --proxyid=nrp1 -l debug
    
Accept Proxy Minion key on master
=================================

Run command on salt master machine::

    [root@localhost /]# salt-key
    Accepted Keys:
    Denied Keys:
    Unaccepted Keys:
    nrp1
    Rejected Keys:
    
Accept ``nrp1`` proxy minion key::

    [root@localhost /]# salt-key -a nrp1
    
Start using Nornir Proxy Minion
===============================

Run commands to test nornir proxy minion operations::

    salt nrp1 test.ping # verify that process is running
    salt nrp1 nr.stats # check statistics for Nornir proxy minion
    salt nrp1 nr.task test # test task to verify module operation
    salt nrp1 nr.task nr_test # test task to verify Nornir operation
    salt nrp1 nr.inventory # to check Nornir inventory content
    

Test connectivity to devices::

    [root@localhost /]# salt nrp1 nr.tping 
    nrp1:
        ----------
        IOL1:
            ----------
            nornir_salt.plugins.tasks.tcp_ping:
                ----------
                22:
                    True
        IOL2:
            ----------
            nornir_salt.plugins.tasks.tcp_ping:
                ----------
                22:
                    True
                    
Start interacting with devices::

    [root@localhost /]# salt nrp1 nr.cli "show clock"
    nrp1:
        ----------
        IOL1:
            ----------
            show clock:
                
                *03:03:04.566 EET Sat Feb 13 2021
        IOL2:
            ----------
            show clock:
                *03:03:04.699 EET Sat Feb 13 2021
    
Check documentation for Nornir execution module ``nr.cfg`` function::

    [root@localhost /]# salt nrp1 sys.doc nr.cfg
    nr.cfg:
    
        Function to push configuration to devices using ``napalm_configure`` or
        ``netmiko_send_config`` or Scrapli ``send_config`` task plugin.
    
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
    
        :param add_cpid_to_task_name: boolean, include Child Process ID (cpid) for debugging
    
        Warning: ``dry_run`` not supported by ``netmiko`` plugin
    
        In addition to normal `context variables <https://docs.saltstack.com/en/latest/ref/states/vars.html>`_
        template engine loaded with additional context variable `host`, to access Nornir host
        inventory data.
    
        Sample usage::
    
            salt nornir-proxy-1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" FB="R[12]" dry_run=True
            salt nornir-proxy-1 nr.cfg commands='["logging host 1.1.1.1", "ntp server 1.1.1.2"]' FB="R[12]"
            salt nornir-proxy-1 nr.cfg "logging host 1.1.1.1" "ntp server 1.1.1.2" plugin="netmiko"
            salt nornir-proxy-1 nr.cfg filename=salt://template/template_cfg.j2 FB="R[12]"
            
As example, configure syslog server using Netmiko::

    [root@localhost /]# salt nrp1 nr.cfg "logging host 1.1.1.1" "logging host 1.1.1.2" plugin=netmiko
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
                    IOL1(config)#logging host 1.1.1.1
                    IOL1(config)#logging host 1.1.1.2
                    IOL1(config)#end
                    IOL1#
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
                    IOL2(config)#logging host 1.1.1.1
                    IOL2(config)#logging host 1.1.1.2
                    IOL2(config)#end
                    IOL2#

Additional resources
====================

Reference :ref:`salt_nornir_examples` section for more information on how to use Nornir Proxy Minion.

`SALTSTACK official documentation <https://docs.saltproject.io/en/latest/>`_

Collection of useful SALTSTACK resource `awesome-saltstack <https://github.com/hbokh/awesome-saltstack>`_