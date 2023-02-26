Salt Nornir Robot Library
=========================

``salt_nornir.salt_nornir_robot`` is a Robot Framework test library to 
use with Salt-Nornir.

Keywords
++++++++

* ``Minions`` - glob patterns of minions to target using Salt local 
  client ``cmd.run`` function, additional parameters can be passed 
  as key-word arguments
* ``Hosts`` - hosts to target, supports ``Fx`` filters as key-word
  arguments, by default expects a list of glob patterns to use with 
  ``FB`` filter
* ``nr.test`` - runs Salt-Nornir ``nr.test`` execution function with 
  provided arguments and key-word arguments

Examples
++++++++

This test suite runs two tests::

    *** Settings ***
    Library    salt_nornir.salt_nornir_robot
    
    *** Test Cases ***
    Test NTP
        Minions    nrp1    
        Hosts      ceos*
        nr.test    show clock    contains    local
        
    Test Software Version
        Minions    nrp1    
        Hosts      FM=arista_eos
        nr.test    show version    contains    7.3.2
    
to run it using ``robot`` command line tool::

    robot /path/to//salt_nornir_robot_suite.robot
    
