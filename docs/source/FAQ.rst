FAQ
###

Collection of answers to Frequently Asked Question

.. contents:: :local:

How to refresh Nornir Proxy Pillar?
===================================

Calling ``pillar.refresh`` will not update running Nornir instance. Instead, after 
updating pillar on salt-master, to propagate updates to proxy-minion process either 
of these will work:

* restart Nornir proxy-minion process e.g. ``systemctl restart nrp1``
* run ``salt nrp1 nr.refresh`` command to re-instanticate Nornir instance
* run ``salt nrp1 nr.restart`` command to restart Nornir proxy minion process

