FAQ
###

Collection of answers to Frequently Asked Question

.. contents:: :local:

How to refresh Nornir Proxy Pillar?
===================================

Calling ``pillar.refresh`` will not update running Nornir instance. Instead, after 
updating pillar on salt-master, to propagate updates to proxy-minion process either 
of these will work:

* restart Nornir proxy-minion process e.g. ``systemctl restart salt-proxy@nrp1.service``
* run ``salt nrp1 nr.refresh`` command to re-instantiate Nornir instance
* run ``salt nrp1 nr.restart`` command to restart Nornir proxy minion process

where ``nrp1`` - Nornir Proxy minion id/name.

How to target individual hosts behind nornir proxy minion?
==========================================================

To address individual hosts targeting, Nornir filtering capabilities utilized using additional 
filtering functions, reference nornir-salt module 
`FFun function <https://nornir-salt.readthedocs.io/en/latest/Functions.html#ffun>`_ for more 
information. But in short have to use ``Fx`` parameters to filter hosts, for example::

    # target only IOL1 and IOL2 hosts:
    salt nrp1 nr.cli "show clock" FB="IOL[12]"