Getting started
###############

.. contents:: :local:

Install SALTSTACK
=================

For installation of SALTSTACK master and minion (proxy-minion is part
of minion) modules refer to `official documentation <https://repo.saltproject.io/>`_.

For example, CentOS7 Python3 latest SaltStack installation boils down to these commands:

* Import SaltStack repository key - ``sudo rpm --import https://repo.saltproject.io/py3/redhat/7/x86_64/latest/SALTSTACK-GPG-KEY.pub``
* Add SaltStack repository - ``curl -fsSL https://repo.saltproject.io/py3/redhat/7/x86_64/latest.repo | sudo tee /etc/yum.repos.d/salt.repo``
* Clear yum cache - ``sudo yum clean expire-cache``
* Install master and minion - ``sudo yum install salt-master salt-minion``
* Start salt-master - ``sudo systemctl enable salt-master && sudo systemctl start salt-master``

Install Nornir
==============

From PyPi::

    python3 -m pip install salt_nornir[prodmax]

If it fails due to PyYAML incompatibility try running this command::

    python3 -m pip install salt_nornir[prodmax] --ignore-installed PyYAML

Configure SALT Master
=====================

Master configuration file located on SALT Master machine - machine where you installed
``salt-master`` package.

Backup original master config file - ``mv /etc/salt/master /etc/salt/master.old``
and edit file ``/etc/salt/master``::

    interface: 0.0.0.0 # indicates IP address to listen/use for connections
    master_id: lab_salt_master
    pki_dir: /etc/salt/pki/master
    timeout: 120

    file_roots:
      base:
        - /etc/salt

    pillar_roots:
      base:
        - /etc/salt/pillar

Create pillar directory if required - ``mkdir /etc/salt/pillar/``.

Define Proxy Minion pillar inventory
====================================

Pillar files located on Salt Master machine.

Add Nornir Inventory and proxy settings to file ``/etc/salt/pillar/nrp1.sls``::

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

Create top file ``/etc/salt/pillar/top.sls`` and add Proxy Minion pillar to base environment::

    base:
      nrp1:
        - nrp1

Start SALT Master
=================

Start or restart salt-master process to pick up updated configurations::

    systemctl restart salt-master
    systemctl status salt-master

Configure Proxy Minion
======================

Proxy Minion configuration files located on SALT Minion machine - machine where you installed
``salt-minion`` software. You only need to configure it once and all proxy-minion processes
will use it.

Backup original proxy configuration file - ``mv /etc/salt/proxy /etc/salt/proxy.old``.

Edit file ``/etc/salt/proxy`` to look like::

    master: 192.168.1.1 # IP address or FQDN of master machine e.g. localhost or master.lab
    multiprocessing: false # default, but overridden in Nornir proxy minion pillar
    mine_enabled: true # not required, but nice to have
    pki_dir: /etc/salt/pki/proxy # not required - this separates the proxy keys into a different directory
    log_level: debug # default is warning, adjust as required

Define Proxy Minion service in file ``/etc/systemd/system/salt-proxy@.service``::

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

.. warning:: beware that log level in above configuration set to ``debug`` that can log and expose
  sensitive data like device credentials and can consume significant amount of disk space over time.

Start Nornir Proxy Minion process
=================================

Run command to start Nornir Proxy Minion process::

    systemctl start salt-proxy@nrp1.service
    systemctl enable salt-proxy@nrp1.service
    systemctl status salt-proxy@nrp1.service

Or run in debug mode::

    salt-proxy --proxyid=nrp1 -l debug

To check proxy logs::

    tail -f /var/log/salt/proxy

Accept Proxy Minion key on master
=================================

Run command on salt master machine to view pending keys::

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
    salt nrp1 nr.nornir stats # check statistics for Nornir proxy minion
    salt nrp1 nr.nornir test # test task to verify module operation
    salt nrp1 nr.nornir inventory # to check Nornir inventory content
    salt nrp1 nr.task nr_test # test task to verify Nornir operation

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

Get show commands output from devices::

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

    [root@salt-master /]# salt nrp1 sys.doc nr.cfg
    nr.cfg:

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
        :param commit: (bool or dict) by default commit is ``True``. With ``netmiko`` plugin
            dictionary ``commit`` argument supplied to commit call using ``**commit``

        Warning: ``dry_run`` not supported by ``netmiko`` plugin

        Warning: ``commit`` not supported by ``scrapli`` plugin. To commit need to send commit
            command as part of configuration, moreover, scrapli will not exit configuration mode,
            need to send exit command as part of configuration mode as well.

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

Configure syslog server using ``nr.cfg`` with Netmiko::

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

Additional Resources
====================

Reference :ref:`salt_nornir_examples` section for more information on how to use Nornir Proxy Minion.

`SALTSTACK official documentation <https://docs.saltproject.io/en/latest/>`_

Collection of useful SALTSTACK resource `awesome-saltstack <https://github.com/hbokh/awesome-saltstack>`_
